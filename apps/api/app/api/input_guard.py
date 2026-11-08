"""Request-wide rejection of NUL characters (``\\x00``).

PostgreSQL ``text`` cannot store U+0000, so a NUL in a query parameter, path segment or JSON
string would otherwise surface as a database error (500). Every ``/v1`` and health route depends
on :func:`reject_nul_characters`, which answers ``422 validation_error`` with the offending
locations before authentication, body validation or any database call.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import Request

from app.errors import AppError

NUL = "\x00"
MAX_REPORTED_FIELDS = 20


def _json_nul_locations(value: Any, location: list[str | int], out: list[list[str | int]]) -> None:
    if len(out) >= MAX_REPORTED_FIELDS:
        return
    if isinstance(value, str):
        if NUL in value:
            out.append(location)
    elif isinstance(value, dict):
        for key, item in value.items():
            if NUL in key:
                out.append([*location, key.replace(NUL, "")])
            _json_nul_locations(item, [*location, key], out)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _json_nul_locations(item, [*location, index], out)


async def reject_nul_characters(request: Request) -> None:
    """Raise ``422 validation_error`` when a query parameter, the path or a JSON body string
    contains ``\\x00``. Non-JSON bodies and malformed JSON are left to the normal validation."""
    locations: list[list[str | int]] = []
    if NUL in request.url.path:
        locations.append(["path"])
    for name, value in request.query_params.multi_items():
        if NUL in name or NUL in value:
            locations.append(["query", name.replace(NUL, "")])
    content_type = request.headers.get("content-type", "")
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and "json" in content_type:
        body = await request.body()  # cached on the request; FastAPI re-reads the same bytes
        if body:
            try:
                parsed = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                parsed = None
            _json_nul_locations(parsed, ["body"], locations)
    if locations:
        raise AppError(
            422,
            "validation_error",
            "Request validation failed",
            context={
                "fields": [
                    {
                        "type": "string_nul_character",
                        "location": location,
                        "message": "NUL characters are not allowed",
                    }
                    for location in locations[:MAX_REPORTED_FIELDS]
                ]
            },
        )
