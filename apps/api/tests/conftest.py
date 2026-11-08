"""Hermetic settings for every test.

``Settings()`` would otherwise read ``apps/api/.env`` and ``GONARRA_*`` variables of the developer
shell (e.g. a present-but-unusable Google Maps key), so provider-selection tests would depend on the
machine. Each test sees no ``.env`` file and no ``GONARRA_*`` variable except the database URL
(integration tests need it). The cached app settings used by ``app.db.session`` are untouched.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from app.config import Settings

KEEP = frozenset({"GONARRA_DATABASE_URL"})


@pytest.fixture(autouse=True)
def hermetic_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in list(os.environ):
        if name.startswith("GONARRA_") and name not in KEEP:
            monkeypatch.delenv(name)
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    yield
