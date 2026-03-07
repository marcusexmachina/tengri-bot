"""Tests for reputation_thresholds module."""
from config import REPUTATION_DEFAULT
from reputation_thresholds import get_rep, is_fully_muted


def test_get_rep_default():
    context = type("C", (), {"bot_data": {}})()
    assert get_rep(context, 1, 123) == REPUTATION_DEFAULT


def test_get_rep_from_data():
    context = type("C", (), {"bot_data": {"reputation": {(1, 123): 50}}})()
    assert get_rep(context, 1, 123) == 50


def test_is_fully_muted():
    assert is_fully_muted(9) is True
    assert is_fully_muted(10) is False
