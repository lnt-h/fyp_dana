"""The three Agno roles (architecture §3.1): ``selector``, ``researcher``, ``grounded_writer``.

Only this package (via :mod:`app.agents.runtime`) builds an Agno ``Agent``. It imports
``app.ai`` and its own modules only; repositories, provider adapters and HTTP code are injected
by the orchestrators (``planning.workflows``, ``guide.workflow``).
"""
