"""Hermetic settings for every test.

``Settings()`` would otherwise read ``apps/api/.env`` and ``GONARRA_*`` variables of the developer
shell (e.g. a present-but-unusable Google Maps key or ``GONARRA_DEMO_SHARED_USER=1``), so tests
would depend on the machine. The ``.env`` file is switched off at import time (before any test
module imports ``app.db.session``, whose engine reads the cached settings) and the lru-cached
:func:`app.config.get_settings` is cleared around every test. Each test sees no ``.env`` file, no
``GONARRA_*`` variable except the database URL (integration tests need it), and
``GONARRA_ENVIRONMENT=test`` (the settings default is ``production``, fail-safe).

Integration tests (``-m integration``) refuse to run against a database whose name does not end
in ``_test``, ``_it`` or ``_ci`` (optionally numbered, e.g. ``gonarra_it3``) unless
``GONARRA_ALLOW_INTEGRATION_DB=1`` is set: they write and delete rows, so they must never touch
the developer database by accident.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator

import pytest
from sqlalchemy.engine import make_url

from app.config import Settings, get_settings

KEEP = frozenset({"GONARRA_DATABASE_URL"})
INTEGRATION_DB_SUFFIXES = ("_test", "_it", "_ci")
# A numbered disposable database (``gonarra_it3``, ``gonarra_test2``) counts as well.
INTEGRATION_DB_RE = re.compile(r"_(?:test|it|ci)\d*$")
ALLOW_INTEGRATION_DB = "GONARRA_ALLOW_INTEGRATION_DB"

# Before collection imports any app module: no developer .env for the whole run.
Settings.model_config["env_file"] = None
get_settings.cache_clear()


def integration_db_allowed(database_url: str, *, override: str | None) -> bool:
    """True when the URL names a disposable test database or the override flag is ``1``."""
    if override == "1":
        return True
    name = make_url(database_url).database or ""
    return bool(INTEGRATION_DB_RE.search(name))


@pytest.hookimpl(trylast=True)  # after ``-m`` deselection: only selected tests count
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not any(item.get_closest_marker("integration") for item in items):
        return
    override = os.environ.get(ALLOW_INTEGRATION_DB)
    urls = {get_settings().database_url}
    try:  # the app engine (routes under test) must point at the same safe database
        from app.db.session import engine

        urls.add(engine.url.render_as_string(hide_password=False))
    except Exception:  # noqa: BLE001 - no engine, nothing else to check
        pass
    unsafe = sorted(
        make_url(url).database or "?"
        for url in urls
        if not integration_db_allowed(url, override=override)
    )
    if unsafe:
        raise pytest.UsageError(
            f"integration tests refuse database(s) {unsafe}: use a database whose name ends in "
            f"{', '.join(INTEGRATION_DB_SUFFIXES)} (GONARRA_DATABASE_URL) or set "
            f"{ALLOW_INTEGRATION_DB}=1"
        )


@pytest.fixture(autouse=True)
def hermetic_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in list(os.environ):
        if name.startswith("GONARRA_") and name not in KEEP:
            monkeypatch.delenv(name)
    monkeypatch.setenv("GONARRA_ENVIRONMENT", "test")
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
