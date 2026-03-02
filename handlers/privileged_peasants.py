"""Handler for /privileged_peasants."""
import html
import logging
import time

from telegram import Update
from telegram.ext import ContextTypes

from config import STFU_MAX_TARGETS
from responses import get_response
from utils import _format_time_left, _schedule_notification_delete

logger = logging.getLogger(__name__)


async def cmd_privileged_peasants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
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
    grants = context.bot_data.get("stfu_grants") or {}
    now = time.time()
    chat_id = int(chat.id)
    active = [
        (k, g) for k, g in grants.items()
        if int(k[0]) == chat_id and float(g.get("expires_at", 0)) > now
    ]
    if not active:
        keys_in_chat = [k for k in grants if int(k[0]) == chat_id]
        logger.info(
            "privileged_peasants: total_grants=%s chat_id=%s keys_in_this_chat=%s (all expired or wrong chat?)",
            len(grants), chat_id, len(keys_in_chat),
        )
        msg = get_response("privileged_peasants_empty")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    header = get_response("privileged_peasants_header")
    lines = [header, ""]
    for (_cid, user_id), g in active[:STFU_MAX_TARGETS]:
        try:
            member = await context.bot.get_chat_member(chat.id, user_id)
            u = member.user
            display = f"@{u.username}" if u.username else (u.first_name or str(u.id))
            display = html.escape(display)
        except Exception as e:
            logger.warning("get_chat_member failed for list_grants user_id=%s: %s", user_id, e)
            display = html.escape(str(user_id))
        expires_at = float(g.get("expires_at", 0))
        time_left = _format_time_left(expires_at - now)
        link = f'<a href="tg://user?id={user_id}">{display}</a>'
        lines.append(f"• {link}  —  enabled  —  {time_left}")
    if len(active) > STFU_MAX_TARGETS:
        lines.append(f"… and {len(active) - STFU_MAX_TARGETS} more")
    text = "\n".join(lines)
    sent = await message.reply_text(text, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
