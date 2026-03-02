"""Text spam and media flood detection."""
import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    BULK_DELETE_CHUNK,
    MEDIA_FLOOD_THRESHOLD,
    MUTE_SECONDS,
    REPEAT_WINDOW_SECONDS,
    SPAM_CATCHUP_SECONDS,
    SPAM_THRESHOLD,
)
from permissions import _mute_permissions
from resolvers import _update_username_cache
from responses import get_response
from utils import _schedule_notification_delete

logger = logging.getLogger(__name__)


@dataclass
class MessageBucket:
    message_ids: list[int] = field(default_factory=list)
    timestamps: list[float] = field(default_factory=list)


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


async def handle_message_or_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route to text spam or media flood handler."""
    message = update.effective_message
    if not message:
        return
    if message.sticker or message.animation:
        await handle_media_flood(update, context)
        return
    if message.text:
        await handle_message(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat or not message.text:
        return
    target_group = context.bot_data["target_group"]
    if chat.id != target_group:
        return
    _update_username_cache(context, chat.id, user)
    text = normalize_text(message.text)
    now = asyncio.get_event_loop().time()
    spam_last_trigger = context.bot_data.get("spam_last_trigger") or {}
    key = (chat.id, user.id, text)
    if key in spam_last_trigger and (now - spam_last_trigger[key]) <= SPAM_CATCHUP_SECONDS:
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
        except Exception as e:
            logger.warning("Catch-up delete failed message_id=%s: %s", message.message_id, e)
        return
    spam_state = context.bot_data["spam_state"]
    user_state = spam_state[(chat.id, user.id)]
    bucket = user_state[text]
    bucket.message_ids.append(message.message_id)
    bucket.timestamps.append(now)
    recent_count = sum(1 for ts in bucket.timestamps if now - ts <= REPEAT_WINDOW_SECONDS)
    if recent_count < SPAM_THRESHOLD:
        recent_message_ids = []
        recent_timestamps = []
        for msg_id, ts in zip(bucket.message_ids, bucket.timestamps):
            if now - ts <= REPEAT_WINDOW_SECONDS:
                recent_message_ids.append(msg_id)
                recent_timestamps.append(ts)
        bucket.message_ids = recent_message_ids
        bucket.timestamps = recent_timestamps
        return
    ids_to_delete = sorted(bucket.message_ids)
    chat_id = chat.id
    try:
        for i in range(0, len(ids_to_delete), BULK_DELETE_CHUNK):
            chunk = ids_to_delete[i : i + BULK_DELETE_CHUNK]
            await context.bot.delete_messages(chat_id=chat_id, message_ids=chunk)
            if i + BULK_DELETE_CHUNK < len(ids_to_delete):
                await asyncio.sleep(0.3)
    except Exception as bulk_err:
        logger.warning("Bulk delete failed (%s), falling back to one-by-one: %s", bulk_err, ids_to_delete)
        for msg_id in ids_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.warning("Could not delete message %s: %s", msg_id, e)
    until_ts = int((update.message.date + timedelta(seconds=MUTE_SECONDS)).timestamp())
    await context.bot.restrict_chat_member(
        chat_id=chat.id,
        user_id=user.id,
        permissions=_mute_permissions(),
        until_date=until_ts,
        use_independent_chat_permissions=True,
    )
    mention = user.mention_html()
    msg = get_response("spam_warning", mention=mention)
    sent = await context.bot.send_message(chat_id=chat.id, text=msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
    if "spam_last_trigger" not in context.bot_data:
        context.bot_data["spam_last_trigger"] = {}
    context.bot_data["spam_last_trigger"][(chat.id, user.id, text)] = now
    bucket.message_ids.clear()
    bucket.timestamps.clear()


async def handle_media_flood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return
    target_group = context.bot_data["target_group"]
    if chat.id != target_group:
        return
    _update_username_cache(context, chat.id, user)
    now = asyncio.get_event_loop().time()
    media_key = (chat.id, user.id)
    media_last_trigger = context.bot_data.get("media_flood_last_trigger") or {}
    if media_key in media_last_trigger and (now - media_last_trigger[media_key]) <= SPAM_CATCHUP_SECONDS:
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
        except Exception as e:
            logger.warning("Media catch-up delete failed message_id=%s: %s", message.message_id, e)
        return
    media_state = context.bot_data["media_flood_state"]
    bucket = media_state[media_key]
    bucket.message_ids.append(message.message_id)
    bucket.timestamps.append(now)
    recent_ids = []
    recent_ts = []
    for mid, ts in zip(bucket.message_ids, bucket.timestamps):
        if now - ts <= REPEAT_WINDOW_SECONDS:
            recent_ids.append(mid)
            recent_ts.append(ts)
    bucket.message_ids = recent_ids
    bucket.timestamps = recent_ts
    if len(bucket.message_ids) < MEDIA_FLOOD_THRESHOLD:
        return
    ids_to_delete = sorted(bucket.message_ids)
    chat_id = chat.id
    try:
        for i in range(0, len(ids_to_delete), BULK_DELETE_CHUNK):
            chunk = ids_to_delete[i : i + BULK_DELETE_CHUNK]
            await context.bot.delete_messages(chat_id=chat_id, message_ids=chunk)
            if i + BULK_DELETE_CHUNK < len(ids_to_delete):
                await asyncio.sleep(0.3)
    except Exception as bulk_err:
        logger.warning("Media flood bulk delete failed (%s), falling back to one-by-one: %s", bulk_err, ids_to_delete)
        for msg_id in ids_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.warning("Could not delete message %s: %s", msg_id, e)
    until_ts = int((update.message.date + timedelta(seconds=MUTE_SECONDS)).timestamp())
    await context.bot.restrict_chat_member(
        chat_id=chat.id,
        user_id=user.id,
        permissions=_mute_permissions(),
        until_date=until_ts,
        use_independent_chat_permissions=True,
    )
    mention = user.mention_html()
    msg = get_response("spam_warning", mention=mention)
    sent = await context.bot.send_message(chat_id=chat.id, text=msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
    if "media_flood_last_trigger" not in context.bot_data:
        context.bot_data["media_flood_last_trigger"] = {}
    context.bot_data["media_flood_last_trigger"][media_key] = now
    bucket.message_ids.clear()
    bucket.timestamps.clear()
