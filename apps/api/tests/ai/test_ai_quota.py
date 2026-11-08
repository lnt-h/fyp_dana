import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.ai.providers import Role, role_chain
from app.ai.quota import (
    PROPOSE_BUDGET,
    Bucket,
    BudgetItem,
    QuotaBudget,
    QuotaLedger,
    bucket_cap,
    period_start,
    select_model,
)
from app.config import Settings

ACCOUNT = uuid.UUID("11111111-1111-4111-8111-111111111111")
# 2026-11-06 18:30 UTC is already 2026-11-07 in Đà Nẵng (UTC+7).
NOW = datetime(2026, 11, 6, 18, 30, tzinfo=UTC)


def ledger_for(db: Any, settings: Settings) -> QuotaLedger:
    return QuotaLedger(db.factory(), settings, clock=lambda: NOW)


def test_period_is_utc_plus_7_day_or_month() -> None:
    assert period_start(Bucket.GROQ, NOW) == date(2026, 11, 7)
    assert period_start(Bucket.TAVILY_MONTH, NOW) == date(2026, 11, 1)


def test_caps_come_from_settings(settings: Settings) -> None:
    assert bucket_cap(Bucket.GEMINI_FLASH, settings) == 2
    assert bucket_cap(Bucket.TAVILY_MONTH, settings) == settings.quota_tavily_per_month
    assert bucket_cap(Bucket.GEMINI_EMBED, settings) == settings.quota_gemini_embed_per_day


async def test_reserve_until_cap_then_deny(db: Any, settings: Settings) -> None:
    ledger = ledger_for(db, settings)
    first = await ledger.reserve(bucket=Bucket.GEMINI_FLASH)
    second = await ledger.reserve(bucket=Bucket.GEMINI_FLASH)
    third = await ledger.reserve(bucket=Bucket.GEMINI_FLASH)
    assert first.allowed and first.remaining == 1 and first.reservation is not None
    assert second.allowed and second.remaining == 0
    assert not third.allowed and third.remaining == 0 and third.reservation is None
    assert first.reservation.period_start == date(2026, 11, 7)
    # One short transaction per reservation.
    assert db.sessions_opened == 3 and db.commits == 3
    assert db.statements[:2] == ["quota:ensure", "quota:reserve"]
    assert db.statements[-1] == "quota:read"


async def test_commit_and_release(db: Any, settings: Settings) -> None:
    ledger = ledger_for(db, settings)
    a = (await ledger.reserve(bucket=Bucket.GROQ)).reservation
    b = (await ledger.reserve(bucket=Bucket.GROQ)).reservation
    assert a is not None and b is not None
    await ledger.commit(a)
    await ledger.release(b)
    (row,) = db.ledger.values()
    assert row["used"] == 1 and row["reserved"] == 0
    again = await ledger.reserve(bucket=Bucket.GROQ)
    assert again.allowed and again.remaining == 0


async def test_account_buckets_are_per_account(db: Any, settings: Settings) -> None:
    ledger = ledger_for(db, settings)
    with pytest.raises(ValueError):
        await ledger.reserve(bucket=Bucket.ACCOUNT_PROPOSALS)
    assert (await ledger.reserve(bucket=Bucket.ACCOUNT_PROPOSALS, account_id=ACCOUNT)).allowed
    assert not (await ledger.reserve(bucket=Bucket.ACCOUNT_PROPOSALS, account_id=ACCOUNT)).allowed
    other = uuid.uuid4()
    assert (await ledger.reserve(bucket=Bucket.ACCOUNT_PROPOSALS, account_id=other)).allowed
    # Global buckets ignore the account id.
    await ledger.reserve(bucket=Bucket.GROQ, account_id=ACCOUNT)
    assert any(key[1] is None and key[2] == "GROQ" for key in db.ledger)


async def test_database_error_degrades_instead_of_raising(db: Any, settings: Settings) -> None:
    db.fail = True
    decision = await ledger_for(db, settings).reserve(bucket=Bucket.PLACES)
    assert not decision.allowed and decision.reservation is None


