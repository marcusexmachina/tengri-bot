"""Handler for /tengriguideme and its callback."""
import logging
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from handlers.acquire_stfu import _get_acquire_button_label
from responses import (
    GROUP_HEARMY_PRAYERS_REPLIES,
    TENGRIGUIDEME_PANEL_TEXT,
    get_response,
)
from utils import (
    ASK_TENGRI_CALLBACK,
    _schedule_notification_delete,
    ask_tengri_button,
    delete_last_dm_message,
    schedule_replace_with_minimal,
    set_last_dm_message,
)

logger = logging.getLogger(__name__)


async def _get_tengri_menu_role(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Return (is_mod, is_real_admin, has_stfu_grant, has_doxx_grant) for menu visibility."""
    target_group = context.bot_data.get("target_group")
    if not target_group:
        return False, False, False, False
    from commands_menu import user_grants
    has_stfu, has_doxx = user_grants(context.bot_data, target_group, user_id)
    try:
        member = await context.bot.get_chat_member(target_group, user_id)
        from permissions import _has_moderation_rights, _is_real_admin
        return _has_moderation_rights(member), _is_real_admin(member), has_stfu, has_doxx
    except Exception:
        return False, False, has_stfu, has_doxx


def _build_tengri_keyboard(
    context: ContextTypes.DEFAULT_TYPE | None,
    user_id: int | None,
    is_mod: bool = False,
    is_real_admin: bool = False,
    has_stfu_grant: bool = False,
    has_doxx_grant: bool = False,
) -> InlineKeyboardMarkup:
    """Build menu keyboard; only show buttons the user can use."""
    # Only admins/mods get the full per-command keyboard; granted-but-non-admin get same 3-button menu
    is_privileged = is_mod or is_real_admin
    if not is_privileged:
        # Regular members: greeting + COMMANDS, TUTORIAL, Replenish STFU only
        keyboard = [
            [InlineKeyboardButton("COMMANDS", callback_data="help:commands")],
            [InlineKeyboardButton("TUTORIAL", callback_data="help:tutorial")],
        ]
        if context and user_id is not None:
            label, callback = _get_acquire_button_label(context, user_id)
            keyboard.append([InlineKeyboardButton(label, callback_data=callback)])
        return InlineKeyboardMarkup(keyboard)
    # Privileged: full per-command buttons
    keyboard = [
        [
            InlineKeyboardButton("Who has /stfu?", callback_data="cmd:privileged_peasants"),
            InlineKeyboardButton("Armor", callback_data="cmd:holycowshithindupajeetarmor"),
        ],
        [
            InlineKeyboardButton("BASED", callback_data="help:based"),
            InlineKeyboardButton("CUNT", callback_data="help:cunt"),
        ],
        [
            InlineKeyboardButton("HOW BASED ARE YOU?", callback_data="help:howbasedami"),
        ],
        [
            InlineKeyboardButton("FOOL", callback_data="help:fool"),
        ],
        [
            InlineKeyboardButton("REDEEM CODE SAAR", callback_data="help:redeem"),
        ],
    ]
    if is_mod or has_stfu_grant:
        keyboard.insert(2, [
            InlineKeyboardButton("STFU", callback_data="help:stfu"),
            InlineKeyboardButton("UNSTFU", callback_data="help:unstfu"),
        ])
    if is_real_admin:
        keyboard.append([InlineKeyboardButton("UNFOOL", callback_data="help:unfool")])
    if has_doxx_grant:
        keyboard.append([InlineKeyboardButton("DOXX", callback_data="help:doxx")])
    if is_real_admin:
        keyboard.append([
            InlineKeyboardButton("DOXXED", callback_data="help:doxxed"),
            InlineKeyboardButton("REVOKE DOXX", callback_data="help:revoke_doxx"),
        ])
    if is_real_admin:
        keyboard.append([InlineKeyboardButton("EDICT OF TENGRI", callback_data="help:edictoftengri")])
    if context and user_id is not None:
        label, callback = _get_acquire_button_label(context, user_id)
        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])
    return InlineKeyboardMarkup(keyboard)


def _build_deeplink_markup(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup | None:
    bot_username = context.bot.username
    if not bot_username:
        return None
    deeplink = f"https://t.me/{bot_username}?start=tengriguideme"
    keyboard = [[InlineKeyboardButton("Open Tengri menu in PM", url=deeplink)]]
    return InlineKeyboardMarkup(keyboard)


async def cmd_tengriguideme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    from commands_menu import update_dm_commands_for_user
    await update_dm_commands_for_user(context.bot, context.bot_data, target_group, sender.id)
    deeplink_markup = _build_deeplink_markup(context)
    try:
        ok = await _send_minimal_view(context.bot, sender.id, context, sender.id)
        if not ok:
            raise BadRequest("DM failed")
    except (BadRequest, Forbidden):
        msg = get_response("tengriguideme_dm_fail")
        await message.reply_text(msg, reply_markup=deeplink_markup, parse_mode="HTML")
        return
    group_msg = random.choice(GROUP_HEARMY_PRAYERS_REPLIES)
    await message.reply_text(group_msg, reply_markup=deeplink_markup)


# Telegram rejects empty/whitespace-only text. Use actual visible text.
_MINIMAL_VIEW_TEXT = "Do you wish to speak to the Eternal Skyfather?"


async def _send_minimal_view(bot, chat_id: int, context: ContextTypes.DEFAULT_TYPE, user_id: int | None) -> bool:
    """Send only the 'Ask Tengri for Guidance' button. Returns True on success."""
    try:
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        if user_id is not None:
            await delete_last_dm_message(context, user_id)
        sent = await bot.send_message(chat_id, _MINIMAL_VIEW_TEXT, reply_markup=markup)
        if user_id is not None:
            set_last_dm_message(context, user_id, chat_id, sent.message_id)
        return True
    except Exception as e:
        logger.warning("_send_minimal_view failed chat_id=%s user_id=%s: %s", chat_id, user_id, e)
        return False


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return
    if chat.type != "private":
        return
    args = context.args or []
    user = update.effective_user
    try:
        if user:
            from commands_menu import update_dm_commands_for_user
            target_group = context.bot_data.get("target_group")
            if target_group:
                await update_dm_commands_for_user(context.bot, context.bot_data, target_group, user.id)
    except Exception:
        pass
    started = context.bot_data.get("dm_started_users") or set()
    user_id = user.id if user else 0
    if args and args[0] == "reset" and user_id:
        started = started - {user_id}
        context.bot_data["dm_started_users"] = started
        from state import _save_dm_started_users
        _save_dm_started_users(started)
    if user_id and user_id not in started:
        # First-time (or DM was deleted): show full menu as default
        if user_id:
            await delete_last_dm_message(context, user_id)
        try:
            role = await _get_tengri_menu_role(context, user_id)
            reply_markup = _build_tengri_keyboard(
                context, user_id,
                is_mod=role[0], is_real_admin=role[1], has_stfu_grant=role[2], has_doxx_grant=role[3],
            )
            panel_text = random.choice(TENGRIGUIDEME_PANEL_TEXT)
            sent = await context.bot.send_message(chat.id, panel_text, reply_markup=reply_markup)
            if user_id:
                set_last_dm_message(context, user_id, chat.id, sent.message_id)
            schedule_replace_with_minimal(context, chat.id, sent.message_id, user_id)
            from state import _save_dm_started_users
            started = started | {user_id}
            context.bot_data["dm_started_users"] = started
            _save_dm_started_users(started)
        except (BadRequest, Forbidden) as e:
            logger.warning("cmd_start DM send failed user_id=%s chat_id=%s: %s", user_id, chat.id, e)
            ok = await _send_minimal_view(context.bot, chat.id, context, user_id)
            if not ok:
                logger.warning("cmd_start fallback _send_minimal_view also failed user_id=%s", user_id)
    else:
        # Returning user: show minimal view (Ask Tengri for Guidance only)
        ok = await _send_minimal_view(context.bot, chat.id, context, user_id if user_id else None)
        if not ok:
            logger.warning("cmd_start _send_minimal_view failed user_id=%s chat_id=%s", user_id, chat.id)


async def _handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    if query.data.startswith("acquire:"):
        from handlers.acquire_stfu import _handle_acquire_start, _handle_acquire_generate, _handle_acquire_timeleft
        if query.data == "acquire:gen":
            await _handle_acquire_generate(update, context)
        elif query.data == "acquire:timeleft":
            await _handle_acquire_timeleft(update, context)
        elif query.data == "acquire:blocked":
            await query.answer()
            user = update.effective_user
            chat = update.effective_chat
            if user and chat and chat.type == "private":
                await delete_last_dm_message(context, user.id)
                try:
                    await query.message.delete()
                except BadRequest:
                    pass
                msg = get_response("acquire_stfu_blocked_low_rep")
                markup = InlineKeyboardMarkup([[ask_tengri_button()]])
                sent = await context.bot.send_message(chat.id, msg, reply_markup=markup)
                set_last_dm_message(context, user.id, chat.id, sent.message_id)
                schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        else:
            await _handle_acquire_start(update, context)
        return
    await query.answer()
    chat = update.effective_chat
    if not chat:
        return
    if chat.type != "private":
        return
    if query.data == "cmd:privileged_peasants":
        user = update.effective_user
        await delete_last_dm_message(context, user.id if user else 0)
        try:
            await query.message.delete()
        except BadRequest:
            pass
        msg = get_response("tengriguideme_cmd_privileged")
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, msg, parse_mode="HTML", reply_markup=markup)
        if user:
            set_last_dm_message(context, user.id, chat.id, sent.message_id)
            schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        return
    if query.data == "cmd:holycowshithindupajeetarmor":
        user = update.effective_user
        await delete_last_dm_message(context, user.id if user else 0)
        try:
            await query.message.delete()
        except BadRequest:
            pass
        msg = get_response("tengriguideme_cmd_armor")
        markup = InlineKeyboardMarkup([[ask_tengri_button()]])
        sent = await context.bot.send_message(chat.id, msg, parse_mode="HTML", reply_markup=markup)
        if user:
            set_last_dm_message(context, user.id, chat.id, sent.message_id)
            schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        return
    if query.data == ASK_TENGRI_CALLBACK or query.data == "help:back":
        user = update.effective_user
        await delete_last_dm_message(context, user.id if user else 0)
        try:
            await query.message.delete()
        except BadRequest:
            pass
        role = await _get_tengri_menu_role(context, user.id) if user else (False, False, False, False)
        reply_markup = _build_tengri_keyboard(
            context, user.id if user else None,
            is_mod=role[0], is_real_admin=role[1], has_stfu_grant=role[2], has_doxx_grant=role[3],
        )
        panel_text = random.choice(TENGRIGUIDEME_PANEL_TEXT)
        sent = await context.bot.send_message(chat.id, panel_text, reply_markup=reply_markup)
        if user:
            set_last_dm_message(context, user.id, chat.id, sent.message_id)
            schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
        return
    try:
        await query.message.delete()
    except BadRequest:
        pass
    if query.data == "help:stfu":
        text = get_response("tengriguideme_help_stfu")
    elif query.data == "help:unstfu":
        text = get_response("tengriguideme_help_unstfu")
    elif query.data == "help:fool":
        text = get_response("tengriguideme_help_fool")
    elif query.data == "help:unfool":
        text = get_response("tengriguideme_help_unfool")
    elif query.data == "help:doxx":
        text = get_response("tengriguideme_help_doxx")
    elif query.data == "help:doxxed":
        text = get_response("tengriguideme_help_doxxed")
    elif query.data == "help:revoke_doxx":
        text = get_response("tengriguideme_help_revoke_doxx")
    elif query.data == "help:based":
        text = get_response("tengriguideme_help_based")
    elif query.data == "help:cunt":
        text = get_response("tengriguideme_help_cunt")
    elif query.data == "help:howbasedami":
        text = get_response("tengriguideme_help_howbasedami")
    elif query.data == "help:edictoftengri":
        text = get_response("tengriguideme_help_edictoftengri")
    elif query.data == "help:redeem":
        text = get_response("tengriguideme_help_redeem")
    elif query.data == "help:commands":
        user = update.effective_user
        role = await _get_tengri_menu_role(context, user.id) if user else (False, False, False, False)
        from commands_menu import _ADMIN, _granted_commands
        if role[0]:
            commands = _ADMIN
        else:
            commands = _granted_commands(role[2], role[3])
        lines = [f"• /{c.command} — {c.description}" for c in commands]
        text = "<b>Commands you can use</b>\n\n" + "\n".join(lines)
    elif query.data == "help:tutorial":
        text = get_response("tengriguideme_tutorial")
    else:
        return
    user = update.effective_user
    await delete_last_dm_message(context, user.id if user else 0)
    markup = InlineKeyboardMarkup([[ask_tengri_button()]])
    sent = await context.bot.send_message(chat.id, text, parse_mode="HTML", reply_markup=markup)
    if user:
        set_last_dm_message(context, user.id, chat.id, sent.message_id)
        schedule_replace_with_minimal(context, chat.id, sent.message_id, user.id)
