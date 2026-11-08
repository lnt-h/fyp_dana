"""Planning workflow seam (architecture §3.2).

The routes validate ownership and the body, then hand a command and an event sink to the
injected :class:`PlanningWorkflow`. :func:`get_planning_workflow` (FastAPI dependency) returns the
deterministic ``propose_trip`` / ``regenerate_day`` orchestrator
(:class:`app.planning.orchestrator.PlanningOrchestrator`); :class:`NotImplementedWorkflow` stays
for tests.

This module must not import ``app.api`` or ``app.agents`` directly (import-linter); only the
orchestrator talks to the agent roles. The sink is a structural Protocol that
``app.api.sse.ProgressSink`` satisfies.
"""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from app.observability import error_payload
from app.schemas.trips import PlanPreviewCreate, RegenerateDayRequest


class EventSink(Protocol):
    """Where a workflow emits ``PlanningStreamEvent`` payloads (``type`` field required)."""

    def emit(self, event: BaseModel | Mapping[str, Any]) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class ProposeTripCommand:
    account_id: uuid.UUID
    trip_id: uuid.UUID
    request: PlanPreviewCreate
    idempotency_key: str | None
    request_id: str


@dataclass(frozen=True)
class RegenerateDayCommand:
    account_id: uuid.UUID
    preview_id: uuid.UUID
    trip_id: uuid.UUID
    request: RegenerateDayRequest
    idempotency_key: str | None
    request_id: str


class PlanningWorkflow(Protocol):
    """Runs one planning request and streams its stages into ``sink``.

    Contract for implementations: emit zero or more ``progress`` events, then exactly one terminal
    event (``preview_ready``, ``clarification_required`` or ``error``), then ``sink.close()``.
    Ownership was checked by the caller; quota, idempotency and persistence are the workflow's.
    """

    async def propose_trip(self, command: ProposeTripCommand, sink: EventSink) -> None: ...

    async def regenerate_day(self, command: RegenerateDayCommand, sink: EventSink) -> None: ...


def not_implemented_event(request_id: str) -> dict[str, Any]:
    detail = error_payload(
        "not_implemented",
        "AI planning is not available yet",
        request_id,
        retryable=False,
    )["error"]
    return {"type": "error", "error": detail}


class NotImplementedWorkflow:
    """M2 stub: reserves nothing, calls nothing, ends with one terminal ``error`` event."""

    async def propose_trip(self, command: ProposeTripCommand, sink: EventSink) -> None:
        sink.emit(not_implemented_event(command.request_id))
        sink.close()

    async def regenerate_day(self, command: RegenerateDayCommand, sink: EventSink) -> None:
        sink.emit(not_implemented_event(command.request_id))
        sink.close()


def get_planning_workflow() -> PlanningWorkflow:
    """FastAPI dependency: the M3 orchestrator over the app's session factory and settings."""
    from app.config import get_settings
    from app.db.session import session_factory
    from app.planning.orchestrator import PlanningOrchestrator

    return PlanningOrchestrator(session_factory, get_settings())
