"""In-memory stand-ins for the ``ai_quota_ledger`` / ``ai_invocations`` tables.

Statements are recognised by the ``/* quota:… */`` and ``/* ai:… */`` tags that
``app.ai`` puts on every SQL statement; the fake mimics the PostgreSQL semantics.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import pytest
from sqlalchemy.exc import OperationalError

from app.config import Settings


class _Result:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _Result:
        return self

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None


@dataclass
class FakeDb:
    ledger: dict[tuple[Any, ...], dict[str, Any]] = field(default_factory=dict)
    invocations: list[dict[str, Any]] = field(default_factory=list)
    statements: list[str] = field(default_factory=list)
    commits: int = 0
    sessions_opened: int = 0
    fail: bool = False

    def _key(self, p: dict[str, Any]) -> tuple[Any, ...]:
        return (p["scope"], p["account_id"], p["bucket"], p["period_start"])

    def _by_id(self, ledger_id: uuid.UUID) -> dict[str, Any]:
        return next(row for row in self.ledger.values() if row["id"] == ledger_id)

    async def execute(self, stmt: Any, params: dict[str, Any]) -> _Result:
        if self.fail:
            raise OperationalError("stmt", {}, Exception("offline"))
        sql = str(stmt)
        tag = sql.split("*/")[0].replace("/*", "").strip()
        self.statements.append(tag)
        if tag == "quota:ensure":
            self.ledger.setdefault(
                self._key(params),
                {"id": params["id"], "cap": params["cap"], "used": 0, "reserved": 0},
            )
            return _Result([])
        if tag == "quota:reserve":
            row = self.ledger.get(self._key(params))
            if row is None or row["used"] + row["reserved"] + params["amount"] > params["cap"]:
                return _Result([])
            row["reserved"] += params["amount"]
            row["cap"] = params["cap"]
            return _Result([dict(row)])
        if tag == "quota:read":
            row = self.ledger.get(self._key(params))
            return _Result([dict(row)] if row else [])
        if tag == "quota:commit":
            row = self._by_id(params["id"])
            row["used"] += params["amount"]
            row["reserved"] = max(row["reserved"] - params["amount"], 0)
            return _Result([])
        if tag == "quota:release":
            row = self._by_id(params["id"])
            row["reserved"] = max(row["reserved"] - params["amount"], 0)
            return _Result([])
        if tag == "ai:invocation":
            self.invocations.append(dict(params))
            return _Result([])
        raise AssertionError(f"unexpected statement: {sql}")

    async def commit(self) -> None:
        self.commits += 1

    def factory(self) -> Callable[[], Any]:
        @asynccontextmanager
        async def open_session() -> Any:
            self.sessions_opened += 1
            yield self

        return open_session


@pytest.fixture
def db() -> FakeDb:
    return FakeDb()


def make_settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "gemini_api_key": "gem-test-SECRET-123",
        "groq_api_key": "groq-test-SECRET-456",
        "quota_gemini_flash_per_day": 2,
        "quota_gemini_flash_lite_per_day": 2,
        "quota_groq_per_day": 2,
        "quota_account_proposals_per_day": 1,
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def settings_factory() -> Callable[..., Settings]:
    return make_settings
