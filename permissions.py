"""Mod/admin checks and ChatPermissions helpers."""
from telegram import ChatMemberAdministrator, ChatPermissions


def _has_moderation_rights(member) -> bool:
    if member.status == "creator":
        return True
    if member.status != "administrator":
        return False
    if isinstance(member, ChatMemberAdministrator):
        return bool(
            getattr(member, "can_delete_messages", False)
            or getattr(member, "can_restrict_members", False)
        )
    return False


def _is_real_admin(member) -> bool:
    """True if member can restrict/ban (real admin). Required for /fool (1 vote) and /doxxed."""
    if member.status == "creator":
        return True
    if member.status != "administrator":
        return False
    if isinstance(member, ChatMemberAdministrator):
        return bool(getattr(member, "can_restrict_members", False))
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
