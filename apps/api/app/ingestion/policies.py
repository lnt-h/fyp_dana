"""Provider policy activation (ADR-006, OQ-016, DEC-022).

``activate`` records the terms version the owner checked and sets the policy ACTIVE with
``approved_at``. A DRAFT revision is activated in place; when an ACTIVE revision exists with a
different terms version, a new revision (copying purpose, attribution and field rules) becomes
ACTIVE and the old one is RETIRED. Activating the same terms version again is a no-op.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import audit
from app.curation.system import system_account_id
from app.models.providers import DataProvider, ProviderFieldRule, ProviderPolicy


@dataclass(frozen=True)
class PolicyRow:
    provider_key: str
    provider_kind: str
    policy_revision: int
    status: str
    terms_version: str
    approved_at: datetime | None


async def list_policies(session: AsyncSession) -> list[PolicyRow]:
    rows = (
        await session.execute(
            select(DataProvider.provider_key, DataProvider.provider_kind, ProviderPolicy)
            .join(ProviderPolicy, ProviderPolicy.data_provider_id == DataProvider.id)
            .order_by(DataProvider.provider_key, ProviderPolicy.policy_revision)
        )
    ).all()
    return [
        PolicyRow(
            provider_key=key,
            provider_kind=kind,
            policy_revision=policy.policy_revision,
            status=policy.status,
            terms_version=policy.terms_version,
            approved_at=policy.approved_at,
        )
        for key, kind, policy in rows
    ]


async def activate_policy(session: AsyncSession, provider_key: str, terms_version: str) -> str:
    """Return a one-line outcome; raises ``ValueError`` for an unknown provider."""
    terms_version = terms_version.strip()
    if not terms_version:
        raise ValueError("terms version must not be empty")
    provider_id = await session.scalar(
        select(DataProvider.id).where(DataProvider.provider_key == provider_key)
    )
    if provider_id is None:
        raise ValueError(f"unknown provider {provider_key!r}")
    actor = await system_account_id(session)
    now = datetime.now(UTC)
    active = await session.scalar(
        select(ProviderPolicy).where(
            ProviderPolicy.data_provider_id == provider_id, ProviderPolicy.status == "ACTIVE"
        )
    )
    if active is not None and active.terms_version == terms_version:
        return f"{provider_key}: already ACTIVE (revision {active.policy_revision})"
    latest = await session.scalar(
        select(ProviderPolicy)
        .where(ProviderPolicy.data_provider_id == provider_id)
        .order_by(ProviderPolicy.policy_revision.desc())
        .limit(1)
    )
    if latest is None:
        raise ValueError(f"provider {provider_key!r} has no policy revision; run seed first")
    if active is None and latest.status == "DRAFT":
        latest.terms_version = terms_version
        latest.status = "ACTIVE"
        latest.approved_at = now
        target = latest
    else:
        if active is not None:
            active.status = "RETIRED"
            await session.flush()
        template = active or latest
        next_revision = (
            await session.scalar(
                select(func.max(ProviderPolicy.policy_revision)).where(
                    ProviderPolicy.data_provider_id == provider_id
                )
            )
            or 0
        ) + 1
        target = ProviderPolicy(
            data_provider_id=provider_id,
            policy_revision=next_revision,
            terms_version=terms_version,
            terms_url=template.terms_url,
            purpose=template.purpose,
            attribution_text=template.attribution_text,
            status="ACTIVE",
            approved_at=now,
        )
        session.add(target)
        await session.flush()
        rules = (
            await session.scalars(
                select(ProviderFieldRule).where(ProviderFieldRule.provider_policy_id == template.id)
            )
        ).all()
        for rule in rules:
            session.add(
                ProviderFieldRule(
                    provider_policy_id=target.id,
                    field_name=rule.field_name,
                    persistence_class=rule.persistence_class,
                    max_retention=rule.max_retention,
                )
            )
    await session.flush()
    audit(
        session,
        actor_account_id=actor,
        entity_table="provider_policies",
        entity_id=target.id,
        action="POLICY_CHANGE",
        to_state="ACTIVE",
        detail={
            "provider_key": provider_key,
            "policy_revision": target.policy_revision,
            "terms_version": terms_version,
        },
    )
    await session.commit()
    return f"{provider_key}: ACTIVE (revision {target.policy_revision}, terms {terms_version!r})"
