"""NSFW detection for media messages. Opt-in via NSFW_ENABLED env var."""

from nsfw.check import check_media_nsfw

__all__ = ["check_media_nsfw"]
