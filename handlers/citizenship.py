"""Handlers for /grant_citizenship and /revoke_citizenship."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import REPUTATION_DEFAULT
from grants import _save_stfu_grants
from permissions import _has_moderation_rights
from reputation_thresholds import get_rep_tier
from resolvers import _get_target_user_from_message
from responses import get_response
from state import (
    _load_acquired_stfu,
    _load_citizens,
    _load_doxx_grants,
    _load_reputation,
    _save_acquired_stfu,
    _save_citizens,
    _save_doxx_grants,
    _save_reputation,
)
from utils import _schedule_notification_delete

logger = logging.getLogger(__name__)

# Citizen tier starts at 90 (Peasant is 73-89). Revoke only applies to Citizen+.
REVOKE_MIN_REP = 90
# Rep >= 120 (Herald) grants citizenship automatically.
CITIZEN_REP_THRESHOLD = 120


def has_citizenship(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """True if user is a citizen: in reputation AND (in citizens set OR rep >= 120)."""
    rep = context.bot_data.get("reputation")
    if rep is None:
        rep = _load_reputation()
        context.bot_data["reputation"] = rep
    key = (chat_id, user_id)
    if key not in rep:
        return False
    citizens = context.bot_data.get("citizens")
    if citizens is None:
        citizens = _load_citizens()
        context.bot_data["citizens"] = citizens
    return key in citizens or rep[key] >= CITIZEN_REP_THRESHOLD


async def require_citizenship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Returns True if allowed (citizen or admin), False if blocked.
    Sends reply when blocked. Only checks when in target group.
    """
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return True
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
    except Exception:
        return True
    if member.status in ("creator", "administrator"):
        return True
    if has_citizenship(context, chat.id, user.id):
        return True
    msg = get_response("citizenship_required")
    sent = await update.effective_message.reply_text(msg)
    _schedule_notification_delete(context, chat.id, sent.message_id)
    return False


async def cmd_grant_citizenship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mod-only: grant citizenship to target (reply or @mention)."""
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
    if not _has_moderation_rights(member):
        msg = get_response("grant_citizenship_mod_only")
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("grant_citizenship_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    rep = context.bot_data.get("reputation")
    if rep is None:
        rep = _load_reputation()
        context.bot_data["reputation"] = rep
    citizens = context.bot_data.get("citizens")
    if citizens is None:
        citizens = _load_citizens()
        context.bot_data["citizens"] = citizens

    key = (chat.id, target_user.id)
    rep[key] = REPUTATION_DEFAULT
    _save_reputation(rep)
    citizens.add(key)
    _save_citizens(citizens)

    try:
        if hasattr(context.bot, "_post"):
            await context.bot._post(
                "setChatMemberTag",
                data={"chat_id": chat.id, "user_id": target_user.id, "tag": get_rep_tier(REPUTATION_DEFAULT)},
            )
    except Exception as e:
        logger.warning("grant_citizenship: failed to set tag for %s: %s", target_user.id, e)

    msg = get_response("grant_citizenship_done", mention=target_user.mention_html())
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_revoke_citizenship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mod-only: revoke citizenship from target (Citizen+ only)."""
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
    if not _has_moderation_rights(member):
        msg = get_response("revoke_citizenship_mod_only")
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("revoke_citizenship_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    rep = context.bot_data.get("reputation")
    if rep is None:
        rep = _load_reputation()
        context.bot_data["reputation"] = rep
    key = (chat.id, target_user.id)

    if key not in rep:
        msg = get_response("revoke_citizenship_not_citizen", mention=target_user.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    current_rep = rep[key]
    if current_rep < REVOKE_MIN_REP:
        msg = get_response("revoke_citizenship_peasant_below")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    del rep[key]
    _save_reputation(rep)

    citizens = context.bot_data.get("citizens")
    if citizens is None:
        citizens = _load_citizens()
        context.bot_data["citizens"] = citizens
    citizens.discard(key)
    _save_citizens(citizens)

    grants = context.bot_data.get("stfu_grants")
    if grants and key in grants:
        del grants[key]
        _save_stfu_grants(context.bot_data.get("state_file") or "", grants)

    doxx = context.bot_data.get("doxx_grants")
    if doxx is None:
        doxx = _load_doxx_grants()
        context.bot_data["doxx_grants"] = doxx
    if key in doxx:
        del doxx[key]
        _save_doxx_grants(doxx)

    acquired = context.bot_data.get("acquired_stfu")
    if acquired is None:
        acquired = _load_acquired_stfu()
        context.bot_data["acquired_stfu"] = acquired
    acquired.discard(key)
    _save_acquired_stfu(acquired)

    try:
        if hasattr(context.bot, "_post"):
            await context.bot._post(
                "setChatMemberTag",
                data={"chat_id": chat.id, "user_id": target_user.id, "tag": ""},
            )
    except Exception as e:
        logger.warning("revoke_citizenship: failed to clear tag for %s: %s", target_user.id, e)

    from commands_menu import update_dm_commands_for_user, update_user_commands

    await update_user_commands(context.bot, chat.id, target_user.id, has_stfu_grant=False, has_doxx_grant=False)
    await update_dm_commands_for_user(context.bot, context.bot_data, chat.id, target_user.id)

    msg = get_response("revoke_citizenship_done", mention=target_user.mention_html())
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
