"""Handlers for /fool and /unfool."""

import logging
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import ContextTypes

from config import FOOL_VOTE_THRESHOLD, MUTE_SECONDS
from handlers.citizenship import require_citizenship
from permissions import _demote_zero_perms_admin, _is_real_admin, _mute_permissions
from responses import get_response
from state import _load_fool_marked, _save_fool_marked
from utils import _schedule_notification_delete

logger = logging.getLogger(__name__)


def _is_forwarded(message) -> bool:
    return bool(getattr(message, "forward_origin", None) or getattr(message, "forward_from", None))


def _has_media_or_sticker(message) -> bool:
    return bool(
        message.photo or message.video or message.video_note or message.document or message.sticker or message.animation
    )


async def cmd_fool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        return
    replied = message.reply_to_message
    target_user = replied.from_user
    if not target_user:
        return
    if not (_is_forwarded(replied) or _has_media_or_sticker(replied)):
        return

    _schedule_notification_delete(context, chat.id, message.message_id)

    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        return

    fool_marked = context.bot_data.get("fool_marked")
    if fool_marked is None:
        fool_marked = _load_fool_marked()
        context.bot_data["fool_marked"] = fool_marked

    is_real = _is_real_admin(member)
    if is_real:
        await _apply_fool_mark_and_penalty(context, chat, target_user, sender, replied)
        return

    reply_msg_id = replied.message_id
    votes = context.bot_data.setdefault("fool_votes", {})
    key = (chat.id, reply_msg_id)
    if key not in votes:
        votes[key] = set()
    votes[key].add(sender.id)
    if len(votes[key]) >= FOOL_VOTE_THRESHOLD:
        await _apply_fool_mark_and_penalty(context, chat, target_user, sender, replied)
        del votes[key]


async def _apply_fool_mark_and_penalty(context, chat, target_user, marker, replied) -> None:
    fool_marked = context.bot_data.get("fool_marked") or set()
    fool_marked.add(target_user.id)
    context.bot_data["fool_marked"] = fool_marked
    _save_fool_marked(fool_marked)

    if _is_forwarded(replied):
        forward_history = context.bot_data.get("forward_history") or {}
        key = (chat.id, target_user.id)
        bucket = forward_history.get(key, [])
        ids_to_del = sorted([mid for mid, _ in bucket], reverse=True)[:5]
        for mid in ids_to_del:
            try:
                await context.bot.delete_message(chat_id=chat.id, message_id=mid)
            except Exception as e:
                logger.warning("Fool penalty delete %s: %s", mid, e)
        if key in forward_history:
            forward_history[key] = [(m, t) for m, t in bucket if m not in ids_to_del]

        until_ts = int((datetime.now(timezone.utc) + timedelta(seconds=MUTE_SECONDS)).timestamp())
        restrictable = await _demote_zero_perms_admin(context.bot, chat.id, target_user.id)
        if restrictable:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=target_user.id,
                    permissions=_mute_permissions(),
                    until_date=until_ts,
                    use_independent_chat_permissions=True,
                )
            except Exception as e:
                logger.warning("Fool mute failed: %s", e)

    mention = target_user.mention_html()
    msg = get_response("fool_marked", mention=mention)
    sent = await context.bot.send_message(chat_id=chat.id, text=msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_unfool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        msg = get_response("unfool_real_admin_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    from resolvers import _get_target_user_from_message

    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("unfool_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    fool_marked = context.bot_data.get("fool_marked") or set()
    if target_user.id in fool_marked:
        fool_marked.discard(target_user.id)
        context.bot_data["fool_marked"] = fool_marked
        _save_fool_marked(fool_marked)
        msg = get_response("unfool_done", mention=target_user.mention_html())
    else:
        msg = get_response("unfool_not_marked", mention=target_user.mention_html())
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
