"""OpenStreetMap and Wikimedia Commons importers against the Compose database (DEC-022).

Same isolation as ``test_pipeline.py``: one outer transaction rolled back per test. Fixture data
uses random OSM ids, Wikidata ids, names and file names that cannot collide with live imports.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.catalog.places import PlacesRepository
from app.config import get_settings
from app.curation.auto_publish import auto_publish
from app.curation.embedding import Embedding
from app.ingestion.common import (
    get_or_create_revision,
    get_or_create_source,
    load_city,
    require_active_policy,
)
from app.ingestion.commons import (
    Article,
    CommonsFile,
    PageImage,
    Rejected,
    add_page_images,
    place_articles,
    place_images,
    stage_files,
)
from app.ingestion.osm import OsmElement, stage_elements
from app.ingestion.policies import activate_policy
from app.ingestion.wikidata import WikidataItem, stage_items
from app.ingestion.wikidata_link import stage_links
from app.ingestion.wikipedia import PageSummary, stage_summaries
from app.models.catalog import CatalogPublication, MediaAsset, Place, PlaceMedia, PublicationMedia
from app.models.providers import ImportRecord
from app.research.fact_extract import FactCandidate, FactExtractor, _Evidence

pytestmark = pytest.mark.integration

CITY = "da-nang"
HOI_AN = (108.3262, 15.8771)  # inside the hoi-an-old-town polygon


class FakeEmbedder:
    async def embed(self, text: str) -> Embedding | None:
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


def _token() -> str:
    return f"{uuid.uuid4().int % 10**9:09d}"


def _qid() -> str:
    return f"Q9{_token()}"


def _wikidata(qid: str, *, lng: float, lat: float, images: tuple[str, ...] = ()) -> WikidataItem:
    return WikidataItem(
        qid=qid,
        lng=lng,
        lat=lat,
        labels={"vi": f"Chùa thử {qid}", "en": f"Test pagoda {qid}"},
        descriptions={"vi": "mô tả", "en": "description"},
        aliases={},
        sitelinks={"vi": f"T {qid} vi", "en": f"T {qid} en"},
        class_labels=("pagoda",),
        category="RELIGIOUS_SITE",
        images=images,
    )


def _osm(tags: dict[str, str], *, lng: float, lat: float, category: str | None) -> OsmElement:
    return OsmElement(
        osm_type="node",
        osm_id=9_000_000_000 + int(_token()),
        lng=lng,
        lat=lat,
        tags=tags,
        category=category,
    )


async def _place_for(session: AsyncSession, provider_key: str, upstream_id: str) -> uuid.UUID:
    value = await session.scalar(
        text(
            "SELECT i.place_id FROM external_place_identities i "
            "JOIN data_providers d ON d.id = i.data_provider_id "
            "WHERE d.provider_key = :key AND i.upstream_id = :id"
        ),
        {"key": provider_key, "id": upstream_id},
    )
    assert value is not None
    return uuid.UUID(str(value))


async def _summaries(session: AsyncSession, place_id: uuid.UUID, qid: str) -> None:
    await stage_summaries(
        session,
        city_code=CITY,
        summaries=[
            PageSummary(
                place_id=place_id,
                locale=locale,
                title=f"T {qid} {locale}",
                page_url=f"https://{locale}.wikipedia.org/wiki/T_{qid}",
                summary=f"Summary of {qid} in {locale}.",
                revision="1",
            )
            for locale in ("vi", "en")
        ],
    )


async def test_osm_dedupes_creates_and_feeds_opening_hours_to_the_gate(
    session: AsyncSession,
) -> None:
    for key in ("wikidata", "wikipedia", "openstreetmap"):
        await activate_policy(session, key, f"test terms {key}")
    tagged_qid, named_qid = _qid(), _qid()
    await stage_items(
        session,
        city_code=CITY,
        items=[
            _wikidata(tagged_qid, lng=HOI_AN[0], lat=HOI_AN[1]),
            _wikidata(named_qid, lng=108.2779, lat=16.1003),
        ],
        policy_key="wikidata",
    )
    tagged_place = await _place_for(session, "wikidata", tagged_qid)
    named_place = await _place_for(session, "wikidata", named_qid)
    new_name = f"Quán thử {_token()}"
    by_tag = _osm(
        {
            "name": "Some other name",
            "historic": "temple",
            "wikidata": tagged_qid,
            "opening_hours": "Mo-Su 07:00-21:30",
        },
        lng=HOI_AN[0] + 0.0005,
        lat=HOI_AN[1],
        category="HERITAGE",
    )
    # Same name without diacritics, ~40 m away: matched by normalized name.
    by_name = _osm(
        {"name": f"Chua thu {named_qid}", "amenity": "place_of_worship"},
        lng=108.2783,
        lat=16.1003,
        category="RELIGIOUS_SITE",
    )
    # Same name but ~1.1 km away: a different place.
    far = _osm(
        {"name": f"Chùa thử {named_qid}", "amenity": "place_of_worship"},
        lng=108.2879,
        lat=16.1003,
        category="RELIGIOUS_SITE",
    )
    fresh = _osm(
        {"name": new_name, "name:en": "Test eatery", "amenity": "restaurant"},
        lng=108.2200,
        lat=16.0600,
        category="FOOD",
    )
    outside = _osm(
        {"name": "Saigon cafe", "amenity": "cafe", "cuisine": "coffee_shop"},
        lng=106.7,
        lat=10.77,
        category="CAFE",
    )
    # FOOD/CAFE without name:en, website, opening_hours, cuisine or wikidata: not imported.
    sparse = _osm(
        {"name": "Quán vỉa hè", "amenity": "cafe"}, lng=108.22, lat=16.06, category="CAFE"
    )
    unmapped = _osm({"name": "Hotel", "tourism": "hotel"}, lng=108.22, lat=16.06, category=None)
    elements = [by_tag, by_name, far, fresh, outside, unmapped, sparse]
    report = await stage_elements(session, city_code=CITY, elements=elements)
    assert (report.accepted, report.rejected, report.unmapped) == (4, 1, 1)
    assert report.skipped_sparse == 1
    assert report.rejection_reasons == {"OUTSIDE_CITY": 1}
    assert (report.matched_wikidata, report.matched_name, report.created_places) == (1, 1, 2)
    assert report.with_opening_hours == 1
    assert await _place_for(session, "openstreetmap", by_tag.upstream_id) == tagged_place
    assert await _place_for(session, "openstreetmap", by_name.upstream_id) == named_place
    assert await _place_for(session, "openstreetmap", far.upstream_id) != named_place
    fresh_place = await session.get(
        Place, await _place_for(session, "openstreetmap", fresh.upstream_id)
    )
    assert fresh_place is not None and fresh_place.workflow_state == "IMPORTED"
    assert fresh_place.category_code == "FOOD"

    again = await stage_elements(session, city_code=CITY, elements=elements)
    assert again.skipped_unchanged

    # The OSM opening hours reach the gate as a KNOWN fact with the OSM element as evidence.
    await _summaries(session, tagged_place, tagged_qid)
    published = await auto_publish(
        session,
        city_code=CITY,
        embedder=FakeEmbedder(),
        place_ids=[tagged_place, fresh_place.id],
    )
    outcomes = {o.place_id: o for o in published.outcomes}
    assert outcomes[tagged_place].status == "published"
    assert outcomes[fresh_place.id].status == "rejected"  # no description in either locale
    assert "MISSING_DESCRIPTION:vi" in outcomes[fresh_place.id].reasons
    fact = (
        await session.execute(
            text(
                "SELECT knowledge_state, value, sources FROM vw_published_place_facts "
                "WHERE place_id = :id AND field_code = 'OPENING_HOURS'"
            ),
            {"id": tagged_place},
        )
    ).one()
    assert fact[0] == "KNOWN"
    assert fact[1]["weekly"]["1"] == [["07:00", "21:30"]]
    assert fact[1]["text"] == "Mo-Su 07:00-21:30"
    assert "openstreetmap.org/node/" in str(fact[2])


async def test_osm_foreign_names_are_skipped_and_shared_commons_links_not_creates(
    session: AsyncSession,
) -> None:
    for key in ("wikidata", "openstreetmap"):
        await activate_policy(session, key, f"test terms {key}")
    qid = _qid()
    image = f"Chua Cau {qid}.jpg"
    await stage_items(
        session,
        city_code=CITY,
        items=[_wikidata(qid, lng=HOI_AN[0], lat=HOI_AN[1], images=(image,))],
        policy_key="wikidata",
    )
    bridge = await _place_for(session, "wikidata", qid)
    # A Korean label without name:vi (the "일본건설다리" / place-3 duplicate): never imported.
    korean = _osm(
        {"name": "일본건설다리", "historic": "monument"},
        lng=HOI_AN[0] + 0.0002,
        lat=HOI_AN[1],
        category="HERITAGE",
    )
    # A differently named element ~50 m away sharing the Commons photo: linked, not created.
    shared = _osm(
        {
            "name": f"Cầu Nhật Bản {qid}",
            "historic": "monument",
            "wikimedia_commons": f"File:{image.replace(' ', '_')}",
        },
        lng=HOI_AN[0] + 0.0005,
        lat=HOI_AN[1],
        category="HERITAGE",
    )
    # Same photo but ~1.1 km away: a different place.
    far = _osm(
        {"name": f"Đình xa {qid}", "historic": "monument", "image": f"File:{image}"},
        lng=HOI_AN[0] + 0.0105,
        lat=HOI_AN[1],
        category="HERITAGE",
    )
    report = await stage_elements(session, city_code=CITY, elements=[korean, shared, far])
    assert report.skipped_foreign_name == 1
    assert (report.matched_shared, report.created_places) == (1, 1)
    assert await _place_for(session, "openstreetmap", shared.upstream_id) == bridge
    assert await _place_for(session, "openstreetmap", far.upstream_id) != bridge
    korean_rows = await session.scalar(
        text("SELECT count(*) FROM import_records WHERE upstream_id = :id"),
        {"id": korean.upstream_id},
    )
    assert korean_rows == 0


def _file(title: str, *, license_code: str = "CC-BY-SA-4.0") -> CommonsFile:
    slug = title.removeprefix("File:").replace(" ", "_")
    return CommonsFile(
        title=title,
        file_url=f"https://upload.wikimedia.org/wikipedia/commons/thumb/x/xy/{slug}/1280px-{slug}",
        description_url=f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}",
        width=1280,
        height=853,
        mime="image/jpeg",
        sha1=uuid.uuid4().hex[:40],
        license_code=license_code,
        license_name="CC BY-SA 4.0",
        creator="Photographer",
        attribution="Photographer, CC BY-SA 4.0, via Wikimedia Commons",
    )


async def test_commons_media_is_licensed_ordered_idempotent_and_published(
    session: AsyncSession,
) -> None:
    for key in ("wikidata", "wikipedia", "wikimedia_commons"):
        await activate_policy(session, key, f"test terms {key}")
    qid, token = _qid(), _token()
    main, second, nc = f"Main {token}.jpg", f"Second {token}.jpg", f"Nc {token}.jpg"
    await stage_items(
        session,
        city_code=CITY,
        items=[_wikidata(qid, lng=HOI_AN[0], lat=HOI_AN[1], images=(main, second, nc))],
        policy_key="wikidata",
    )
    place_id = await _place_for(session, "wikidata", qid)
    await _summaries(session, place_id, qid)
    city = await load_city(session, CITY)
    candidates = [c for c in await place_images(session, city.id) if c.place_id == place_id]
    assert [c.titles for c in candidates] == [[f"File:{main}", f"File:{second}", f"File:{nc}"]]
    files: dict[str, CommonsFile | Rejected] = {
        f"File:{main}": _file(f"File:{main}"),
        f"File:{second}": _file(f"File:{second}"),
        f"File:{nc}": Rejected(f"File:{nc}", "LICENSE_NOT_ALLOWED"),
    }
    report = await stage_files(session, city_code=CITY, candidates=candidates, files=files)
    assert (report.accepted, report.rejected, report.places_with_media) == (2, 1, 1)
    assert report.rejection_reasons == {"LICENSE_NOT_ALLOWED": 1}
    media = (
        await session.execute(
            select(PlaceMedia.ordinal, MediaAsset.object_key, MediaAsset.rights_state)
            .join(MediaAsset, MediaAsset.id == PlaceMedia.media_asset_id)
            .where(PlaceMedia.place_id == place_id)
            .order_by(PlaceMedia.ordinal)
        )
    ).all()
    assert [(m[0], m[2]) for m in media] == [(1, "CLEARED"), (2, "CLEARED")]
    assert media[0][1].endswith(f"1280px-Main_{token}.jpg")  # P18 order: sorted file names
    alt = await session.scalar(
        select(PlaceMedia.alt_text_en).where(
            PlaceMedia.place_id == place_id, PlaceMedia.ordinal == 1
        )
    )
    assert alt == f"Photo: Test pagoda {qid}"

    again = await stage_files(session, city_code=CITY, candidates=candidates, files=files)
    assert again.skipped_unchanged
    assets = await session.scalar(
        select(func.count()).select_from(PlaceMedia).where(PlaceMedia.place_id == place_id)
    )
    assert assets == 2

    first = await auto_publish(
        session, city_code=CITY, embedder=FakeEmbedder(), place_ids=[place_id]
    )
    assert first.outcomes[0].status == "published"
    place = await session.get(Place, place_id, populate_existing=True)
    assert place is not None and place.has_no_media is False
    published_media = await session.scalar(
        select(func.count())
        .select_from(PublicationMedia)
        .join(
            CatalogPublication,
            CatalogPublication.id == PublicationMedia.catalog_publication_id,
        )
        .where(CatalogPublication.place_id == place_id, CatalogPublication.state == "PUBLISHED")
    )
    assert published_media == 2

    # The second file disappears upstream: its place_media row goes and the place re-publishes.
    files[f"File:{second}"] = Rejected(f"File:{second}", "MISSING_FILE")
    await stage_files(session, city_code=CITY, candidates=candidates, files=files)
    remaining = await session.scalar(
        select(func.count()).select_from(PlaceMedia).where(PlaceMedia.place_id == place_id)
    )
    assert remaining == 1
    republished = await auto_publish(
        session, city_code=CITY, embedder=FakeEmbedder(), place_ids=[place_id]
    )
    assert republished.outcomes[0].status == "published"
    records = await session.scalar(
        select(func.count())
        .select_from(ImportRecord)
        .where(ImportRecord.place_id == place_id, ImportRecord.validation_status == "REJECTED")
    )
    assert records == 3  # NC file (twice: two runs) and the missing file


async def test_wikipedia_page_image_is_staged_with_article_provenance(
    session: AsyncSession,
) -> None:
    for key in ("wikidata", "wikipedia", "wikimedia_commons"):
        await activate_policy(session, key, f"test terms {key}")
    qid, token = _qid(), _token()
    await stage_items(
        session,
        city_code=CITY,
        items=[_wikidata(qid, lng=HOI_AN[0], lat=HOI_AN[1])],
        policy_key="wikidata",
    )
    place_id = await _place_for(session, "wikidata", qid)
    city = await load_city(session, CITY)
    articles = [a for a in await place_articles(session, city.id) if a.place_id == place_id]
    assert len(articles) == 1 and articles[0].qid == qid
    assert articles[0].articles == [Article("vi", f"T {qid} vi"), Article("en", f"T {qid} en")]
    lead = f"File:Lead {token}.jpg"
    images = {
        Article("vi", f"T {qid} vi"): PageImage(
            "vi", f"T {qid} vi", f"https://vi.wikipedia.org/wiki/T_{qid}", "42", qid, lead
        ),
        # The EN article is about another item (e.g. the parent complex): never used.
        Article("en", f"T {qid} en"): PageImage(
            "en", f"T {qid} en", f"https://en.wikipedia.org/wiki/T_{qid}", "7", "Q1", "File:P.jpg"
        ),
    }
    candidates, wrong = add_page_images([], articles, images, skip=set())
    assert wrong == 1 and [c.titles for c in candidates] == [[lead]]
    report = await stage_files(
        session, city_code=CITY, candidates=candidates, files={lead: _file(lead)}
    )
    assert (report.accepted, report.places_with_media, report.places_with_page_image) == (1, 1, 1)
    record = await session.scalar(
        select(ImportRecord.allowed_payload).where(
            ImportRecord.place_id == place_id, ImportRecord.raw_name == lead
        )
    )
    assert record is not None
    provenance = record["_provenance"]
    assert provenance["via"] == "wikipedia_page_image"
    locator = await session.scalar(
        text("SELECT locator FROM source_revisions WHERE id = :id"),
        {"id": provenance["via_source_revision_id"]},
    )
    assert locator == f"https://vi.wikipedia.org/wiki/T_{qid}"
    count = await session.scalar(
        select(func.count()).select_from(PlaceMedia).where(PlaceMedia.place_id == place_id)
    )
    assert count == 1


async def test_osm_code_and_human_names_are_skipped(session: AsyncSession) -> None:
    await activate_policy(session, "openstreetmap", "test terms openstreetmap")
    human = _qid()
    code = _osm(
        {"name": "A7", "historic": "ruins"}, lng=HOI_AN[0], lat=HOI_AN[1], category="HERITAGE"
    )
    statue = _osm(
        {"name": f"Tượng {human}", "historic": "memorial", "wikidata": human},
        lng=HOI_AN[0],
        lat=HOI_AN[1] + 0.0003,
        category="HERITAGE",
    )
    report = await stage_elements(
        session, city_code=CITY, elements=[code, statue], human_qids={human}
    )
    assert (report.skipped_code_name, report.skipped_human_name) == (1, 1)
    assert report.record_count == 0 and report.created_places == 0


async def test_wikidata_link_names_an_osm_place_and_backfills_a_tagged_one(
    session: AsyncSession,
) -> None:
    for key in ("wikidata", "openstreetmap"):
        await activate_policy(session, key, f"test terms {key}")
    token = _token()
    linked_qid, tagged_qid, human_qid = _qid(), _qid(), _qid()
    name = f"Chùa Thử Nghiệm {token}"
    plain = _osm(
        {"name": name, "amenity": "place_of_worship"},
        lng=HOI_AN[0],
        lat=HOI_AN[1],
        category="RELIGIOUS_SITE",
    )
    tagged = _osm(
        {"name": f"Núi Thử {token}", "natural": "peak", "wikidata": tagged_qid},
        lng=HOI_AN[0] + 0.003,
        lat=HOI_AN[1],
        category="NATURE",
    )
    statue = _osm(
        {"name": f"Đài Thử {token}", "historic": "memorial", "wikidata": human_qid},
        lng=HOI_AN[0] - 0.003,
        lat=HOI_AN[1],
        category="HERITAGE",
    )
    await stage_elements(session, city_code=CITY, elements=[plain, tagged, statue])
    plain_id = await _place_for(session, "openstreetmap", plain.upstream_id)
    tagged_id = await _place_for(session, "openstreetmap", tagged.upstream_id)
    items = [
        WikidataItem(
            qid=linked_qid,
            lng=HOI_AN[0] + 0.001,  # ~107 m
            lat=HOI_AN[1],
            labels={"vi": name, "en": f"Test Pagoda {token}"},
            descriptions={"en": "pagoda in Hội An"},
            aliases={},
            sitelinks={"vi": name},
            class_labels=("pagoda",),
            images=(f"Pagoda {token}.jpg",),
        ),
        WikidataItem(
            qid=tagged_qid,
            lng=HOI_AN[0] + 0.004,
            lat=HOI_AN[1],
            labels={"vi": f"Núi Thử {token}"},
            descriptions={},
            aliases={},
            sitelinks={},
            class_labels=("mountain",),
        ),
    ]
    report = await stage_links(session, city_code=CITY, items=items, humans={human_qid})
    assert (report.linked, report.backfilled) == (1, 1)
    assert any(qid == human_qid for _slug, qid in report.humans)
    assert await _place_for(session, "wikidata", linked_qid) == plain_id
    payload = await session.scalar(
        select(ImportRecord.allowed_payload).where(
            ImportRecord.place_id == plain_id, ImportRecord.upstream_id == linked_qid
        )
    )
    assert payload is not None and "location" not in payload
    assert payload["_provenance"]["match"]["method"] == "NAME_AND_DISTANCE"
    tagged_payload = await session.scalar(
        select(ImportRecord.allowed_payload).where(
            ImportRecord.place_id == tagged_id, ImportRecord.upstream_id == tagged_qid
        )
    )
    assert tagged_payload is not None
    assert tagged_payload["_provenance"]["match"]["method"] == "OSM_WIKIDATA_TAG"
    again = await stage_links(session, city_code=CITY, items=items, humans={human_qid})
    assert again.linked == 0 or again.skipped_unchanged


async def test_ai_extracted_fact_is_published_with_origin_and_cited_link(
    session: AsyncSession,
) -> None:
    from app.agents.schemas import FactExtraction, ValidatedFact

    for key in ("wikidata", "wikipedia", "gonarra_ai_facts"):
        await activate_policy(session, key, f"test terms {key}")
    qid = _qid()
    await stage_items(
        session,
        city_code=CITY,
        items=[_wikidata(qid, lng=HOI_AN[0], lat=HOI_AN[1])],
        policy_key="wikidata",
    )
    place_id = await _place_for(session, "wikidata", qid)
    await _summaries(session, place_id, qid)
    web_source = await get_or_create_source(
        session,
        data_provider_id=None,
        publisher="example.vn",
        source_kind="WEB",
        license_code="UNKNOWN",
        attribution_text="example.vn",
    )
    page = await get_or_create_revision(
        session,
        source_id=web_source.id,
        locator=f"https://example.vn/{qid}",
        content_sha256=uuid.uuid4().hex * 2,
        title="Giờ mở cửa",
    )
    evidence = _Evidence()
    evidence.add(
        "web1", "Mở cửa 7h-17h. Miễn phí vé.", kind="WEB", revision=page.id, url=page.locator
    )
    extraction = FactExtraction(
        facts=(ValidatedFact("ADMISSION_PRICE", {"free": True}, "web1", "Miễn phí vé", "STRONG"),),
        short_description={"vi": ("Ngôi chùa thử.", "desc:vi")},
    )
    candidate = FactCandidate(
        place_id=place_id,
        slug="x",
        name_vi="x",
        name_en=None,
        category="RELIGIOUS_SITE",
        area_code=None,
        unknown=("ADDRESS_VI", "OPENING_HOURS", "ADMISSION_PRICE"),
        short_missing=(),
    )
    policy = await require_active_policy(session, "gonarra_ai_facts")
    city = await load_city(session, CITY)
    source = await get_or_create_source(
        session,
        data_provider_id=policy.provider_id,
        publisher="Gonarra",
        source_kind="REFERENCE",
        license_code="GONARRA-AI-FACTS",
        attribution_text="Facts extracted by Gonarra",
    )
    extractor = FactExtractor.__new__(FactExtractor)
    staged = await extractor._stage(
        session, policy, city.id, source.id, candidate, extraction, evidence
    )
    assert staged
    result = await auto_publish(
        session, city_code=CITY, embedder=FakeEmbedder(), place_ids=[place_id]
    )
    assert result.outcomes[0].status == "published", result.outcomes[0].reasons
    facts = await PlacesRepository(session).list_published_facts(place_id)
    price = next(f for f in facts if f.field_code == "ADMISSION_PRICE")
    assert (price.knowledge_state, price.origin, price.grounding) == (
        "KNOWN",
        "AI_EXTRACTED",
        "STRONG",
    )
    assert price.value == {"free": True}
    assert [s.locator for s in price.sources] == [f"https://example.vn/{qid}"]
    address = next(f for f in facts if f.field_code == "ADDRESS_VI")
    assert (address.knowledge_state, address.origin) == ("UNKNOWN", "SOURCE")
