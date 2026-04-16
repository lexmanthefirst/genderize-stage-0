from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(
    status_code: int = 200,
    message: str | None = None,
    data: dict[str, Any] | None = None,
) -> JSONResponse:
    """Return a standardized success payload for this API."""
    payload: dict[str, Any] = {
        "status": "success",
        "data": data or {},
    }
    if message is not None:
        payload["message"] = message
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def fail_response(
    status_code: int,
    message: str,
    context: dict[str, Any] | None = None,
) -> JSONResponse:
    """Return a standardized failure payload for this API."""
    payload: dict[str, Any] = {
        "status": "error",
        "message": message,
    }
    if context:
        payload["error"] = context
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))
