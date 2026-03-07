"""Handlers for acquire/replenish STFU flow (password-based)."""

import asyncio
import json
import logging
import random
import string
import time
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from grants import _save_stfu_grants
from reputation_thresholds import acquire_session_seconds, can_acquire_stfu, get_rep
from state import _save_acquire_pending, _save_acquired_stfu
from utils import (
    _schedule_notification_delete,
    ask_tengri_button,
    delete_last_dm_message,
    schedule_replace_with_minimal,
    set_last_dm_message,
)

logger = logging.getLogger(__name__)

ACQUIRE_PASSWORD_MIN_LENGTH = 6
ACQUIRE_PASSWORD_MAX_LENGTH = 13
ACQUIRE_PENDING_EXPIRE_SECONDS = 600

# Toggle for STFU password generation mode.
# If True: incremental, one-character-at-a-time, hidden-length (6–13).
# If False: generate a full random string when clicking Generate.
STFU_PASSWORD_INCREMENTAL = True


def _load_password_mode_from_config() -> None:
    """Load STFU password mode from config.json, defaulting to incremental."""
    global STFU_PASSWORD_INCREMENTAL
    try:
        # config.json is expected at the project root.
        root = Path(__file__).resolve().parent.parent
        config_path = root / "config.json"
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        val = data.get("stfu_password_incremental")
        if isinstance(val, bool):
            STFU_PASSWORD_INCREMENTAL = val
        else:
            STFU_PASSWORD_INCREMENTAL = True
    except Exception as e:
        # On any error (missing file, parse error, etc.), keep safe default.
        logger.warning("Failed to load STFU password mode from config.json: %s", e)
        STFU_PASSWORD_INCREMENTAL = True

    logger.info("STFU password incremental mode: %s", STFU_PASSWORD_INCREMENTAL)


_load_password_mode_from_config()


def _get_acquire_button_label(context, user_id: int) -> tuple[str, str]:
    """Return (button_label, callback_data). If active session, return time left."""
    target_group = context.bot_data.get("target_group")
    if not target_group:
        return "Acquire /stfu", "acquire:start"
    grants = context.bot_data.setdefault("stfu_grants", {})
    grant = grants.get((target_group, user_id))
    if grant:
        exp = grant.get("expires_at", 0)
        granted_by = grant.get("granted_by")
        if exp == 0 and granted_by is not None and granted_by != user_id:
            return "You already have permanent STFU privileges", "acquire:timeleft"
        if exp == 0:
            return "Time left: permanent", "acquire:timeleft"
        import time

        now = time.time()
        if exp > now:
            from utils import _format_time_left

            left = _format_time_left(exp - now)
            return f"Time left: {left}", "acquire:timeleft"
    rep = get_rep(context, target_group, user_id)
    if not can_acquire_stfu(rep):
        return "Acquire /stfu (reputation too low)", "acquire:blocked"
    acquired = context.bot_data.get("acquired_stfu") or set()
    if (target_group, user_id) in acquired:
        return "Replenish /stfu", "acquire:start"
    return "Acquire /stfu", "acquire:start"


async def _handle_acquire_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("acquire:"):
        return
    await query.answer()
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or chat.type != "private":
        return
    target_group = context.bot_data.get("target_group")
    if not target_group:
        return
    rep = get_rep(context, target_group, user.id)
    if not can_acquire_stfu(rep):
        from responses import get_response

        await delete_last_dm_message(context, user.id)
        try:
            await query.message.delete()
        except Exception:
            pass
        msg = get_response("acquire_stfu_blocked_low_rep")
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, msg, reply_markup=markup)
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        return
    await delete_last_dm_message(context, user.id)
    try:
        await query.message.delete()
    except Exception:
        pass
    pending = context.bot_data.setdefault("acquire_pending", {})
    pending[user.id] = {
        "password": "",
        "target_group": target_group,
        "created_at": time.time(),
        "last_char_message_id": None,
        "target_length": random.randint(ACQUIRE_PASSWORD_MIN_LENGTH, ACQUIRE_PASSWORD_MAX_LENGTH),
        "completed": False,
    }
    _save_acquire_pending(pending)
    from responses import get_response

    msg = get_response("acquire_stfu_password_intro")
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Generate", callback_data="acquire:gen")],
            [ask_tengri_button()],
        ]
    )
    sent = await context.bot.send_message(chat.id, msg, reply_markup=markup, parse_mode="HTML")
    set_last_dm_message(context, user.id, chat.id, sent.message_id)
    schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)