async def test_budget_releases_everything_when_required_item_fails(
    db: Any, settings: Settings
) -> None:
    ledger = ledger_for(db, settings)
    budget = QuotaBudget(ledger, account_id=ACCOUNT)
    items = (
        BudgetItem(Bucket.GEMINI_FLASH, required=False),
        BudgetItem(Bucket.ACCOUNT_PROPOSALS, amount=2),  # cap 1 → denied
    )
    decision = await budget.acquire(items)
    assert not decision.allowed and decision.bucket is Bucket.ACCOUNT_PROPOSALS
    assert budget.held == ()
    assert all(row["reserved"] == 0 for row in db.ledger.values())


async def test_budget_optional_items_may_be_missing(
    db: Any, settings_factory: Callable[..., Settings]
) -> None:
    ledger = ledger_for(db, settings_factory(quota_gemini_flash_per_day=0))
    async with QuotaBudget(ledger, account_id=ACCOUNT) as budget:
        decision = await budget.acquire(PROPOSE_BUDGET)
        assert decision.allowed
        assert {r.bucket for r in budget.held} == {
            Bucket.ACCOUNT_PROPOSALS,
            Bucket.GEMINI_FLASH_LITE,
        }
        await budget.commit(Bucket.ACCOUNT_PROPOSALS)
    # Exit released the unused Flash-Lite reservation; the proposal stays committed.
    rows = {key[2]: row for key, row in db.ledger.items()}
    assert rows["ACCOUNT_PROPOSALS"]["used"] == 1
    assert rows["GEMINI_FLASH_LITE"]["reserved"] == 0 and rows["GEMINI_FLASH_LITE"]["used"] == 0


async def test_budget_releases_on_exception(db: Any, settings: Settings) -> None:
    ledger = ledger_for(db, settings)
    with pytest.raises(RuntimeError):
        async with QuotaBudget(ledger, account_id=ACCOUNT) as budget:
            await budget.acquire(PROPOSE_BUDGET)
            raise RuntimeError("provider exploded")
    assert all(row["reserved"] == 0 for row in db.ledger.values())


async def test_select_model_uses_budget_reservation_first(db: Any, settings: Settings) -> None:
    ledger = ledger_for(db, settings)
    async with QuotaBudget(ledger, account_id=ACCOUNT) as budget:
        await budget.acquire(PROPOSE_BUDGET)
        pick = await select_model(role_chain(Role.SELECTOR), ledger, budget=budget)
        assert pick is not None and pick.index == 0
        assert pick.spec.model_id == "gemini-3.6-flash"
        assert pick.reservation.bucket is Bucket.GEMINI_FLASH
    rows = {key[2]: row for key, row in db.ledger.items()}
    assert rows["GEMINI_FLASH"]["reserved"] == 1  # handed to the caller, not double-booked


async def test_chain_falls_back_to_groq_then_exhausts(
    db: Any, settings_factory: Callable[..., Settings]
) -> None:
    ledger = ledger_for(
        db,
        settings_factory(
            quota_gemini_flash_per_day=0,
            quota_gemini_flash_lite_per_day=0,
            quota_groq_per_day=1,
        ),
    )
    chain = role_chain(Role.SELECTOR)
    pick = await select_model(chain, ledger)
    assert pick is not None and pick.spec.model_id == "openai/gpt-oss-120b" and pick.index == 2
    await ledger.commit(pick.reservation)
    assert await select_model(chain, ledger) is None


async def test_chain_skips_unconfigured_provider(
    db: Any, settings_factory: Callable[..., Settings]
) -> None:
    ledger = ledger_for(db, settings_factory(gemini_api_key=None))
    pick = await select_model(role_chain(Role.WRITER_GUIDE), ledger)
    assert pick is not None and pick.spec.model_id == "openai/gpt-oss-120b"
    assert not any(key[2] == "GEMINI_FLASH" for key in db.ledger)  # nothing reserved for it


async def test_chain_retry_after_failed_call(db: Any, settings: Settings) -> None:
    ledger = ledger_for(db, settings)
    chain = role_chain(Role.WRITER_RATIONALE)
    first = await select_model(chain, ledger)
    assert first is not None and first.index == 0
    await ledger.commit(first.reservation)  # attempted, failed validation
    second = await select_model(chain[first.index + 1 :], ledger)
    assert second is not None and second.spec.model_id == "openai/gpt-oss-120b"
