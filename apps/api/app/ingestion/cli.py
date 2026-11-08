"""Content pipeline commands (DEC-022), registered on ``python -m app.cli``.

policy list | policy activate <provider_key> --terms-version <text>
areas load
ingest wikidata | ingest wikipedia | ingest osm | ingest commons | ingest sheet <csv>
web-candidates promote
publish auto [--dry-run] [--include-withdrawn] [--no-embed]
closure-rules load [--file <yaml>]
pipeline run [--sheet <csv>] [--dry-run] [--no-embed]
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.curation.auto_publish import GATE_RULES, PublishReport, auto_publish
from app.curation.embedding import ChunkEmbedder, DisabledEmbedder, GeminiChunkEmbedder
from app.curation.web_promotion import promote_pending
from app.db.session import engine, session_factory
from app.ingestion.areas import DATA_DIR, write_area_boundaries
from app.ingestion.calendar import CalendarReport, load_calendar
from app.ingestion.common import PolicyNotActiveError, RunReport, load_city
from app.ingestion.commons import import_commons
from app.ingestion.osm import import_osm
from app.ingestion.policies import activate_policy, list_policies
from app.ingestion.sheet import import_sheet
from app.ingestion.wikidata import import_wikidata
from app.ingestion.wikipedia import import_wikipedia

policy_app = typer.Typer(help="Provider policies (ADR-006 default deny).", no_args_is_help=True)
areas_app = typer.Typer(help="Travel-area polygons.", no_args_is_help=True)
ingest_app = typer.Typer(help="Importers (create/update DRAFT places).", no_args_is_help=True)
web_app = typer.Typer(help="Research web candidates.", no_args_is_help=True)
publish_app = typer.Typer(help="Automated publication gate.", no_args_is_help=True)
calendar_app = typer.Typer(help="Operator calendar (closure rules).", no_args_is_help=True)
pipeline_app = typer.Typer(help="All pipeline steps in order.", no_args_is_help=True)

DEFAULT_SHEET = DATA_DIR / "sheet" / "da-nang.csv"


def _run[T](work: Callable[[AsyncSession], Awaitable[T]]) -> T:
    async def runner() -> T:
        try:
            async with session_factory() as session:
                return await work(session)
        finally:
            await engine.dispose()

    return asyncio.run(runner())


def _city() -> str:
    return get_settings().default_city_code


def _embedder(no_embed: bool) -> ChunkEmbedder:
    if no_embed:
        return DisabledEmbedder()
    return GeminiChunkEmbedder(get_settings(), session_factory)


def _echo_run(report: RunReport) -> None:
    if report.skipped_unchanged:
        typer.echo(f"{report.provider_key}: unchanged release, run skipped")
        return
    typer.echo(
        f"{report.provider_key}: records={report.record_count} accepted={report.accepted} "
        f"rejected={report.rejected} new_places={report.created_places}"
    )
    for reason, count in sorted(report.rejection_reasons.items()):
        typer.echo(f"  rejected {reason}: {count}")
    extra = getattr(report, "unmapped", None)
    if extra is not None:
        typer.echo(f"  skipped (unmapped class): {extra}")
    for label, attribute in (
        ("matched by wikidata tag", "matched_wikidata"),
        ("matched by name within 100 m", "matched_name"),
        ("with parsed opening hours", "with_opening_hours"),
        ("places with photos", "places_with_media"),
        ("media assets", "media_assets"),
    ):
        value = getattr(report, attribute, None)
        if value is not None:
            typer.echo(f"  {label}: {value}")
    by_license = getattr(report, "by_license", None)
    if by_license:
        typer.echo(
            "  accepted by licence: "
            + ", ".join(f"{code}={count}" for code, count in sorted(by_license.items()))
        )
    by_category = getattr(report, "by_category", None)
    if by_category:
        typer.echo(
            "  accepted by category: "
            + ", ".join(f"{code}={count}" for code, count in sorted(by_category.items()))
        )


def _echo_publish(report: PublishReport, *, verbose: bool) -> None:
    label = "would publish" if report.dry_run else "published"
    typer.echo(
        f"publish{' (dry run)' if report.dry_run else ''}: "
        f"{label}={report.count('would_publish') if report.dry_run else report.count('published')} "
        f"unchanged={report.count('unchanged')} rejected={report.count('rejected')} "
        f"withdrawn_by_gate={report.count('withdrawn_by_gate')} "
        f"skipped_owner_withdrawn={report.count('withdrawn')}"
    )
    for code, count in report.rejection_counts().items():
        typer.echo(f"  rejected {code}: {count}  ({GATE_RULES.get(code, '')})")
    typer.echo(
        "  publishable by area: "
        + ", ".join(f"{area}={count}" for area, count in report.published_by_area().items())
    )
    pending = sum(outcome.chunks_pending for outcome in report.outcomes)
    if pending:
        typer.echo(f"  chunks pending embedding: {pending} (re-run with GEMINI_API_KEY set)")
    if verbose:
        for outcome in report.outcomes:
            reasons = f" {', '.join(outcome.reasons)}" if outcome.reasons else ""
            typer.echo(
                f"  {outcome.status:13} {outcome.slug} [{outcome.area_code or '-'}]{reasons}"
            )


def _echo_calendar(report: CalendarReport) -> None:
    typer.echo(
        f"closure rules: listed={report.loaded} unchanged={report.unchanged} "
        f"inserted={report.inserted} retired={report.retired}"
    )
    for error in report.errors:
        typer.echo(f"  {error}")


# ---- policy -------------------------------------------------------------------------------


@policy_app.command("list")
def policy_list() -> None:
    """List providers with their policy revisions and status."""
    for row in _run(list_policies):
        approved = row.approved_at.date().isoformat() if row.approved_at else "-"
        typer.echo(
            f"{row.provider_key:22} rev {row.policy_revision} {row.status:8} "
            f"{row.provider_kind:15} terms={row.terms_version!r} approved={approved}"
        )


@policy_app.command("activate")
def policy_activate(
    provider_key: str,
    terms_version: str = typer.Option(..., "--terms-version", help="What the owner checked."),
) -> None:
    """Record the checked terms version and make the provider's policy ACTIVE."""
    try:
        typer.echo(_run(lambda s: activate_policy(s, provider_key, terms_version)))
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


