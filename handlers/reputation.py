"""Handlers for /based and /cunt reputation commands."""

import asyncio
import html
import logging
import time

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    REPUTATION_COOLDOWN_SECONDS,
    REPUTATION_DEFAULT,
    REPUTATION_MAX,
    REPUTATION_MIN,
)
from grants import _save_stfu_grants
from permissions import _demote_zero_perms_admin, _full_permissions, _is_real_admin, _mute_permissions
from reputation_thresholds import get_rep, get_rep_tier
from resolvers import _get_target_user_from_message
from responses import get_response
from state import (
    _load_reputation,
    _load_reputation_shields,
    _load_reputation_votes,
    _save_reputation,
    _save_reputation_shields,
    _save_reputation_votes,
)
from utils import _schedule_notification_delete

logger = logging.getLogger(__name__)


def _get_reputation(context, chat_id: int, user_id: int) -> int:
    rep = context.bot_data.get("reputation") or {}
    return rep.get((chat_id, user_id), REPUTATION_DEFAULT)


def _set_reputation(context, chat_id: int, user_id: int, points: int) -> None:
    rep = context.bot_data.get("reputation")
    if rep is None:
        rep = _load_reputation()
        context.bot_data["reputation"] = rep
    rep[(chat_id, user_id)] = points
    _save_reputation(rep)


