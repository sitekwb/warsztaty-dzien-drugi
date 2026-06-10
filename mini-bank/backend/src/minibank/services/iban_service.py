"""IBAN validation: local mod-97 checksum + openiban.com cache lookup.

Public surface: async `validate(iban: str) -> dict` returning at least
`{iban, valid, source}` and optionally `bank_name`, `bic`.

`source` is one of:
  - "local"    — answer came from on-board checksum check only
  - "external" — answer came from a fresh openiban.com call
  - "cache"    — answer was previously cached (originally external)

Graceful degradation: if openiban times out or 5xx's, we return the local
checksum verdict as `source="local"` (without bank_name).
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from minibank.db.seed_helpers import is_valid_iban


# Simple in-memory cache: {iban_normalized: (result_dict, expires_at_unix)}
_cache: dict[str, tuple[dict[str, Any], float]] = {}
_CACHE_TTL_SECONDS = 3600
_OPENIBAN_TIMEOUT = 1.5


def _normalize(iban: str) -> str:
    return iban.replace(" ", "").upper()


def _format_display(iban: str) -> str:
    """Group every 4 chars with spaces: PL21114020040000... → PL21 1140 2004 0000..."""
    s = _normalize(iban)
    return " ".join(s[i:i + 4] for i in range(0, len(s), 4))


async def _fetch_openiban(iban_no_spaces: str) -> dict[str, Any]:
    """Call openiban.com. Returns parsed JSON. Caller handles exceptions."""
    async with httpx.AsyncClient(timeout=_OPENIBAN_TIMEOUT) as client:
        resp = await client.get(f"https://openiban.com/validate/{iban_no_spaces}")
        resp.raise_for_status()
        return resp.json()


async def validate(iban: str) -> dict[str, Any]:
    """Validate an IBAN, preferring external lookup but degrading gracefully."""
    normalized = _normalize(iban)
    display = _format_display(iban)

    # Local first — cheap reject for garbage input.
    if not is_valid_iban(normalized):
        return {
            "iban": display,
            "valid": False,
            "source": "local",
        }

    # Cache hit?
    now = time.time()
    cached = _cache.get(normalized)
    if cached is not None and cached[1] > now:
        result = dict(cached[0])
        result["source"] = "cache"
        return result

    # Try openiban.
    try:
        data = await _fetch_openiban(normalized)
        bank = data.get("bankData") or {}
        result = {
            "iban": display,
            "valid": bool(data.get("valid")),
            "source": "external",
            "bank_name": bank.get("name") or None,
            "bic": bank.get("bic") or None,
        }
        _cache[normalized] = (result, now + _CACHE_TTL_SECONDS)
        return result
    except (httpx.TimeoutException, httpx.HTTPError):
        # Fallback: local checksum says it's valid, but we couldn't enrich.
        return {
            "iban": display,
            "valid": True,
            "source": "local",
        }
