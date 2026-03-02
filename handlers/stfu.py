"""Handlers for /stfu, /unstfu, /grant_stfu, /revoke_stfu, /save_grants."""
import logging
import time
from datetime import timedelta

from telegram import Update, User
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from config import (
    ADMIN_STFU_DEFAULT_SECONDS,
    ADMIN_STFU_MAX_SECONDS,
    DELEGATE_STFU_DEFAULT_SECONDS,
    DELEGATE_STFU_MAX_SECONDS,
    MAX_TEMP_RESTRICT_SECONDS,
    TELEGRAM_MIN_RESTRICT_SECONDS,
)
from grants import _load_stfu_grants, _save_stfu_grants
from permissions import _full_permissions, _has_moderation_rights, _mute_permissions
from resolvers import _get_target_user_from_message, _get_target_users_from_message
from responses import get_response
from utils import _format_time_left, _schedule_notification_delete, extract_duration_from_message

logger = logging.getLogger(__name__)


async def cmd_unstfu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data["target_group"]
    if chat.id != target_group:
        sent = await message.reply_text(
            get_response("wrong_chat", chat_id=chat.id),
            parse_mode="HTML",
        )
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    _schedule_notification_delete(context, chat.id, message.message_id)
    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    is_mod = _has_moderation_rights(member)
    if not is_mod:
        now = time.time()
        grants = context.bot_data.get("stfu_grants") or {}
        grant = grants.get((chat.id, sender.id))
        if not grant or grant.get("expires_at", 0) < now:
            msg = get_response("not_admin_unmute", mention=sender.mention_html())
            sent = await message.reply_text(msg, parse_mode="HTML")
            _schedule_notification_delete(context, chat.id, sent.message_id)
            return
    chat_type = getattr(chat, "type", None) or getattr(chat, "_type", None)
    if str(chat_type).lower() == "group":
        msg = get_response("unmute_basic_group")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    users_to_unmute = await _get_target_users_from_message(message, context)
    if not users_to_unmute:
        msg = get_response("no_target_unmute")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    unmuted: list[User] = []
    failed: list[User] = []
    for user in users_to_unmute:
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                permissions=_full_permissions(),
                until_date=0,
                use_independent_chat_permissions=True,
            )
            unmuted.append(user)
        except Exception as e:
            logger.warning("Unmute failed for user_id=%s: %s", user.id, e)
            failed.append(user)
    if not unmuted:
        msg = get_response("unmute_fail")
        sent = await message.reply_text(msg)
    elif len(unmuted) == 1 and not failed:
        msg = get_response("unmute_success", mention=unmuted[0].mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
    else:
        parts = ["Unmuted: " + ", ".join(u.mention_html() for u in unmuted)]
        if failed:
            parts.append("Failed: " + ", ".join(u.mention_html() for u in failed))
        sent = await message.reply_text(" ".join(parts), parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_grant_stfu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data["target_group"]
    if chat.id != target_group:
        sent = await message.reply_text(get_response("wrong_chat", chat_id=chat.id), parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
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
        msg = get_response("grant_stfu_mod_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("grant_stfu_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    duration_seconds = extract_duration_from_message(message, target_user)
    default_grant_seconds = 24 * 60 * 60
    if duration_seconds is None:
        duration_seconds = default_grant_seconds
    duration_seconds = min(duration_seconds, MAX_TEMP_RESTRICT_SECONDS)
    now = time.time()
    grants = context.bot_data.get("stfu_grants")
    if grants is None:
        grants = {}
        context.bot_data["stfu_grants"] = grants
    grants[(chat.id, target_user.id)] = {"granted_by": sender.id, "expires_at": now + duration_seconds}
    _save_stfu_grants(context.bot_data.get("state_file") or "", grants)
    hours = round(duration_seconds / 3600, 1)
    msg = get_response("grant_stfu_done", target=target_user.mention_html(), sender=sender.mention_html(), hours=hours)
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_revoke_stfu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data["target_group"]
    if chat.id != target_group:
        sent = await message.reply_text(get_response("wrong_chat", chat_id=chat.id), parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
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
        msg = get_response("revoke_stfu_mod_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    parts = (message.text or "").strip().split(maxsplit=1)
    rest = (parts[1].strip().lower() if len(parts) > 1 else "") or ""
    if rest == "all":
        grants = context.bot_data.get("stfu_grants") or {}
        keys_to_remove = [k for k in grants if k[0] == chat.id]
        for k in keys_to_remove:
            del grants[k]
        _save_stfu_grants(context.bot_data.get("state_file") or "", grants)
        msg = get_response("revoke_stfu_all_done", count=len(keys_to_remove)) if keys_to_remove else get_response("revoke_stfu_all_empty")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("revoke_stfu_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    grants = context.bot_data.get("stfu_grants") or {}
    key = (chat.id, target_user.id)
    if key in grants:
        del grants[key]
        _save_stfu_grants(context.bot_data.get("state_file") or "", grants)
        msg = get_response("revoke_stfu_user_done", mention=target_user.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
    else:
        msg = get_response("revoke_stfu_user_empty")
        sent = await message.reply_text(msg)
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_save_grants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data["target_group"]
    if chat.id != target_group:
        sent = await message.reply_text(get_response("wrong_chat_short", chat_id=chat.id), parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if not _has_moderation_rights(member):
        msg = get_response("save_grants_mod_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    grants = context.bot_data.get("stfu_grants") or {}
    path = context.bot_data.get("state_file") or ""
    _save_stfu_grants(path, grants)
    msg = get_response("save_grants_done", count=len(grants))
    sent = await message.reply_text(msg)
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_stfu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data["target_group"]
    if chat.id != target_group:
        sent = await message.reply_text(get_response("wrong_chat_stfu", chat_id=chat.id), parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    logger.info("cmd_stfu in target group chat_id=%s", chat.id)
    _schedule_notification_delete(context, chat.id, message.message_id)
    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    now = time.time()
    is_mod = _has_moderation_rights(member)
    is_delegate = False
    if not is_mod:
        grants = context.bot_data.get("stfu_grants") or {}
        grant = grants.get((chat.id, sender.id))
        if not grant or grant.get("expires_at", 0) < now:
            msg = get_response("not_admin_mute", mention=sender.mention_html())
            sent = await message.reply_text(msg, parse_mode="HTML")
            _schedule_notification_delete(context, chat.id, sent.message_id)
            return
        is_delegate = True
    chat_type = getattr(chat, "type", None) or getattr(chat, "_type", None)
    if str(chat_type).lower() == "group":
        msg = get_response("mute_basic_group")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    users_to_mute = await _get_target_users_from_message(message, context)
    if not users_to_mute:
        msg = get_response("no_target_mute")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    logger.info("cmd_stfu: targets user_ids=%s", [int(u.id) for u in users_to_mute])
    duration_seconds = extract_duration_from_message(message, None)
    if is_delegate:
        if duration_seconds is None:
            duration_seconds = DELEGATE_STFU_DEFAULT_SECONDS
        duration_seconds = min(duration_seconds, DELEGATE_STFU_MAX_SECONDS)
    else:
        if duration_seconds is None:
            duration_seconds = ADMIN_STFU_DEFAULT_SECONDS
        duration_seconds = min(duration_seconds, ADMIN_STFU_MAX_SECONDS)
    if duration_seconds <= MAX_TEMP_RESTRICT_SECONDS:
        effective_seconds = max(duration_seconds, TELEGRAM_MIN_RESTRICT_SECONDS)
        until_ts = int((update.message.date + timedelta(seconds=effective_seconds)).timestamp())
        use_until = True
    else:
        until_ts = None
        use_until = False
    muted: list[User] = []
    failed: list[tuple[User, str]] = []
    skipped_immune: list[tuple[User, int]] = []
    immunity = context.bot_data.get("stfuproof_immunity") or {}
    chat_id_int = int(chat.id)
    logger.info("stfuproof: immunity dict has %s entries, keys=%s", len(immunity), list(immunity.keys()))
    for user in users_to_mute:
        uid = int(user.id)
        imm_key = (chat_id_int, uid)
        imm = immunity.get(imm_key)
        if imm is None and (chat.id, user.id) != imm_key:
            imm = immunity.get((chat.id, user.id))
        if imm is not None:
            try:
                imm_expires_at = float(imm.get("expires_at", 0))
            except (TypeError, ValueError):
                imm_expires_at = 0
            if imm_expires_at > now:
                secs_left = int(imm_expires_at - now)
                skipped_immune.append((user, secs_left))
                logger.info("stfuproof: skipping mute for user_id=%s (immune for %ss)", uid, secs_left)
                continue
            immunity.pop(imm_key, None)
            if (chat.id, user.id) != imm_key:
                immunity.pop((chat.id, user.id), None)
        else:
            logger.info("stfuproof: user_id=%s has no immunity (or expired), will mute", uid)
        try:
            if use_until:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=user.id,
                    permissions=_mute_permissions(),
                    until_date=until_ts,
                    use_independent_chat_permissions=True,
                )
            else:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=user.id,
                    permissions=_mute_permissions(),
                    use_independent_chat_permissions=True,
                )
            logger.info("restrict_chat_member ok chat_id=%s user_id=%s", chat.id, user.id)
            muted.append(user)
        except BadRequest as e:
            logger.warning("restrict_chat_member 400: %s (chat_id=%s user_id=%s)", e.message, chat.id, user.id)
            failed.append((user, e.message or "BadRequest"))
        except Exception as e:
            logger.exception("restrict_chat_member failed for user_id=%s: %s", user.id, e)
            failed.append((user, str(e)))
    if not muted:
        if skipped_immune and not failed:
            if len(skipped_immune) == 1:
                u, secs = skipped_immune[0]
                msg = get_response("stfu_immune_single", mention=u.mention_html(), time_left=_format_time_left(secs))
                sent = await message.reply_text(msg, parse_mode="HTML")
            else:
                skipped_list = ", ".join(
                    f"{u.mention_html()} (~{_format_time_left(secs)} — holy cow shit shielded pajeet)"
                    for u, secs in skipped_immune
                )
                msg = get_response("stfu_immune_multi", skipped_list=skipped_list)
                sent = await message.reply_text(msg, parse_mode="HTML")
        else:
            msg = get_response("mute_fail")
            sent = await message.reply_text(msg)
    elif len(muted) == 1 and not failed:
        msg = get_response("mute_success", mention=muted[0].mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
    else:
        parts = ["Muted: " + ", ".join(u.mention_html() for u in muted)]
        if skipped_immune:
            parts.append(
                "Skipped (stfuproof, not even admins can override): "
                + ", ".join(f"{u.mention_html()} (~{_format_time_left(secs)})" for u, secs in skipped_immune)
            )
        if failed:
            parts.append("Failed: " + ", ".join(u.mention_html() for u, _ in failed))
        sent = await message.reply_text(" ".join(parts), parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
