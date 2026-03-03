"""Handler for /tengriguideme and its callback."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from responses import (
    GROUP_HEARMY_PRAYERS_REPLIES,
    TENGRIGUIDEME_PANEL_TEXT,
    get_response,
)
from utils import _schedule_notification_delete

import random


def _build_tengri_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Who has /stfu?", callback_data="cmd:privileged_peasants"),
            InlineKeyboardButton("Armor", callback_data="cmd:holycowshithindupajeetarmor"),
        ],
        [
            InlineKeyboardButton("How to /stfu", callback_data="help:stfu"),
            InlineKeyboardButton("How to /unstfu", callback_data="help:unstfu"),
        ],
        [
            InlineKeyboardButton("How to /fool", callback_data="help:fool"),
            InlineKeyboardButton("How to /unfool", callback_data="help:unfool"),
        ],
        [
            InlineKeyboardButton("How to /doxx", callback_data="help:doxx"),
            InlineKeyboardButton("How to /doxxed", callback_data="help:doxxed"),
        ],
        [
            InlineKeyboardButton("How to /revoke_doxx", callback_data="help:revoke_doxx"),
        ],
    ]
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
    reply_markup = _build_tengri_keyboard()
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
    reply_markup = _build_tengri_keyboard()
    panel_text = random.choice(TENGRIGUIDEME_PANEL_TEXT)
    await message.reply_text(panel_text, reply_markup=reply_markup)


async def _handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
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
        reply_markup = _build_tengri_keyboard()
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
    else:
        return
    back_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Back to Tengri menu", callback_data="help:back")]]
    )
    sent = await query.message.reply_text(text, parse_mode="HTML", reply_markup=back_markup)
    _schedule_notification_delete(context, chat.id, sent.message_id)
