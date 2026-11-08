"""Test doubles for agent tests: in-memory quota ledger, invocation sink and scripted runner."""

from __future__ import annotations

import json
import uuid
from collections import Counter
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import date
from typing import Any

from agno.agent import Agent
from agno.models.message import Message
from agno.run.agent import RunOutput
from agno.run.base import RunStatus

from app.ai.quota import Bucket, QuotaDecision, QuotaReservation
from app.config import Settings


def make_settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "gemini_api_key": "gem-test-SECRET-123",
        "groq_api_key": "groq-test-SECRET-456",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


class FakeLedger:
    def __init__(self, settings: Settings, caps: dict[Bucket, int] | None = None) -> None:
        self.settings = settings
        self.caps = caps or {}
        self.used: Counter[Bucket] = Counter()
        self.reserved: Counter[Bucket] = Counter()

    async def reserve(
        self, *, bucket: Bucket, amount: int = 1, account_id: uuid.UUID | None = None
    ) -> QuotaDecision:
        cap = self.caps.get(bucket, 1000)
        if self.used[bucket] + self.reserved[bucket] + amount > cap:
            return QuotaDecision(allowed=False, bucket=bucket, remaining=0)
        self.reserved[bucket] += amount
        res = QuotaReservation(uuid.uuid4(), bucket, amount, account_id, date(2026, 11, 6))
        return QuotaDecision(True, bucket, cap - self.used[bucket], res)

    async def commit(self, reservation: QuotaReservation) -> None:
        self.reserved[reservation.bucket] -= reservation.amount
        self.used[reservation.bucket] += reservation.amount

    async def release(self, reservation: QuotaReservation) -> None:
        self.reserved[reservation.bucket] -= reservation.amount


class FakeSession:
    def __init__(self, sink: list[dict[str, Any]]) -> None:
        self.sink = sink

    async def execute(self, stmt: Any, params: dict[str, Any]) -> None:
        assert "ai:invocation" in str(stmt)
        self.sink.append(dict(params))

    async def commit(self) -> None:
        return None


class InvocationSink:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def factory(self) -> Callable[[], Any]:
        @asynccontextmanager
        async def open_session() -> Any:
            yield FakeSession(self.rows)

        return open_session


Step = Any  # str | dict | Exception | Callable[[Agent, str], Awaitable[RunOutput]]


def output(
    content: Any, *, status: RunStatus = RunStatus.completed, assistant_msgs: int = 1
) -> RunOutput:
    messages = [Message(role="assistant", content="x") for _ in range(assistant_msgs)]
    return RunOutput(content=content, status=status, messages=messages)


class ScriptedRunner:
    """Replaces ``agent.arun``: returns scripted outputs in order and records each call."""

    def __init__(self, steps: list[Step]) -> None:
        self.steps = list(steps)
        self.calls: list[tuple[str, str, Agent]] = []

    async def __call__(self, agent: Agent, prompt: str) -> RunOutput:
        assert agent.model is not None
        self.calls.append((str(agent.model.id), prompt, agent))
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        if callable(step):
            result: RunOutput = await step(agent, prompt)
            return result
        if isinstance(step, RunOutput):
            return step
        return output(json.dumps(step) if isinstance(step, dict) else step)
