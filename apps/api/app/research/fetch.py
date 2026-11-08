"""Evidence page fetcher (ADR-014, architecture §6, ADR-006 ``web_page``).

* SSRF guard: HTTPS only, every hop's host resolved and refused if any address is private,
  loopback, link-local, multicast or reserved; ≤ 3 redirects, each re-checked.
* robots.txt honoured for ``GonarraBot``; a 401/403 robots file means "disallow all".
* Size (≤ 2 MiB) and time (≤ 10 s per request) limits; HTML/plain text only; text via
  trafilatura. Nothing but text is kept.
* Cache: ``research_cache`` (WEB_PAGE, 7 d, key = SHA-256 of the normalised URL). Each fresh
  fetch appends a ``source_revisions`` row (locator = URL, content_sha256 of the text).
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from urllib import robotparser
from urllib.parse import urljoin, urlsplit

import httpx

from app.agents.validators import normalise_url
from app.research.extract import clean_text, content_sha256, html_title, html_to_text, url_key
from app.research.store import WEB_PAGE, ResearchStore

logger = logging.getLogger("gonarra.research")

USER_AGENT = "GonarraBot/0.1 (university FYP)"
ROBOTS_AGENT = "GonarraBot"
MAX_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
TIMEOUT_S = 10.0
_ALLOWED_TYPES = ("text/html", "application/xhtml+xml", "text/plain")

Resolver = Callable[[str], Awaitable[list[str]]]


class FetchStatus(StrEnum):
    OK = "OK"
    CACHED = "CACHED"
    BLOCKED_URL = "BLOCKED_URL"  # scheme, host or address refused by the SSRF guard
    ROBOTS_DISALLOWED = "ROBOTS_DISALLOWED"
    TOO_LARGE = "TOO_LARGE"
    UNSUPPORTED_TYPE = "UNSUPPORTED_TYPE"
    HTTP_ERROR = "HTTP_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    EMPTY = "EMPTY"


@dataclass(frozen=True, slots=True)
class FetchedPage:
    url: str  # normalised requested URL
    status: FetchStatus
    final_url: str | None = None
    title: str | None = None
    text: str = ""
    content_sha256: str | None = None
    source_revision_id: uuid.UUID | None = None
    retrieved_at: datetime | None = None

    @property
    def ok(self) -> bool:
        return self.status in {FetchStatus.OK, FetchStatus.CACHED} and bool(self.text)


async def system_resolver(host: str) -> list[str]:
    infos = await asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    return sorted({str(info[4][0]) for info in infos})


def _public(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_global and not ip.is_multicast


class PageFetcher:
    def __init__(
        self,
        *,
        store: ResearchStore,
        client: httpx.AsyncClient | None = None,
        resolver: Resolver = system_resolver,
    ) -> None:
        self._store = store
        self._client = client or httpx.AsyncClient(
            timeout=TIMEOUT_S, follow_redirects=False, headers={"User-Agent": USER_AGENT}
        )
        self._resolver = resolver
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch(self, url: str) -> FetchedPage:
        given = urlsplit(url.strip())
        if given.username or given.password:
            return FetchedPage(url="", status=FetchStatus.BLOCKED_URL)
        normalised = normalise_url(url)
        key = url_key(normalised)
        cached = await self._store.get_cached(WEB_PAGE, key)
        if cached is not None and cached.payload.get("text"):
            return FetchedPage(
                url=normalised,
                status=FetchStatus.CACHED,
                final_url=str(cached.payload.get("final_url") or normalised),
                title=cached.payload.get("title"),
                text=str(cached.payload["text"]),
                content_sha256=cached.payload.get("content_sha256"),
                source_revision_id=cached.source_revision_id,
                retrieved_at=cached.fetched_at,
            )

        current = normalised
        for _ in range(MAX_REDIRECTS + 1):
            refusal = await self._guard(current)
            if refusal is not None:
                return FetchedPage(url=normalised, status=refusal)
            try:
                response, body = await self._get(current)
            except _TooLarge:
                return FetchedPage(url=normalised, status=FetchStatus.TOO_LARGE)
            except httpx.HTTPError as exc:
                logger.info("fetch error=%s", type(exc).__name__)
                return FetchedPage(url=normalised, status=FetchStatus.NETWORK_ERROR)
            if response.is_redirect and "location" in response.headers:
                current = normalise_url(urljoin(current, response.headers["location"]))
                continue
            break
        else:
            return FetchedPage(url=normalised, status=FetchStatus.BLOCKED_URL)

        if response.status_code != 200:
            return FetchedPage(url=normalised, status=FetchStatus.HTTP_ERROR)
        ctype = response.headers.get("content-type", "").split(";")[0].strip().lower()
        if ctype and ctype not in _ALLOWED_TYPES:
            return FetchedPage(url=normalised, status=FetchStatus.UNSUPPORTED_TYPE)
        raw = body.decode(response.encoding or "utf-8", errors="replace")
        if ctype == "text/plain":
            title, text = None, clean_text(raw)
        else:
            title, text = html_title(raw), html_to_text(raw, url=current)
        if not text:
            return FetchedPage(url=normalised, status=FetchStatus.EMPTY)

        retrieved_at = datetime.now(UTC)
        digest = content_sha256(text)
        revision_id = await self._store.append_source_revision(
            url=normalised, title=title, content_sha256=digest, retrieved_at=retrieved_at
        )
        policy = await self._store.policy_id("web_page")
        if policy is not None:
            await self._store.put_cached(
                WEB_PAGE,
                key,
                {
                    "url": normalised,
                    "final_url": current,
                    "title": title,
                    "text": text,
                    "content_sha256": digest,
                },
                policy_id=policy,
                source_revision_id=revision_id,
            )
        return FetchedPage(
            url=normalised,
            status=FetchStatus.OK,
            final_url=current,
            title=title,
            text=text,
            content_sha256=digest,
            source_revision_id=revision_id,
            retrieved_at=retrieved_at,
        )

    async def _guard(self, url: str) -> FetchStatus | None:
        parts = urlsplit(url)
        host = parts.hostname
        if parts.scheme != "https" or not host or parts.username or parts.password:
            return FetchStatus.BLOCKED_URL
        if parts.port not in (None, 443):
            return FetchStatus.BLOCKED_URL
        try:
            addresses = await self._resolver(host)
        except (OSError, UnicodeError):
            return FetchStatus.NETWORK_ERROR
        if not addresses or not all(_public(a) for a in addresses):
            return FetchStatus.BLOCKED_URL
        if not await self._robots_allow(url):
            return FetchStatus.ROBOTS_DISALLOWED
        return None

    async def _robots_allow(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            self._robots[origin] = await self._load_robots(origin)
        parser = self._robots[origin]
        return True if parser is None else parser.can_fetch(ROBOTS_AGENT, url)

    async def _load_robots(self, origin: str) -> robotparser.RobotFileParser | None:
        parser = robotparser.RobotFileParser()
        try:
            response, body = await self._get(f"{origin}/robots.txt", limit=256 * 1024)
        except (httpx.HTTPError, _TooLarge):
            return None  # unreachable robots.txt: treat as no restrictions
        if response.status_code in (401, 403):
            parser.parse(["User-agent: *", "Disallow: /"])
            return parser
        if response.status_code != 200:
            return None
        parser.parse(body.decode("utf-8", errors="replace").splitlines())
        return parser

    async def _get(self, url: str, *, limit: int = MAX_BYTES) -> tuple[httpx.Response, bytes]:
        async with self._client.stream("GET", url, headers={"User-Agent": USER_AGENT}) as resp:
            declared = resp.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > limit:
                raise _TooLarge
            chunks: list[bytes] = []
            size = 0
            async for chunk in resp.aiter_bytes():
                size += len(chunk)
                if size > limit:
                    raise _TooLarge
                chunks.append(chunk)
        return resp, b"".join(chunks)


class _TooLarge(Exception):
    pass