def _get_reputation_shields(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Return in-memory reputation shields, loading from disk if needed, and prune expired."""
    shields = context.bot_data.get("reputation_shields")
    if shields is None:
        shields = _load_reputation_shields()
        context.bot_data["reputation_shields"] = shields
    now = time.time()
    keys_to_delete = [k for k, exp in shields.items() if not isinstance(exp, (int, float)) or exp <= now]
    for k in keys_to_delete:
        shields.pop(k, None)
    if keys_to_delete:
        _save_reputation_shields(shields)
    return shields


def _has_active_rank_shield(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    shields = _get_reputation_shields(context)
    exp = shields.get((chat_id, user_id))
    if not isinstance(exp, (int, float)):
        return False
    return exp > time.time()


async def _handle_rank_change(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    old_points: int,
    new_points: int,
) -> None:
    """Apply side effects for rank ascension/descension: shield + notification."""
    if old_points == new_points:
        return
    old_tier = get_rep_tier(old_points)
    new_tier = get_rep_tier(new_points)
    if old_tier == new_tier:
        return

    direction = "ascended" if new_points > old_points else "descended"

    # Apply 24h shield from reputation votes.
    shields = _get_reputation_shields(context)
    expires_at = time.time() + 24 * 60 * 60
    shields[(chat_id, user_id)] = expires_at
    _save_reputation_shields(shields)

    # Resolve mention for notification and for potential tag updates.
    mention = f"User {user_id}"
    is_admin = False
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if getattr(member, "user", None):
            mention = member.user.mention_html()
        status = getattr(member, "status", None)
        is_admin = status in ("administrator", "creator")
    except Exception as e:  # pragma: no cover - best-effort lookup
        logger.warning("Rank change: failed to resolve mention for %s: %s", user_id, e)

    # Update Telegram member tag to match the new tier for non-admins, if the bot has rights.
    # Admins often have custom titles; we do not override those.
    if not is_admin:
        try:
            if hasattr(context.bot, "_post"):
                await context.bot._post(
                    "setChatMemberTag",
                    data={"chat_id": chat_id, "user_id": user_id, "tag": new_tier},
                )
        except Exception as e:  # pragma: no cover - best-effort tag update
            logger.warning("Failed to set member tag for chat_id=%s user_id=%s: %s", chat_id, user_id, e)

    if direction == "ascended":
        msg = get_response(
            "reputation_rank_ascended",
            mention=mention,
            tier=new_tier,
            points=new_points,
        )
    else:
        msg = get_response(
            "reputation_rank_descended",
            mention=mention,
            tier=new_tier,
            points=new_points,
        )
    try:
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")
    except Exception as e:  # pragma: no cover - best-effort notify
        logger.warning("Rank change notification failed for chat_id=%s user_id=%s: %s", chat_id, user_id, e)


def _can_vote(context, chat_id: int, voter_id: int, target_id: int, command: str) -> bool:
    votes = context.bot_data.get("reputation_votes") or []
    now = time.time()
    cutoff = now - REPUTATION_COOLDOWN_SECONDS
    for v in votes:
        if not isinstance(v, dict):
            continue
        if (
            v.get("chat_id") == chat_id
            and v.get("voter_id") == voter_id
            and v.get("command") == command
            and v.get("at", 0) > cutoff
        ):
            return False
    return True


async def apply_reputation_delta(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    delta: int,
) -> int:
    """Apply a reputation delta (e.g. -1 for exile penalty). Handles restrict/unrestrict at rep 10.
    Does not record votes. Returns new reputation points."""
    reputation = context.bot_data.get("reputation")
    if reputation is None:
        reputation = _load_reputation()
        context.bot_data["reputation"] = reputation
    key = (chat_id, user_id)
    current = reputation.get(key, REPUTATION_DEFAULT)
    new_points = max(REPUTATION_MIN, min(REPUTATION_MAX, current + delta))
    reputation[key] = new_points
    _save_reputation(reputation)
    old_points = current
    if new_points < 10 and delta < 0:
        grants = context.bot_data.setdefault("stfu_grants", {})
        gkey = (chat_id, user_id)
        if gkey in grants:
            del grants[gkey]
            _save_stfu_grants(context.bot_data.get("state_file") or "", grants)
        restrictable = await _demote_zero_perms_admin(context.bot, chat_id, user_id)
        if restrictable:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=_mute_permissions(),
                    until_date=0,
                    use_independent_chat_permissions=True,
                )
            except Exception as e:
                logger.warning("Low-rep restrict failed for %s: %s", user_id, e)
    elif new_points >= 10 and old_points < 10:
        restrictable = await _demote_zero_perms_admin(context.bot, chat_id, user_id)
        if restrictable:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=_full_permissions(),
                    until_date=0,
                    use_independent_chat_permissions=True,
                )
            except Exception as e:
                logger.warning("Low-rep unrestrict failed for %s: %s", user_id, e)

    # Handle possible rank ascension/descension (no shield for divine overrides beyond votes).
    await _handle_rank_change(context, chat_id, user_id, old_points, new_points)
    return new_points


def _record_vote(context, chat_id: int, voter_id: int, target_id: int, command: str) -> None:
    votes = context.bot_data.get("reputation_votes")
    if votes is None:
        votes = _load_reputation_votes()
        context.bot_data["reputation_votes"] = votes
    votes.append(
        {
            "chat_id": chat_id,
            "voter_id": voter_id,
            "target_id": target_id,
            "command": command,
            "at": time.time(),
        }
    )
    from config import REPUTATION_COOLDOWN_SECONDS

    cutoff = time.time() - REPUTATION_COOLDOWN_SECONDS
    votes[:] = [v for v in votes if isinstance(v, dict) and v.get("at", 0) > cutoff]
    _save_reputation_votes(votes)


async def _cmd_reputation(update: Update, context: ContextTypes.DEFAULT_TYPE, delta: int, command: str) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    _schedule_notification_delete(context, chat.id, message.message_id)
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("reputation_no_target", command=command)
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if target_user.id == sender.id:
        msg = get_response("reputation_no_self", command=command)
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    is_real_admin = _is_real_admin(member)
    if not is_real_admin and not _can_vote(context, chat.id, sender.id, target_user.id, command):
        # Compute remaining cooldown based on last vote timestamp for this voter+command
        votes = context.bot_data.get("reputation_votes") or []
        now = time.time()
        last_at = None
        for v in votes:
            if not isinstance(v, dict):
                continue
            if v.get("chat_id") == chat.id and v.get("voter_id") == sender.id and v.get("command") == command:
                ts = float(v.get("at", 0))
                if last_at is None or ts > last_at:
                    last_at = ts
        if last_at is not None:
            remaining_secs = max(0, REPUTATION_COOLDOWN_SECONDS - (now - last_at))
            hours = max(0.1, round(remaining_secs / 3600, 1)) if remaining_secs > 0 else 0
        else:
            hours = REPUTATION_COOLDOWN_SECONDS / 3600
        msg = get_response("reputation_cooldown", command=command, hours=hours)
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    reputation = context.bot_data.get("reputation")
    if reputation is None:
        reputation = _load_reputation()
        context.bot_data["reputation"] = reputation
    key = (chat.id, target_user.id)
    current = reputation.get(key, REPUTATION_DEFAULT)

    # Rank shield: consume vote and send normal response, but do not adjust reputation points.
    if _has_active_rank_shield(context, chat.id, target_user.id):
        if not is_real_admin:
            _record_vote(context, chat.id, sender.id, target_user.id, command)
        mention = target_user.mention_html()
        if delta > 0:
            msg = get_response("reputation_based", mention=mention, points=current)
        else:
            msg = get_response("reputation_cunt", mention=mention, points=current)
        # Clarify that rank shield is active without changing points.
        shield_note = get_response("reputation_rank_shield_note")
        full_msg = f"{msg} {shield_note}"
        sent = await message.reply_text(full_msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    new_points = max(REPUTATION_MIN, min(REPUTATION_MAX, current + delta))
    reputation[key] = new_points
    _save_reputation(reputation)
    old_points = current
    if new_points < 10 and delta < 0:
        grants = context.bot_data.setdefault("stfu_grants", {})
        gkey = (chat.id, target_user.id)
        if gkey in grants:
            del grants[gkey]
            _save_stfu_grants(context.bot_data.get("state_file") or "", grants)
        restrictable = await _demote_zero_perms_admin(context.bot, chat.id, target_user.id)
        if restrictable:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=target_user.id,
                    permissions=_mute_permissions(),
                    until_date=0,
                    use_independent_chat_permissions=True,
                )
            except Exception as e:
                logger.warning("Low-rep restrict failed for %s: %s", target_user.id, e)
    elif new_points >= 10 and old_points < 10:
        restrictable = await _demote_zero_perms_admin(context.bot, chat.id, target_user.id)
        if restrictable:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=target_user.id,
                    permissions=_full_permissions(),
                    until_date=0,
                    use_independent_chat_permissions=True,
                )
            except Exception as e:
                logger.warning("Low-rep unrestrict failed for %s: %s", target_user.id, e)

    # Record vote after reputation has been updated.
    if not is_real_admin:
        _record_vote(context, chat.id, sender.id, target_user.id, command)

    # Handle possible rank ascension/descension and apply shield.
    await _handle_rank_change(context, chat.id, target_user.id, old_points, new_points)
    mention = target_user.mention_html()
    if delta > 0:
        msg = get_response("reputation_based", mention=mention, points=new_points)
    else:
        msg = get_response("reputation_cunt", mention=mention, points=new_points)
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_based(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_reputation(update, context, 1, "based")


async def cmd_cunt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_reputation(update, context, -1, "cunt")


def _get_howbasedami_checkpoint(rep: int) -> str:
    """Return Babylonian title-based checkpoint message."""
    tier = get_rep_tier(rep)
    return get_response("howbasedami", tier=tier, pts=rep)


# --- HOWBASEDISEVERYONE (rollback: remove handler, bot.py, commands_menu, __init__) ---
_HOWBASEDISEVERYONE_CAP = 30
_BASED_THRESHOLD = 100


async def cmd_howbasediseveryone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Anyone can invoke. Lists all users with rep: BASED (>=100) and CUNTS (<100)."""
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    _schedule_notification_delete(context, chat.id, message.message_id)

    reputation = context.bot_data.get("reputation")
    if reputation is None:
        reputation = _load_reputation()
        context.bot_data["reputation"] = reputation

    entries = [(user_id, pts) for (cid, user_id), pts in reputation.items() if cid == target_group]
    if not entries:
        sent = await message.reply_text("No peasants in the record.")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    based = sorted([e for e in entries if e[1] >= _BASED_THRESHOLD], key=lambda x: -x[1])
    cunts = sorted([e for e in entries if e[1] < _BASED_THRESHOLD], key=lambda x: -x[1])

    async def _get_display(bot, chat_id: int, user_id: int) -> str:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            u = member.user
            if u.username:
                return f"@{u.username}"
            if u.first_name:
                return html.escape(u.first_name)
        except Exception:
            pass
        return f"User {user_id}"

    async def _resolve_all(user_ids: list[int]) -> dict[int, str]:
        out = {}
        sem = asyncio.Semaphore(10)

        async def one(uid):
            async with sem:
                disp = await _get_display(context.bot, target_group, uid)
                out[uid] = disp

        await asyncio.gather(*[one(uid) for uid in user_ids])
        return out

    all_ids = list({uid for uid, _ in entries})
    display_map = await _resolve_all(all_ids)

    def _format_section_resolved(items: list, cap: int) -> str:
        lines = []
        for user_id, pts in items[:cap]:
            disp = display_map.get(user_id, f"User {user_id}")
            lines.append(f"{disp}: {pts} points")
        if len(items) > cap:
            lines.append(f"... and {len(items) - cap} more")
        return "\n".join(lines) if lines else ""

    parts = ["<b>LIST OF PEASANTS:</b>", ""]
    if based:
        parts.append("<b>BASED:</b>")
        parts.append(_format_section_resolved(based, _HOWBASEDISEVERYONE_CAP))
        parts.append("")
    if cunts:
        parts.append("<b>CUNTS:</b>")
        parts.append(_format_section_resolved(cunts, _HOWBASEDISEVERYONE_CAP))

    msg = "\n".join(parts).strip()
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)


