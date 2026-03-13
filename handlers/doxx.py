"""Handlers for /doxx, /doxxed, /revoke_doxx."""

import hashlib
import logging
import time

from telegram import Update
from telegram.ext import ContextTypes

from config import DOXX_HASH_MAX_SIZE_MB
from permissions import _is_real_admin
from responses import get_response
from state import _load_doxx_grants, _load_doxx_hashes, _save_doxx_grants, _save_doxx_hashes
from utils import _schedule_notification_delete

from handlers.citizenship import require_citizenship

logger = logging.getLogger(__name__)


def _has_media(message) -> bool:
    return bool(
        message.photo or message.video or message.video_note or message.document or message.sticker or message.animation
    )


async def cmd_doxxed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Real admin grants /doxx right to a user (reply or mention)."""
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return

    _schedule_notification_delete(context, chat.id, message.message_id)
    if not await require_citizenship(update, context):
        return

    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if not _is_real_admin(member):
        msg = get_response("doxxed_real_admin_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    from resolvers import _get_target_user_from_message

    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("doxxed_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    grants = context.bot_data.get("doxx_grants")
    if grants is None:
        grants = _load_doxx_grants()
        context.bot_data["doxx_grants"] = grants
    key = (chat.id, target_user.id)
    grants[key] = {"granted_by": sender.id, "expires_at": time.time() + 365 * 24 * 60 * 60}
    _save_doxx_grants(grants)
    from commands_menu import update_dm_commands_for_user, update_user_commands, user_grants

    has_stfu, _ = user_grants(context.bot_data, chat.id, target_user.id)
    await update_user_commands(context.bot, chat.id, target_user.id, has_stfu_grant=has_stfu, has_doxx_grant=True)
    await update_dm_commands_for_user(context.bot, context.bot_data, chat.id, target_user.id)
    msg = get_response("doxxed_done", target=target_user.mention_html())
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_doxx(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Granted user replies /doxx to media -> delete it and remember hash."""
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    if not await require_citizenship(update, context):
        return
    if not message.reply_to_message:
        msg = get_response("doxx_reply_required")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    _schedule_notification_delete(context, chat.id, message.message_id)

    replied = message.reply_to_message
    if not _has_media(replied):
        msg = get_response("doxx_not_media")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    grants = context.bot_data.get("doxx_grants")
    if grants is None:
        grants = _load_doxx_grants()
        context.bot_data["doxx_grants"] = grants
    now = time.time()
    key = (chat.id, sender.id)
    grant = grants.get(key)
    if not grant or grant.get("expires_at", 0) < now:
        msg = get_response("doxx_not_granted", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    file_id = None
    if replied.photo:
        file_id = replied.photo[-1].file_id
    elif replied.sticker:
        file_id = replied.sticker.file_id
    elif replied.animation:
        file_id = replied.animation.file_id
    elif replied.video:
        file_id = replied.video.file_id
    elif replied.video_note:
        file_id = replied.video_note.file_id
    elif replied.document:
        file_id = replied.document.file_id
    if not file_id:
        return

    try:
        tg_file = await context.bot.get_file(file_id)
        data = bytes(await tg_file.download_as_bytearray())
    except Exception as e:
        logger.warning("Doxx download failed: %s", e)
        msg = get_response("doxx_download_failed")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    max_bytes = DOXX_HASH_MAX_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        msg = get_response("doxx_too_large")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    h = hashlib.sha256(data).hexdigest()
    doxx_hashes = context.bot_data.get("doxx_hashes")
    if doxx_hashes is None:
        doxx_hashes = _load_doxx_hashes()
        context.bot_data["doxx_hashes"] = doxx_hashes
    doxx_hashes.add(h)
    context.bot_data["doxx_hashes"] = doxx_hashes
    _save_doxx_hashes(doxx_hashes)

    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=replied.message_id)
    except Exception as e:
        logger.warning("Doxx delete failed: %s", e)

    msg = get_response("doxx_done")
    sent = await message.reply_text(msg)
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_revoke_doxx(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Real admin revokes /doxx right from a user."""
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return

    _schedule_notification_delete(context, chat.id, message.message_id)
    if not await require_citizenship(update, context):
        return

    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if not _is_real_admin(member):
        msg = get_response("revoke_doxx_real_admin_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    from resolvers import _get_target_user_from_message

    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("revoke_doxx_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    grants = context.bot_data.get("doxx_grants") or {}
    key = (chat.id, target_user.id)
    if key in grants:
        del grants[key]
        _save_doxx_grants(grants)
        from commands_menu import update_dm_commands_for_user, update_user_commands, user_grants

        has_stfu, _ = user_grants(context.bot_data, chat.id, target_user.id)
        await update_user_commands(context.bot, chat.id, target_user.id, has_stfu_grant=has_stfu, has_doxx_grant=False)
        await update_dm_commands_for_user(context.bot, context.bot_data, chat.id, target_user.id)
        msg = get_response("revoke_doxx_done", mention=target_user.mention_html())
    else:
        msg = get_response("revoke_doxx_not_granted", mention=target_user.mention_html())
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
