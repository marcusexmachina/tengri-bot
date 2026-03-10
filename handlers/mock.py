"""Handler for /mock and /unmock — toggle mock mode; when on, target's messages get auto-mocked."""

import asyncio
import logging
import random

from telegram import ReplyParameters, Update
from telegram.ext import ContextTypes

from permissions import _is_real_admin
from resolvers import _get_target_user_from_message

logger = logging.getLogger(__name__)

CLOWN = "\N{CLOWN FACE}"
MAX_TEXT_LENGTH = 500
BULK_DELETE_CHUNK = 100

# Common typo substitutions (word -> possible misspellings)
TYPO_MAP: dict[str, list[str]] = {
    "your": ["yuor", "yoru", "yor"],
    "you": ["yuo", "uoy"],
    "are": ["aer", "rae"],
    "the": ["teh", "hte"],
    "is": ["iz", "si"],
    "and": ["adn", "nad"],
    "fuck": ["fukc", "fuc", "fukk", "fuckk"],
    "fucking": ["fuking", "fukcing"],
    "what": ["waht", "whta"],
    "that": ["taht", "thta"],
    "this": ["tihs", "thsi"],
    "with": ["wiht", "wtih"],
    "have": ["hvae", "ahve"],
    "from": ["form", "from"],
    "mom": ["mOM", "moom", "mom"],
    "whore": ["whoree", "whoer", "whre"],
}


def _random_case(char: str) -> str:
    """Randomly uppercase or lowercase a letter."""
    if not char.isalpha():
        return char
    return char.upper() if random.random() < 0.5 else char.lower()


def _apply_typos(text: str) -> str:
    """Randomly substitute words with typos."""
    words = text.split()
    result = []
    for w in words:
        key = w.lower()
        if key in TYPO_MAP and random.random() < 0.4:
            result.append(random.choice(TYPO_MAP[key]))
        else:
            result.append(w)
    return " ".join(result)


def _add_random_punctuation(text: str) -> str:
    """Append random punctuation."""
    suffixes = ["!!", "!!!", "?!", "!?", "!?", "@#!", "!!", "!!!", "?!?!"]
    return text.rstrip() + random.choice(suffixes)


def _add_clown_emojis() -> str:
    """Return 1–3 clown emojis."""
    return CLOWN * random.randint(1, 3)


def _spaced_letters(text: str) -> str:
    """Insert spaces between letters with random case (e.g. Y o U r  m O m)."""
    words = text.split()
    spaced = [" ".join(_random_case(c) for c in w) for w in words]
    return "  ".join(spaced)


def _mock_transform(text: str) -> str:
    """Apply mocking transformation: random case, typos, punctuation, clown emoji. Wrapped in quotes."""
    if random.random() < 0.5:
        text = _apply_typos(text)
    if random.random() < 0.15:
        mocked = _spaced_letters(text)
    else:
        mocked = "".join(_random_case(c) for c in text)
    mocked = _add_random_punctuation(mocked)
    mocked += " " + _add_clown_emojis()
    return f'"{mocked}"'


def _extract_text(message) -> str | None:
    """Extract text from message (text or caption)."""
    if message.text:
        return message.text.strip()
    if message.caption:
        return message.caption.strip()
    return None


def _mock_mode_users(context: ContextTypes.DEFAULT_TYPE) -> set[int]:
    """Set of user_ids in mock mode (their messages get auto-mocked)."""
    return context.bot_data.setdefault("mock_mode_users", set())


def _mock_reply_ids(context: ContextTypes.DEFAULT_TYPE) -> dict[tuple[int, int], list[int]]:
    """Map (chat_id, user_id) -> list of bot message IDs (mock replies). Deleted on /unmock."""
    return context.bot_data.setdefault("mock_reply_ids", {})


async def cmd_mock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cast mock on target: reply or /mock @user. Admin only. No notification. Command deleted."""
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return

    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return

    # Delete command immediately so nobody sees it
    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
    except Exception as e:
        logger.warning("Mock cmd delete failed: %s", e)

    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        return

    if not _is_real_admin(member):
        return

    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        return

    _mock_mode_users(context).add(target_user.id)


async def cmd_unmock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove mock from target: reply or /unmock @user. Admin only. No notification. Command deleted. Deletes all mock replies."""
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return

    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return

    # Delete command immediately
    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
    except Exception as e:
        logger.warning("Unmock cmd delete failed: %s", e)

    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        return

    if not _is_real_admin(member):
        return

    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        return

    _mock_mode_users(context).discard(target_user.id)

    # Delete all mock replies we sent for this user in this chat
    key = (chat.id, target_user.id)
    ids = _mock_reply_ids(context).pop(key, [])
    if ids:
        try:
            for i in range(0, len(ids), BULK_DELETE_CHUNK):
                chunk = ids[i : i + BULK_DELETE_CHUNK]
                await context.bot.delete_messages(chat_id=chat.id, message_ids=chunk)
                if i + BULK_DELETE_CHUNK < len(ids):
                    await asyncio.sleep(0.3)
        except Exception as bulk_err:
            logger.warning("Mock reply bulk delete failed, falling back: %s", bulk_err)
            for msg_id in ids:
                try:
                    await context.bot.delete_message(chat_id=chat.id, message_id=msg_id)
                    await asyncio.sleep(0.05)
                except Exception:
                    pass


async def maybe_mock_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    If sender is in mock mode and message has text, mock it and reply. Returns True if mocked.
    Tracks reply IDs for deletion on /unmock.
    """
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return False

    if user.id not in _mock_mode_users(context):
        return False

    text = _extract_text(message)
    if not text or len(text) > MAX_TEXT_LENGTH:
        return False

    mocked = _mock_transform(text)
    sent = await context.bot.send_message(
        chat.id,
        mocked,
        reply_parameters=ReplyParameters(message_id=message.message_id),
    )

    # Track for deletion on /unmock
    key = (chat.id, user.id)
    _mock_reply_ids(context).setdefault(key, []).append(sent.message_id)

    return True
