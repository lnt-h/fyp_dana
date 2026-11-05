"""Shared expectations for the schema tests (unit and integration)."""

import importlib.util
import re
from pathlib import Path
from types import ModuleType

API_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = API_ROOT / "migrations" / "versions"

MIGRATION_FILES = (
    "20261102_0001_foundation.py",
    "20261106_0002_catalog.py",
    "20261106_0003_planning.py",
    "20261106_0004_caches.py",
    "20261106_0005_study.py",
)

TABLES_BY_MIGRATION: dict[str, frozenset[str]] = {
    "0001": frozenset({"accounts"}),
    "0002": frozenset(
        {
            "cities",
            "areas",
            "categories",
            "fact_fields",
            "data_providers",
            "provider_policies",
            "provider_field_rules",
            "places",
            "import_runs",
            "import_records",
            "external_place_identities",
            "place_localizations",
            "place_aliases",
            "sources",
            "source_revisions",
            "place_facts",
            "fact_evidence",
            "media_assets",
            "place_media",
            "web_place_candidates",
            "place_closure_rules",
            "knowledge_chunks",
            "knowledge_chunk_sources",
            "catalog_publications",
            "publication_facts",
            "publication_media",
            "catalog_audit_events",
        }
    ),
    "0003": frozenset(
        {
            "account_preferences",
            "trips",
            "trip_days",
            "trip_stops",
            "route_legs",
            "plan_previews",
            "preview_revisions",
            "guide_sessions",
            "guide_messages",
            "guide_message_citations",
            "ai_invocations",
            "idempotency_records",
            "account_deletion_jobs",
        }
    ),
    "0004": frozenset(
        {
            "ai_quota_ledger",
            "routes_matrix_cache",
            "research_cache",
            "places_lookup_cache",
            "query_embedding_cache",
        }
    ),
    "0005": frozenset({"study_participants", "study_session_logs"}),
}
EXPECTED_TABLES: frozenset[str] = frozenset().union(*TABLES_BY_MIGRATION.values())

EXPECTED_VIEWS = frozenset(
    {"vw_published_places", "vw_published_place_facts", "vw_guide_chunks", "vw_trip_stop_trust"}
)
PUBLISH_FUNCTIONS = frozenset(
    {"fn_publication_gate_violations", "fn_publish_place", "fn_withdraw_place"}
)


def load_migration(filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        f"migration_{filename[:-3]}", VERSIONS_DIR / filename
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def upgrade_sql() -> str:
    """Concatenated upgrade SQL of the raw-SQL migrations (0002+), in revision order."""
    parts: list[str] = []
    for filename in MIGRATION_FILES[1:]:
        module = load_migration(filename)
        parts.extend(
            value
            for name, value in vars(module).items()
            if name.endswith("_SQL") and name != "DOWNGRADE_SQL" and isinstance(value, str)
        )
    return "\n".join(parts)


def check_in_lists(sql: str) -> dict[str, tuple[str, ...]]:
    """Map CHECK constraint name -> IN-list for single-column `col IN (...)` checks (last wins)."""
    pattern = re.compile(r"CONSTRAINT (ck_\w+) CHECK \(\s*\w+ IN\s*\(([^()]*)\)\)", re.DOTALL)
    return {
        match.group(1): tuple(re.findall(r"'([^']*)'", match.group(2)))
        for match in pattern.finditer(sql)
    }
