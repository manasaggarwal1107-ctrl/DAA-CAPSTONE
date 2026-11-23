"""Centralised error type and handlers.

Every error leaves the API as ``{"error": {"code", "message", "details"}}``.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from .algorithms.errors import AlgorithmError, ResourceLimitError, UnknownNodeError

log = logging.getLogger("courier")


class ApiError(Exception):
    """An error the client caused (bad input, missing record, conflict)."""

    def __init__(self, status: int, code: str, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


def friendly_validation_errors(exc: ValidationError, prefix: str = "") -> list[dict]:
    """Turn a pydantic error into ``[{field, message}]`` with readable wording."""
    out = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "body"
        msg = err["msg"]
        if err["type"] == "missing":
            msg = "This field is required"
        elif msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        out.append({"field": f"{prefix}{loc}", "message": msg})
    return out


def _response(status: int, code: str, message: str, details: Any = None) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message, "details": details}}, status_code=status)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return _response(exc.status, exc.code, exc.message, exc.details)


async def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
    errors = friendly_validation_errors(exc)
    return _response(422, "validation_error", "; ".join(f"{e['field']}: {e['message']}" for e in errors), errors)


async def algorithm_handler(_: Request, exc: AlgorithmError) -> JSONResponse:
    if isinstance(exc, UnknownNodeError):
        return _response(404, "unknown_location", str(exc))
    if isinstance(exc, ResourceLimitError):
        return _response(413, "resource_limit", str(exc))
    return _response(422, "invalid_input", str(exc))


async def unexpected_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error")
    return _response(500, "internal_error", "Unexpected server error. See the server log for details.")