# ---- areas --------------------------------------------------------------------------------


@areas_app.command("load")
def areas_load() -> None:
    """Write data/areas/<city>.yaml polygons into areas.boundary."""

    async def work(session: AsyncSession) -> int:
        updated = await write_area_boundaries(session, _city())
        await session.commit()
        return updated

    typer.echo(f"area boundaries written: {_run(work)}")


# ---- ingest -------------------------------------------------------------------------------


def _ingest(work: Callable[[AsyncSession], Awaitable[RunReport]]) -> None:
    try:
        _echo_run(_run(work))
    except PolicyNotActiveError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc


@ingest_app.command("wikidata")
def ingest_wikidata() -> None:
    """Import tourism-relevant Wikidata items inside the city boundary."""
    _ingest(lambda s: import_wikidata(s, city_code=_city()))


@ingest_app.command("wikipedia")
def ingest_wikipedia() -> None:
    """Fetch VI/EN Wikipedia summaries for imported places with sitelinks."""
    _ingest(lambda s: import_wikipedia(s, city_code=_city()))


@ingest_app.command("osm")
def ingest_osm() -> None:
    """Import named OpenStreetMap POIs (Overpass) with names and opening hours."""
    _ingest(lambda s: import_osm(s, city_code=_city()))


@ingest_app.command("commons")
def ingest_commons() -> None:
    """Attach licensed Wikimedia Commons photos (Wikidata P18, OSM tags) to imported places."""
    _ingest(lambda s: import_commons(s, city_code=_city()))


@ingest_app.command("sheet")
def ingest_sheet(
    path: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
) -> None:
    """Import the owner's place sheet (CSV; columns in data/README.md)."""
    _ingest(lambda s: import_sheet(s, city_code=_city(), path=path))


# ---- web candidates -----------------------------------------------------------------------


@web_app.command("promote")
def web_promote() -> None:
    """Promote eligible PENDING web candidates to DRAFT places."""

    async def work(session: AsyncSession) -> tuple[int, int]:
        city = await load_city(session, _city())
        results = await promote_pending(session, city.id)
        return sum(r.promoted for r in results), len(results)

    promoted, total = _run(work)
    typer.echo(f"web candidates: pending={total} promoted={promoted}")


# ---- publish ------------------------------------------------------------------------------


@publish_app.command("auto")
def publish_auto(
    dry_run: bool = typer.Option(False, "--dry-run", help="Run the gate, write nothing."),
    include_withdrawn: bool = typer.Option(
        False, "--include-withdrawn", help="Also re-publish places the owner unpublished."
    ),
    no_embed: bool = typer.Option(False, "--no-embed", help="Do not call the embedder."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="One line per place."),
) -> None:
    """Gate every candidate place and publish the ones that pass."""
    report = _run(
        lambda s: auto_publish(
            s,
            city_code=_city(),
            embedder=_embedder(no_embed),
            dry_run=dry_run,
            include_withdrawn=include_withdrawn,
        )
    )
    _echo_publish(report, verbose=verbose)


# ---- closure rules ------------------------------------------------------------------------


@calendar_app.command("load")
def closure_rules_load(
    file: Annotated[Path | None, typer.Option("--file", exists=True, dir_okay=False)] = None,
) -> None:
    """Sync data/closure_rules/<city>.yaml into APPROVED closure rules."""
    try:
        _echo_calendar(_run(lambda s: load_calendar(s, city_code=_city(), path=file)))
    except ValueError as exc:
        typer.echo(f"invalid calendar: {exc}", err=True)
        raise typer.Exit(code=1) from exc


# ---- pipeline -----------------------------------------------------------------------------


@pipeline_app.command("run")
def pipeline_run(
    sheet: Annotated[
        Path | None,
        typer.Option("--sheet", dir_okay=False, help="Defaults to data/sheet/<city>.csv."),
    ] = None,
    dry_run: bool = typer.Option(False, "--dry-run", help="Stage imports; publish nothing."),
    no_embed: bool = typer.Option(False, "--no-embed"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """areas → wikidata → wikipedia → osm → commons → sheet → web candidates → publish →
    closure rules.

    An importer whose provider policy is not ACTIVE is skipped with a message (default deny).
    """
    city = _city()
    areas_load()
    steps: list[tuple[str, Callable[[AsyncSession], Awaitable[RunReport]]]] = [
        ("wikidata", lambda s: import_wikidata(s, city_code=city)),
        ("wikipedia", lambda s: import_wikipedia(s, city_code=city)),
        ("osm", lambda s: import_osm(s, city_code=city)),
        ("commons", lambda s: import_commons(s, city_code=city)),
    ]
    sheet_path = sheet or (DEFAULT_SHEET if DEFAULT_SHEET.exists() else None)
    if sheet_path is not None:
        steps.append(("sheet", lambda s: import_sheet(s, city_code=city, path=sheet_path)))
    for name, work in steps:
        try:
            _echo_run(_run(work))
        except PolicyNotActiveError as exc:
            typer.echo(f"{name}: skipped — {exc}")
    web_promote()
    publish_auto(dry_run=dry_run, include_withdrawn=False, no_embed=no_embed, verbose=verbose)
    if not dry_run:
        closure_rules_load(file=None)
