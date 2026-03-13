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
    MAX_TEMP_RESTRICT_SECONDS,
    TELEGRAM_MIN_RESTRICT_SECONDS,
)
from grants import _save_stfu_grants
from permissions import (
    _demote_zero_perms_admin,
    _full_permissions,
    _has_moderation_rights,
    _mute_permissions,
)
from reputation_thresholds import (
    delegate_stfu_cast_seconds,
    delegate_stfu_max_seconds,
    get_rep,
    has_stfu_immunity,
)
from handlers.citizenship import require_citizenship
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
        grants = context.bot_data.setdefault("stfu_grants", {})
        grant = grants.get((chat.id, sender.id))
        exp = grant.get("expires_at", 0) if grant else 0
        if not grant or (exp > 0 and exp < now):
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
        restrictable = await _demote_zero_perms_admin(context.bot, chat.id, user.id)
        if not restrictable:
            failed.append(user)
            continue
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
    grants = context.bot_data.get("stfu_grants")
    if grants is None:
        grants = {}
        context.bot_data["stfu_grants"] = grants
    grants[(chat.id, target_user.id)] = {"granted_by": sender.id, "expires_at": 0}
    _save_stfu_grants(context.bot_data.get("state_file") or "", grants)
    from commands_menu import update_dm_commands_for_user, update_user_commands, user_grants

    _, has_doxx = user_grants(context.bot_data, chat.id, target_user.id)
    await update_user_commands(context.bot, chat.id, target_user.id, has_stfu_grant=True, has_doxx_grant=has_doxx)
    await update_dm_commands_for_user(context.bot, context.bot_data, chat.id, target_user.id)
    msg = get_response("grant_stfu_done_permanent", target=target_user.mention_html(), sender=sender.mention_html())
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
        grants = context.bot_data.setdefault("stfu_grants", {})
        keys_to_remove = [k for k in grants if k[0] == chat.id]
        for k in keys_to_remove:
            del grants[k]
        _save_stfu_grants(context.bot_data.get("state_file") or "", grants)
        from commands_menu import update_dm_commands_for_user, update_user_commands, user_grants

        for _cid, uid in keys_to_remove:
            _, has_doxx = user_grants(context.bot_data, chat.id, uid)
            await update_user_commands(context.bot, chat.id, uid, has_stfu_grant=False, has_doxx_grant=has_doxx)
            await update_dm_commands_for_user(context.bot, context.bot_data, chat.id, uid)
        msg = (
            get_response("revoke_stfu_all_done", count=len(keys_to_remove))
            if keys_to_remove
            else get_response("revoke_stfu_all_empty")
        )
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("revoke_stfu_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    grants = context.bot_data.setdefault("stfu_grants", {})
    key = (chat.id, target_user.id)
    if key in grants:
        del grants[key]
        _save_stfu_grants(context.bot_data.get("state_file") or "", grants)
        from commands_menu import update_dm_commands_for_user, update_user_commands, user_grants

        _, has_doxx = user_grants(context.bot_data, chat.id, target_user.id)
        await update_user_commands(context.bot, chat.id, target_user.id, has_stfu_grant=False, has_doxx_grant=has_doxx)
        await update_dm_commands_for_user(context.bot, context.bot_data, chat.id, target_user.id)
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
    if not await require_citizenship(update, context):
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
    grants = context.bot_data.setdefault("stfu_grants", {})
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
    # 30s per-sender cooldown on /stfu to prevent spam.
    now = time.time()
    cooldown_map = context.bot_data.setdefault("stfu_cooldown", {})
    caster_key = (int(chat.id), int(sender.id))
    last_ts = float(cooldown_map.get(caster_key, 0) or 0)
    remaining_cd = 30 - (now - last_ts)
    if remaining_cd > 0:
        msg = get_response("stfu_cooldown", seconds=int(remaining_cd) + 1)
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    cooldown_map[caster_key] = now
    _schedule_notification_delete(context, chat.id, message.message_id)
    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    is_mod = _has_moderation_rights(member)
    is_delegate = False
    logger.info("cmd_stfu: sender_id=%s status=%s is_mod=%s", sender.id, getattr(member, "status", "?"), is_mod)
    if not is_mod:
        grants = context.bot_data.setdefault("stfu_grants", {})
        lookup_key = (int(chat.id), int(sender.id))
        grant = grants.get(lookup_key)
        grant_keys = list(grants.keys())
        exp = 0.0
        if grant is not None:
            try:
                exp = float(grant.get("expires_at", 0) or 0)
            except (TypeError, ValueError):
                exp = 0.0
        logger.info(
            "cmd_stfu: grant lookup key=%s (types: chat.id=%s sender.id=%s), found=%s, expires_at=%s, all_keys=%s",
            lookup_key,
            type(chat.id).__name__,
            type(sender.id).__name__,
            grant is not None,
            exp if grant is not None else None,
            grant_keys,
        )
        # Permanent grants use expires_at == 0 (never expires). Timed grants expire when exp < now.
        if not grant or (exp > 0 and exp < now):
            logger.info("cmd_stfu: sender has no mod rights and no valid grant -> not_admin_mute")
            from commands_menu import update_dm_commands_for_user, update_user_commands, user_grants

            _, has_doxx = user_grants(context.bot_data, chat.id, sender.id)
            await update_user_commands(context.bot, chat.id, sender.id, has_stfu_grant=False, has_doxx_grant=has_doxx)
            await update_dm_commands_for_user(context.bot, context.bot_data, chat.id, sender.id)
            msg = get_response("not_admin_mute", mention=sender.mention_html())
            sent = await message.reply_text(msg, parse_mode="HTML")
            _schedule_notification_delete(context, chat.id, sent.message_id)
            return
        is_delegate = True
    chat_type = getattr(chat, "type", None) or getattr(chat, "_type", None)
    logger.info("cmd_stfu: chat_type=%s", chat_type)
    if str(chat_type).lower() == "group":
        logger.info("cmd_stfu: basic group -> mute_basic_group")
        msg = get_response("mute_basic_group")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    users_to_mute = await _get_target_users_from_message(message, context)
    logger.info("cmd_stfu: resolved targets count=%s", len(users_to_mute))
    if not users_to_mute:
        msg = get_response("no_target_mute")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    logger.info("cmd_stfu: targets user_ids=%s", [int(u.id) for u in users_to_mute])
    if is_delegate:
        rep = get_rep(context, chat.id, sender.id)
        max_secs = delegate_stfu_max_seconds(rep)
        if max_secs is not None:
            duration_seconds = extract_duration_from_message(message, None)
            if duration_seconds is None:
                duration_seconds = delegate_stfu_cast_seconds(rep)
            duration_seconds = min(duration_seconds, max_secs)
        else:
            duration_seconds = delegate_stfu_cast_seconds(rep)
    else:
        duration_seconds = extract_duration_from_message(message, None)
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
        target_rep = get_rep(context, chat.id, user.id)
        if has_stfu_immunity(target_rep):
            skipped_immune.append((user, -1))
            logger.info("stfu: skipping user_id=%s (rep 250+ immunity)", uid)
            continue
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
        restrictable = await _demote_zero_perms_admin(context.bot, chat.id, user.id)
        if not restrictable:
            failed.append((user, "Cannot restrict (creator or admin with rights)"))
            continue
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
                if secs < 0:
                    msg = get_response("stfu_immune_rep200", mention=u.mention_html())
                else:
                    msg = get_response(
                        "stfu_immune_single", mention=u.mention_html(), time_left=_format_time_left(secs)
                    )
                sent = await message.reply_text(msg, parse_mode="HTML")
            else:

                def _skip_desc(u, secs):
                    if secs < 0:
                        return f"{u.mention_html()} (rep 250+ immunity)"
                    return f"{u.mention_html()} (~{_format_time_left(secs)} — holy cow shit shielded pajeet)"

                skipped_list = ", ".join(_skip_desc(u, secs) for u, secs in skipped_immune)
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
            skip_parts = []
            for u, secs in skipped_immune:
                if secs < 0:
                    skip_parts.append(f"{u.mention_html()} (rep 250+ immunity)")
                else:
                    skip_parts.append(f"{u.mention_html()} (~{_format_time_left(secs)})")
            parts.append("Skipped: " + ", ".join(skip_parts))
        if failed:
            parts.append("Failed: " + ", ".join(u.mention_html() for u, _ in failed))
        sent = await message.reply_text(" ".join(parts), parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
