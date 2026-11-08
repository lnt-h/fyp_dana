"""Persistence for trips, previews, Save, idempotency and deletion jobs (schema.sql §7).

Every owner-scoped read filters by ``account_id`` in SQL, so a foreign row is indistinguishable
from a missing one. Services own transaction boundaries through :meth:`commit` / :meth:`rollback`.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Literal, Protocol

from sqlalchemy import and_, delete, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.account import Account
from app.models.catalog import (
    CatalogPublication,
    FactEvidence,
    PlaceFact,
    PlaceLocalization,
    PublicationFact,
    Source,
    SourceRevision,
    WebPlaceCandidate,
)
from app.models.planning import (
    AccountDeletionJob,
    AccountPreferences,
    IdempotencyRecord,
    PlanPreview,
    PreviewRevision,
    RouteLeg,
    Trip,
    TripDay,
    TripStop,
)
from app.models.providers import DataProvider
from app.models.reference import City, FactField
from app.repositories.accounts import subject_sha256
from app.trips.snapshot import PlanSnapshot, PublishedPlace, SnapshotDay, SnapshotLeg, SnapshotStop

TripSort = Literal["-updated_at", "start_date"]
# data_providers row behind demo-estimated legs (registered by the planner on first use).
ROUTES_ESTIMATE_PROVIDER_KEY = "routes_estimate"
OPEN_DELETION_STATES = ("REQUESTED", "IN_PROGRESS", "FAILED")


@dataclass(frozen=True)
class CityInfo:
    id: uuid.UUID
    code: str
    name_vi: str
    name_en: str
    time_zone: str
    is_enabled: bool


@dataclass(frozen=True)
class PublicationInfo:
    id: uuid.UUID
    place_id: uuid.UUID
    state: str
    name_vi: str
    name_en: str
    location: str | None
    entrance_location: str | None


@dataclass(frozen=True)
class CandidateInfo:
    id: uuid.UUID
    name: str
    name_vi: str | None
    name_en: str | None
    location: str | None
    source_url: str
    fetched_at: datetime


@dataclass(frozen=True)
class FactSource:
    source_revision_id: uuid.UUID
    publisher: str
    title: str | None
    locator: str
    attribution_text: str | None
    license_code: str
    homepage_url: str | None


@dataclass(frozen=True)
class FactInfo:
    id: uuid.UUID
    field_code: str
    knowledge_state: str
    value: dict[str, Any] | None
    verified_at: datetime | None
    valid_until: date | None
    stale_after_days: int | None
    sources: list[FactSource]


@dataclass(frozen=True)
class TripCursor:
    sort: TripSort
    updated_at: datetime | None
    start_date: date | None
    trip_id: uuid.UUID


@dataclass(frozen=True)
class SavedItinerary:
    snapshot: PlanSnapshot
    trip_day_ids: dict[int, uuid.UUID]


class TripStore(Protocol):
    """What the services need from persistence; unit tests provide an in-memory fake."""

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...

    async def get_city(self, city_id: uuid.UUID) -> CityInfo | None: ...
    async def get_account_locale(self, account_id: uuid.UUID) -> str | None: ...

    async def get_trip(
        self, account_id: uuid.UUID, trip_id: uuid.UUID, *, for_update: bool = False
    ) -> Trip | None: ...
    async def list_trips(
        self,
        account_id: uuid.UUID,
        *,
        status: str | None,
        sort: TripSort,
        after: TripCursor | None,
        limit: int,
    ) -> list[Trip]: ...
    async def add_trip(self, trip: Trip) -> Trip: ...
    async def update_trip_title(self, trip: Trip, title: str | None) -> Trip: ...
    async def delete_trip(self, trip: Trip) -> None: ...
    async def saved_itinerary(self, trip_id: uuid.UUID) -> SavedItinerary: ...
    async def active_preview_id(self, trip_id: uuid.UUID) -> uuid.UUID | None: ...
    async def replace_itinerary(self, trip: Trip, snapshot: PlanSnapshot) -> Trip: ...

    async def get_preview(
        self, account_id: uuid.UUID, preview_id: uuid.UUID, *, for_update: bool = False
    ) -> PlanPreview | None: ...
    async def get_revision(
        self, preview_id: uuid.UUID, revision: int
    ) -> PreviewRevision | None: ...
    async def append_revision(
        self, preview: PlanPreview, revision: PreviewRevision
    ) -> PreviewRevision: ...
    async def set_preview_status(self, preview: PlanPreview, status: str) -> None: ...

    async def publications(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, PublicationInfo]: ...
    async def candidates(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, CandidateInfo]: ...
    async def published_places(
        self, place_ids: set[uuid.UUID], city_id: uuid.UUID
    ) -> dict[uuid.UUID, PublishedPlace]: ...
    async def publication_facts(
        self, publication_id: uuid.UUID, field_codes: tuple[str, ...]
    ) -> list[FactInfo]: ...

    async def claim_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        request_sha256: str,
        expires_at: datetime,
    ) -> IdempotencyRecord | None: ...
    async def complete_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        *,
        status: int,
        body: dict[str, Any],
        resource_id: uuid.UUID | None,
    ) -> None: ...

    async def open_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob | None: ...
    async def latest_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob | None: ...
    async def add_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob: ...


SAVED_STOPS_SQL = text(
    """
    SELECT ts.id, ts.trip_day_id, td.day_index, td.day_window_start, td.day_window_end,
           v.effective_trust_level, v.effective_place_id, v.effective_catalog_publication_id,
           ts.web_place_candidate_id, ts.ordinal, ts.planned_arrival, ts.planned_departure,
           ts.visit_minutes, ts.is_locked
      FROM trip_days td
      LEFT JOIN trip_stops ts ON ts.trip_day_id = td.id
      LEFT JOIN vw_trip_stop_trust v ON v.trip_stop_id = ts.id
     WHERE td.trip_id = :trip_id
     ORDER BY td.day_index, ts.ordinal
    """
)


class SQLAlchemyTripStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    # -- reference -----------------------------------------------------------------------------

    async def get_city(self, city_id: uuid.UUID) -> CityInfo | None:
        city = await self.session.get(City, city_id)
        if city is None:
            return None
        return CityInfo(
            id=city.id,
            code=city.code,
            name_vi=city.name_vi,
            name_en=city.name_en,
            time_zone=city.time_zone,
            is_enabled=city.is_enabled,
        )

    async def get_account_locale(self, account_id: uuid.UUID) -> str | None:
        return await self.session.scalar(
            select(AccountPreferences.locale).where(AccountPreferences.account_id == account_id)
        )

    # -- trips ---------------------------------------------------------------------------------

    async def get_trip(
        self, account_id: uuid.UUID, trip_id: uuid.UUID, *, for_update: bool = False
    ) -> Trip | None:
        statement = select(Trip).where(Trip.id == trip_id, Trip.account_id == account_id)
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement.execution_options(populate_existing=True))

    async def list_trips(
        self,
        account_id: uuid.UUID,
        *,
        status: str | None,
        sort: TripSort,
        after: TripCursor | None,
        limit: int,
    ) -> list[Trip]:
        statement = select(Trip).where(Trip.account_id == account_id)
        if status is not None:
            statement = statement.where(Trip.status == status)
        if sort == "-updated_at":
            if after is not None and after.updated_at is not None:
                statement = statement.where(
                    or_(
                        Trip.updated_at < after.updated_at,
                        and_(Trip.updated_at == after.updated_at, Trip.id < after.trip_id),
                    )
                )
            statement = statement.order_by(Trip.updated_at.desc(), Trip.id.desc())
        else:
            if after is not None:
                if after.start_date is None:
                    statement = statement.where(Trip.start_date.is_(None), Trip.id > after.trip_id)
                else:
                    statement = statement.where(
                        or_(
                            Trip.start_date > after.start_date,
                            Trip.start_date.is_(None),
                            and_(Trip.start_date == after.start_date, Trip.id > after.trip_id),
                        )
                    )
            statement = statement.order_by(Trip.start_date.asc().nulls_last(), Trip.id.asc())
        return list((await self.session.scalars(statement.limit(limit))).all())

    async def add_trip(self, trip: Trip) -> Trip:
        self.session.add(trip)
        await self.session.flush()
        await self.session.refresh(trip)
        return trip

    async def update_trip_title(self, trip: Trip, title: str | None) -> Trip:
        trip.title = title
        await self.session.flush()
        await self.session.refresh(trip)
        return trip

    async def delete_trip(self, trip: Trip) -> None:
        await self.session.execute(delete(Trip).where(Trip.id == trip.id))

    async def active_preview_id(self, trip_id: uuid.UUID) -> uuid.UUID | None:
        return await self.session.scalar(
            select(PlanPreview.id).where(
                PlanPreview.trip_id == trip_id,
                PlanPreview.status == "ACTIVE",
                PlanPreview.expires_at > datetime.now(UTC),
            )
        )

    async def saved_itinerary(self, trip_id: uuid.UUID) -> SavedItinerary:
        rows = (await self.session.execute(SAVED_STOPS_SQL, {"trip_id": trip_id})).mappings()
        days: dict[int, SnapshotDay] = {}
        day_ids: dict[int, uuid.UUID] = {}
        for row in rows:
            day_index = int(row["day_index"])
            if day_index not in days:
                day_ids[day_index] = row["trip_day_id"]
                days[day_index] = SnapshotDay(
                    day_index=day_index,
                    day_window_start=row["day_window_start"],
                    day_window_end=row["day_window_end"],
                )
            if row["id"] is None:
                continue
            verified = row["effective_trust_level"] == "VERIFIED"
            days[day_index].stops.append(
                SnapshotStop(
                    id=row["id"],
                    trust_level="VERIFIED" if verified else "WEB_UNVERIFIED",
                    place_id=row["effective_place_id"] if verified else None,
                    catalog_publication_id=(
                        row["effective_catalog_publication_id"] if verified else None
                    ),
                    web_place_candidate_id=None if verified else row["web_place_candidate_id"],
                    ordinal=row["ordinal"],
                    planned_arrival=row["planned_arrival"],
                    planned_departure=row["planned_departure"],
                    visit_minutes=row["visit_minutes"],
                    is_locked=row["is_locked"],
                )
            )
        if day_ids:
            leg_rows = await self.session.execute(
                select(RouteLeg, DataProvider.provider_key)
                .outerjoin(DataProvider, DataProvider.id == RouteLeg.data_provider_id)
                .where(RouteLeg.trip_day_id.in_(list(day_ids.values())))
            )
            by_day = {day_id: index for index, day_id in day_ids.items()}
            for leg, provider_key in leg_rows.tuples():
                days[by_day[leg.trip_day_id]].legs.append(
                    SnapshotLeg(
                        from_stop_id=leg.from_stop_id,
                        to_stop_id=leg.to_stop_id,
                        travel_mode=leg.travel_mode,
                        availability=leg.availability,
                        distance_m=leg.distance_m,
                        duration_s=leg.duration_s,
                        data_provider_id=leg.data_provider_id,
                        measured_at=leg.measured_at,
                        expires_at=leg.expires_at,
                        estimated=provider_key == ROUTES_ESTIMATE_PROVIDER_KEY,
                    )
                )
            for day in days.values():
                order = {stop.id: stop.ordinal for stop in day.stops}
                day.legs.sort(key=lambda leg: order.get(leg.from_stop_id, 0))
        snapshot = PlanSnapshot(days=[days[index] for index in sorted(days)])
        return SavedItinerary(snapshot=snapshot, trip_day_ids=day_ids)

    async def replace_itinerary(self, trip: Trip, snapshot: PlanSnapshot) -> Trip:
        """Replace saved days/stops/legs with ``snapshot`` and advance the trip revision; the
        snapshot's effective planning preferences, when present, become the trip's.

        Runs inside the caller's transaction (ADR-009): the trip row must already be locked.
        """
        await self.session.execute(delete(TripDay).where(TripDay.trip_id == trip.id))
        for day in snapshot.days:
            day_id = uuid.uuid4()
            self.session.add(
                TripDay(
                    id=day_id,
                    trip_id=trip.id,
                    day_index=day.day_index,
                    day_window_start=day.day_window_start,
                    day_window_end=day.day_window_end,
                )
            )
            await self.session.flush()
            for stop in day.stops:
                self.session.add(
                    TripStop(
                        id=stop.id,
                        trip_id=trip.id,
                        trip_day_id=day_id,
                        city_id=trip.city_id,
                        trust_level=stop.trust_level,
                        place_id=stop.place_id,
                        catalog_publication_id=stop.catalog_publication_id,
                        web_place_candidate_id=stop.web_place_candidate_id,
                        ordinal=stop.ordinal,
                        planned_arrival=stop.planned_arrival,
                        planned_departure=stop.planned_departure,
                        visit_minutes=stop.visit_minutes,
                        is_locked=stop.is_locked,
                    )
                )
            await self.session.flush()
            for leg in day.legs:
                self.session.add(
                    RouteLeg(
                        trip_day_id=day_id,
                        from_stop_id=leg.from_stop_id,
                        to_stop_id=leg.to_stop_id,
                        travel_mode=leg.travel_mode,
                        availability=leg.availability,
                        distance_m=leg.distance_m,
                        duration_s=leg.duration_s,
                        data_provider_id=leg.data_provider_id,
                        measured_at=leg.measured_at,
                        expires_at=leg.expires_at,
                    )
                )
            await self.session.flush()
        values: dict[str, Any] = {
            "revision": Trip.revision + 1,
            "status": "SAVED",
            "saved_at": datetime.now(UTC),
        }
        if snapshot.preferences is not None:
            # The preferences the saved plan was generated with become the trip's own.
            values["planning_preferences"] = snapshot.preferences.model_dump(
                mode="json", exclude_none=True
            )
        await self.session.execute(update(Trip).where(Trip.id == trip.id).values(**values))
        await self.session.flush()
        await self.session.refresh(trip)
        return trip

    # -- previews ------------------------------------------------------------------------------

    async def get_preview(
        self, account_id: uuid.UUID, preview_id: uuid.UUID, *, for_update: bool = False
    ) -> PlanPreview | None:
        statement = select(PlanPreview).where(
            PlanPreview.id == preview_id, PlanPreview.account_id == account_id
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement.execution_options(populate_existing=True))

    async def get_revision(self, preview_id: uuid.UUID, revision: int) -> PreviewRevision | None:
        return await self.session.get(PreviewRevision, (preview_id, revision))

    async def append_revision(
        self, preview: PlanPreview, revision: PreviewRevision
    ) -> PreviewRevision:
        self.session.add(revision)
        await self.session.execute(
            update(PlanPreview)
            .where(PlanPreview.id == preview.id)
            .values(head_revision=revision.preview_revision)
        )
        await self.session.flush()
        await self.session.refresh(preview)
        await self.session.refresh(revision)
        return revision

    async def set_preview_status(self, preview: PlanPreview, status: str) -> None:
        await self.session.execute(
            update(PlanPreview).where(PlanPreview.id == preview.id).values(status=status)
        )
        await self.session.flush()
        await self.session.refresh(preview)

    # -- catalog lookups -----------------------------------------------------------------------

    async def publications(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, PublicationInfo]:
        if not ids:
            return {}
        vi = aliased(PlaceLocalization)
        en = aliased(PlaceLocalization)
        rows = await self.session.execute(
            select(
                CatalogPublication.id,
                CatalogPublication.place_id,
                CatalogPublication.state,
                vi.name,
                en.name,
                CatalogPublication.location,
                CatalogPublication.entrance_location,
            )
            .join(vi, vi.id == CatalogPublication.localization_vi_id)
            .join(en, en.id == CatalogPublication.localization_en_id)
            .where(CatalogPublication.id.in_(list(ids)))
        )
        return {
            row[0]: PublicationInfo(
                id=row[0],
                place_id=row[1],
                state=row[2],
                name_vi=row[3],
                name_en=row[4],
                location=row[5],
                entrance_location=row[6],
            )
            for row in rows
        }

    async def candidates(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, CandidateInfo]:
        if not ids:
            return {}
        rows = await self.session.execute(
            select(
                WebPlaceCandidate.id,
                WebPlaceCandidate.name,
                WebPlaceCandidate.name_vi,
                WebPlaceCandidate.name_en,
                WebPlaceCandidate.location,
                SourceRevision.locator,
                WebPlaceCandidate.fetched_at,
            )
            .join(SourceRevision, SourceRevision.id == WebPlaceCandidate.source_revision_id)
            .where(WebPlaceCandidate.id.in_(list(ids)))
        )
        return {
            row[0]: CandidateInfo(
                id=row[0],
                name=row[1],
                name_vi=row[2],
                name_en=row[3],
                location=row[4],
                source_url=row[5],
                fetched_at=row[6],
            )
            for row in rows
        }

    async def published_places(
        self, place_ids: set[uuid.UUID], city_id: uuid.UUID
    ) -> dict[uuid.UUID, PublishedPlace]:
        if not place_ids:
            return {}
        rows = await self.session.scalars(
            select(CatalogPublication).where(
                CatalogPublication.place_id.in_(list(place_ids)),
                CatalogPublication.city_id == city_id,
                CatalogPublication.state == "PUBLISHED",
            )
        )
        return {
            row.place_id: PublishedPlace(
                place_id=row.place_id,
                catalog_publication_id=row.id,
                visit_minutes_min=row.visit_minutes_min,
                visit_minutes_suggested=row.visit_minutes_suggested,
                visit_minutes_max=row.visit_minutes_max,
            )
            for row in rows
        }

    async def publication_facts(
        self, publication_id: uuid.UUID, field_codes: tuple[str, ...]
    ) -> list[FactInfo]:
        facts = (
            await self.session.execute(
                select(PlaceFact, FactField.stale_after_days)
                .join(PublicationFact, PublicationFact.place_fact_id == PlaceFact.id)
                .join(FactField, FactField.code == PlaceFact.field_code)
                .where(
                    PublicationFact.catalog_publication_id == publication_id,
                    PlaceFact.field_code.in_(field_codes),
                )
            )
        ).all()
        result: list[FactInfo] = []
        for fact, stale_after_days in facts:
            source_rows = await self.session.execute(
                select(SourceRevision, Source)
                .join(FactEvidence, FactEvidence.source_revision_id == SourceRevision.id)
                .join(Source, Source.id == SourceRevision.source_id)
                .where(FactEvidence.place_fact_id == fact.id)
            )
            sources = [
                FactSource(
                    source_revision_id=revision.id,
                    publisher=source.publisher,
                    title=revision.title,
                    locator=revision.locator,
                    attribution_text=source.attribution_text,
                    license_code=source.license_code,
                    homepage_url=source.homepage_url,
                )
                for revision, source in source_rows.all()
            ]
            result.append(
                FactInfo(
                    id=fact.id,
                    field_code=fact.field_code,
                    knowledge_state=fact.knowledge_state,
                    value=fact.value,
                    verified_at=fact.verified_at,
                    valid_until=fact.valid_until,
                    stale_after_days=stale_after_days,
                    sources=sources,
                )
            )
        return result

    # -- idempotency ---------------------------------------------------------------------------

    async def claim_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        request_sha256: str,
        expires_at: datetime,
    ) -> IdempotencyRecord | None:
        """Insert an IN_PROGRESS record in the caller's transaction.

        Returns ``None`` when this request now owns the key; otherwise the existing live record.
        A concurrent request with the same key blocks on the primary key until the owner commits
        (then sees COMPLETED) or rolls back (then claims the key itself). Expired records are
        replaced.
        """
        await self.session.execute(
            delete(IdempotencyRecord).where(
                IdempotencyRecord.account_id == account_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.idempotency_key == key,
                IdempotencyRecord.expires_at <= datetime.now(UTC),
            )
        )
        inserted = await self.session.scalar(
            insert(IdempotencyRecord)
            .values(
                account_id=account_id,
                operation=operation,
                idempotency_key=key,
                request_sha256=request_sha256,
                state="IN_PROGRESS",
                expires_at=expires_at,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    IdempotencyRecord.account_id,
                    IdempotencyRecord.operation,
                    IdempotencyRecord.idempotency_key,
                ]
            )
            .returning(IdempotencyRecord.idempotency_key)
        )
        if inserted is not None:
            return None
        return await self.session.scalar(
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.account_id == account_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.idempotency_key == key,
            )
            .execution_options(populate_existing=True)
        )

    async def complete_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        *,
        status: int,
        body: dict[str, Any],
        resource_id: uuid.UUID | None,
    ) -> None:
        await self.session.execute(
            update(IdempotencyRecord)
            .where(
                IdempotencyRecord.account_id == account_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.idempotency_key == key,
            )
            .values(
                state="COMPLETED",
                response_status=status,
                response_body=body,
                resource_id=resource_id,
            )
        )

    # -- deletion ------------------------------------------------------------------------------

    async def open_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob | None:
        return await self.session.scalar(
            select(AccountDeletionJob).where(
                AccountDeletionJob.account_id == account_id,
                AccountDeletionJob.status.in_(OPEN_DELETION_STATES),
            )
        )

    async def latest_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob | None:
        return await self.session.scalar(
            select(AccountDeletionJob)
            .where(AccountDeletionJob.account_id == account_id)
            .order_by(AccountDeletionJob.requested_at.desc())
            .limit(1)
        )

    async def add_deletion_job(self, account_id: uuid.UUID) -> AccountDeletionJob:
        subject = await self.session.scalar(
            select(Account.clerk_user_id).where(Account.id == account_id)
        )
        job = AccountDeletionJob(
            account_id=account_id,
            clerk_subject_sha256=subject_sha256(subject) if subject is not None else None,
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job
