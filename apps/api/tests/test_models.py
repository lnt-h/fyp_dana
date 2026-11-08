"""Unit checks: ORM metadata, migration SQL and enumeration constants agree (no database)."""

import re

from integration.schema_expectations import (
    API_ROOT,
    EXPECTED_TABLES,
    PUBLISH_FUNCTIONS,
    TABLES_BY_MIGRATION,
    check_in_lists,
    load_migration,
    upgrade_sql,
)
from pgvector.sqlalchemy import Vector

from app import models  # noqa: F401  (registers every table)
from app.db.base import Base
from app.models.constants import CHECK_ENUMS, EMBEDDING_DIMENSIONS


def test_metadata_has_exactly_the_migrated_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES
    assert len(EXPECTED_TABLES) == 48


def test_every_model_table_has_a_primary_key() -> None:
    for name, table in Base.metadata.tables.items():
        assert table.primary_key.columns, f"{name} has no primary key"


def test_migrations_create_the_expected_tables() -> None:
    created = set(re.findall(r"CREATE TABLE (\w+) \(", upgrade_sql()))
    assert created == EXPECTED_TABLES - TABLES_BY_MIGRATION["0001"]


def test_migration_chain_is_linear() -> None:
    files = sorted(p.name for p in (API_ROOT / "migrations" / "versions").glob("2*.py"))
    previous: str | None = None
    for filename in files:
        module = load_migration(filename)
        assert module.down_revision == previous, filename
        previous = module.revision
    assert previous == "20261108_0007"


def test_check_enum_constants_match_migration_sql() -> None:
    in_lists = check_in_lists(upgrade_sql())
    for name, values in CHECK_ENUMS.items():
        assert in_lists.get(name) == values, name


def test_publish_functions_are_defined_in_0002() -> None:
    sql = upgrade_sql()
    for function in PUBLISH_FUNCTIONS:
        assert f"CREATE OR REPLACE FUNCTION {function}(" in sql


def test_embedding_columns_are_768_dimensional() -> None:
    sql = upgrade_sql()
    assert EMBEDDING_DIMENSIONS == 768
    assert "embedding        vector(768)" in sql
    assert "embedding           vector(768) NOT NULL" in sql
    for table in ("knowledge_chunks", "query_embedding_cache"):
        column_type = Base.metadata.tables[table].c.embedding.type
        assert isinstance(column_type, Vector)
        assert column_type.dim == EMBEDDING_DIMENSIONS


def test_trip_stops_one_shape_rule_is_in_the_migration() -> None:
    sql = upgrade_sql()
    assert "CONSTRAINT ck_trip_stops_shape CHECK" in sql


def test_caches_contract_file_matches_migration_0004() -> None:
    contract = (API_ROOT / "migrations" / "schema_caches_0004.sql").read_text()
    module = load_migration("20261106_0004_caches.py")
    assert module.SECTION_8A_SQL.strip() == contract.strip()


def test_redundant_accounts_index_is_dropped() -> None:
    assert "DROP INDEX IF EXISTS ix_accounts_clerk_user_id" in upgrade_sql()
    accounts = Base.metadata.tables["accounts"]
    assert not accounts.indexes
