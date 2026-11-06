"""Free-tier quota ledger (DEC-018, architecture §3.3).

Every model, search, Places or Routes call reserves budget first. Each ledger operation is a
short transaction of its own, opened from a session factory, so no transaction is held open
across a provider call. Exhaustion is a :class:`QuotaDecision` with ``allowed=False``; the
ledger never raises on a cap, the caller degrades (selector → rule-based, writer → null
rationale, researcher → skipped, Guide → ``INSUFFICIENT_EVIDENCE``).

Accounting rule for callers: commit a reservation once the provider call was *attempted*
(success, validation failure, provider error or timeout all consume provider quota); release
it only when the call never happened.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
from enum import StrEnum
from types import TracebackType
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import (
    GEMINI_EMBEDDING,
    GEMINI_FLASH,
    GEMINI_FLASH_LITE,
    ModelSpec,
    Provider,
    provider_configured,
)
from app.config import Settings

logger = logging.getLogger("gonarra.ai")

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]

# Quota periods follow the Vietnamese calendar day (UTC+7, no DST).
VN_TZ = timezone(timedelta(hours=7))


class Scope(StrEnum):
    GLOBAL = "GLOBAL"
    ACCOUNT = "ACCOUNT"


class Bucket(StrEnum):
    GEMINI_FLASH = "GEMINI_FLASH"
    GEMINI_FLASH_LITE = "GEMINI_FLASH_LITE"
    GEMINI_EMBED = "GEMINI_EMBED"
    GROQ = "GROQ"
    TAVILY_DAY = "TAVILY_DAY"
    TAVILY_MONTH = "TAVILY_MONTH"
    PLACES = "PLACES"
    ROUTES_ELEMENTS = "ROUTES_ELEMENTS"
    ACCOUNT_PROPOSALS = "ACCOUNT_PROPOSALS"
    ACCOUNT_QUESTIONS = "ACCOUNT_QUESTIONS"


ACCOUNT_BUCKETS = frozenset({Bucket.ACCOUNT_PROPOSALS, Bucket.ACCOUNT_QUESTIONS})
MONTHLY_BUCKETS = frozenset({Bucket.TAVILY_MONTH})


def bucket_scope(bucket: Bucket) -> Scope:
    return Scope.ACCOUNT if bucket in ACCOUNT_BUCKETS else Scope.GLOBAL


def bucket_cap(bucket: Bucket, settings: Settings) -> int:
    caps: dict[Bucket, int] = {
        Bucket.GEMINI_FLASH: settings.quota_gemini_flash_per_day,
        Bucket.GEMINI_FLASH_LITE: settings.quota_gemini_flash_lite_per_day,
        Bucket.GEMINI_EMBED: settings.quota_gemini_embed_per_day,
        Bucket.GROQ: settings.quota_groq_per_day,
        Bucket.TAVILY_DAY: settings.quota_tavily_per_day,
        Bucket.TAVILY_MONTH: settings.quota_tavily_per_month,
        Bucket.PLACES: settings.quota_places_per_day,
        Bucket.ROUTES_ELEMENTS: settings.quota_routes_elements_per_day,
        Bucket.ACCOUNT_PROPOSALS: settings.quota_account_proposals_per_day,
        Bucket.ACCOUNT_QUESTIONS: settings.quota_account_questions_per_day,
    }
    return caps[bucket]


def period_start(bucket: Bucket, now: datetime) -> date:
    """Start of the quota period containing ``now``: UTC+7 day, or UTC+7 month."""
    local = now.astimezone(VN_TZ).date()
    return local.replace(day=1) if bucket in MONTHLY_BUCKETS else local


def bucket_for_spec(spec: ModelSpec) -> Bucket:
    if spec.provider is Provider.GROQ:
        return Bucket.GROQ
    by_model = {
        GEMINI_FLASH: Bucket.GEMINI_FLASH,
        GEMINI_FLASH_LITE: Bucket.GEMINI_FLASH_LITE,
        GEMINI_EMBEDDING: Bucket.GEMINI_EMBED,
    }
    try:
        return by_model[spec.model_id]
    except KeyError as exc:
        raise ValueError(f"no quota bucket for model {spec.model_id}") from exc


@dataclass(frozen=True, slots=True)
class QuotaReservation:
    ledger_id: uuid.UUID
    bucket: Bucket
    amount: int
    account_id: uuid.UUID | None
    period_start: date


@dataclass(frozen=True, slots=True)
class QuotaDecision:
    allowed: bool
    bucket: Bucket
    remaining: int
    reservation: QuotaReservation | None = None


# SQL comments tag each statement (visible in pg_stat_statements; used by unit-test fakes).
_ENSURE_ROW = text(
    "/* quota:ensure */ INSERT INTO ai_quota_ledger "
    "(id, scope, account_id, bucket, period_start, cap, used, reserved, updated_at) "
    "VALUES (:id, :scope, :account_id, :bucket, :period_start, :cap, 0, 0, now()) "
    "ON CONFLICT DO NOTHING"
)
_RESERVE = text(
    "/* quota:reserve */ UPDATE ai_quota_ledger "
    "SET reserved = reserved + :amount, cap = :cap, updated_at = now() "
    "WHERE scope = :scope AND account_id IS NOT DISTINCT FROM :account_id "
    "AND bucket = :bucket AND period_start = :period_start "
    "AND used + reserved + :amount <= :cap "
    "RETURNING id, cap, used, reserved"
)
_READ = text(
    "/* quota:read */ SELECT cap, used, reserved FROM ai_quota_ledger "
    "WHERE scope = :scope AND account_id IS NOT DISTINCT FROM :account_id "
    "AND bucket = :bucket AND period_start = :period_start"
)
_COMMIT = text(
    "/* quota:commit */ UPDATE ai_quota_ledger "
    "SET used = used + :amount, reserved = GREATEST(reserved - :amount, 0), updated_at = now() "
    "WHERE id = :id"
)
_RELEASE = text(
    "/* quota:release */ UPDATE ai_quota_ledger "
    "SET reserved = GREATEST(reserved - :amount, 0), updated_at = now() "
    "WHERE id = :id"
)


class QuotaLedger:
    """Atomic reserve / commit / release over ``ai_quota_ledger``."""

    def __init__(
        self,
        session_factory: SessionFactory,
        settings: Settings,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._clock = clock or (lambda: datetime.now(UTC))

    @property
    def settings(self) -> Settings:
        return self._settings

    async def reserve(
        self, *, bucket: Bucket, amount: int = 1, account_id: uuid.UUID | None = None
    ) -> QuotaDecision:
        """Reserve ``amount`` units. Never raises on a cap or a database error."""
        if amount < 1:
            raise ValueError("amount must be >= 1")
        scope = bucket_scope(bucket)
        if scope is Scope.ACCOUNT and account_id is None:
            raise ValueError(f"{bucket.value} is per account; account_id is required")
        owner = account_id if scope is Scope.ACCOUNT else None
        cap = bucket_cap(bucket, self._settings)
        start = period_start(bucket, self._clock())
        params: dict[str, Any] = {
            "scope": scope.value,
            "account_id": owner,
            "bucket": bucket.value,
            "period_start": start,
            "cap": cap,
            "amount": amount,
        }
        current: Any = None
        try:
            async with self._session_factory() as session:
                await session.execute(_ENSURE_ROW, {**params, "id": uuid.uuid4()})
                row = (await session.execute(_RESERVE, params)).mappings().first()
                if row is None:
                    current = (await session.execute(_READ, params)).mappings().first()
                await session.commit()
        except SQLAlchemyError:
            logger.warning("quota bucket=%s decision=error", bucket.value)
            return QuotaDecision(allowed=False, bucket=bucket, remaining=0)

        if row is None:
            remaining = _remaining(current) if current is not None else 0
            logger.info("quota bucket=%s decision=denied remaining=%d", bucket.value, remaining)
            return QuotaDecision(allowed=False, bucket=bucket, remaining=remaining)

        reservation = QuotaReservation(
            ledger_id=row["id"],
            bucket=bucket,
            amount=amount,
            account_id=owner,
            period_start=start,
        )
        remaining = _remaining(row)
        logger.info("quota bucket=%s decision=reserved remaining=%d", bucket.value, remaining)
        return QuotaDecision(
            allowed=True, bucket=bucket, remaining=remaining, reservation=reservation
        )

    async def commit(self, reservation: QuotaReservation) -> None:
        """Move a reservation from ``reserved`` to ``used`` (the call was attempted)."""
        await self._settle(_COMMIT, reservation, "committed")

    async def release(self, reservation: QuotaReservation) -> None:
        """Return an unused reservation (the call never happened)."""
        await self._settle(_RELEASE, reservation, "released")

    async def _settle(self, stmt: Any, reservation: QuotaReservation, label: str) -> None:
        params = {"id": reservation.ledger_id, "amount": reservation.amount}
        try:
            async with self._session_factory() as session:
                await session.execute(stmt, params)
                await session.commit()
        except SQLAlchemyError:
            # Bookkeeping must not fail the request; a stuck reservation expires with its period.
            logger.warning("quota bucket=%s decision=%s_error", reservation.bucket.value, label)
            return
        logger.info("quota bucket=%s decision=%s", reservation.bucket.value, label)


def _remaining(row: Any) -> int:
    return max(0, int(row["cap"]) - int(row["used"]) - int(row["reserved"]))


@dataclass(frozen=True, slots=True)
class BudgetItem:
    bucket: Bucket
    amount: int = 1
    # A required item that cannot be reserved denies the whole operation. An optional item
    # (typically a preferred model) may be missing; the role chain then falls back.
    required: bool = True


# Presets per operation (architecture §3.3). Model buckets are optional: the chain falls back
# to Groq or degrades; only the per-account caps refuse an operation.
PROPOSE_BUDGET: tuple[BudgetItem, ...] = (
    BudgetItem(Bucket.ACCOUNT_PROPOSALS),
    BudgetItem(Bucket.GEMINI_FLASH, required=False),
    BudgetItem(Bucket.GEMINI_FLASH_LITE, required=False),
)
REGENERATE_DAY_BUDGET: tuple[BudgetItem, ...] = (
    BudgetItem(Bucket.ACCOUNT_PROPOSALS),
    BudgetItem(Bucket.GEMINI_FLASH_LITE, required=False),
)
GUIDE_BUDGET: tuple[BudgetItem, ...] = (
    BudgetItem(Bucket.ACCOUNT_QUESTIONS),
    BudgetItem(Bucket.GEMINI_FLASH, required=False),
)


class QuotaBudget:
    """Holds the reservations of one operation; unused ones are released on exit.

    Usage::

        async with QuotaBudget(ledger, account_id=account_id) as budget:
            decision = await budget.acquire(PROPOSE_BUDGET)
            if not decision.allowed:
                ...  # refuse (account cap reached)
            pick = await select_model(role_chain(Role.SELECTOR), ledger, budget=budget)
    """

    def __init__(self, ledger: QuotaLedger, *, account_id: uuid.UUID | None = None) -> None:
        self._ledger = ledger
        self._account_id = account_id
        self._held: list[QuotaReservation] = []

    @property
    def ledger(self) -> QuotaLedger:
        return self._ledger

    @property
    def held(self) -> tuple[QuotaReservation, ...]:
        return tuple(self._held)

    async def acquire(self, items: Sequence[BudgetItem]) -> QuotaDecision:
        """Reserve every item. If a required one fails, release everything and deny."""
        last: QuotaDecision | None = None
        for item in items:
            account = self._account_id if item.bucket in ACCOUNT_BUCKETS else None
            decision = await self._ledger.reserve(
                bucket=item.bucket, amount=item.amount, account_id=account
            )
            if decision.reservation is not None:
                self._held.append(decision.reservation)
            elif item.required:
                await self.release_all()
                return decision
            last = decision
        if last is None:
            raise ValueError("budget needs at least one item")
        return QuotaDecision(allowed=True, bucket=last.bucket, remaining=last.remaining)

    def take(self, bucket: Bucket) -> QuotaReservation | None:
        """Hand over a held reservation for ``bucket``; the caller commits or releases it."""
        for index, reservation in enumerate(self._held):
            if reservation.bucket is bucket:
                return self._held.pop(index)
        return None

    async def commit(self, bucket: Bucket) -> None:
        """Commit a held reservation (e.g. the account proposal once the preview is ready)."""
        reservation = self.take(bucket)
        if reservation is not None:
            await self._ledger.commit(reservation)

    async def release_all(self) -> None:
        held, self._held = self._held, []
        for reservation in held:
            await self._ledger.release(reservation)

    async def __aenter__(self) -> QuotaBudget:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.release_all()


@dataclass(frozen=True, slots=True)
class ChainSelection:
    spec: ModelSpec
    index: int  # position in the chain passed to select_model
    reservation: QuotaReservation


async def select_model(
    chain: Sequence[ModelSpec],
    ledger: QuotaLedger,
    *,
    budget: QuotaBudget | None = None,
) -> ChainSelection | None:
    """First model in ``chain`` whose provider is configured and whose bucket has budget.

    A reservation already held by ``budget`` for the bucket is used before reserving anew.
    ``None`` means the chain is exhausted and the caller degrades. After a failed call, commit
    the reservation and call again with ``chain[selection.index + 1:]``.
    """
    for index, spec in enumerate(chain):
        if not provider_configured(spec.provider, ledger.settings):
            logger.info("chain role=%s model=%s skipped=not_configured", spec.role, spec.model_id)
            continue
        bucket = bucket_for_spec(spec)
        reservation = budget.take(bucket) if budget is not None else None
        if reservation is None:
            decision = await ledger.reserve(bucket=bucket)
            reservation = decision.reservation
        if reservation is not None:
            logger.info("chain role=%s model=%s selected", spec.role, spec.model_id)
            return ChainSelection(spec=spec, index=index, reservation=reservation)
    logger.info("chain role=%s exhausted", chain[0].role if chain else "-")
    return None
