"""Traveler preferences (``account_preferences``; FR-073..FR-075). Callers pass the verified
internal account ID only; ownership is the caller's account, never a client-supplied ID."""

import uuid
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import AccountPreferences

DEFAULT_LOCALE = "vi"
DEFAULT_ALLOWED_MODES: tuple[str, ...] = ("WALK", "DRIVE")


@dataclass(frozen=True)
class PreferencesRecord:
    locale: str = DEFAULT_LOCALE
    pace: str | None = None
    interest_category_codes: tuple[str, ...] = ()
    allowed_modes: tuple[str, ...] = DEFAULT_ALLOWED_MODES
    day_start_time: time | None = None
    day_end_time: time | None = None
    ai_notice_acknowledged_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PreferencesUpdate:
    locale: str
    allowed_modes: tuple[str, ...]
    interest_category_codes: tuple[str, ...] = ()
    pace: str | None = None
    day_start_time: time | None = None
    day_end_time: time | None = None
    ai_notice_acknowledged: bool = False


def _record(row: Any) -> PreferencesRecord:
    return PreferencesRecord(
        locale=row.locale,
        pace=row.pace,
        interest_category_codes=tuple(row.interest_category_codes),
        allowed_modes=tuple(row.allowed_modes),
        day_start_time=row.day_start_time,
        day_end_time=row.day_end_time,
        ai_notice_acknowledged_at=row.ai_notice_acknowledged_at,
        updated_at=row.updated_at,
    )


class PreferencesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, account_id: uuid.UUID) -> PreferencesRecord | None:
        row = await self._session.scalar(
            select(AccountPreferences).where(AccountPreferences.account_id == account_id)
        )
        return None if row is None else _record(row)

    async def get_or_default(self, account_id: uuid.UUID) -> PreferencesRecord:
        return await self.get(account_id) or PreferencesRecord()

    async def get_locale(self, account_id: uuid.UUID) -> str | None:
        locale: str | None = await self._session.scalar(
            select(AccountPreferences.locale).where(AccountPreferences.account_id == account_id)
        )
        return locale

    async def upsert(self, account_id: uuid.UUID, update: PreferencesUpdate) -> PreferencesRecord:
        """Full replace (PUT semantics). The AI-notice timestamp is set once and kept."""
        values = {
            "locale": update.locale,
            "pace": update.pace,
            "interest_category_codes": list(update.interest_category_codes),
            "allowed_modes": list(update.allowed_modes),
            "day_start_time": update.day_start_time,
            "day_end_time": update.day_end_time,
        }
        acknowledged = func.now() if update.ai_notice_acknowledged else None
        stmt = insert(AccountPreferences).values(
            account_id=account_id, ai_notice_acknowledged_at=acknowledged, **values
        )
        upsert = stmt.on_conflict_do_update(
            index_elements=[AccountPreferences.account_id],
            set_={
                **values,
                "ai_notice_acknowledged_at": func.coalesce(
                    AccountPreferences.ai_notice_acknowledged_at,
                    stmt.excluded.ai_notice_acknowledged_at,
                ),
                "updated_at": func.now(),
            },
        ).returning(*AccountPreferences.__table__.columns)
        row = (await self._session.execute(upsert)).one()
        await self._session.commit()
        return _record(row)
