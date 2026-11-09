"""SqlMatrixCache writes only under the ACTIVE google_routes policy (ADR-006)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from app.routing.matrix_cache import _POLICY_ID, CachedLeg, SqlMatrixCache


class _Session:
    def __init__(self, policy_id: uuid.UUID | None) -> None:
        self.policy_id = policy_id
        self.queries: list[str] = []
        self.executed = 0

    async def scalar(self, statement: Any, params: dict[str, Any]) -> uuid.UUID | None:
        self.queries.append(str(statement))
        return self.policy_id

    async def execute(self, statement: Any) -> None:
        self.executed += 1

    async def commit(self) -> None:
        return None


def _factory(session: _Session) -> Any:
    @asynccontextmanager
    async def factory() -> AsyncIterator[_Session]:
        yield session

    return factory


LEG = CachedLeg("anchor:a", "place:b", True, 1200, 300)


def test_policy_query_selects_only_active_policies() -> None:
    sql = str(_POLICY_ID)
    assert "pp.status = 'ACTIVE'" in sql and "APPROVED" not in sql


async def test_no_active_policy_caches_nothing() -> None:
    session = _Session(None)
    written = await SqlMatrixCache(_factory(session)).write([LEG], "DRIVE", now=datetime.now(UTC))
    assert written == 0 and session.executed == 0


async def test_active_policy_caches_legs() -> None:
    session = _Session(uuid.uuid4())
    written = await SqlMatrixCache(_factory(session)).write([LEG], "DRIVE", now=datetime.now(UTC))
    assert written == 1 and session.executed == 1
