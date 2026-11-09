# ruff: noqa: E501
"""Automated content pipeline against the Compose database (DEC-022).

Each test runs in one outer transaction that is rolled back: services commit their own unit of
work, which only releases a savepoint (``join_transaction_mode="create_savepoint"``). Fixture
data uses Wikidata IDs and slugs that cannot collide with live imports in the dev database.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.curation.auto_publish import PublishReport, auto_publish
from app.curation.embedding import Embedding
from app.curation.operator import OperatorService
from app.curation.web_promotion import promote_web_candidate_if_eligible
from app.ingestion.calendar import load_calendar
from app.ingestion.common import (
    PolicyNotActiveError,
    get_or_create_revision,
    get_or_create_source,
    load_city,
)
from app.ingestion.policies import activate_policy
from app.ingestion.sheet import import_sheet_text
from app.ingestion.wikidata import WikidataItem, stage_items
from app.ingestion.wikipedia import PageSummary, stage_summaries
from app.models.catalog import CatalogPublication, Place, PlaceClosureRule, WebPlaceCandidate
from app.models.providers import DataProvider, ProviderPolicy
from app.schemas.admin import UnpublishRequest

pytestmark = pytest.mark.integration

CITY = "da-nang"


class FakeEmbedder:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def embed(self, text: str) -> Embedding | None:
        self.calls.append(text)
        return Embedding(vector=[1.0] + [0.0] * 767, model="gemini-embedding-001")


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    db = AsyncSession(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    try:
        yield db
    finally:
        await db.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


def _qid() -> str:
    return f"Q9{uuid.uuid4().int % 10**9:09d}"


def _item(
    qid: str,
    *,
    lng: float = 108.3262,
    lat: float = 15.8771,
    labels: dict[str, str] | None = None,
    category: str | None = "HERITAGE",
) -> WikidataItem:
    names = labels if labels is not None else {"vi": f"Chùa thử {qid}", "en": f"Test pagoda {qid}"}
    return WikidataItem(
        qid=qid,
        lng=lng,
        lat=lat,
        labels=names,
        descriptions={locale: f"desc {locale}" for locale in names},
        aliases={"vi": [f"Bí danh {qid}"]},
        sitelinks={locale: f"Title {qid} {locale}" for locale in names},
        class_labels=("covered bridge",),
        category=category,
    )


async def _activate(session: AsyncSession, *keys: str) -> None:
    for key in keys:
        await activate_policy(session, key, f"test terms {key}")


async def _place_id(session: AsyncSession, qid: str) -> uuid.UUID:
    place_id = await session.scalar(
        text(
            "SELECT i.place_id FROM external_place_identities i "
            "JOIN data_providers d ON d.id = i.data_provider_id "
            "WHERE d.provider_key = 'wikidata' AND i.upstream_id = :qid"
        ),
        {"qid": qid},
    )
    assert place_id is not None
    return uuid.UUID(str(place_id))


async def _summaries(session: AsyncSession, qid: str, locales: Sequence[str]) -> None:
    place_id = await _place_id(session, qid)
    await stage_summaries(
        session,
        city_code=CITY,
        summaries=[
            PageSummary(
                place_id=place_id,
                locale=locale,
                title=f"Title {qid} {locale}",
                page_url=f"https://{locale}.wikipedia.org/wiki/Title_{qid}",
                summary=f"Summary of {qid} in {locale}. This lead is long enough to pass the 80-character stub check for a description.",
                revision="1",
            )
            for locale in locales
        ],
    )


async def _publish(
    session: AsyncSession, place_ids: Sequence[uuid.UUID], **kwargs: object
) -> PublishReport:
    return await auto_publish(
        session,
        city_code=CITY,
        embedder=FakeEmbedder(),
        place_ids=list(place_ids),
        **kwargs,  # type: ignore[arg-type]
    )


async def test_importers_refuse_without_active_policy(session: AsyncSession) -> None:
    await session.execute(
        update(ProviderPolicy)
        .where(
            ProviderPolicy.data_provider_id
            == select(DataProvider.id)
            .where(DataProvider.provider_key == "wikidata")
            .scalar_subquery()
        )
        .values(status="RETIRED")
    )
    with pytest.raises(PolicyNotActiveError):
        await stage_items(session, city_code=CITY, items=[_item(_qid())], policy_key="wikidata")


async def test_policy_activation_is_idempotent(session: AsyncSession) -> None:
    first = await activate_policy(session, "gonarra_sheet", "owner sheet v1")
    again = await activate_policy(session, "gonarra_sheet", "owner sheet v1")
    assert "ACTIVE" in first and "already ACTIVE" in again
    newer = await activate_policy(session, "gonarra_sheet", "owner sheet v2")
    assert "terms 'owner sheet v2'" in newer
    statuses = (
        await session.execute(
            select(ProviderPolicy.policy_revision, ProviderPolicy.status)
            .join(DataProvider, DataProvider.id == ProviderPolicy.data_provider_id)
            .where(DataProvider.provider_key == "gonarra_sheet")
            .order_by(ProviderPolicy.policy_revision)
        )
    ).all()
    assert [status for _, status in statuses].count("ACTIVE") == 1
    with pytest.raises(ValueError):
        await activate_policy(session, "no_such_provider", "x")


async def test_import_auto_publish_and_idempotency(session: AsyncSession) -> None:
    await _activate(session, "wikidata", "wikipedia")
    good, vi_only = _qid(), _qid()
    report = await stage_items(
        session,
        city_code=CITY,
        items=[
            _item(good),
            _item(vi_only, labels={"vi": "Chỉ có tiếng Việt"}, lng=108.2779, lat=16.1003),
            _item(_qid(), lng=106.70, lat=10.77),  # Hồ Chí Minh City: outside the boundary
            _item(_qid(), category=None),  # unmapped class: skipped
        ],
        policy_key="wikidata",
    )
    assert (report.accepted, report.rejected, report.unmapped) == (2, 1, 1)
    assert report.rejection_reasons == {"OUTSIDE_CITY": 1}
    again = await stage_items(
        session,
        city_code=CITY,
        items=[
            _item(good),
            _item(vi_only, labels={"vi": "Chỉ có tiếng Việt"}, lng=108.2779, lat=16.1003),
            _item(_qid(), lng=106.70, lat=10.77),
        ],
        policy_key="wikidata",
    )
    assert again.created_places == 0  # keyed by external identity
    await _summaries(session, good, ["vi", "en"])
    good_id, vi_only_id = await _place_id(session, good), await _place_id(session, vi_only)

    first = await _publish(session, [good_id, vi_only_id])
    outcome = {o.place_id: o for o in first.outcomes}
    assert outcome[good_id].status == "published"
    assert outcome[good_id].area_code == "hoi-an-old-town"
    # DEC-033 (option A): descriptions are optional at the gate. A VI-only place publishes with the
    # VI proper name reused as the EN name and no description; the card shows "No description yet".
    assert outcome[vi_only_id].status == "published"
    assert outcome[vi_only_id].description_sources == {"vi": None, "en": None}
    vi_row = (
        await session.execute(
            text(
                "SELECT name_en, description_vi, description_en FROM vw_published_places"
                " WHERE place_id = :id"
            ),
            {"id": vi_only_id},
        )
    ).one()
    assert vi_row[0] == "Chỉ có tiếng Việt" and vi_row[1] is None and vi_row[2] is None

    row = (
        await session.execute(
            text(
                "SELECT name_vi, name_en, description_vi, description_en, corpus_revision "
                "FROM vw_published_places WHERE place_id = :id"
            ),
            {"id": good_id},
        )
    ).one()
    assert row[0] == f"Chùa thử {good}" and row[1] == f"Test pagoda {good}"
    assert (
        row[2]
        == f"Summary of {good} in vi. This lead is long enough to pass the 80-character stub check for a description."
        and row[4] is not None
    )
    facts = (
        await session.execute(
            text(
                "SELECT field_code, knowledge_state, jsonb_array_length(sources) "
                "FROM vw_published_place_facts WHERE place_id = :id ORDER BY field_code"
            ),
            {"id": good_id},
        )
    ).all()
    assert {f[0] for f in facts} == {
        "ADDRESS_VI",
        "ADMISSION_PRICE",
        "ENTRANCE_LOCATION",
        "OPENING_HOURS",
    }
    assert all(f[1] == "UNKNOWN" and f[2] == 1 for f in facts)
    chunks = await session.scalar(
        text("SELECT count(*) FROM vw_guide_chunks WHERE place_id = :id"), {"id": good_id}
    )
    assert chunks == 2
    publisher = await session.scalar(
        text(
            "SELECT a.clerk_user_id FROM catalog_publications cp JOIN accounts a "
            "ON a.id = cp.published_by_account_id WHERE cp.place_id = :id"
        ),
        {"id": good_id},
    )
    assert publisher == "system:gonarra-pipeline"

    second = await _publish(session, [good_id, vi_only_id])
    assert {o.place_id: o.status for o in second.outcomes}[good_id] == "unchanged"
    revisions = await session.scalar(
        select(func.count())
        .select_from(CatalogPublication)
        .where(CatalogPublication.place_id == good_id)
    )
    assert revisions == 1

    # A changed upstream description re-publishes exactly once.
    await stage_summaries(
        session,
        city_code=CITY,
        summaries=[
            PageSummary(
                good_id,
                "en",
                f"Title {good} en",
                f"https://en.wikipedia.org/wiki/T_{good}",
                "A new summary. This lead is long enough to pass the 80-character stub check for a description.",
                "2",
            ),
            PageSummary(
                good_id,
                "vi",
                f"Title {good} vi",
                f"https://vi.wikipedia.org/wiki/T_{good}",
                f"Summary of {good} in vi. This lead is long enough to pass the 80-character stub check for a description.",
                "1",
            ),
        ],
    )
    third = await _publish(session, [good_id])
    assert third.outcomes[0].status == "published"
    states = (
        await session.scalars(
            select(CatalogPublication.state)
            .where(CatalogPublication.place_id == good_id)
            .order_by(CatalogPublication.publication_revision)
        )
    ).all()
    assert states == ["SUPERSEDED", "PUBLISHED"]

    # Dry run writes nothing.
    dry = await _publish(session, [good_id], dry_run=True)
    assert dry.outcomes[0].status == "would_publish"


async def test_gate_rejects_out_of_boundary_and_withdraws(session: AsyncSession) -> None:
    await _activate(session, "wikidata", "wikipedia")
    qid = _qid()
    await stage_items(session, city_code=CITY, items=[_item(qid)], policy_key="wikidata")
    await _summaries(session, qid, ["vi", "en"])
    place_id = await _place_id(session, qid)
    assert (await _publish(session, [place_id])).outcomes[0].status == "published"
    # Shrink the city boundary (rolled back) so the place now lies outside it.
    await session.execute(
        text(
            "UPDATE cities SET boundary = ST_GeogFromText("
            "'SRID=4326;MULTIPOLYGON(((108.0 16.0, 108.1 16.0, 108.1 16.1, 108.0 16.1, 108.0 16.0)))') "
            "WHERE code = :code"
        ),
        {"code": CITY},
    )
    report = await _publish(session, [place_id])
    assert report.outcomes[0].status == "withdrawn_by_gate"
    assert report.outcomes[0].reasons == ["OUTSIDE_CITY"]
    state = await session.scalar(
        select(CatalogPublication.state)
        .where(CatalogPublication.place_id == place_id)
        .order_by(CatalogPublication.publication_revision.desc())
        .limit(1)
    )
    assert state == "WITHDRAWN"


SHEET_HEADER = (
    "slug,category_code,area_code,lat,lng,name_vi,name_en,short_description_vi,"
    "short_description_en,description_vi,description_en,source_url,source_publisher,licence,"
    "opening_hours,opening_hours_source_url,ticket_price,ticket_price_source_url\n"
)


async def test_sheet_import_known_facts_and_missing_licence(session: AsyncSession) -> None:
    await _activate(session, "gonarra_sheet")
    suffix = uuid.uuid4().hex[:8]
    sheet = SHEET_HEADER + (
        f"test-an-bang-{suffix},BEACH,,15.9135,108.3415,Biển An Bàng,An Bang Beach,"
        "Bãi biển yên tĩnh,Quiet beach,Mô tả tiếng Việt.,English description.,"
        "https://example.org/an-bang,Example Travel Board,CC-BY-4.0,"
        "daily 00:00-24:00,https://example.org/an-bang/hours,Miễn phí,https://example.org/an-bang/fees\n"
        f"test-no-licence-{suffix},BEACH,,15.8890,108.3670,Biển Cửa Đại,Cua Dai Beach,"
        "Bãi biển,Beach,Mô tả.,Description.,https://example.org/cua-dai,Example Blog,,,,,\n"
    )
    report = await import_sheet_text(session, city_code=CITY, text=sheet, release_id=f"t-{suffix}")
    assert report.accepted == 2
    again = await import_sheet_text(session, city_code=CITY, text=sheet, release_id=f"t-{suffix}")
    assert again.skipped_unchanged
    ids = {
        slug: pid
        for slug, pid in (
            await session.execute(
                select(Place.slug, Place.id).where(Place.slug.like(f"test-%-{suffix}"))
            )
        ).all()
    }
    result = await _publish(session, list(ids.values()))
    outcome = {o.slug: o for o in result.outcomes}
    published = outcome[f"test-an-bang-{suffix}"]
    assert published.status == "published" and published.area_code == "hoi-an-beaches-islands"
    rejected = outcome[f"test-no-licence-{suffix}"]
    assert rejected.status == "rejected"
    assert rejected.reasons == ["MISSING_LICENCE:Example Blog"]
    facts = dict(
        (
            await session.execute(
                text(
                    "SELECT field_code, value FROM vw_published_place_facts "
                    "WHERE place_id = :id AND knowledge_state = 'KNOWN'"
                ),
                {"id": ids[f"test-an-bang-{suffix}"]},
            )
        ).all()
    )
    assert facts["OPENING_HOURS"]["weekly"]["7"] == [["00:00", "24:00"]]
    assert facts["ADMISSION_PRICE"] == {"text": "Miễn phí"}


async def test_unpublish_is_respected_by_the_pipeline(session: AsyncSession) -> None:
    await _activate(session, "wikidata", "wikipedia")
    qid = _qid()
    await stage_items(session, city_code=CITY, items=[_item(qid)], policy_key="wikidata")
    await _summaries(session, qid, ["vi", "en"])
    place_id = await _place_id(session, qid)
    await _publish(session, [place_id])
    owner = await session.scalar(text("SELECT id FROM accounts LIMIT 1"))
    withdrawn = await OperatorService(session).unpublish(
        place_id, UnpublishRequest(state_reason="owner takedown"), uuid.UUID(str(owner))
    )
    assert withdrawn.state == "WITHDRAWN"
    report = await _publish(session, [place_id])
    assert report.outcomes[0].status == "withdrawn"
    forced = await _publish(session, [place_id], include_withdrawn=True)
    assert forced.outcomes[0].status == "published"


async def test_closure_rules_load_is_idempotent(session: AsyncSession, tmp_path: Path) -> None:
    first = await load_calendar(session, city_code=CITY)
    second = await load_calendar(session, city_code=CITY)
    assert first.loaded == second.loaded >= 5
    assert second.inserted == 0 and second.retired == 0
    assert second.unchanged == second.loaded
    rules = (
        await session.scalars(
            select(PlaceClosureRule).where(
                PlaceClosureRule.review_state == "APPROVED",
                PlaceClosureRule.area_code == "hoi-an-old-town",
            )
        )
    ).all()
    assert {r.rule_kind for r in rules} >= {"LUNAR_DATE", "TICKET_VALIDITY", "WEEKLY"}
    assert all(r.reviewed_by_account_id is not None and r.verified_at for r in rules)
    # Removing a rule from the file retires it.
    smaller = tmp_path / "da-nang.yaml"
    smaller.write_text(
        "city: da-nang\nrules:\n  - applies_to: CITY\n    rule_kind: LUNAR_DATE\n"
        "    effect: NOTICE\n    severity: WARNING\n    params: {lunar_days: [1, 2, 3], lunar_months: [1]}\n"
        '    note_vi: "Mùng 1–3 Tết Nguyên Đán: giờ mở cửa thay đổi, nên kiểm tra trước khi đi."\n'
        '    note_en: "First three days of the Lunar New Year: opening hours change; check before you go."\n',
        encoding="utf-8",
    )
    third = await load_calendar(session, city_code=CITY, path=smaller)
    assert third.retired >= first.loaded - 1


async def test_web_candidate_promotion(session: AsyncSession) -> None:
    city = await load_city(session, CITY)
    source = await get_or_create_source(
        session,
        data_provider_id=None,
        publisher="example.org",
        source_kind="WEB",
        license_code="UNKNOWN",
        attribution_text=None,
    )
    revision = await get_or_create_revision(
        session,
        source_id=source.id,
        locator=f"https://example.org/{uuid.uuid4()}",
        content_sha256="0" * 64,
        title="page",
    )
    now = datetime.now(UTC)

    def candidate(outcome: str, lng: float, lat: float) -> WebPlaceCandidate:
        return WebPlaceCandidate(
            city_id=city.id,
            name="Quán thử",
            name_vi="Quán thử",
            name_en="Test eatery",
            category_guess="food",
            location=f"SRID=4326;POINT({lng} {lat})",
            coordinate_source="WEB_PAGE",
            google_place_id=None if outcome == "NOT_FOUND" else f"gp-{uuid.uuid4()}",
            places_check_outcome=outcome,
            places_checked_at=now,
            source_revision_id=revision.id,
            fetched_at=now,
        )

    eligible = candidate("EXISTS_OPERATIONAL", 108.2236, 16.0606)
    closed = candidate("EXISTS_CLOSED", 108.2236, 16.0606)
    missing = candidate("NOT_FOUND", 108.2236, 16.0606)
    session.add_all([eligible, closed, missing])
    await session.flush()
    promoted = await promote_web_candidate_if_eligible(session, eligible.id)
    assert promoted.promoted and promoted.place_id is not None
    place = await session.get(Place, promoted.place_id)
    assert place is not None and place.workflow_state == "IMPORTED"
    assert place.category_code == "FOOD" and place.area_code == "da-nang-center"
    assert not (await promote_web_candidate_if_eligible(session, closed.id)).promoted
    assert (
        await promote_web_candidate_if_eligible(session, missing.id)
    ).reason == "PLACES_NOT_FOUND"
    assert (
        await promote_web_candidate_if_eligible(session, eligible.id)
    ).reason == "STATE_PROMOTED"
    # The promoted place goes through the same gate: unlicensed web source, no editorial source.
    # DEC-033: the missing VI/EN description is no longer a gate reason.
    report = await _publish(session, [promoted.place_id])
    assert report.outcomes[0].status == "rejected"
    assert "MISSING_LICENCE:example.org" in report.outcomes[0].reasons
    assert not any(r.startswith("MISSING_DESCRIPTION") for r in report.outcomes[0].reasons)
