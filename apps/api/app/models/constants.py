"""Enumerations enforced by TEXT + CHECK constraints in the migrations (schema.sql 1.0, 0004).

Each tuple equals the IN-list of the named CHECK constraint; tests/test_models.py and
tests/integration/test_schema.py keep them in sync. To extend a value set, write a migration that
swaps the constraint, then update the tuple here.
"""

from typing import Final

EMBEDDING_DIMENSIONS: Final = 768

LOCALES: Final = ("vi", "en")
TRAVEL_MODES: Final = ("WALK", "DRIVE")
TRUST_LEVELS: Final = ("VERIFIED", "WEB_UNVERIFIED")

PROVIDER_KINDS: Final = (
    "OPEN_DATASET",
    "RUNTIME_API",
    "OFFICIAL_SOURCE",
    "MEDIA_LIBRARY",
    "AI_SERVICE",
    "WEB_SEARCH",
    "WEB_CONTENT",
)
POLICY_STATUSES: Final = ("DRAFT", "ACTIVE", "RETIRED")
PERSISTENCE_CLASSES: Final = ("ALLOW_CANONICAL", "ALLOW_EPHEMERAL", "ALLOW_IDENTIFIER_ONLY", "DENY")
FACT_VALUE_KINDS: Final = ("HOURS", "MONEY", "TEXT", "LOCATION")
SOURCE_KINDS: Final = ("OFFICIAL", "OPEN_DATA", "REFERENCE", "OWN_OBSERVATION", "WEB")

PLACE_WORKFLOW_STATES: Final = (
    "IMPORTED",
    "MATCH_REVIEW",
    "CONTENT_REVIEW",
    "READY_TO_PUBLISH",
    "PUBLISHED",
    "RETIRED",
)
LOCALIZATION_REVIEW_STATES: Final = ("DRAFT", "APPROVED", "REJECTED", "SUPERSEDED")
TRANSLATION_ORIGINS: Final = ("ORIGINAL", "HUMAN_TRANSLATION", "AI_DRAFT")
ALIAS_KINDS: Final = ("NAME", "ALIAS")
ALIAS_REVIEW_STATES: Final = ("DRAFT", "APPROVED", "REJECTED")
KNOWLEDGE_STATES: Final = ("KNOWN", "UNKNOWN", "NOT_APPLICABLE")
FACT_REVIEW_STATES: Final = ("DRAFT", "APPROVED", "REJECTED", "SUPERSEDED")
FACT_CONFLICT_STATES: Final = ("NONE", "OPEN", "RESOLVED")
MEDIA_CONTENT_TYPES: Final = ("image/jpeg", "image/png", "image/webp")
MEDIA_RIGHTS_STATES: Final = ("PENDING", "CLEARED", "REVOKED")

PLACES_CHECK_OUTCOMES: Final = (
    "EXISTS_OPERATIONAL",
    "EXISTS_CLOSED",
    "NOT_FOUND",
    "OUTSIDE_CITY",
    "SKIPPED",
)
PLACES_LOOKUP_OUTCOMES: Final = ("EXISTS_OPERATIONAL", "EXISTS_CLOSED", "NOT_FOUND", "OUTSIDE_CITY")
WEB_CANDIDATE_REVIEW_STATES: Final = ("PENDING", "PROMOTED", "REJECTED", "EXPIRED")

CLOSURE_APPLIES_TO: Final = ("PLACE", "AREA", "CITY")
CLOSURE_RULE_KINDS: Final = ("WEEKLY", "DATE", "LUNAR_DATE", "SEASON", "TICKET_VALIDITY")
CLOSURE_EFFECTS: Final = ("CLOSED", "PARTIAL", "EVENT", "NOTICE")
CLOSURE_SEVERITIES: Final = ("BLOCKING", "WARNING")
CLOSURE_REVIEW_STATES: Final = ("DRAFT", "APPROVED", "RETIRED")

CHUNK_SCOPES: Final = ("PLACE", "CITY")
CHUNK_SECTIONS: Final = (
    "OVERVIEW",
    "HISTORY",
    "HIGHLIGHTS",
    "VISIT_TIPS",
    "ETIQUETTE",
    "ACCESS",
    "CITY_OVERVIEW",
    "GETTING_AROUND",
    "EVENTS_CALENDAR",
    "PRACTICAL",
)
CHUNK_REVIEW_STATES: Final = ("DRAFT", "APPROVED", "RETIRED")

