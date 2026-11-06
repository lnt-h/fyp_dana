"""Account deletion runner (FR-071, BR-021): ``uv run python -m app.cli run-deletion-jobs``.

Per job:

A. Lock the job, read the account's Clerk subject, mark it IN_PROGRESS (attempt + 1), commit.
B. Delete the Clerk user (``DELETE /v1/users/{id}``; 404 = already deleted). This runs *before*
   the DB purge because the purge removes the only copy of the subject: a Clerk failure leaves the
   database untouched and the job FAILED for the next run. If Clerk succeeds and the purge then
   fails, the retry repeats the Clerk call (404 → success) and the purge, so every retry is
   idempotent. Without ``GONARRA_CLERK_SECRET_KEY`` this step is skipped with a warning that
   carries only the job id. Until the purge finishes, the open job makes every other ``/v1``
   route answer 409 ``deletion_in_progress`` (``app.security.clerk``).
C. DB purge, in one transaction (children before parents so every step is explicit even
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

A failure in B or C rolls back, marks the job FAILED with the exception class name only (never
data) and leaves it for the next run.

A COMPLETED job keeps no Clerk subject, only ``clerk_subject_sha256`` (written when the job is
created, backfilled in step A for older jobs); ``get_account_allowing_deletion`` refuses a
still-valid token whose subject hash matches a COMPLETED job instead of re-creating an account.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Final

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
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
from app.repositories.accounts import subject_sha256
from app.security.clerk_backend import ClerkUserDeleter, clerk_user_deleter

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


async def run_job(
    session: AsyncSession, job_id: uuid.UUID, user_deleter: ClerkUserDeleter | None = None
) -> bool:
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
    subject = (
        await session.scalar(select(Account.clerk_user_id).where(Account.id == account_id))
        if account_id is not None
        else None
    )
    if subject is not None and job.clerk_subject_sha256 is None:
        job.clerk_subject_sha256 = subject_sha256(subject)
    job.status = "IN_PROGRESS"
    job.attempt_count += 1
    job.failure_reason = None
    await session.commit()

    try:
        if subject is not None:
            if user_deleter is None:
                logger.warning('{"event": "deletion_clerk_not_configured", "job_id": "%s"}', job_id)
            else:
                await user_deleter.delete_user(subject)
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
    user_deleter: ClerkUserDeleter | None = None,
    settings: Settings | None = None,
) -> DeletionRunReport:
    """Process every due job (REQUESTED, FAILED, or IN_PROGRESS stuck > 1 h).

    ``user_deleter`` defaults to the Clerk Backend client built from ``settings`` (or the process
    settings); it is ``None`` — Clerk step skipped with a warning — when no secret is configured.
    """
    if user_deleter is None:
        user_deleter = clerk_user_deleter(settings or get_settings())
    report = DeletionRunReport()
    ids = await due_job_ids(
        session, max_attempts=max_attempts, now=datetime.now(UTC), job_ids=job_ids
    )
    await session.rollback()
    for job_id in ids:
        if await run_job(session, job_id, user_deleter):
            report.completed.append(job_id)
        else:
            report.failed.append(job_id)
    return report
