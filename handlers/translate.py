"""Handler for /translate — translate replied message to English or specified language."""

import logging

from telegram import ReplyParameters, Update
from telegram.ext import ContextTypes

from responses import get_response
from utils import _schedule_notification_delete

logger = logging.getLogger(__name__)

# Map common language names/aliases to Google Translate target codes
LANGUAGE_ALIASES: dict[str, str] = {
    "english": "en",
    "en": "en",
    "mandarin": "zh-CN",
    "chinese": "zh-CN",
    "zh": "zh-CN",
    "spanish": "es",
    "es": "es",
    "french": "fr",
    "fr": "fr",
    "german": "de",
    "de": "de",
    "japanese": "ja",
    "ja": "ja",
    "korean": "ko",
    "ko": "ko",
    "arabic": "ar",
    "ar": "ar",
    "russian": "ru",
    "ru": "ru",
    "portuguese": "pt",
    "pt": "pt",
    "italian": "it",
    "it": "it",
    "hindi": "hi",
    "hi": "hi",
    "dutch": "nl",
    "nl": "nl",
    "turkish": "tr",
    "tr": "tr",
    "vietnamese": "vi",
    "vi": "vi",
    "thai": "th",
    "th": "th",
    "indonesian": "id",
    "id": "id",
    "polish": "pl",
    "pl": "pl",
    "ukrainian": "uk",
    "uk": "uk",
    "greek": "el",
    "el": "el",
    "swedish": "sv",
    "sv": "sv",
}

MAX_TEXT_LENGTH = 5000


def _resolve_target(target: str | None) -> str:
    """Return Google Translate target code. Default 'en' if None or unknown."""
    if not target or not target.strip():
        return "en"
    key = target.strip().lower()
    return LANGUAGE_ALIASES.get(key, "en")


def _extract_text(message) -> str | None:
    """Extract text from message (text or caption)."""
    if message.text:
        return message.text.strip()
    if message.caption:
        return message.caption.strip()
    return None


async def cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return

    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return

    if not message.reply_to_message:
        msg = get_response("translate_reply_required")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    _schedule_notification_delete(context, chat.id, message.message_id)

    replied = message.reply_to_message
    text = _extract_text(replied)
    if not text:
        msg = get_response("translate_no_text")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    if len(text) > MAX_TEXT_LENGTH:
        msg = get_response("translate_too_long")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    args = context.args or []
    target_arg = args[0] if args else None
    target_code = _resolve_target(target_arg)

    try:
        from deep_translator import GoogleTranslator

        translated = GoogleTranslator(source="auto", target=target_code).translate(text=text)
    except Exception as e:
        logger.warning("Translation failed: %s", e)
        msg = get_response("translate_failed")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    if not translated:
        msg = get_response("translate_failed")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    await context.bot.send_message(
        chat.id,
        translated,
        reply_parameters=ReplyParameters(message_id=replied.message_id),
    )
