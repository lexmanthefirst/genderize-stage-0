import asyncio
from datetime import datetime, timezone
from time import monotonic
from typing import Any

import httpx
from app.utils.exceptions import NoPredictionError, UpstreamServiceError

GENDERIZE_URL = "https://api.genderize.io"
CACHE_TTL_SECONDS = 300.0

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_cache_lock = asyncio.Lock()


def _cache_key(name: str) -> str:
    return name.strip().lower()


def _processed_at_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def classify_name_with_genderize(client: httpx.AsyncClient, name: str) -> dict[str, Any]:
    key = _cache_key(name)
    now = monotonic()

    async with _cache_lock:
        cached = _cache.get(key)
        if cached is not None:
            expires_at, cached_result = cached
            if now < expires_at:
                return {
                    **cached_result,
                    "processed_at": _processed_at_utc(),
                }

    try:
        response = await client.get(GENDERIZE_URL, params={"name": name})
    except httpx.RequestError as exc:
        raise UpstreamServiceError("Failed to reach upstream service") from exc

    if response.status_code != 200:
        raise UpstreamServiceError("Upstream service returned an error")

    try:
        payload: dict[str, Any] = response.json()
    except ValueError as exc:
        raise UpstreamServiceError("Invalid response from upstream service") from exc

    processed = process_genderize_payload(payload=payload, fallback_name=name)

    async with _cache_lock:
        _cache[key] = (monotonic() + CACHE_TTL_SECONDS, processed)

    return {
        **processed,
        "processed_at": _processed_at_utc(),
    }


def process_genderize_payload(payload: dict[str, Any], fallback_name: str) -> dict[str, Any]:
    gender = payload.get("gender")
    probability = payload.get("probability")
    count = payload.get("count")

    if probability is None or count is None:
        raise UpstreamServiceError("Unexpected upstream data format")

    try:
        probability_value = float(probability)
        sample_size = int(count)
    except (TypeError, ValueError) as exc:
        raise UpstreamServiceError("Unexpected upstream data format") from exc

    if gender is None or sample_size == 0:
        raise NoPredictionError("No prediction available for the provided name")

    is_confident = probability_value >= 0.7 and sample_size >= 100
    return {
        "name": str(payload.get("name") or fallback_name),
        "gender": gender,
        "probability": probability_value,
        "sample_size": sample_size,
        "is_confident": is_confident,
    }