async def _handle_acquire_generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or query.data != "acquire:gen":
        return
    await query.answer()
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or chat.type != "private":
        return
    pending = context.bot_data.get("acquire_pending") or {}
    entry = pending.get(user.id)
    if not entry:
        from responses import get_response

        await delete_last_dm_message(context, user.id)
        try:
            await query.message.delete()
        except Exception:
            pass
        msg = get_response("acquire_stfu_expired")
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, msg, reply_markup=markup)
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        return
    now = time.time()
    if now - entry["created_at"] > ACQUIRE_PENDING_EXPIRE_SECONDS:
        del pending[user.id]
        from responses import get_response

        await delete_last_dm_message(context, user.id)
        try:
            await query.message.delete()
        except Exception:
            pass
        msg = get_response("acquire_stfu_expired")
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, msg, reply_markup=markup)
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        return
    # If this session is already completed, nudge user to redeem instead of generating more.
    if entry.get("completed"):
        from responses import get_response

        await delete_last_dm_message(context, user.id)
        try:
            await query.message.delete()
        except Exception:
            pass
        msg = get_response("acquire_stfu_redeem_instruction")
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, msg, parse_mode="HTML", reply_markup=markup)
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        return
    await query.answer()
    from responses import get_response

    chars = string.ascii_letters + string.digits

    # Non-incremental mode: generate a full random password string at once.
    if not STFU_PASSWORD_INCREMENTAL:
        # If a password already exists for this session, just remind them to redeem.
        if entry.get("password"):
            await delete_last_dm_message(context, user.id)
            try:
                await query.message.delete()
            except Exception:
                pass
            msg = get_response("acquire_stfu_redeem_instruction")
            markup = InlineKeyboardMarkup([[ask_tengri_button()]])
            sent = await context.bot.send_message(chat.id, msg, parse_mode="HTML", reply_markup=markup)
            set_last_dm_message(context, user.id, chat.id, sent.message_id)
            schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
            return
        length = random.randint(ACQUIRE_PASSWORD_MIN_LENGTH, ACQUIRE_PASSWORD_MAX_LENGTH)
        password = "".join(random.choice(chars) for _ in range(length))
        entry["password"] = password
        entry["completed"] = True
        _save_acquire_pending(pending)
        await delete_last_dm_message(context, user.id)
        try:
            await query.message.delete()
        except Exception:
            pass
        msg_pwd = f"Your password: <code>{password}</code>"
        msg2 = get_response("acquire_stfu_redeem_instruction")
        combined = f"{msg_pwd}\n\n{msg2}"
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, combined, parse_mode="HTML", reply_markup=markup)
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        return

    # Incremental mode: one-character-at-a-time, hidden total length.
    last_msg_id = entry.get("last_char_message_id")
    if last_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=last_msg_id)
        except Exception:
            pass
    char = random.choice(chars)
    entry["password"] += char
    target_len = entry.get("target_length") or ACQUIRE_PASSWORD_MAX_LENGTH
    current_len = len(entry["password"])
    if current_len >= target_len:
        # Final character for this password; clamp and complete.
        if current_len > target_len:
            entry["password"] = entry["password"][:target_len]
            current_len = target_len
        msg = get_response("acquire_stfu_char", pos=current_len, char=char)
        sent = await query.message.reply_text(msg, parse_mode="HTML")
        entry["last_char_message_id"] = sent.message_id
        try:
            await asyncio.sleep(2)
            await context.bot.delete_message(chat_id=chat.id, message_id=sent.message_id)
        except Exception:
            pass
        await delete_last_dm_message(context, user.id)
        try:
            await query.message.delete()
        except Exception:
            pass
        msg1 = get_response("acquire_stfu_password_saved")
        msg2 = get_response("acquire_stfu_redeem_instruction")
        combined = f"{msg1}\n\n{msg2}"
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, combined, parse_mode="HTML", reply_markup=markup)
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        entry["completed"] = True
        _save_acquire_pending(pending)
        return
    msg = get_response("acquire_stfu_char", pos=current_len, char=char)
    sent = await query.message.reply_text(msg, parse_mode="HTML")
    entry["last_char_message_id"] = sent.message_id


