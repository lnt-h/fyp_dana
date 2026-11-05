"""Account deletion runner (FR-071, BR-021): ``uv run python -m app.cli run-deletion-jobs``.

Purge order, in one transaction per job (children before parents so every step is explicit even
where a cascade would also apply):

1. guide_sessions (cascades guide_messages, guide_message_citations)
2. plan_previews (cascades preview_revisions)
3. trips (cascades trip_days, trip_stops, route_legs)
4. account_preferences
5. ai_quota_ledger rows of scope ACCOUNT
6. ai_invocations
7. idempotency_records
8. the job row is unlinked (account_id NULL) and marked COMPLETED
9. the accounts row (study_participants and curator references are SET NULL by FK)

A failure rolls the purge back, marks the job FAILED with the exception class name only (never
data) and leaves it for the next run. Deleting the Clerk user is not done here (no Clerk backend
call yet); see the T-08 handoff.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Final

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.ai import AIInvocation, AIQuotaLedger
from app.models.guide import GuideSession
from app.models.planning import (
    AccountDeletionJob,
    AccountPreferences,
    IdempotencyRecord,
    PlanPreview,
    Trip,
)

logger = logging.getLogger("gonarra.deletion")

STUCK_AFTER: Final = timedelta(hours=1)
DEFAULT_MAX_ATTEMPTS: Final = 10


@dataclass
class DeletionRunReport:
    completed: list[uuid.UUID] = field(default_factory=list)
    failed: list[uuid.UUID] = field(default_factory=list)


async def purge_account(session: AsyncSession, account_id: uuid.UUID) -> None:
    """Delete the account's private data in the documented order (caller commits)."""
    await session.execute(delete(GuideSession).where(GuideSession.account_id == account_id))
    await session.execute(delete(PlanPreview).where(PlanPreview.account_id == account_id))
    await session.execute(delete(Trip).where(Trip.account_id == account_id))
    await session.execute(
        delete(AccountPreferences).where(AccountPreferences.account_id == account_id)
    )
    await session.execute(
        delete(AIQuotaLedger).where(
            AIQuotaLedger.scope == "ACCOUNT", AIQuotaLedger.account_id == account_id
        )
    )
    await session.execute(delete(AIInvocation).where(AIInvocation.account_id == account_id))
    await session.execute(
        delete(IdempotencyRecord).where(IdempotencyRecord.account_id == account_id)
    )


async def due_job_ids(
    session: AsyncSession, *, max_attempts: int, now: datetime, job_ids: set[uuid.UUID] | None
) -> list[uuid.UUID]:
    statement = (
        select(AccountDeletionJob.id)
        .where(
            AccountDeletionJob.attempt_count < max_attempts,
            or_(
                AccountDeletionJob.status.in_(("REQUESTED", "FAILED")),
                (AccountDeletionJob.status == "IN_PROGRESS")
                & (AccountDeletionJob.updated_at < now - STUCK_AFTER),
            ),
        )
        .order_by(AccountDeletionJob.requested_at)
    )
    if job_ids is not None:
        statement = statement.where(AccountDeletionJob.id.in_(list(job_ids)))
    return list((await session.scalars(statement)).all())


async def run_job(session: AsyncSession, job_id: uuid.UUID) -> bool:
    """Run one job; returns True when it completed. Commits its own transactions."""
    job = await session.scalar(
        select(AccountDeletionJob)
        .where(AccountDeletionJob.id == job_id)
        .with_for_update(skip_locked=True)
    )
    if job is None or job.status == "COMPLETED":
        await session.rollback()
        return False
    account_id = job.account_id
    job.status = "IN_PROGRESS"
    job.attempt_count += 1
    job.failure_reason = None
    await session.commit()

    try:
        if account_id is not None:
            await purge_account(session, account_id)
        await session.execute(
            update(AccountDeletionJob)
            .where(AccountDeletionJob.id == job_id)
            .values(
                status="COMPLETED",
                account_id=None,
                completed_at=datetime.now(UTC),
                failure_reason=None,
            )
        )
        if account_id is not None:
            await session.execute(delete(Account).where(Account.id == account_id))
        await session.commit()
        return True
    except Exception as exc:
        await session.rollback()
        logger.warning('{"event": "deletion_job_failed", "job_id": "%s"}', job_id)
        await session.execute(
            update(AccountDeletionJob)
            .where(AccountDeletionJob.id == job_id)
            .values(status="FAILED", failure_reason=type(exc).__name__)
        )
        await session.commit()
        return False


async def run_deletion_jobs(
    session: AsyncSession,
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    job_ids: set[uuid.UUID] | None = None,
) -> DeletionRunReport:
    """Process every due job (REQUESTED, FAILED, or IN_PROGRESS stuck > 1 h)."""
    report = DeletionRunReport()
    ids = await due_job_ids(
        session, max_attempts=max_attempts, now=datetime.now(UTC), job_ids=job_ids
    )
    await session.rollback()
    for job_id in ids:
        if await run_job(session, job_id):
            report.completed.append(job_id)
        else:
            report.failed.append(job_id)
    return report
