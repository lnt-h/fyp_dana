"""Curator API against the migrated, seeded Compose DB. Each test runs in one rolled-back
transaction (see ``admin_harness``), so nothing persists."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from admin_harness import AdminHarness, admin  # noqa: F401  (pytest fixture)
from sqlalchemy import func, select, text

from app.models.catalog import (
    CatalogAuditEvent,
    Place,
    Source,
    SourceRevision,
    WebPlaceCandidate,
)
from app.models.knowledge import KnowledgeChunk
from app.models.providers import ExternalPlaceIdentity

pytestmark = pytest.mark.integration

DA_NANG = {"latitude": 16.0544, "longitude": 108.2208}
REQUIRED_FACTS: dict[str, dict[str, Any]] = {
    "OPENING_HOURS": {"text": "07:00-17:30"},
    "ADMISSION_PRICE": {"amount": 0, "currency": "VND"},
    "ADDRESS_VI": {"text": "Đường Bạch Đằng, Hải Châu, Đà Nẵng"},
    "ENTRANCE_LOCATION": {"lat": 16.0545, "lng": 108.2209},
}


def _key() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


async def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, response.text
    return response.json()


async def _source_revision(h: AdminHarness) -> str:
    source = await _ok(
        await h.client.post(
            "/v1/admin/sources",
            json={
                "publisher": f"Sở Du lịch Đà Nẵng {uuid.uuid4().hex[:6]}",
                "source_kind": "OFFICIAL",
                "homepage_url": "https://example.gov.vn",
                "license_code": "ALL_RIGHTS_RESERVED",
                "attribution_text": "Sở Du lịch thành phố Đà Nẵng",
            },
        ),
        201,
    )
    revision = await _ok(
        await h.client.post(
            f"/v1/admin/sources/{source['id']}/revisions",
            json={
                "locator": "https://example.gov.vn/diem-den/1",
                "title": "Điểm đến",
                "retrieved_at": datetime.now(UTC).isoformat(),
            },
        ),
        201,
    )
    return str(revision["id"])


async def _create_place(h: AdminHarness, **extra: Any) -> dict[str, Any]:
    slug = f"it-place-{uuid.uuid4().hex[:10]}"
    body: dict[str, Any] = {"slug": slug, "location": DA_NANG, **extra}
    return await _ok(await h.client.post("/v1/admin/candidates", json=body), 201)


async def test_place_lifecycle_gate_publish_unpublish(admin: AdminHarness) -> None:  # noqa: F811
    h = admin
    source_revision_id = await _source_revision(h)
    created = await _create_place(
        h,
        localizations=[
            {"locale": "vi", "name": "Cầu Rồng", "description": "Cây cầu hình rồng."},
            {"locale": "en", "name": "Dragon Bridge", "description": "A dragon-shaped bridge."},
        ],
        aliases=[{"locale": "vi", "alias": "Cầu Rồng", "alias_kind": "NAME"}],
    )
    place_id = created["id"]
    assert created["workflow_state"] == "CONTENT_REVIEW"
    codes = {v["code"] for v in created["gate_violations"]}
    assert {"PLACE_NOT_READY", "MISSING_LOCALIZATION", "MISSING_REQUIRED_FACT"} <= codes

    refused = await h.client.post(
        f"/v1/admin/candidates/{place_id}/publish",
        json={"expected_content_revision": created["content_revision"]},
        headers=_key(),
    )
    assert refused.status_code == 422
    error = refused.json()["error"]
    assert error["code"] == "publication_incomplete"
    assert {m["code"] for m in error["context"]["missing"]} == codes

    stale = await h.client.patch(
        f"/v1/admin/candidates/{place_id}",
        json={"expected_content_revision": created["content_revision"] + 5},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["context"]["current_revision"] == created["content_revision"]

    loc_ids = {loc["locale"]: loc["id"] for loc in created["localizations"]}
    reviewed = await _ok(
        await h.client.patch(
            f"/v1/admin/candidates/{place_id}",
            json={
                "expected_content_revision": created["content_revision"],
                "category_code": "HERITAGE",
                "area_code": "da-nang-center",
                "visit_minutes_min": 20,
                "visit_minutes_suggested": 40,
                "visit_minutes_max": 90,
                "has_no_media": True,
                "workflow_state": "READY_TO_PUBLISH",
                "localizations": [
                    {"id": loc_ids["vi"], "locale": "vi", "review_state": "APPROVED"},
                    {"id": loc_ids["en"], "locale": "en", "review_state": "APPROVED"},
                ],
                "aliases": [
                    {
                        "locale": "vi",
                        "alias": "Cầu Rồng",
                        "alias_kind": "NAME",
                        "review_state": "APPROVED",
                    },
                    {
                        "locale": "en",
                        "alias": "Dragon Bridge",
                        "alias_kind": "NAME",
                        "review_state": "APPROVED",
                    },
                ],
            },
        )
    )
    assert reviewed["content_revision"] == created["content_revision"] + 1
    assert {v["code"] for v in reviewed["gate_violations"]} == {"MISSING_REQUIRED_FACT"}
    assert {a["alias_normalized"] for a in reviewed["aliases"]} == {"cau rong", "dragon bridge"}

    for field_code, value in REQUIRED_FACTS.items():
        fact = await _ok(
            await h.client.post(
                f"/v1/admin/places/{place_id}/facts",
                json={
                    "field_code": field_code,
                    "knowledge_state": "KNOWN",
                    "value": value,
                    "evidence": [
                        {"source_revision_id": source_revision_id, "supported_claim": "page"}
                    ],
                },
            ),
            201,
        )
        assert fact["review_state"] == "DRAFT"
        approved = await _ok(
            await h.client.post(
                f"/v1/admin/places/{place_id}/facts/{fact['id']}/review",
                json={"decision": "APPROVE"},
            )
        )
        assert approved["review_state"] == "APPROVED"
        assert approved["verified_at"] is not None

    # A second revision of one fact supersedes the first on approval.
    second = await _ok(
        await h.client.post(
            f"/v1/admin/places/{place_id}/facts",
            json={
                "field_code": "OPENING_HOURS",
                "knowledge_state": "KNOWN",
                "value": {"text": "07:00-18:00"},
                "evidence": [{"source_revision_id": source_revision_id, "supported_claim": "p"}],
            },
        ),
        201,
    )
    assert second["fact_revision"] == 2
    await _ok(
        await h.client.post(
            f"/v1/admin/places/{place_id}/facts/{second['id']}/review",
            json={"decision": "APPROVE"},
        )
    )
    hours = await _ok(
        await h.client.get(f"/v1/admin/places/{place_id}/facts?field_code=OPENING_HOURS")
    )
    assert [f["review_state"] for f in hours["items"]] == ["APPROVED", "SUPERSEDED"]
    frozen = await h.client.patch(
        f"/v1/admin/places/{place_id}/facts/{second['id']}", json={"value": {"text": "x"}}
    )
    assert frozen.status_code == 409

    # An approved chunk (embedded on write) is pinned by the publication.
    h.embedder.enabled = True
    chunk = await _ok(
        await h.client.post(
            f"/v1/admin/places/{place_id}/chunks",
            json={
                "locale": "vi",
                "section": "OVERVIEW",
                "content": "Cầu Rồng bắc qua sông Hàn.",
                "source_revision_ids": [source_revision_id],
                "review_state": "APPROVED",
            },
        ),
        201,
    )
    assert chunk["embedding_state"] == "EMBEDDED"
    assert chunk["review_state"] == "APPROVED"
    assert chunk["corpus_revision"] == 1

    detail = await _ok(await h.client.get(f"/v1/admin/candidates/{place_id}"))
    assert detail["gate_violations"] == []
    assert detail["gate_missing_count"] == 0

    publication = await _ok(
        await h.client.post(
            f"/v1/admin/candidates/{place_id}/publish",
            json={"expected_content_revision": detail["content_revision"]},
            headers=_key(),
        ),
        201,
    )
    assert publication["state"] == "PUBLISHED"
    assert publication["publication_revision"] == 1
    assert publication["corpus_revision"] == 1
    published = (
        await h.session.execute(
            text("SELECT name_vi, name_en FROM vw_published_places WHERE place_id = :id"),
            {"id": place_id},
        )
    ).all()
    assert [tuple(row) for row in published] == [("Cầu Rồng", "Dragon Bridge")]

    # Editing the pinned corpus opens revision 2; the published revision stays 1.
    edited = await _ok(
        await h.client.patch(
            f"/v1/admin/places/{place_id}/chunks/{chunk['id']}",
            json={"content": "Cầu Rồng bắc qua sông Hàn, phun lửa cuối tuần."},
        )
    )
    assert edited["corpus_revision"] == 2
    assert edited["id"] != chunk["id"]
    assert edited["review_state"] == "DRAFT"
    chunks = await _ok(await h.client.get(f"/v1/admin/places/{place_id}/chunks"))
    assert chunks["corpus_revision"] == 2
    assert chunks["published_corpus_revision"] == 1

    summary = await _ok(await h.client.get("/v1/admin/cities/summary"))
    da_nang = next(item for item in summary["items"] if item["code"] == "da-nang")
    assert da_nang["published_count"] >= 1

    listed = await _ok(await h.client.get("/v1/admin/candidates?q=cau%20rong&limit=50"))
    assert place_id in {item["id"] for item in listed["items"]}

    withdrawn = await _ok(
        await h.client.post(
            f"/v1/admin/places/{place_id}/unpublish",
            json={"state_reason": "integration test"},
            headers=_key(),
        )
    )
    assert withdrawn["state"] == "WITHDRAWN"
    assert withdrawn["state_reason"] == "integration test"
    remaining = await h.session.scalar(
        text("SELECT count(*) FROM vw_published_places WHERE place_id = :id"), {"id": place_id}
    )
    assert remaining == 0
    again = await h.client.post(
        f"/v1/admin/places/{place_id}/unpublish", json={"state_reason": "x"}, headers=_key()
    )
    assert again.status_code == 409

    actions = set(
        (
            await h.session.scalars(
                select(CatalogAuditEvent.action).where(
                    CatalogAuditEvent.entity_id.in_(
                        [uuid.UUID(place_id), uuid.UUID(publication["id"])]
                    )
                )
            )
        ).all()
    )
    assert {"CONTENT_REVIEW", "PUBLISH", "WITHDRAW"} <= actions
    publish_events = await h.session.scalar(
        select(func.count())
        .select_from(CatalogAuditEvent)
        .where(
            CatalogAuditEvent.entity_id == uuid.UUID(publication["id"]),
            CatalogAuditEvent.action == "PUBLISH",
        )
    )
    assert publish_events == 1


async def _web_candidate(h: AdminHarness, **extra: Any) -> WebPlaceCandidate:
    city_id = await h.session.scalar(text("SELECT id FROM cities WHERE code = 'da-nang'"))
    source = Source(
        publisher=f"blog-{uuid.uuid4().hex[:6]}.example",
        source_kind="WEB",
        license_code="UNKNOWN",
    )
    h.session.add(source)
    await h.session.flush()
    revision = SourceRevision(
        source_id=source.id,
        locator=f"https://blog.example/{uuid.uuid4().hex}",
        retrieved_at=datetime.now(UTC),
    )
    h.session.add(revision)
    await h.session.flush()
    candidate = WebPlaceCandidate(
        city_id=city_id,
        name="Bánh xèo Bà Dưỡng",
        source_revision_id=revision.id,
        fetched_at=datetime.now(UTC),
        extraction={"hours": {"text": "9-21", "quote": "open 9am"}},
        **extra,
    )
    h.session.add(candidate)
    await h.session.commit()
    return candidate


async def test_web_candidate_approve_and_reject(admin: AdminHarness) -> None:  # noqa: F811
    h = admin
    gpid = f"it-gpid-{uuid.uuid4().hex}"
    pending = await _web_candidate(
        h,
        category_guess="food",
        google_place_id=gpid,
        places_check_outcome="EXISTS_OPERATIONAL",
        places_checked_at=datetime.now(UTC),
    )
    listed = await _ok(await h.client.get("/v1/admin/web-candidates?review_state=PENDING&limit=50"))
    assert any(item["id"] == str(pending.id) for item in listed["items"])
    one = await _ok(await h.client.get(f"/v1/admin/web-candidates/{pending.id}"))
    assert one["trust_label"] == "WEB_UNVERIFIED"
    assert one["source_locator"].startswith("https://blog.example/")

    no_location = await h.client.patch(
        f"/v1/admin/web-candidates/{pending.id}", json={"decision": "APPROVE"}
    )
    assert no_location.status_code == 422
    assert no_location.json()["error"]["code"] == "location_required"

    promoted = await _ok(
        await h.client.patch(
            f"/v1/admin/web-candidates/{pending.id}",
            json={"decision": "APPROVE", "location": DA_NANG, "name_en": "Ba Duong pancakes"},
        )
    )
    assert promoted["review_state"] == "PROMOTED"
    assert promoted["reviewed_at"] is not None
    place_id = uuid.UUID(promoted["promoted_place_id"])
    place = await h.session.get(Place, place_id)
    assert place is not None
    assert place.workflow_state == "IMPORTED"
    assert place.category_code == "FOOD"
    assert place.slug.startswith("banh-xeo-ba-duong")
    identity = await h.session.scalar(
        select(ExternalPlaceIdentity).where(ExternalPlaceIdentity.place_id == place_id)
    )
    assert identity is not None and identity.upstream_id == gpid
    detail = await _ok(await h.client.get(f"/v1/admin/candidates/{place_id}"))
    assert {
        (loc["locale"], loc["translation_origin"], loc["review_state"])
        for loc in detail["localizations"]
    } == {("vi", "AI_DRAFT", "DRAFT"), ("en", "AI_DRAFT", "DRAFT")}
    assert detail["has_ai_draft"] is True
    published = await h.session.scalar(
        text("SELECT count(*) FROM catalog_publications WHERE place_id = :id"), {"id": place_id}
    )
    assert published == 0

    # AI drafts need explicit confirmation before approval (FR-019).
    vi = next(loc for loc in detail["localizations"] if loc["locale"] == "vi")
    unconfirmed = await h.client.patch(
        f"/v1/admin/candidates/{place_id}",
        json={
            "expected_content_revision": detail["content_revision"],
            "localizations": [
                {
                    "locale": "vi",
                    "name": "Bánh xèo Bà Dưỡng",
                    "description": "Quán bánh xèo.",
                    "translation_origin": "AI_DRAFT",
                    "review_state": "APPROVED",
                }
            ],
        },
    )
    assert unconfirmed.status_code == 422
    assert unconfirmed.json()["error"]["code"] == "ai_draft_unconfirmed"
    assert vi["review_state"] == "DRAFT"

    twice = await h.client.patch(
        f"/v1/admin/web-candidates/{pending.id}",
        json={"decision": "REJECT", "review_note": "dup"},
    )
    assert twice.status_code == 409

    other = await _web_candidate(h)
    missing_note = await h.client.patch(
        f"/v1/admin/web-candidates/{other.id}", json={"decision": "REJECT"}
    )
    assert missing_note.status_code == 422
    rejected = await _ok(
        await h.client.patch(
            f"/v1/admin/web-candidates/{other.id}",
            json={"decision": "REJECT", "review_note": "Permanently closed per curator visit"},
        )
    )
    assert rejected["review_state"] == "REJECTED"
    assert rejected["promoted_place_id"] is None
    events = (
        await h.session.scalars(
            select(CatalogAuditEvent.action).where(
                CatalogAuditEvent.entity_id.in_([pending.id, other.id])
            )
        )
    ).all()
    assert sorted(events) == ["WEB_PROMOTE", "WEB_REJECT"]


async def test_closure_rule_crud(admin: AdminHarness) -> None:  # noqa: F811
    h = admin
    place = await _create_place(h)
    base = f"/v1/admin/places/{place['id']}/closure-rules"
    rule = await _ok(
        await h.client.post(
            base,
            json={
                "rule_kind": "WEEKLY",
                "effect": "CLOSED",
                "params": {"weekdays": [1]},
                "note_vi": "Đóng cửa thứ Hai",
                "note_en": "Closed on Mondays",
            },
        ),
        201,
    )
    assert rule["applies_to"] == "PLACE"
    assert rule["severity"] == "BLOCKING"
    assert rule["review_state"] == "DRAFT"

    bad_payloads: list[dict[str, Any]] = [
        {"rule_kind": "MONTHLY", "effect": "CLOSED", "note_vi": "x", "note_en": "x"},
        {
            "rule_kind": "WEEKLY",
            "effect": "SHUT",
            "params": {"weekdays": [1]},
            "note_vi": "x",
            "note_en": "x",
        },
        {
            "rule_kind": "WEEKLY",
            "effect": "CLOSED",
            "params": {"weekdays": [8]},
            "note_vi": "x",
            "note_en": "x",
        },
        {
            "rule_kind": "WEEKLY",
            "effect": "CLOSED",
            "params": {"weekdays": [1]},
            "note_vi": "",
            "note_en": "x",
        },
        {
            "rule_kind": "DATE",
            "effect": "NOTICE",
            "params": {"dates": ["2027-02-06"]},
            "note_vi": "x",
            "note_en": "x",
            "effective_from": "2027-03-01",
            "effective_to": "2027-01-01",
        },
        {
            "rule_kind": "WEEKLY",
            "effect": "CLOSED",
            "params": {"weekdays": [1]},
            "note_vi": "x",
            "note_en": "x",
            "applies_to": "CITY",
        },
    ]
    for payload in bad_payloads:
        response = await h.client.post(base, json=payload)
        assert response.status_code == 422, payload

    rule_url = f"/v1/admin/closure-rules/{rule['id']}"
    no_source = await h.client.patch(rule_url, json={"review_state": "APPROVED"})
    assert no_source.status_code == 422
    source_revision_id = await _source_revision(h)
    approved = await _ok(
        await h.client.patch(
            rule_url,
            json={"source_revision_id": source_revision_id, "review_state": "APPROVED"},
        )
    )
    assert approved["review_state"] == "APPROVED"
    assert approved["verified_at"] is not None
    assert approved["reviewed_by_account_id"] is not None
    frozen = await h.client.patch(rule_url, json={"note_en": "changed"})
    assert frozen.status_code == 409
    assert (await h.client.delete(rule_url)).status_code == 409
    retired = await _ok(await h.client.patch(rule_url, json={"review_state": "RETIRED"}))
    assert retired["review_state"] == "RETIRED"

    tet = await _ok(
        await h.client.post(
            "/v1/admin/closure-rules",
            json={
                "applies_to": "CITY",
                "rule_kind": "LUNAR_DATE",
                "effect": "PARTIAL",
                "params": {"lunar_days": [1, 2, 3], "lunar_months": [1]},
                "note_vi": "Nhiều nơi đóng cửa dịp Tết",
                "note_en": "Many places close during Tết",
            },
        ),
        201,
    )
    assert tet["severity"] == "WARNING"
    area = await h.client.post(
        "/v1/admin/closure-rules",
        json={
            "applies_to": "AREA",
            "area_code": "nowhere",
            "rule_kind": "SEASON",
            "effect": "NOTICE",
            "params": {"from_month_day": "09-01", "to_month_day": "12-31"},
            "note_vi": "Mùa mưa",
            "note_en": "Rainy season",
        },
    )
    assert area.status_code == 422
    listed = await _ok(await h.client.get(base))
    assert [item["id"] for item in listed["items"]] == [rule["id"]]
    tet_url = f"/v1/admin/closure-rules/{tet['id']}"
    assert (await h.client.delete(tet_url)).status_code == 204
    assert (await h.client.get(tet_url)).status_code == 404


async def test_chunk_without_embedder_stores_null_embedding(admin: AdminHarness) -> None:  # noqa: F811
    h = admin
    place = await _create_place(h)
    source_revision_id = await _source_revision(h)
    url = f"/v1/admin/places/{place['id']}/chunks"
    saved = await _ok(
        await h.client.post(
            url,
            json={
                "locale": "en",
                "section": "HISTORY",
                "content": "Built in the 16th century by Japanese merchants.",
                "source_revision_ids": [source_revision_id],
                "review_state": "APPROVED",
            },
        ),
        201,
    )
    assert saved["embedding_state"] == "PENDING"
    assert saved["review_state"] == "DRAFT"
    assert {w["code"] for w in saved["warnings"]} == {
        "CHUNK_EMBEDDING_PENDING",
        "CHUNK_APPROVAL_DEFERRED",
    }
    row = await h.session.get(KnowledgeChunk, uuid.UUID(saved["id"]))
    assert row is not None
    assert row.embedding is None and row.embedding_model is None
    backfill = await h.session.scalar(
        select(func.count())
        .select_from(KnowledgeChunk)
        .where(
            KnowledgeChunk.id == row.id,
            KnowledgeChunk.embedding.is_(None),
            KnowledgeChunk.review_state != "RETIRED",
        )
    )
    assert backfill == 1

    refused = await h.client.patch(f"{url}/{saved['id']}", json={"review_state": "APPROVED"})
    assert refused.status_code == 422
    assert refused.json()["error"]["code"] == "chunk_embedding_pending"

    h.embedder.enabled = True
    approved = await _ok(
        await h.client.patch(f"{url}/{saved['id']}", json={"review_state": "APPROVED"})
    )
    assert approved["embedding_state"] == "EMBEDDED"
    assert approved["review_state"] == "APPROVED"
    assert approved["warnings"] == []

    unknown_source = await h.client.post(
        url,
        json={
            "locale": "vi",
            "section": "HISTORY",
            "content": "x",
            "source_revision_ids": [str(uuid.uuid4())],
        },
    )
    assert unknown_source.status_code == 422
    assert unknown_source.json()["error"]["code"] == "unknown_source_revision"
