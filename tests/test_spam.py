"""Tests for spam module."""

from spam import MessageBucket, normalize_text


def test_normalize_text():
    assert normalize_text("  Hello   World  ") == "hello world"
    assert normalize_text("SAME") == "same"
    assert normalize_text("") == ""


def test_message_bucket_defaults():
    b = MessageBucket()
    assert b.message_ids == []
    assert b.timestamps == []
