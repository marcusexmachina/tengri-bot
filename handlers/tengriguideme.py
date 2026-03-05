"""Handler for /tengriguideme and its callback."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from handlers.acquire_stfu import _get_acquire_button_label
from responses import (
    GROUP_HEARMY_PRAYERS_REPLIES,
    TENGRIGUIDEME_PANEL_TEXT,
    get_response,
)
from utils import _schedule_notification_delete

import random


def _build_tengri_keyboard(context: ContextTypes.DEFAULT_TYPE | None = None, user_id: int | None = None) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Who has /stfu?", callback_data="cmd:privileged_peasants"),
            InlineKeyboardButton("Armor", callback_data="cmd:holycowshithindupajeetarmor"),
        ],
        [
            InlineKeyboardButton("STFU", callback_data="help:stfu"),
            InlineKeyboardButton("UNSTFU", callback_data="help:unstfu"),
        ],
        [
            InlineKeyboardButton("FOOL", callback_data="help:fool"),
            InlineKeyboardButton("UNFOOL", callback_data="help:unfool"),
        ],
        [
            InlineKeyboardButton("DOXX", callback_data="help:doxx"),
            InlineKeyboardButton("DOXXED", callback_data="help:doxxed"),
        ],
        [
            InlineKeyboardButton("REVOKE DOXX", callback_data="help:revoke_doxx"),
        ],
        [
            InlineKeyboardButton("BASED", callback_data="help:based"),
            InlineKeyboardButton("CUNT", callback_data="help:cunt"),
        ],
        [
            InlineKeyboardButton("HOW BASED ARE YOU?", callback_data="help:howbasedami"),
            InlineKeyboardButton("EDICT OF TENGRI", callback_data="help:edictoftengri"),
        ],
        [
            InlineKeyboardButton("REDEEM CODE SAAR", callback_data="help:redeem"),
        ],
    ]
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
    reply_markup = _build_tengri_keyboard(context, sender.id)
    deeplink_markup = _build_deeplink_markup(context)
    panel_text = random.choice(TENGRIGUIDEME_PANEL_TEXT)
    try:
        await context.bot.send_message(sender.id, panel_text, reply_markup=reply_markup)
    except (BadRequest, Forbidden):
        msg = get_response("tengriguideme_dm_fail")
        sent = await message.reply_text(msg, reply_markup=deeplink_markup)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    group_msg = random.choice(GROUP_HEARMY_PRAYERS_REPLIES)
    sent = await message.reply_text(group_msg, reply_markup=deeplink_markup)
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return
    # Only handle /start in private chat.
    if chat.type != "private":
        return
    args = context.args or []
    # For /start tengriguideme or plain /start, show the Tengri menu panel.
    if args and args[0] != "tengriguideme":
        return
    user = update.effective_user
    reply_markup = _build_tengri_keyboard(context, user.id if user else None)
    panel_text = random.choice(TENGRIGUIDEME_PANEL_TEXT)
    await message.reply_text(panel_text, reply_markup=reply_markup)


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
            msg = get_response("acquire_stfu_blocked_low_rep")
            await query.message.reply_text(msg)
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
        msg = get_response("tengriguideme_cmd_privileged")
        sent = await query.message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if query.data == "cmd:holycowshithindupajeetarmor":
        msg = get_response("tengriguideme_cmd_armor")
        sent = await query.message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    try:
        await query.message.delete()
    except BadRequest:
        pass
    if query.data == "help:back":
        user = update.effective_user
        reply_markup = _build_tengri_keyboard(context, user.id if user else None)
        panel_text = random.choice(TENGRIGUIDEME_PANEL_TEXT)
        await query.message.reply_text(panel_text, reply_markup=reply_markup)
        return
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
    else:
        return
    back_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Back to Tengri menu", callback_data="help:back")]]
    )
    sent = await query.message.reply_text(text, parse_mode="HTML", reply_markup=back_markup)
    _schedule_notification_delete(context, chat.id, sent.message_id)
