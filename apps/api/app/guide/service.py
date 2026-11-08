"""Guide sessions and the grounded answer pipeline (API-024..028, ADR-010, DEC-017).

``ask`` is deterministic Gonarra code around one ``grounded_writer`` GUIDE_ANSWER call:

1. ``VALIDATING`` — ownership, optional ``Idempotency-Key`` claim (operation ``GUIDE_ASK``),
   the traveler message is stored.
2. ``RETRIEVING`` — after the per-account question quota and the Guide budget are reserved
   (an over-quota question spends no embedding quota). PLACE scope: Tier 1 evidence of the
   pinned place; CITY scope: entity → lexical → vector, rank-fused (:mod:`app.guide.retrieval`).
3. No evidence → ``INSUFFICIENT_EVIDENCE`` without a model call. (Extension point: the labelled
   ``WEB_UNVERIFIED`` web fallback would run here with stage ``SEARCHING_WEB``; out of scope.)
4. ``ANSWERING`` — the writer through the shared runtime
   (redactor + quota ledger + invocation metadata). Citations are re-validated against the
   supplied evidence; an answer without a valid citation is ``INSUFFICIENT_EVIDENCE``.
5. The assistant message is stored with its citations; ``text`` deltas then the terminal
   ``result`` event are emitted.

Questions, answers and prompts are never logged; logs carry counts and codes only.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.agents.runtime import AgentContext, AgentRunner, default_runner
from app.agents.schemas import GuideAnswerOutcome, ResultSource
from app.agents.writer import write_guide_answer
from app.ai.invocations import Outcome, Purpose
from app.ai.quota import GUIDE_BUDGET, Bucket, QuotaBudget, QuotaLedger, SessionFactory
from app.ai.redaction import RedactionError
from app.config import Settings
from app.errors import AppError
from app.guide.answer import ComposedAnswer, compose, evidence_items, insufficient
from app.guide.retrieval import HybridRetriever, RetrievalResult
from app.guide.store import GuideStore, SessionRecord, UnitOfWork, citation_rows
from app.observability import error_payload
from app.schemas.guide import (
    GuideMessage,
    GuideMessagePage,
    GuideQuestion,
    GuideSession,
    GuideSessionCreate,
)
from app.trips import idempotency

logger = logging.getLogger("gonarra.guide")

OP_GUIDE_ASK = "GUIDE_ASK"
MAX_HISTORY_TURNS = 4

# Terminal ``error`` codes → HTTP status for the JSON mode of API-028.
ERROR_STATUS: dict[str, int] = {
    "resource_not_found": 404,
    "idempotency_in_progress": 409,
    "idempotency_key_reused": 409,
    "deletion_in_progress": 409,
    "quota_exceeded": 429,
    "unsupported_request": 422,
    "validation_error": 422,
    "ai_unavailable": 503,
    "internal_error": 503,
}


class EventSink(Protocol):
    def emit(self, event: BaseModel | Mapping[str, Any]) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class AskCommand:
    account_id: uuid.UUID
    session_id: uuid.UUID
    question: GuideQuestion
    idempotency_key: str | None
    request_id: str


class GuideAbort(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def _not_found(what: str = "Guide session") -> AppError:
    return AppError(404, "resource_not_found", f"{what} not found")


def encode_cursor(session_id: uuid.UUID, seq: int) -> str:
    raw = json.dumps({"sid": str(session_id), "seq": seq}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str, session_id: uuid.UUID) -> int:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if data["sid"] != str(session_id):
            raise ValueError("cursor of another session")
        seq = data["seq"]
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
            raise ValueError("bad seq")
        return seq
    except (ValueError, KeyError, TypeError, binascii.Error, json.JSONDecodeError) as exc:
        raise AppError(400, "invalid_cursor", "The cursor is invalid") from exc


def _model_answered(outcome: GuideAnswerOutcome) -> bool:
    """True when a model produced a parseable answer (MODEL source, or a validation failure
    that is the model's, not the provider's)."""
    if outcome.source is not ResultSource.DEGRADED:
        return True
    return any(
        attempt.outcome == Outcome.VALIDATION_FAILED.value
        and attempt.error_code == "validation_failed"  # not "malformed_output" (truncated)
        for attempt in outcome.attempts
    )


class GuideService:
    def __init__(
        self,
        *,
        settings: Settings,
        uow: UnitOfWork,
        session_factory: SessionFactory,
        retriever: HybridRetriever,
        ledger: QuotaLedger | None = None,
        runner: AgentRunner = default_runner,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._settings = settings
        self._uow = uow
        self._sf = session_factory
        self._retriever = retriever
        self._ledger = ledger
        self._runner = runner
        self._clock = clock

    # ---- sessions -------------------------------------------------------------------------------

    async def _city_of(self, store: GuideStore, session: SessionRecord) -> tuple[uuid.UUID, str]:
        city_id: uuid.UUID | None = None
        if session.place_id is not None:
            city_id = await store.published_place_city(session.place_id)
        if city_id is None and session.trip_id is not None:
            city_id = await store.owned_trip_city(session.trip_id, session.account_id)
        city = await store.city(city_id) if city_id is not None else None
        if city is None:
            city = await store.enabled_city(self._settings.default_city_code)
        if city is None:
            raise AppError(503, "internal_error", "No enabled city", retryable=True)
        return city.id, city.code

    async def _to_schema(self, store: GuideStore, session: SessionRecord) -> GuideSession:
        _, city_code = await self._city_of(store, session)
        return GuideSession(
            id=session.id,
            scope="PLACE" if session.place_id is not None else "CITY",
            city_code=city_code,
            trip_id=session.trip_id,
            place_id=session.place_id,
            locale=session.locale,
            expires_at=session.expires_at,
            created_at=session.created_at,
        )

    async def _owned(
        self, store: GuideStore, account_id: uuid.UUID, session_id: uuid.UUID, *, lock: bool = False
    ) -> SessionRecord:
        session = await store.get_session(session_id, account_id, lock=lock)
        if session is None or session.expires_at <= self._clock():
            raise _not_found()
        return session

    async def create_session(self, account_id: uuid.UUID, body: GuideSessionCreate) -> GuideSession:
        def invalid(message: str, field: str) -> AppError:
            return AppError(
                422,
                "validation_error",
                message,
                context={"fields": [{"location": ["body", field]}]},
            )

        async with self._uow() as store:
            place_city: uuid.UUID | None = None
            if body.scope == "PLACE":
                if body.place_id is None:
                    raise invalid("place_id is required for scope PLACE", "place_id")
                place_city = await store.published_place_city(body.place_id)
                if place_city is None:
                    raise _not_found("Place")
            elif body.place_id is not None:
                raise invalid("place_id must be null for scope CITY", "place_id")
            trip_city: uuid.UUID | None = None
            if body.trip_id is not None:
                trip_city = await store.owned_trip_city(body.trip_id, account_id)
                if trip_city is None:
                    raise _not_found("Trip")
                if place_city is not None and trip_city != place_city:
                    raise invalid("The place is not in the trip's city", "place_id")
            resolved = place_city or trip_city
            if body.city_code is not None:
                city = await store.enabled_city(body.city_code)
                if city is None:
                    raise _not_found("City")
                if resolved is not None and city.id != resolved:
                    raise invalid("city_code does not match the place or trip", "city_code")
                if resolved is None and city.code != self._settings.default_city_code:
                    # A city session without a trip has no city column to pin another city.
                    raise invalid("Only the enabled release city is supported", "city_code")
            elif (
                resolved is None
                and await store.enabled_city(self._settings.default_city_code) is None
            ):
                raise _not_found("City")
            try:
                record = await store.insert_session(
                    account_id=account_id,
                    trip_id=body.trip_id,
                    place_id=body.place_id,
                    locale=body.locale,
                    expires_at=self._clock()
                    + timedelta(days=self._settings.guide_session_ttl_days),
                )
            except IntegrityError as exc:
                await store.rollback()
                if "ck_guide_sessions_context" in str(exc.orig):
                    logger.error("guide city_session_blocked reason=ck_guide_sessions_context")
                    raise AppError(
                        503,
                        "internal_error",
                        "City-level Guide sessions are not available on this database yet",
                        retryable=False,
                    ) from exc
                raise
            result = await self._to_schema(store, record)
            await store.commit()
            return result

    async def get_session(self, account_id: uuid.UUID, session_id: uuid.UUID) -> GuideSession:
        async with self._uow() as store:
            return await self._to_schema(store, await self._owned(store, account_id, session_id))

    async def delete_session(self, account_id: uuid.UUID, session_id: uuid.UUID) -> None:
        async with self._uow() as store:
            session = await self._owned(store, account_id, session_id, lock=True)
            await store.delete_session(session.id)
            await store.commit()

    async def list_messages(
        self, account_id: uuid.UUID, session_id: uuid.UUID, *, cursor: str | None, limit: int
    ) -> GuideMessagePage:
        async with self._uow() as store:
            session = await self._owned(store, account_id, session_id)
            after = decode_cursor(cursor, session.id) if cursor else 0
            items = await store.list_messages(session.id, after_seq=after, limit=limit + 1)
        more = len(items) > limit
        items = items[:limit]
        next_cursor = encode_cursor(session.id, items[-1].seq) if more and items else None
        return GuideMessagePage(next_cursor=next_cursor, items=items)

    # ---- ask ------------------------------------------------------------------------------------

    async def ask(self, command: AskCommand, sink: EventSink) -> None:
        """Emit ``progress``* → (``text``* → ``result``) | ``error``, then close the sink."""
        try:
            await self._ask(command, sink)
        except (GuideAbort, AppError) as abort:
            sink.emit(self._error(command.request_id, abort.code, abort.message, abort.retryable))
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - reported as an error event
            # No traceback or exception text: either may carry the question or bound SQL
            # parameters (privacy rule: never log user questions).
            logger.error(
                json.dumps(
                    {
                        "request_id": command.request_id,
                        "event": "guide_ask_failed",
                        "error": type(exc).__name__,
                    }
                )
            )
            sink.emit(
                self._error(
                    command.request_id, "internal_error", "The answer could not be created", True
                )
            )
        finally:
            sink.close()

    @staticmethod
    def _error(request_id: str, code: str, message: str, retryable: bool) -> dict[str, Any]:
        detail = error_payload(code, message, request_id, retryable=retryable)["error"]
        return {"type": "error", "error": detail}

    async def _claim(
        self, command: AskCommand, fingerprint: str
    ) -> tuple[bool, dict[str, Any] | None]:
        """``(claimed, replay_body)``. A database without the GUIDE_ASK operation (migration
        pending) degrades to no idempotency, logged."""
        key = command.idempotency_key
        if key is None:
            return False, None
        async with self._uow() as store:
            await self._owned(store, command.account_id, command.session_id)
            try:
                existing = await store.claim_idempotency(
                    command.account_id,
                    OP_GUIDE_ASK,
                    key,
                    fingerprint,
                    idempotency.expires_at(self._clock()),
                )
            except IntegrityError:
                await store.rollback()
                logger.warning("guide idempotency=skipped reason=operation_not_allowed")
                return False, None
            if existing is None:
                await store.commit()
                return True, None
            stored = idempotency.replay_or_raise(existing, fingerprint)
            await store.rollback()
            return False, stored.body

    async def _release(
        self, command: AskCommand, claimed: bool, traveler_id: uuid.UUID | None
    ) -> None:
        if not claimed and traveler_id is None:
            return
        try:
            async with self._uow() as store:
                if traveler_id is not None:
                    await store.delete_message(traveler_id)
                if claimed and command.idempotency_key is not None:
                    await store.release_idempotency(
                        command.account_id, OP_GUIDE_ASK, command.idempotency_key
                    )
                await store.commit()
        except Exception:  # noqa: BLE001 - the claim expires on its own
            logger.warning("guide release_failed")

    async def _ask(self, command: AskCommand, sink: EventSink) -> None:
        sink.emit({"type": "progress", "stage": "VALIDATING"})
        question = command.question
        fingerprint = idempotency.request_fingerprint(
            command.session_id, question.model_dump(mode="json")
        )
        claimed, replay = await self._claim(command, fingerprint)
        if replay is not None:
            message = GuideMessage.model_validate(replay)
            sink.emit({"type": "result", "message": message.model_dump(mode="json")})
            return
        traveler_id: uuid.UUID | None = None
        try:
            async with self._uow() as store:
                session = await self._owned(
                    store, command.account_id, command.session_id, lock=True
                )
                seq = await store.next_seq(session.id)
                traveler_id = await store.add_message(
                    session_id=session.id,
                    seq=seq,
                    role="TRAVELER",
                    input_mode=question.input_mode,
                    content=question.content,
                    answer_status=None,
                )
                history = await store.recent_turns(
                    session.id, before_seq=seq, limit=MAX_HISTORY_TURNS
                )
                city_id, _ = await self._city_of(store, session)
                await store.commit()

            ledger = self._ledger or QuotaLedger(self._sf, self._settings)
            async with QuotaBudget(ledger, account_id=command.account_id) as budget:
                # The account question quota (and the Guide budget) is reserved before
                # retrieval, so an over-quota question spends no embedding or model quota.
                decision = await budget.acquire(GUIDE_BUDGET)
                if not decision.allowed:
                    raise GuideAbort(
                        "quota_exceeded", "Daily Guide question limit reached", retryable=True
                    )
                sink.emit({"type": "progress", "stage": "RETRIEVING"})
                async with self._uow() as store:
                    retrieved = await self._retrieve(store, session, city_id, command)
                composed = await self._answer(
                    command, session, retrieved, history, sink, ledger=ledger, budget=budget
                )

            async with self._uow() as store:
                await self._owned(store, command.account_id, session.id, lock=True)
                assistant_id = await store.add_message(
                    session_id=session.id,
                    seq=await store.next_seq(session.id),
                    role="ASSISTANT",
                    input_mode=None,
                    content=composed.content,
                    answer_status=composed.status,
                    citations=citation_rows([citation for _, citation in composed.citations]),
                )
                stored = await store.get_message(assistant_id)
                if stored is None:  # pragma: no cover - just inserted
                    raise GuideAbort(
                        "internal_error", "The answer could not be stored", retryable=True
                    )
                body = stored.model_dump(mode="json")
                if claimed and command.idempotency_key is not None:
                    await store.complete_idempotency(
                        command.account_id,
                        OP_GUIDE_ASK,
                        command.idempotency_key,
                        status=200,
                        body=body,
                        resource_id=assistant_id,
                    )
                await store.commit()
        except BaseException:
            await self._release(command, claimed, traveler_id)
            raise
        logger.info(
            "guide answer status=%s scope=%s evidence=%d citations=%d channels=%s",
            composed.status,
            session.scope,
            len(retrieved.evidence),
            len(composed.citations),
            ",".join(f"{name}:{count}" for name, count in sorted(retrieved.channels.items())),
        )
        for index, claim in enumerate(composed.claims):
            sink.emit({"type": "text", "delta": claim if index == 0 else f" {claim}"})
        sink.emit({"type": "result", "message": body})

    async def _retrieve(
        self,
        store: GuideStore,
        session: SessionRecord,
        city_id: uuid.UUID,
        command: AskCommand,
    ) -> RetrievalResult:
        if session.place_id is not None:
            return await self._retriever.for_place(store, session.place_id, session.locale)
        return await self._retriever.for_city(
            store,
            city_id=city_id,
            question=command.question.content,
            locale=session.locale,
            account_id=command.account_id,
        )

    async def _answer(
        self,
        command: AskCommand,
        session: SessionRecord,
        retrieved: RetrievalResult,
        history: list[tuple[str, str]],
        sink: EventSink,
        *,
        ledger: QuotaLedger,
        budget: QuotaBudget,
    ) -> ComposedAnswer:
        """Answer from the retrieved evidence. ``budget`` already holds ``GUIDE_BUDGET``; the
        account question is committed only when a model answered (released otherwise)."""
        if not retrieved.evidence:
            # Extension point (ADR-010 1.0, out of scope here): the deterministic web fallback,
            # stage SEARCHING_WEB, answer_status ANSWERED_WEB_UNVERIFIED, WEB citations.
            return insufficient(session.locale)
        items, by_id = evidence_items(retrieved.evidence)
        sink.emit({"type": "progress", "stage": "ANSWERING"})
        ctx = AgentContext(
            settings=self._settings,
            ledger=ledger,
            session_factory=self._sf,
            purpose=Purpose.GUIDE_ANSWER,
            account_id=command.account_id,
            budget=budget,
            runner=self._runner,
        )
        try:
            outcome = await write_guide_answer(
                ctx,
                question=command.question.content,
                evidence=items,
                locale="en" if session.locale == "en" else "vi",
                history=history,
            )
        except RedactionError as exc:
            raise GuideAbort(
                "unsupported_request", "The question could not be sent to the Guide safely"
            ) from exc
        if not _model_answered(outcome):
            raise GuideAbort("ai_unavailable", "The Guide is unavailable right now", retryable=True)
        await budget.commit(Bucket.ACCOUNT_QUESTIONS)
        if outcome.dropped_claims:
            logger.info("guide citations dropped_claims=%d", outcome.dropped_claims)
        return compose(outcome.answer, by_id, session.locale)


class CollectingSink:
    """JSON mode of API-028: keeps the events in memory."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event: BaseModel | Mapping[str, Any]) -> None:
        data = event.model_dump(mode="json") if isinstance(event, BaseModel) else dict(event)
        self.events.append(data)

    def close(self) -> None:
        return None

    def terminal(self) -> dict[str, Any] | None:
        return next(
            (e for e in reversed(self.events) if e.get("type") in ("result", "error")), None
        )
