"""Per-user command menu updates so granted users see /stfu, /unstfu, /doxx in the group and in DM."""
import logging
import time

from telegram import BotCommand, BotCommandScopeChatMember

logger = logging.getLogger(__name__)

# Must match the default common list in bot.py so granted users see common + their grants
_COMMON = [
    BotCommand("start", "Open Tengri menu"),
    BotCommand("tengriguideme", "Open Tengri menu in DM"),
    BotCommand("based", "+1 reputation"),
    BotCommand("cunt", "-1 reputation"),
    BotCommand("howbasedami", "Check your reputation"),
    BotCommand("howbasediseveryone", "List all peasants by rep"),
    BotCommand("fool", "Mark forward spammer"),
    BotCommand("privileged_peasants", "Who has /stfu"),
    BotCommand("redeem", "Redeem password for /stfu (DM)"),
    BotCommand("holycowshithindupajeetarmor", "STFU immunity"),
]

# Full list for admins (group and DM)
_ADMIN = [
    BotCommand("start", "Open Tengri menu"),
    BotCommand("stfu", "Mute user(s)"),
    BotCommand("unstfu", "Unmute user(s)"),
    BotCommand("grant_stfu", "Grant permanent /stfu (mod)"),
    BotCommand("revoke_stfu", "Revoke /stfu (mod)"),
    BotCommand("save_grants", "Save grants to disk (mod)"),
    BotCommand("doxx", "Flag media as doxx (granted)"),
    BotCommand("doxxed", "Grant doxx rights (admin)"),
    BotCommand("revoke_doxx", "Revoke doxx rights (admin)"),
    BotCommand("fool", "Mark forward spammer"),
    BotCommand("unfool", "Unmark fool (admin)"),
    BotCommand("exile", "Ban user from the group (King of Babylon)"),
    BotCommand("based", "+1 reputation"),
    BotCommand("cunt", "-1 reputation"),
    BotCommand("howbasedami", "Check your reputation"),
    BotCommand("howbasediseveryone", "List all peasants by rep"),
    BotCommand("edictoftengri", "Set reputation (admin)"),
    BotCommand("tengriguideme", "Open Tengri menu in DM"),
    BotCommand("redeem", "Redeem password for /stfu (DM)"),
    BotCommand("privileged_peasants", "Who has /stfu"),
    BotCommand("holycowshithindupajeetarmor", "STFU immunity"),
]


def _granted_commands(has_stfu_grant: bool, has_doxx_grant: bool) -> list[BotCommand]:
    """Build command list for a user in the group: common + optional stfu/unstfu + optional doxx."""
    out = list(_COMMON)
    if has_stfu_grant:
        out.append(BotCommand("stfu", "Mute user(s)"))
        out.append(BotCommand("unstfu", "Unmute user(s)"))
    if has_doxx_grant:
        out.append(BotCommand("doxx", "Flag media as doxx (granted)"))
    return out


async def update_user_commands(
    bot,
    chat_id: int,
    user_id: int,
    has_stfu_grant: bool,
    has_doxx_grant: bool,
) -> None:
    """
    Set the command menu for this user in this chat (group).
    Use after grant add/revoke so they see or stop seeing /stfu, /doxx.
    Does not affect admin scope; admins still see the full admin list.
    """
    try:
        commands = _granted_commands(has_stfu_grant, has_doxx_grant)
        await bot.set_my_commands(
            commands,
            scope=BotCommandScopeChatMember(chat_id=chat_id, user_id=user_id),
        )
    except Exception as e:
        logger.warning("update_user_commands chat_id=%s user_id=%s: %s", chat_id, user_id, e)


def user_grants(bot_data: dict, chat_id: int, user_id: int) -> tuple[bool, bool]:
    """Return (has_stfu_grant, has_doxx_grant) for this user in this chat."""
    now = time.time()
    grants = bot_data.setdefault("stfu_grants", {})
    g = grants.get((chat_id, user_id))
    has_stfu = g is not None and (g.get("expires_at") == 0 or (g.get("expires_at") or 0) > now)
    doxx = bot_data.get("doxx_grants") or {}
    d = doxx.get((chat_id, user_id))
    has_doxx = d is not None and (d.get("expires_at") or 0) > now
    return has_stfu, has_doxx


async def update_dm_commands_for_user(bot, bot_data: dict, target_group: int, user_id: int) -> None:
    """
    Set the command menu for this user in their DM with the bot (private chat).
    Uses BotCommandScopeChatMember(chat_id=user_id, user_id=user_id) so the list is scoped to their DM.
    Chooses admin list, granted list, or common list based on their role in the target group.
    """
    try:
        from permissions import _has_moderation_rights
        member = await bot.get_chat_member(target_group, user_id)
        if _has_moderation_rights(member):
            commands = list(_ADMIN)
        else:
            has_stfu, has_doxx = user_grants(bot_data, target_group, user_id)
            commands = _granted_commands(has_stfu, has_doxx)
        await bot.set_my_commands(
            commands,
            scope=BotCommandScopeChatMember(chat_id=user_id, user_id=user_id),
        )
    except Exception as e:
        # User may not be in the group (e.g. started bot in DM only)
        logger.debug("update_dm_commands_for_user user_id=%s: %s", user_id, e)
        try:
            await bot.set_my_commands(
                list(_COMMON),
                scope=BotCommandScopeChatMember(chat_id=user_id, user_id=user_id),
            )
        except Exception as e2:
            logger.warning("update_dm_commands_for_user fallback user_id=%s: %s", user_id, e2)
