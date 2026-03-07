"""Text spam and media flood detection."""
import asyncio
import logging
import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    BULK_DELETE_CHUNK,
    CHAT_STICKER_CAP,
    CHAT_STICKER_WINDOW_SECONDS,
    MEDIA_FLOOD_THRESHOLD,
    MUTE_SECONDS,
    REPEAT_WINDOW_SECONDS,
    REP_LOW_COOLDOWN_SECONDS,
    SPAM_CATCHUP_SECONDS,
    SPAM_THRESHOLD,
)
from permissions import _demote_zero_perms_admin, _mute_permissions
from reputation_thresholds import get_rep, is_fully_muted, low_rep_text_cooldown_seconds
from resolvers import _update_username_cache
from responses import get_response
from utils import _schedule_notification_delete

logger = logging.getLogger(__name__)


def _log_task_exception(task: asyncio.Task) -> None:
    """Log exceptions from fire-and-forget tasks."""
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("Background task failed")


@dataclass
class MessageBucket:
    message_ids: list[int] = field(default_factory=list)
    timestamps: list[float] = field(default_factory=list)


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


async def _check_nsfw_and_act(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    If NSFW is enabled and message has checkable media in target group,
    run NSFW detection. Returns True if we deleted+muted (caller should return).
    Returns False to continue with normal handling.
    """
    try:
        from nsfw.config import NSFW_ENABLED, NSFW_MUTE_SECONDS, NSFW_THRESHOLD
    except ImportError:
        return False

    if not NSFW_ENABLED:
        return False

    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return False

    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return False

    file_id = None
    media_type = None
    needs_path = False  # video/archive need temp file path

    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "image"
    elif message.sticker:
        file_id = message.sticker.file_id
        # Animated/video stickers are WebM; static are WebP. Only images can go to PIL.
        if getattr(message.sticker, "is_animated", False) or getattr(message.sticker, "is_video", False):
            media_type = "video"
            needs_path = True
        else:
            media_type = "image"
    elif message.animation:
        file_id = message.animation.file_id
        # Animations (GIFs) are sent as MP4 by Telegram; need ffmpeg to extract frames.
        media_type = "video"
        needs_path = True
    elif message.video:
        file_id = message.video.file_id
        media_type = "video"
        needs_path = True
    elif message.video_note:
        file_id = message.video_note.file_id
        media_type = "video"
        needs_path = True
    elif message.document:
        try:
            from nsfw.check import get_media_type_from_document
            media_type = get_media_type_from_document(
                message.document.mime_type,
                message.document.file_name,
            )
        except ImportError:
            pass
        if media_type:
            file_id = message.document.file_id
            needs_path = media_type in ("video", "archive")

    if not file_id or not media_type:
        return False

    try:
        tg_file = await context.bot.get_file(file_id)
    except Exception as e:
        logger.warning("NSFW: failed to get file: %s", e)
        return False

    data = None
    temp_path = None
    try:
        if needs_path:
            if message.document:
                suffix = Path(message.document.file_name or "video.mp4").suffix
            elif message.sticker:
                suffix = ".webm"
            else:
                suffix = ".mp4"
            fd, temp_path = tempfile.mkstemp(suffix=suffix)
            try:
                os.close(fd)
                await tg_file.download_to_drive(temp_path)
                data = temp_path
            except Exception:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass
                raise
        else:
            data = bytes(await tg_file.download_as_bytearray())
    except Exception as e:
        logger.warning("NSFW: failed to download file: %s", e)
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        return False

    try:
        from nsfw.check import check_media_nsfw

        result = await asyncio.to_thread(
            check_media_nsfw,
            data,
            media_type,
            message.document.file_name if message.document else None,
        )
    except Exception as e:
        logger.warning("NSFW: detection failed: %s", e)
        return False
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    if not result or result.get("nsfw", 0) <= NSFW_THRESHOLD:
        return False

    mute_seconds = NSFW_MUTE_SECONDS if NSFW_MUTE_SECONDS is not None else MUTE_SECONDS
    until_ts = int((message.date + timedelta(seconds=mute_seconds)).timestamp())

    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
    except Exception as e:
        logger.warning("NSFW: delete failed: %s", e)

    restrictable = await _demote_zero_perms_admin(context.bot, chat.id, user.id)
    if restrictable:
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                permissions=_mute_permissions(),
                until_date=until_ts,
                use_independent_chat_permissions=True,
            )
        except Exception as e:
            logger.warning("NSFW: mute failed: %s", e)

    _update_username_cache(context, chat.id, user)
    mention = user.mention_html()
    msg = get_response("nsfw_warning", mention=mention)
    try:
        sent = await context.bot.send_message(chat_id=chat.id, text=msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
    except Exception as e:
        logger.warning("NSFW: warning message failed: %s", e)

    return True


def _is_forwarded(message) -> bool:
    return bool(getattr(message, "forward_origin", None) or getattr(message, "forward_from", None))


def _track_forward_for_fool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Track all forwards for potential /fool penalty (delete last 5)."""
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat or not _is_forwarded(message):
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    from config import FORWARD_TRACK_WINDOW_SECONDS
    now = asyncio.get_event_loop().time()
    key = (chat.id, user.id)
    bucket = context.bot_data.setdefault("forward_history", {}).setdefault(key, [])
    bucket.append((message.message_id, now))
    cutoff = now - FORWARD_TRACK_WINDOW_SECONDS
    bucket[:] = [(mid, ts) for mid, ts in bucket if ts > cutoff]


def _forward_identity(message) -> str:
    """Combination of forward metadata for duplicate detection."""
    parts = []
    if message.text:
        parts.append(message.text.strip().lower()[:500])
    fo = getattr(message, "forward_origin", None)
    if fo:
        parts.append(repr(type(fo).__name__))
        if hasattr(fo, "sender_user_name"):
            parts.append(str(getattr(fo, "sender_user_name", "")))
        if hasattr(fo, "chat"):
            c = getattr(fo, "chat", None)
            if c:
                parts.append(str(getattr(c, "id", "")))
    ff = getattr(message, "forward_from", None)
    if ff:
        parts.append(str(ff.id))
    ffc = getattr(message, "forward_from_chat", None)
    if ffc:
        parts.append(str(getattr(ffc, "id", "")))
        parts.append(str(getattr(message, "forward_from_message_id", "")))
    return "|".join(parts) if parts else str(message.message_id)


async def _check_doxx_and_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """If media hash is in doxx store, delete and return True."""
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return False
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return False
    doxx_hashes = context.bot_data.get("doxx_hashes") or set()
    if not doxx_hashes:
        return False
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.sticker:
        file_id = message.sticker.file_id
    elif message.animation:
        file_id = message.animation.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.video_note:
        file_id = message.video_note.file_id
    elif message.document:
        file_id = message.document.file_id
    if not file_id:
        return False
    try:
        tg_file = await context.bot.get_file(file_id)
        data = bytes(await tg_file.download_as_bytearray())
    except Exception as e:
        logger.debug("Doxx check: failed to download: %s", e)
        return False
    from config import DOXX_HASH_MAX_SIZE_MB
    if len(data) > DOXX_HASH_MAX_SIZE_MB * 1024 * 1024:
        return False
    import hashlib
    h = hashlib.sha256(data).hexdigest()
    if h not in doxx_hashes:
        return False
    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
    except Exception as e:
        logger.warning("Doxx: delete failed: %s", e)
    return True


async def _apply_chat_sticker_cap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Keep chat sticker/GIF count at CHAT_STICKER_CAP in rolling window. Delete oldest if over."""
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat or not (message.sticker or message.animation):
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    now = asyncio.get_event_loop().time()
    bucket = context.bot_data.setdefault("chat_sticker_bucket", {}).setdefault(chat.id, [])
    bucket.append((message.message_id, now))
    cutoff = now - CHAT_STICKER_WINDOW_SECONDS
    bucket[:] = [(mid, ts) for mid, ts in bucket if ts > cutoff]
    while len(bucket) > CHAT_STICKER_CAP:
        oldest = min(bucket, key=lambda x: x[1])
        bucket.remove(oldest)
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=oldest[0])
        except Exception as e:
            logger.warning("Chat sticker cap: delete failed %s: %s", oldest[0], e)


async def _handle_marked_user_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """If sender is fool-marked and message is forward, delete it. Returns True if we handled."""
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat or not _is_forwarded(message):
        return False
    fool_marked = context.bot_data.get("fool_marked") or set()
    if user.id not in fool_marked:
        return False
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return False
    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
    except Exception as e:
        logger.warning("Fool forward delete failed %s: %s", message.message_id, e)
        return False
    return True


async def handle_message_or_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route to text spam or media flood handler."""
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    rep = get_rep(context, chat.id, user.id)
    if is_fully_muted(rep):
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
        except Exception as e:
            logger.warning("Low-rep delete failed: %s", e)
        restrictable = await _demote_zero_perms_admin(context.bot, chat.id, user.id)
        if restrictable:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=user.id,
                    permissions=_mute_permissions(),
                    until_date=0,
                    use_independent_chat_permissions=True,
                )
            except Exception as e:
                logger.debug("Low-rep restrict failed (may already restricted): %s", e)
        return
    cooldown = low_rep_text_cooldown_seconds(rep)
    if cooldown is not None:
        last_key = (chat.id, user.id)
        last_map = context.bot_data.setdefault("low_rep_last_message", {})
        now = asyncio.get_event_loop().time()
        last_ts = last_map.get(last_key, 0)
        if now - last_ts < cooldown:
            try:
                await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
            except Exception as e:
                logger.warning("Low-rep cooldown delete failed: %s", e)
            return
        if message.sticker or message.animation or message.photo or message.video or message.video_note or message.document:
            try:
                await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
            except Exception as e:
                logger.warning("Low-rep media delete failed: %s", e)
            return
        last_map[last_key] = now

    if _is_forwarded(message):
        _track_forward_for_fool(update, context)
        handled = await _handle_marked_user_forward(update, context)
        if handled:
            return

    if message.sticker or message.animation or message.photo or message.video or message.video_note or message.document:
        acted = await _check_doxx_and_delete(update, context)
        if acted:
            return

        # Run NSFW in parallel so it doesn't block doxx/sticker cap/media flood
        nsfw_task = asyncio.create_task(_check_nsfw_and_act(update, context))
        nsfw_task.add_done_callback(_log_task_exception)

    if message.sticker or message.animation:
        await _apply_chat_sticker_cap(update, context)
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
    restrictable = await _demote_zero_perms_admin(context.bot, chat.id, user.id)
    if restrictable:
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
    restrictable = await _demote_zero_perms_admin(context.bot, chat.id, user.id)
    if restrictable:
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
