"""Shared fixtures for mini-bank tests."""

import pytest


@pytest.fixture
def sample_account_id() -> str:
    return "ACC-0001"
