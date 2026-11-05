"""Schema checks against the migrated Compose database (`alembic upgrade head` first)."""

import re
import uuid
from collections.abc import AsyncIterator

import pytest
from schema_expectations import EXPECTED_TABLES, EXPECTED_VIEWS, PUBLISH_FUNCTIONS
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app import models  # noqa: F401
from app.cli import seed_reference_data
from app.config import get_settings
from app.db.base import Base
from app.models.constants import CHECK_ENUMS

pytestmark = pytest.mark.integration


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session


async def test_expected_tables_views_and_functions_exist(session: AsyncSession) -> None:
    tables = set(
        (
            await session.scalars(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                    "AND table_name NOT IN ('alembic_version', 'spatial_ref_sys')"
                )
            )
        ).all()
    )
    assert tables == EXPECTED_TABLES

    views = set(
        (
            await session.scalars(
                text(
                    "SELECT table_name FROM information_schema.views WHERE table_schema = 'public'"
                )
            )
        ).all()
    )
    assert EXPECTED_VIEWS <= views

    functions = set(
        (
            await session.scalars(
                text("SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace")
            )
        ).all()
    )
    assert PUBLISH_FUNCTIONS <= functions

    indexdef = await session.scalar(
        text(
            "SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_knowledge_chunks_embedding_hnsw'"
        )
    )
    assert indexdef is not None
    assert "USING hnsw (embedding vector_cosine_ops)" in indexdef

    redundant = await session.scalar(
        text("SELECT count(*) FROM pg_indexes WHERE indexname = 'ix_accounts_clerk_user_id'")
    )
    assert redundant == 0


async def test_model_columns_match_database(session: AsyncSession) -> None:
    rows = (
        await session.execute(
            text(
                "SELECT table_name, column_name, is_nullable = 'YES' "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public'"
            )
        )
    ).all()
    database: dict[str, dict[str, bool]] = {}
    for table_name, column_name, nullable in rows:
        database.setdefault(table_name, {})[column_name] = nullable
    for name, table in Base.metadata.tables.items():
        model_columns = {column.name: bool(column.nullable) for column in table.columns}
        assert model_columns == database[name], name


async def test_check_enums_match_database(session: AsyncSession) -> None:
    rows = (
        await session.execute(
            text(
                "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE contype = 'c' AND connamespace = 'public'::regnamespace"
            )
        )
    ).all()
    definitions = dict(rows)
    for name, values in CHECK_ENUMS.items():
        assert tuple(re.findall(r"'([^']*)'::text", definitions[name])) == values, name


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    first = await seed_reference_data(session)
    second = await seed_reference_data(session)
    assert first == second
    assert first["areas"] >= 6
    enabled = (await session.scalars(text("SELECT code FROM cities WHERE is_enabled"))).all()
    assert enabled == ["da-nang"]
    hoi_an_areas = await session.scalar(
        text("SELECT count(*) FROM areas WHERE code LIKE 'hoi-an-%'")
    )
    assert hoi_an_areas == 2
    google_place_rule = await session.scalar(
        text(
            "SELECT r.persistence_class FROM provider_field_rules r "
            "JOIN provider_policies p ON p.id = r.provider_policy_id "
            "JOIN data_providers d ON d.id = p.data_provider_id "
            "WHERE d.provider_key = 'google_places' AND r.field_name = 'place_id'"
        )
    )
    assert google_place_rule == "ALLOW_IDENTIFIER_ONLY"


async def test_trip_stop_must_have_exactly_one_shape(session: AsyncSession) -> None:
    await seed_reference_data(session)
    account_id = uuid.uuid4()
    trip_id = uuid.uuid4()
    day_id = uuid.uuid4()
    try:
        await session.execute(
            text("INSERT INTO accounts (id, clerk_user_id) VALUES (:id, :clerk)"),
            {"id": account_id, "clerk": f"integration_{account_id}"},
        )
        await session.execute(
            text(
                "INSERT INTO trips (id, account_id, city_id, day_count) "
                "SELECT :id, :account, id, 1 FROM cities WHERE code = 'da-nang'"
            ),
            {"id": trip_id, "account": account_id},
        )
        await session.execute(
            text(
                "INSERT INTO trip_days (id, trip_id, day_index, day_window_start, day_window_end) "
                "VALUES (:id, :trip, 1, '08:00', '20:00')"
            ),
            {"id": day_id, "trip": trip_id},
        )
        insert_stop = text(
            "INSERT INTO trip_stops (id, trip_id, trip_day_id, city_id, trust_level, place_id, "
            "catalog_publication_id, web_place_candidate_id, ordinal, planned_arrival, "
            "planned_departure, visit_minutes) "
            "SELECT :id, :trip, :day, id, :trust, NULL, NULL, :candidate, 1, '09:00', '10:00', 60 "
            "FROM cities WHERE code = 'da-nang'"
        )
        # VERIFIED without a published place, and WEB_UNVERIFIED without a candidate.
        for trust, candidate in (("VERIFIED", None), ("WEB_UNVERIFIED", None)):
            savepoint = await session.begin_nested()
            with pytest.raises(IntegrityError, match="ck_trip_stops_shape"):
                await session.execute(
                    insert_stop,
                    {
                        "id": uuid.uuid4(),
                        "trip": trip_id,
                        "day": day_id,
                        "trust": trust,
                        "candidate": candidate,
                    },
                )
            await savepoint.rollback()
    finally:
        await session.rollback()
