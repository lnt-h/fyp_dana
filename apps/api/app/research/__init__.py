"""Web research adapters for the researcher role (ADR-014): Tavily search, page fetch,
Places check, per-run toolbox and the ``web_place_candidates`` writer.

This package must not import the HTTP layer. It implements
:class:`app.agents.schemas.ResearchTools`; Agno itself is never imported here.
"""
