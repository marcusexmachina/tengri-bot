"""Handler for /exile (ban user from the group)."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.reputation import apply_reputation_delta
from permissions import _can_exile
from resolvers import _get_target_user_from_message
from responses import get_response
from utils import _schedule_notification_delete

logger = logging.getLogger(__name__)


async def cmd_exile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return

    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return

    _schedule_notification_delete(context, chat.id, message.message_id)

    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    if not _can_exile(member):
        await apply_reputation_delta(context, chat.id, sender.id, -1)
        msg = get_response("exile_not_allowed", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("exile_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    try:
        await context.bot.ban_chat_member(chat_id=chat.id, user_id=target_user.id)
    except Exception as e:
        logger.warning("Exile failed for user_id=%s: %s", target_user.id, e)
        msg = get_response("exile_failed", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    # Standalone pinned announcement — separate from other Tengri messages, not auto-deleted
    msg = get_response(
        "exile_announcement",
        exiled=target_user.mention_html(),
        caster=sender.mention_html(),
    )
    sent = await context.bot.send_message(
        chat_id=chat.id,
        text=msg,
        parse_mode="HTML",
    )
    try:
        await context.bot.pin_chat_message(chat_id=chat.id, message_id=sent.message_id)
    except Exception as e:
        logger.warning("Could not pin exile announcement: %s", e)
