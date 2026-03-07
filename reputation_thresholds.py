"""Reputation-based thresholds for STFU, acquire, armor, and restrictions."""

from config import REPUTATION_DEFAULT, REPUTATION_MAX


def get_rep(context, chat_id: int, user_id: int) -> int:
    """Get user reputation, default 100."""
    rep = context.bot_data.get("reputation") or {}
    return rep.get((chat_id, user_id), REPUTATION_DEFAULT)


def is_fully_muted(rep: int) -> bool:
    """Rep < 10: completely muted, nothing allowed."""
    return rep < 10


def can_acquire_stfu(rep: int) -> bool:
    """Rep 10-29 cannot acquire. Rep >= 30 can."""
    return rep >= 30


def acquire_session_seconds(rep: int) -> int:
    """Acquire/replenish session duration in seconds. 0 = cannot acquire."""
    if rep < 30:
        return 0
    if rep >= 200:
        return 24 * 60 * 60
    if rep >= 175:
        return 18 * 60 * 60
    if rep >= 150:
        return 12 * 60 * 60
    if rep >= 120:
        return 6 * 60 * 60
    if rep >= 100:
        return 4 * 60 * 60
    if rep >= 80:
        return 2 * 60 * 60
    if rep >= 60:
        return 15 * 60
    if rep >= 30:
        return 8 * 60
    return 0


def delegate_stfu_cast_seconds(rep: int) -> int:
    """Fixed mute duration when delegate casts /stfu. Used when rep < threshold for max."""
    if rep >= 30 and rep < 60:
        return 60
    return 60


def delegate_stfu_max_seconds(rep: int) -> int | None:
    """Max duration delegate can set when casting /stfu. None = use fixed duration only."""
    if rep >= 200:
        return 20 * 60
    if rep >= 175:
        return 6 * 60
    if rep >= 150:
        return 2 * 60
    return None


def can_use_armor(rep: int) -> bool:
    """Rep 30-59 cannot cast /holycowshithindupajeetarmor; enabled from 60+."""
    return rep >= 60


def armor_duration_seconds(rep: int) -> int:
    """Default armor duration by rep."""
    if rep >= 175:
        return 10 * 60
    if rep >= 150:
        return 3 * 60
    if rep >= 125:
        return 2 * 60
    if rep >= 60:
        return 60
    return 60


def has_stfu_immunity(rep: int) -> bool:
    """Rep >= 200: immunity from /stfu (cannot be muted)."""
    return rep >= REPUTATION_MAX


def is_media_blocked(rep: int) -> bool:
    """Rep 10-29: all media blocked."""
    return 10 <= rep < 30


def low_rep_text_cooldown_seconds(rep: int) -> int | None:
    """Rep 10-29: 30s cooldown on text. Returns cooldown seconds or None if no cooldown."""
    if 10 <= rep < 30:
        return 30
    return None
