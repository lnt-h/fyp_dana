"""Content ingestion (ADR-012, DEC-022): Wikidata, Wikipedia, owner sheet, areas, calendar.

Importers stage DRAFT (IMPORTED) places under ACTIVE provider policies only; the automated gate
in ``app.curation.auto_publish`` publishes them. Must not import ``app.api`` or ``app.agents``.
"""
