"""Handler for /translate — translate replied message to English or specified language."""

import logging

from telegram import ReplyParameters, Update
from telegram.ext import ContextTypes

from responses import get_response
from utils import _schedule_notification_delete

logger = logging.getLogger(__name__)

# Map common language names/aliases to Google Translate target codes.
# Covers languages supported by Google Translate (deep_translator). No ancient scripts (e.g. hieroglyphs, cuneiform).
LANGUAGE_ALIASES: dict[str, str] = {
    "afrikaans": "af",
    "af": "af",
    "albanian": "sq",
    "sq": "sq",
    "amharic": "am",
    "am": "am",
    "arabic": "ar",
    "ar": "ar",
    "armenian": "hy",
    "hy": "hy",
    "azerbaijani": "az",
    "az": "az",
    "basque": "eu",
    "eu": "eu",
    "belarusian": "be",
    "be": "be",
    "bengali": "bn",
    "bn": "bn",
    "bosnian": "bs",
    "bs": "bs",
    "bulgarian": "bg",
    "bg": "bg",
    "catalan": "ca",
    "ca": "ca",
    "chinese": "zh-CN",
    "mandarin": "zh-CN",
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "cantonese": "zh-TW",
    "zh-tw": "zh-TW",
    "corsican": "co",
    "co": "co",
    "croatian": "hr",
    "hr": "hr",
    "czech": "cs",
    "cs": "cs",
    "danish": "da",
    "da": "da",
    "dutch": "nl",
    "nl": "nl",
    "english": "en",
    "en": "en",
    "esperanto": "eo",
    "eo": "eo",
    "estonian": "et",
    "et": "et",
    "filipino": "fil",
    "fil": "fil",
    "tagalog": "tl",
    "tl": "tl",
    "finnish": "fi",
    "fi": "fi",
    "french": "fr",
    "fr": "fr",
    "frisian": "fy",
    "fy": "fy",
    "galician": "gl",
    "gl": "gl",
    "georgian": "ka",
    "ka": "ka",
    "german": "de",
    "de": "de",
    "greek": "el",
    "el": "el",
    "gujarati": "gu",
    "gu": "gu",
    "haitian": "ht",
    "creole": "ht",
    "ht": "ht",
    "hausa": "ha",
    "ha": "ha",
    "hawaiian": "haw",
    "haw": "haw",
    "hebrew": "iw",
    "he": "iw",
    "iw": "iw",  # deep_translator uses "iw" for Hebrew, not "he"
    "hindi": "hi",
    "hi": "hi",
    "hmong": "hmn",
    "hmn": "hmn",
    "hungarian": "hu",
    "hu": "hu",
    "icelandic": "is",
    "is": "is",
    "igbo": "ig",
    "ig": "ig",
    "indonesian": "id",
    "id": "id",
    "irish": "ga",
    "ga": "ga",
    "italian": "it",
    "it": "it",
    "japanese": "ja",
    "ja": "ja",
    "javanese": "jv",
    "jv": "jv",
    "kannada": "kn",
    "kn": "kn",
    "kazakh": "kk",
    "kk": "kk",
    "khmer": "km",
    "km": "km",
    "kinyarwanda": "rw",
    "rw": "rw",
    "korean": "ko",
    "ko": "ko",
    "kurdish": "ku",
    "ku": "ku",
    "kyrgyz": "ky",
    "ky": "ky",
    "lao": "lo",
    "lo": "lo",
    "latin": "la",
    "la": "la",
    "latvian": "lv",
    "lv": "lv",
    "lithuanian": "lt",
    "lt": "lt",
    "luxembourgish": "lb",
    "lb": "lb",
    "macedonian": "mk",
    "mk": "mk",
    "malagasy": "mg",
    "mg": "mg",
    "malay": "ms",
    "ms": "ms",
    "malayalam": "ml",
    "ml": "ml",
    "maltese": "mt",
    "mt": "mt",
    "maori": "mi",
    "mi": "mi",
    "marathi": "mr",
    "mr": "mr",
    "mongolian": "mn",
    "mn": "mn",
    "myanmar": "my",
    "burmese": "my",
    "my": "my",
    "nepali": "ne",
    "ne": "ne",
    "norwegian": "no",
    "no": "no",
    "nyanja": "ny",
    "chichewa": "ny",
    "ny": "ny",
    "odia": "or",
    "oriya": "or",
    "or": "or",
    "pashto": "ps",
    "ps": "ps",
    "persian": "fa",
    "fa": "fa",
    "polish": "pl",
    "pl": "pl",
    "portuguese": "pt",
    "pt": "pt",
    "punjabi": "pa",
    "pa": "pa",
    "romanian": "ro",
    "ro": "ro",
    "russian": "ru",
    "ru": "ru",
    "samoan": "sm",
    "sm": "sm",
    "scots": "gd",
    "gaelic": "gd",
    "gd": "gd",
    "serbian": "sr",
    "sr": "sr",
    "sesotho": "st",
    "st": "st",
    "shona": "sn",
    "sn": "sn",
    "sindhi": "sd",
    "sd": "sd",
    "sinhala": "si",
    "sinhalese": "si",
    "si": "si",
    "slovak": "sk",
    "sk": "sk",
    "slovenian": "sl",
    "sl": "sl",
    "somali": "so",
    "so": "so",
    "spanish": "es",
    "es": "es",
    "sundanese": "su",
    "su": "su",
    "swahili": "sw",
    "sw": "sw",
    "swedish": "sv",
    "sv": "sv",
    "tajik": "tg",
    "tg": "tg",
    "tamil": "ta",
    "ta": "ta",
    "tatar": "tt",
    "tt": "tt",
    "telugu": "te",
    "te": "te",
    "thai": "th",
    "th": "th",
    "tibetan": "bo",
    "bo": "bo",
    "turkmen": "tk",
    "tk": "tk",
    "turkish": "tr",
    "tr": "tr",
    "ukrainian": "uk",
    "uk": "uk",
    "urdu": "ur",
    "ur": "ur",
    "uyghur": "ug",
    "ug": "ug",
    "uzbek": "uz",
    "uz": "uz",
    "vietnamese": "vi",
    "vi": "vi",
    "welsh": "cy",
    "cy": "cy",
    "xhosa": "xh",
    "xh": "xh",
    "yiddish": "yi",
    "yi": "yi",
    "yoruba": "yo",
    "yo": "yo",
    "zulu": "zu",
    "zu": "zu",
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
    except Exception:
        logger.exception("Translation failed for target=%s text_len=%s", target_code, len(text))
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
