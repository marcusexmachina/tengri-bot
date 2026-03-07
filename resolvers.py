"""User resolution from reply, @mention, username cache."""

from telegram import MessageEntity, User
from telegram.ext import ContextTypes

from config import STFU_MAX_TARGETS


def _update_username_cache(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user: User | None) -> None:
    if not user or not user.username:
        return
    cache = context.bot_data.get("username_cache")
    if cache is None:
        cache = {}
        context.bot_data["username_cache"] = cache
    cache[(chat_id, user.username.lower())] = user.id


async def _get_target_user_from_message(message, context: ContextTypes.DEFAULT_TYPE) -> User | None:
    chat = message.chat or message.effective_chat
    if not chat:
        return None
    if message.reply_to_message and message.reply_to_message.from_user:
        _update_username_cache(context, chat.id, message.reply_to_message.from_user)
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntity.TEXT_MENTION and entity.user:
                _update_username_cache(context, chat.id, entity.user)
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntity.TEXT_MENTION and entity.user:
                return entity.user
        for entity in message.entities:
            if entity.type == MessageEntity.MENTION and message.text:
                try:
                    raw = message.parse_entity(entity)
                except (ValueError, IndexError, AttributeError):
                    raw = message.text[entity.offset : entity.offset + entity.length]
                username = (raw or "").lstrip("@").strip()
                if not username:
                    continue
                cache = context.bot_data.get("username_cache") or {}
                user_id = cache.get((chat.id, username.lower()))
                if user_id is not None:
                    try:
                        member = await context.bot.get_chat_member(chat.id, user_id)
                        _update_username_cache(context, chat.id, member.user)
                        return member.user
                    except Exception as e:
                        logger = __import__("logging").getLogger(__name__)
                        logger.warning("get_chat_member failed for @%s (id=%s): %s", username, user_id, e)
                else:
                    logger = __import__("logging").getLogger(__name__)
                    logger.info(
                        "Could not resolve @%s in this chat (not in cache); try reply or tap their name.", username
                    )
    return None


async def _get_target_users_from_message(message, context: ContextTypes.DEFAULT_TYPE) -> list[User]:
    chat = message.chat or message.effective_chat
    if not chat:
        return []
    if message.reply_to_message and message.reply_to_message.from_user:
        _update_username_cache(context, chat.id, message.reply_to_message.from_user)
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntity.TEXT_MENTION and entity.user:
                _update_username_cache(context, chat.id, entity.user)
    seen: set[int] = set()
    users: list[User] = []

    def add(u: User) -> None:
        if u.id not in seen and len(users) < STFU_MAX_TARGETS:
            seen.add(u.id)
            users.append(u)

    if message.reply_to_message and message.reply_to_message.from_user:
        add(message.reply_to_message.from_user)
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntity.TEXT_MENTION and entity.user:
                add(entity.user)
        for entity in message.entities:
            if entity.type == MessageEntity.MENTION and message.text and len(users) < STFU_MAX_TARGETS:
                try:
                    raw = message.parse_entity(entity)
                except (ValueError, IndexError, AttributeError):
                    raw = message.text[entity.offset : entity.offset + entity.length]
                username = (raw or "").lstrip("@").strip()
                if not username:
                    continue
                cache = context.bot_data.get("username_cache") or {}
                user_id = cache.get((chat.id, username.lower()))
                if user_id is not None:
                    try:
                        member = await context.bot.get_chat_member(chat.id, user_id)
                        _update_username_cache(context, chat.id, member.user)
                        add(member.user)
                    except Exception as e:
                        logger = __import__("logging").getLogger(__name__)
                        logger.warning("get_chat_member failed for @%s (id=%s): %s", username, user_id, e)
    return users
