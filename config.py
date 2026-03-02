"""Configuration constants for Tengri bot."""

SPAM_THRESHOLD = 3
MEDIA_FLOOD_THRESHOLD = 5
REPEAT_WINDOW_SECONDS = 120
MUTE_SECONDS = 60
BULK_DELETE_CHUNK = 100
NOTIFICATION_AUTO_DELETE_SECONDS = 20
DELEGATE_STFU_DEFAULT_SECONDS = 60
DELEGATE_STFU_MAX_SECONDS = 5 * 60
ADMIN_STFU_DEFAULT_SECONDS = 60
ADMIN_STFU_MAX_SECONDS = 10 * 60
STFU_MAX_TARGETS = 20
STFUPROOF_DEFAULT_SECONDS = 60
STFUPROOF_COOLDOWN_SECONDS = 60

SPAM_CATCHUP_SECONDS = 15
MAX_TEMP_RESTRICT_SECONDS = 366 * 24 * 60 * 60
TELEGRAM_MIN_RESTRICT_SECONDS = 30

DURATION_UNITS = {
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "h": 60 * 60, "hr": 60 * 60, "hrs": 60 * 60, "hour": 60 * 60, "hours": 60 * 60,
    "d": 24 * 60 * 60, "day": 24 * 60 * 60, "days": 24 * 60 * 60,
    "w": 7 * 24 * 60 * 60, "week": 7 * 24 * 60 * 60, "weeks": 7 * 24 * 60 * 60,
    "mo": 30 * 24 * 60 * 60, "month": 30 * 24 * 60 * 60, "months": 30 * 24 * 60 * 60,
    "y": 365 * 24 * 60 * 60, "yr": 365 * 24 * 60 * 60, "yrs": 365 * 24 * 60 * 60,
    "year": 365 * 24 * 60 * 60, "years": 365 * 24 * 60 * 60,
}