PUBLICATION_STATES: Final = ("PUBLISHED", "SUPERSEDED", "WITHDRAWN")
AUDIT_ACTIONS: Final = (
    "IMPORT",
    "MATCH_REVIEW",
    "CONTENT_REVIEW",
    "FACT_REVIEW",
    "MEDIA_REVIEW",
    "PUBLISH",
    "WITHDRAW",
    "POLICY_CHANGE",
    "WEB_PROMOTE",
    "WEB_REJECT",
)
IMPORT_RUN_STATUSES: Final = ("RUNNING", "SUCCEEDED", "FAILED")
IMPORT_VALIDATION_STATUSES: Final = ("ACCEPTED", "REJECTED")
IMPORT_MATCH_STATES: Final = ("UNMATCHED", "MATCHED", "AMBIGUOUS", "NEW_CANDIDATE")
IDENTITY_MATCH_METHODS: Final = ("EXACT_ID", "NAME_AND_DISTANCE", "MANUAL")
IDENTITY_REVIEW_STATES: Final = ("PENDING", "APPROVED", "REJECTED")

TRIP_STATUSES: Final = ("DRAFT", "SAVED")
ROUTE_LEG_AVAILABILITIES: Final = ("AVAILABLE", "UNAVAILABLE", "EXPIRED")
PREVIEW_STATUSES: Final = ("ACTIVE", "SAVED", "DISCARDED", "EXPIRED")
PREVIEW_ORIGINS: Final = ("GENERATED", "MANUAL_EDIT", "DAY_REGENERATED", "REPAIRED")
PLAN_HEALTH_LEVELS: Final = ("GOOD", "WARNING", "BLOCKED")
GUIDE_MESSAGE_ROLES: Final = ("TRAVELER", "ASSISTANT")
IDEMPOTENCY_OPERATIONS: Final = ("TRIP_SAVE", "PREVIEW_CREATE", "DAY_REGENERATE", "ACCOUNT_DELETE")
IDEMPOTENCY_STATES: Final = ("IN_PROGRESS", "COMPLETED")
DELETION_JOB_STATUSES: Final = ("REQUESTED", "IN_PROGRESS", "COMPLETED", "FAILED")

AI_PURPOSES: Final = (
    "PLAN_GENERATE",
    "PLAN_REPAIR",
    "DAY_REGENERATE",
    "RESEARCH",
    "GUIDE_ANSWER",
    "PHOTO_IDENTIFY",
    "CORPUS_EMBED",
    "QUERY_EMBED",
    "TRANSLATION_DRAFT",
)
AI_OUTCOMES: Final = (
    "OK",
    "VALIDATION_FAILED",
    "PROVIDER_ERROR",
    "TIMEOUT",
    "QUOTA_EXCEEDED",
    "REFUSED_BY_CAP",
)

QUOTA_SCOPES: Final = ("GLOBAL", "ACCOUNT")
QUOTA_BUCKETS: Final = (
    "GEMINI_FLASH",
    "GEMINI_FLASH_LITE",
    "GEMINI_EMBED",
    "GROQ",
    "TAVILY_DAY",
    "TAVILY_MONTH",
    "PLACES",
    "ROUTES_ELEMENTS",
    "ACCOUNT_PROPOSALS",
    "ACCOUNT_QUESTIONS",
)
ACCOUNT_QUOTA_BUCKETS: Final = ("ACCOUNT_PROPOSALS", "ACCOUNT_QUESTIONS")
ROUTES_CACHE_AVAILABILITIES: Final = ("AVAILABLE", "UNAVAILABLE")
RESEARCH_CACHE_PROVIDERS: Final = ("TAVILY", "WEB_PAGE")
STUDY_SAVE_OUTCOMES: Final = ("SAVED", "NOT_SAVED", "SAVE_REFUSED")

