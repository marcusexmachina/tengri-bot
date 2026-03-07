"""Mod/admin checks and ChatPermissions helpers."""

import logging

from telegram import ChatMemberAdministrator, ChatPermissions

logger = logging.getLogger(__name__)


def _is_admin_with_zero_permissions(member) -> bool:
    """True if member is administrator with no restrict/delete rights. Such admins are treated as regular members for restrict/mute."""
    if member.status != "administrator":
        return False
    if not isinstance(member, ChatMemberAdministrator):
        return False
    # Only treat as zero-perms if they have no restrict or delete power
    if getattr(member, "can_restrict_members", False) or getattr(member, "can_delete_messages", False):
        return False
    return True


async def _demote_zero_perms_admin(bot, chat_id: int, user_id: int) -> bool:
    """If user is admin with zero permissions, demote them to regular member so they can be restricted. Returns True if restrictable (demoted or already regular)."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception as e:
        logger.warning("get_chat_member failed for demote check user_id=%s: %s", user_id, e)
        return False
    if member.status == "creator":
        return False
    if member.status != "administrator":
        return True
    if not _is_admin_with_zero_permissions(member):
        return False
    try:
        await bot.promote_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_pin_messages=False,
            can_manage_topics=False,
        )
        logger.info("Demoted zero-perms admin user_id=%s to regular member", user_id)
        return True
    except Exception as e:
        logger.warning("Demote failed for user_id=%s: %s", user_id, e)
        logger.info(
            "Cannot mute zero-perms admin user_id=%s: demote failed. "
            "Ensure the bot has 'add new admins' (can_promote_members) permission.",
            user_id,
        )
        return False


def _has_moderation_rights(member) -> bool:
    if member.status == "creator":
        return True
    if member.status != "administrator":
        return False
    if _is_admin_with_zero_permissions(member):
        return False
    if isinstance(member, ChatMemberAdministrator):
        return bool(getattr(member, "can_delete_messages", False) or getattr(member, "can_restrict_members", False))
    return False


def _is_real_admin(member) -> bool:
    """True if member can restrict/ban (real admin). Required for /fool (1 vote) and /doxxed."""
    if member.status == "creator":
        return True
    if member.status != "administrator":
        return False
    if _is_admin_with_zero_permissions(member):
        return False
    if isinstance(member, ChatMemberAdministrator):
        return bool(getattr(member, "can_restrict_members", False))
    return False


def _can_exile(member) -> bool:
    """True only for group owner or admins with ban/restrict AND change-info rights. Required for /exile."""
    if member.status == "creator":
        return True
    if member.status != "administrator":
        return False
    if _is_admin_with_zero_permissions(member):
        return False
    if isinstance(member, ChatMemberAdministrator):
        return bool(getattr(member, "can_restrict_members", False) and getattr(member, "can_change_info", False))
    return False


def _full_permissions() -> ChatPermissions:
    return ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False,
    )


def _mute_permissions() -> ChatPermissions:
    return ChatPermissions(
        can_send_messages=False,
        can_send_audios=False,
        can_send_documents=False,
        can_send_photos=False,
        can_send_videos=False,
        can_send_video_notes=False,
        can_send_voice_notes=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False,
    )
