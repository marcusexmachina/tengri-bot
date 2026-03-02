"""Handler for /tengriguideme and its callback."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from responses import GROUP_HEARMY_PRAYERS_REPLIES, get_response
from utils import _schedule_notification_delete

import random


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
    keyboard = [
        [
            InlineKeyboardButton("Who has /stfu?", callback_data="cmd:privileged_peasants"),
            InlineKeyboardButton("Armor", callback_data="cmd:holycowshithindupajeetarmor"),
        ],
        [
            InlineKeyboardButton("How to /stfu", callback_data="help:stfu"),
            InlineKeyboardButton("How to /unstfu", callback_data="help:unstfu"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    panel_text = get_response("tengriguideme_panel_text")
    try:
        await context.bot.send_message(sender.id, panel_text, reply_markup=reply_markup)
    except (BadRequest, Forbidden):
        msg = get_response("tengriguideme_dm_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    msg = random.choice(GROUP_HEARMY_PRAYERS_REPLIES)
    sent = await message.reply_text(msg)
    _schedule_notification_delete(context, chat.id, sent.message_id)


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
    if query.data == "help:stfu":
        text = get_response("tengriguideme_help_stfu")
    elif query.data == "help:unstfu":
        text = get_response("tengriguideme_help_unstfu")
    else:
        return
    sent = await query.message.reply_text(text, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