# CHECK constraint name -> allowed values (single-column IN-lists only).
CHECK_ENUMS: Final[dict[str, tuple[str, ...]]] = {
    "ck_account_deletion_jobs_status": DELETION_JOB_STATUSES,
    "ck_account_preferences_locale": LOCALES,
    "ck_ai_invocations_outcome": AI_OUTCOMES,
    "ck_ai_invocations_purpose": AI_PURPOSES,
    "ck_ai_quota_ledger_bucket": QUOTA_BUCKETS,
    "ck_ai_quota_ledger_scope": QUOTA_SCOPES,
    "ck_catalog_audit_events_action": AUDIT_ACTIONS,
    "ck_catalog_publications_state": PUBLICATION_STATES,
    "ck_data_providers_provider_kind": PROVIDER_KINDS,
    "ck_external_place_identities_match_method": IDENTITY_MATCH_METHODS,
    "ck_external_place_identities_review_state": IDENTITY_REVIEW_STATES,
    "ck_fact_fields_value_kind": FACT_VALUE_KINDS,
    "ck_guide_messages_role": GUIDE_MESSAGE_ROLES,
    "ck_guide_sessions_locale": LOCALES,
    "ck_idempotency_records_operation": IDEMPOTENCY_OPERATIONS,
    "ck_idempotency_records_state": IDEMPOTENCY_STATES,
    "ck_import_records_match_state": IMPORT_MATCH_STATES,
    "ck_import_records_validation_status": IMPORT_VALIDATION_STATUSES,
    "ck_import_runs_status": IMPORT_RUN_STATUSES,
    "ck_knowledge_chunks_locale": LOCALES,
    "ck_knowledge_chunks_review_state": CHUNK_REVIEW_STATES,
    "ck_knowledge_chunks_scope": CHUNK_SCOPES,
    "ck_knowledge_chunks_section": CHUNK_SECTIONS,
    "ck_media_assets_content_type": MEDIA_CONTENT_TYPES,
    "ck_media_assets_rights_state": MEDIA_RIGHTS_STATES,
    "ck_place_aliases_alias_kind": ALIAS_KINDS,
    "ck_place_aliases_locale": LOCALES,
    "ck_place_aliases_review_state": ALIAS_REVIEW_STATES,
    "ck_place_closure_rules_applies_to": CLOSURE_APPLIES_TO,
    "ck_place_closure_rules_effect": CLOSURE_EFFECTS,
    "ck_place_closure_rules_review_state": CLOSURE_REVIEW_STATES,
    "ck_place_closure_rules_rule_kind": CLOSURE_RULE_KINDS,
    "ck_place_closure_rules_severity": CLOSURE_SEVERITIES,
    "ck_place_facts_conflict_state": FACT_CONFLICT_STATES,
    "ck_place_facts_knowledge_state": KNOWLEDGE_STATES,
    "ck_place_facts_review_state": FACT_REVIEW_STATES,
    "ck_place_localizations_locale": LOCALES,
    "ck_place_localizations_review_state": LOCALIZATION_REVIEW_STATES,
    "ck_place_localizations_translation_origin": TRANSLATION_ORIGINS,
    "ck_places_lookup_cache_outcome": PLACES_LOOKUP_OUTCOMES,
    "ck_places_workflow_state": PLACE_WORKFLOW_STATES,
    "ck_plan_previews_status": PREVIEW_STATUSES,
    "ck_preview_revisions_origin": PREVIEW_ORIGINS,
    "ck_preview_revisions_plan_health": PLAN_HEALTH_LEVELS,
    "ck_provider_field_rules_persistence_class": PERSISTENCE_CLASSES,
    "ck_provider_policies_status": POLICY_STATUSES,
    "ck_query_embedding_cache_locale": LOCALES,
    "ck_research_cache_provider": RESEARCH_CACHE_PROVIDERS,
    "ck_route_legs_availability": ROUTE_LEG_AVAILABILITIES,
    "ck_route_legs_travel_mode": TRAVEL_MODES,
    "ck_routes_matrix_cache_availability": ROUTES_CACHE_AVAILABILITIES,
    "ck_routes_matrix_cache_travel_mode": TRAVEL_MODES,
    "ck_sources_source_kind": SOURCE_KINDS,
    "ck_study_session_logs_interface_locale": LOCALES,
    "ck_study_session_logs_save_outcome": STUDY_SAVE_OUTCOMES,
    "ck_trip_stops_trust_level": TRUST_LEVELS,
    "ck_trips_status": TRIP_STATUSES,
    "ck_web_place_candidates_places_check_outcome": PLACES_CHECK_OUTCOMES,
    "ck_web_place_candidates_review_state": WEB_CANDIDATE_REVIEW_STATES,
}
