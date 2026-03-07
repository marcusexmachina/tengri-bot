"""Tests for config module."""
import pytest

from config import DURATION_UNITS


def test_duration_units():
    assert DURATION_UNITS["s"] == 1
    assert DURATION_UNITS["m"] == 60
    assert DURATION_UNITS["h"] == 3600
    assert DURATION_UNITS["d"] == 86400
