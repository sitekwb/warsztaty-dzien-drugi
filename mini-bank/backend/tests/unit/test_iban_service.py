"""Tests for iban_service. Local mod-97 + openiban.com cache + graceful fallback."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from minibank.services import iban_service


@pytest.fixture(autouse=True)
def clear_cache():
    iban_service._cache.clear()
    yield
    iban_service._cache.clear()


@pytest.mark.asyncio
async def test_local_invalid_short():
    r = await iban_service.validate("PL12")
    assert r["valid"] is False
    assert r["source"] == "local"


@pytest.mark.asyncio
async def test_local_invalid_checksum():
    r = await iban_service.validate("PL00 0000 0000 0000 0000 0000 0000")
    assert r["valid"] is False


@pytest.mark.asyncio
async def test_external_success_caches_result():
    fake_response = {"valid": True, "bankData": {"name": "mBank S.A.", "bic": "BREXPLPWMBK"}}
    with patch.object(iban_service, "_fetch_openiban", new=AsyncMock(return_value=fake_response)) as mock_fetch:
        r1 = await iban_service.validate("PL21 1140 2004 0000 0000 0000 0000")
        assert r1["valid"] is True
        assert r1["bank_name"] == "mBank S.A."
        assert r1["source"] == "external"

        # Second call hits cache, not the network.
        r2 = await iban_service.validate("PL21 1140 2004 0000 0000 0000 0000")
        assert r2["source"] == "cache"
        assert mock_fetch.call_count == 1


@pytest.mark.asyncio
async def test_external_timeout_falls_back_to_local_valid():
    with patch.object(iban_service, "_fetch_openiban", new=AsyncMock(side_effect=httpx.TimeoutException("slow"))):
        r = await iban_service.validate("PL21 1140 2004 0000 0000 0000 0000")
        # Local checksum is valid for this IBAN; fallback is "valid but no bank_name"
        assert r["valid"] is True
        assert r["source"] == "local"
        assert r.get("bank_name") is None


@pytest.mark.asyncio
async def test_external_says_invalid_returns_invalid():
    fake_response = {"valid": False}
    with patch.object(iban_service, "_fetch_openiban", new=AsyncMock(return_value=fake_response)):
        r = await iban_service.validate("PL21 1140 2004 0000 0000 0000 0000")
        assert r["valid"] is False
        assert r["source"] == "external"
