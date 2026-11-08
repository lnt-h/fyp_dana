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

from app.config import get_settings
from app.curation.auto_publish import auto_publish
from app.curation.embedding import Embedding
from app.ingestion.common import load_city
from app.ingestion.commons import (
    CommonsFile,
    Rejected,
    place_images,
    stage_files,
)
from app.ingestion.osm import OsmElement, stage_elements
from app.ingestion.policies import activate_policy
from app.ingestion.wikidata import WikidataItem, stage_items
from app.ingestion.wikipedia import PageSummary, stage_summaries
from app.models.catalog import CatalogPublication, MediaAsset, Place, PlaceMedia, PublicationMedia
from app.models.providers import ImportRecord

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
        {"name": "Saigon cafe", "amenity": "cafe"}, lng=106.7, lat=10.77, category="CAFE"
    )
    unmapped = _osm({"name": "Hotel", "tourism": "hotel"}, lng=108.22, lat=16.06, category=None)
    elements = [by_tag, by_name, far, fresh, outside, unmapped]
    report = await stage_elements(session, city_code=CITY, elements=elements)
    assert (report.accepted, report.rejected, report.unmapped) == (4, 1, 1)
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
