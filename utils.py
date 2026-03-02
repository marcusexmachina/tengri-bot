"""Shared utilities: duration parsing, message scheduling, formatting."""
import asyncio
import re

from telegram import User
from telegram.ext import ContextTypes

from config import DURATION_UNITS, NOTIFICATION_AUTO_DELETE_SECONDS

logger = __import__("logging").getLogger(__name__)


def parse_duration_spec(spec: str) -> int | None:
    """Parse strings like '5m', '2w 1mo', '10yrs' into seconds."""
    spec = spec.strip()
    if not spec:
        return None
    total = 0
    for token in spec.split():
        m = re.fullmatch(r"(\d+)([a-zA-Z]+)", token)
        if not m:
            return None
        value, unit = m.groups()
        unit = unit.lower()
        if unit not in DURATION_UNITS:
            return None
        total += int(value) * DURATION_UNITS[unit]
    return total if total > 0 else None


def extract_duration_from_message(message, target_user: User | None) -> int | None:
    """Extract a duration spec from the message text."""
    if not message.text:
        return None
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    rest = parts[1]
    tokens = rest.split()
    duration_tokens = [t for t in tokens if re.fullmatch(r"(\d+)([a-zA-Z]+)", t.strip())]
    if not duration_tokens:
        return None
    spec = " ".join(duration_tokens)
    return parse_duration_spec(spec)


async def _job_delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback: delete a single message after delay."""
    chat_id, message_id = context.job.data
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning("Auto-delete failed chat_id=%s message_id=%s: %s", chat_id, message_id, e)


async def _delete_message_after(bot, chat_id: int, message_id: int, seconds: int) -> None:
    try:
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.warning("Auto-delete failed chat_id=%s message_id=%s: %s", chat_id, message_id, e)


def _schedule_notification_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int) -> None:
    """Schedule message for deletion after NOTIFICATION_AUTO_DELETE_SECONDS."""
    jq = getattr(context.application, "job_queue", None)
    if jq is not None:
        jq.run_once(
            _job_delete_message,
            when=NOTIFICATION_AUTO_DELETE_SECONDS,
            data=(chat_id, message_id),
        )
    else:
        asyncio.create_task(
            _delete_message_after(context.bot, chat_id, message_id, NOTIFICATION_AUTO_DELETE_SECONDS)
        )


def _format_time_left(seconds: float) -> str:
    """Format seconds as e.g. '4h', '2d 3h', '23h 45m'."""
    if seconds <= 0:
        return "expired"
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m or not parts:
        parts.append(f"{m}m")
    return " ".join(parts)