# --- END HOWBASEDISEVERYONE ---


async def cmd_howbasedami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not chat or not user:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    _schedule_notification_delete(context, chat.id, message.message_id)
    rep = (context.bot_data.get("reputation") or {}).get((chat.id, user.id), REPUTATION_DEFAULT)
    msg = _get_howbasedami_checkpoint(rep)
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)


async def cmd_shieldnull(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Testing helper: clear rank shield for a target user (admin-only)."""
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
    except Exception as e:
        logger.warning("shieldnull cmd delete failed: %s", e)
    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if not _is_real_admin(member):
        msg = get_response("edictoftengri_admin_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("reputation_no_target", command="shieldnull")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    shields = _get_reputation_shields(context)
    key = (chat.id, target_user.id)
    if key in shields:
        shields.pop(key, None)
        _save_reputation_shields(shields)


async def cmd_retag_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin-only: recompute and apply member tag for a single user."""
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    try:
        await context.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
    except Exception as e:
        logger.warning("retag_user cmd delete failed: %s", e)
    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if not _is_real_admin(member):
        msg = get_response("edictoftengri_admin_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("reputation_no_target", command="retag_user")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return

    # Do not override admin titles.
    try:
        target_member = await context.bot.get_chat_member(chat.id, target_user.id)
        status = getattr(target_member, "status", None)
        is_admin = status in ("administrator", "creator")
    except Exception:
        is_admin = False

    rep = _get_reputation(context, chat.id, target_user.id)
    tier = get_rep_tier(rep)

    if not is_admin:
        try:
            if hasattr(context.bot, "_post"):
                await context.bot._post(
                    "setChatMemberTag",
                    data={"chat_id": chat.id, "user_id": target_user.id, "tag": tier},
                )
        except Exception as e:  # pragma: no cover - best-effort tag update
            logger.warning(
                "retag_user: failed to set member tag for chat_id=%s user_id=%s: %s", chat.id, target_user.id, e
            )


async def cmd_edictoftengri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    sender = update.effective_user
    if not message or not chat or not sender:
        return
    target_group = context.bot_data.get("target_group")
    if not target_group or chat.id != target_group:
        return
    _schedule_notification_delete(context, chat.id, message.message_id)
    try:
        member = await context.bot.get_chat_member(chat.id, sender.id)
    except Exception:
        msg = get_response("admin_check_fail")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    if not _is_real_admin(member):
        msg = get_response("edictoftengri_admin_only", mention=sender.mention_html())
        sent = await message.reply_text(msg, parse_mode="HTML")
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    target_user = await _get_target_user_from_message(message, context)
    if not target_user:
        msg = get_response("edictoftengri_no_target")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    parts = (message.text or "").strip().split()
    new_pts = None
    for p in parts[1:] if len(parts) > 1 else []:
        if p.lstrip("-").isdigit():
            new_pts = int(p)
            break
    if new_pts is None:
        msg = get_response("edictoftengri_usage")
        sent = await message.reply_text(msg)
        _schedule_notification_delete(context, chat.id, sent.message_id)
        return
    new_pts = max(REPUTATION_MIN, min(REPUTATION_MAX, new_pts))
    old_pts = get_rep(context, chat.id, target_user.id)
    _set_reputation(context, chat.id, target_user.id, new_pts)
    if new_pts < 10:
        restrictable = await _demote_zero_perms_admin(context.bot, chat.id, target_user.id)
        if restrictable:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=target_user.id,
                    permissions=_mute_permissions(),
                    until_date=0,
                    use_independent_chat_permissions=True,
                )
            except Exception as e:
                logger.warning("Edict low-rep restrict failed for %s: %s", target_user.id, e)
    elif old_pts < 10 and new_pts >= 10:
        restrictable = await _demote_zero_perms_admin(context.bot, chat.id, target_user.id)
        if restrictable:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=target_user.id,
                    permissions=_full_permissions(),
                    until_date=0,
                    use_independent_chat_permissions=True,
                )
            except Exception as e:
                logger.warning("Edict low-rep unrestrict failed for %s: %s", target_user.id, e)
    msg = get_response("edictoftengri_done", mention=target_user.mention_html(), points=new_pts)
    sent = await message.reply_text(msg, parse_mode="HTML")
    _schedule_notification_delete(context, chat.id, sent.message_id)
