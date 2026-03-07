"""Handler for /holycowshithindupajeetarmor (stfu-proof armor)."""

import logging
import time

from telegram import Update
from telegram.ext import ContextTypes

from config import STFUPROOF_COOLDOWN_SECONDS
from reputation_thresholds import armor_duration_seconds, can_use_armor, get_rep
from resolvers import _get_target_user_from_message
from responses import get_response
from utils import _format_time_left, _schedule_notification_delete

logger = logging.getLogger(__name__)


async def cmd_stfuproof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data["target_group"]
    if chat.id != target_group:
        sent = await message.reply_text(
            get_response("wrong_chat_short", chat_id=chat.id),
            parse_mode="HTML",
        )
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    _schedule_notification_delete(context, chat.id, message.message_id)
    rep = get_rep(context, chat.id, sender.id)
    if not can_use_armor(rep):
        msg = get_response("stfuproof_blocked_low_rep")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    now = time.time()
    caster_key = (int(chat.id), int(sender.id))
    cooldown = context.bot_data.get("stfuproof_cooldown")
    if cooldown is None:
        cooldown = {}
        context.bot_data["stfuproof_cooldown"] = cooldown
    last = float(cooldown.get(caster_key, 0))
    remaining_cd = STFUPROOF_COOLDOWN_SECONDS - (now - last)
    if remaining_cd > 0:
        msg = get_response("stfuproof_cooldown", seconds=int(remaining_cd) + 1)
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if target_user and target_user.id != sender.id:
        recipient_key = (int(chat.id), int(target_user.id))
        recipient_id = target_user.id
    else:
        recipient_key = caster_key
        recipient_id = sender.id
    duration_overrides = context.bot_data.get("stfuproof_duration_overrides")
    if duration_overrides is None:
        duration_overrides = {}
        context.bot_data["stfuproof_duration_overrides"] = duration_overrides
    recipient_rep = get_rep(context, chat.id, recipient_id)
    default_duration = armor_duration_seconds(recipient_rep)
    duration = int(duration_overrides.get(recipient_key, default_duration))
    duration = max(1, duration)
    immunity = context.bot_data.get("stfuproof_immunity")
    if immunity is None:
        immunity = {}
        context.bot_data["stfuproof_immunity"] = immunity
    immunity[recipient_key] = {"expires_at": now + duration}
    cooldown[caster_key] = now
    logger.info("stfuproof: user_id=%s immune for %ss (key=%s)", recipient_id, duration, recipient_key)
    time_str = _format_time_left(duration)
    if recipient_id == sender.id:
        msg = get_response("stfuproof_self", time_str=time_str)
        sent = await message.reply_text(msg, parse_mode="HTML")
    else:
        msg = get_response("stfuproof_other", mention=target_user.mention_html(), time_str=time_str)
        sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
