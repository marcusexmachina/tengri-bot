"""Pytest configuration."""
import os

import pytest


@pytest.fixture(autouse=True)
def set_env():
    """Set minimal env for tests that load config."""
    os.environ.setdefault("TELEGRAM_TOKEN", "dummy")
    os.environ.setdefault("TELEGRAM_GROUP", "-1001234567890")