async def _handle_acquire_timeleft(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or chat.type != "private":
        return
    target_group = context.bot_data.get("target_group")
    if not target_group:
        return
    grants = context.bot_data.setdefault("stfu_grants", {})
    grant = grants.get((target_group, user.id))
    if not grant:
        return
    exp = grant.get("expires_at", 0)
    granted_by = grant.get("granted_by")
    if exp == 0 and granted_by is not None and granted_by != user.id:
        from responses import get_response

        await delete_last_dm_message(context, user.id)
        try:
            await query.message.delete()
        except Exception:
            pass
        msg = get_response("acquire_permanent_admin")
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, msg, reply_markup=markup)
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        return
    if exp == 0:
        from responses import get_response

        await delete_last_dm_message(context, user.id)
        try:
            await query.message.delete()
        except Exception:
            pass
        msg = get_response("acquire_timeleft_permanent")
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, msg, reply_markup=markup)
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        return
    import time

    now = time.time()
    if exp <= now:
        return
    from responses import get_response
    from utils import _format_time_left

    await delete_last_dm_message(context, user.id)
    try:
        await query.message.delete()
    except Exception:
        pass
    left = _format_time_left(exp - now)
    msg = get_response("acquire_timeleft", time_left=left)
    markup = InlineKeyboardMarkup([[ask_tengri_button()]])
    sent = await context.bot.send_message(chat.id, msg, reply_markup=markup)
    set_last_dm_message(context, user.id, chat.id, sent.message_id)
    schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)


async def cmd_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user:
        return
    if chat.type != "private":
        from responses import get_response

        msg = get_response("redeem_usage")
        await message.reply_text(msg, parse_mode="HTML")
        logger.info("redeem: ignored in non-DM chat_id=%s user_id=%s", chat.id, user.id)
        return
    target_group = context.bot_data.get("target_group")
    if not target_group:
        return
    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        from responses import get_response

        msg = get_response("redeem_usage")
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    password = parts[1].strip()
    pending = context.bot_data.get("acquire_pending") or {}
    entry = pending.get(user.id)
    if not entry:
        logger.info("redeem: no pending entry user_id=%s", user.id)
        from responses import get_response

        msg = get_response("redeem_invalid")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if entry.get("password") != password:
        logger.info("redeem: password mismatch user_id=%s", user.id)
        from responses import get_response

        msg = get_response("redeem_invalid")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if entry.get("target_group") != target_group:
        logger.info("redeem: target_group mismatch user_id=%s", user.id)
        from responses import get_response

        msg = get_response("redeem_invalid")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    del pending[user.id]
    _save_acquire_pending(pending)
    rep = get_rep(context, target_group, user.id)
    if not can_acquire_stfu(rep):
        from responses import get_response

        msg = get_response("acquire_stfu_blocked_low_rep")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    duration_seconds = acquire_session_seconds(rep)
    if duration_seconds <= 0:
        from responses import get_response

        msg = get_response("acquire_stfu_blocked_low_rep")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    now = time.time()
    grants = context.bot_data.setdefault("stfu_grants", {})
    save_key = (int(target_group), int(user.id))
    grants[save_key] = {"granted_by": user.id, "expires_at": now + duration_seconds}
    state_file = context.bot_data.get("state_file") or ""
    _save_stfu_grants(state_file, grants)
    logger.info(
        "redeem: saved grant key=%s expires_at=%s state_file=%s grants_count=%s",
        save_key,
        now + duration_seconds,
        state_file or "(empty)",
        len(grants),
    )
    acquired = context.bot_data.get("acquired_stfu") or set()
    is_replenish = (target_group, user.id) in acquired
    acquired.add((target_group, user.id))
    context.bot_data["acquired_stfu"] = acquired
    _save_acquired_stfu(acquired)
    hours = round(duration_seconds / 3600, 1)
    from responses import get_response

    msg = get_response("redeem_success", mention=user.mention_html(), hours=hours)
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
    key = "acquire_stfu_group_replenish" if is_replenish else "acquire_stfu_group_notify"
    group_msg = get_response(key, mention=user.mention_html(), hours=hours)
    logger.info("redeem: success user_id=%s duration_h=%.1f", user.id, hours)
    try:
        await context.bot.send_message(target_group, group_msg, parse_mode="HTML")
    except Exception as e:
        logger.warning("Failed to notify group of acquire: %s", e)
    from commands_menu import update_dm_commands_for_user, update_user_commands, user_grants

    _, has_doxx = user_grants(context.bot_data, target_group, user.id)
    await update_user_commands(context.bot, target_group, user.id, has_stfu_grant=True, has_doxx_grant=has_doxx)
    await update_dm_commands_for_user(context.bot, context.bot_data, target_group, user.id)
