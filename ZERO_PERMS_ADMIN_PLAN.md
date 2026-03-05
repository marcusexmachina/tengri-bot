# Zero-Permission Admin Treatment — Implementation Plan

## Objective

Treat **all admins with zero permissions** (like the "Regular User" role in your screenshot — every permission OFF) as **regular members** for:
1. **Casting commands** — they must use grants/votes like regular members (no admin shortcuts)
2. **Being targeted** — they can be muted, restricted, fooled, etc. like regular members (no immunity)

---

## Current State (Already Implemented)

The codebase **already has** zero-perms logic. Here's what exists:

### 1. Permission Module (`permissions.py`)

| Function | Purpose | Zero-perms behavior |
|----------|---------|---------------------|
| `_is_admin_with_zero_permissions(member)` | Detect admins with no restrict/delete power | Returns True when `can_restrict_members=False` AND `can_delete_messages=False` |
| `_demote_zero_perms_admin(bot, chat_id, user_id)` | Demote before restrict | Demotes zero-perms admins to regular member so `restrict_chat_member` succeeds |
| `_has_moderation_rights(member)` | Can cast /stfu, /grant_stfu, etc. | Returns **False** for zero-perms → they need grants |
| `_is_real_admin(member)` | Can cast /fool (1 vote), /doxxed, /unfool, /edictoftengri | Returns **False** for zero-perms → they need vote threshold |
| `_can_exile(member)` | Can cast /exile | Returns **False** for zero-perms |

### 2. Call Sites — Demote Before Restrict

Every `restrict_chat_member` call is preceded by `_demote_zero_perms_admin`:

| File | Location | Purpose |
|------|----------|---------|
| `handlers/stfu.py` | cmd_stfu (mute), cmd_unstfu (unmute) | /stfu and /unstfu targets |
| `handlers/fool.py` | _apply_fool_mark_and_penalty | /fool target mute |
| `handlers/reputation.py` | apply_reputation_delta, _cmd_reputation | Low-rep restrict, based/cunt vote restrict |
| `spam.py` | Low-rep, text spam, media flood, NSFW | Auto-mute on spam/NSFW |

### 3. Call Sites — Sender Permission Checks

| Command | Check | Zero-perms result |
|---------|-------|-------------------|
| /stfu, /unstfu, /grant_stfu, /revoke_stfu, /save_grants | `_has_moderation_rights` | Must have grant to cast |
| /fool | `_is_real_admin` | Needs FOOL_VOTE_THRESHOLD votes (not 1) |
| /unfool | `_is_real_admin` | Cannot cast |
| /doxxed, /revoke_doxx | `_is_real_admin` | Cannot cast |
| /exile | `_can_exile` | Cannot cast |
| /edictoftengri (reputation) | `_is_real_admin` | Cannot cast |
| /based, /cunt | `_is_real_admin` or `_can_vote` | Can vote (like regular member) |

---

## Why It Might Still Fail

### 1. Bot Lacks `can_promote_members`

`_demote_zero_perms_admin` uses `promote_chat_member` with all permissions set to False to demote. **This requires the bot to have "Add New Admins" (can_promote_members)**. Without it, the demote fails → `restrict_chat_member` is never called → zero-perms admin stays immune.

**README already documents this** (line 42).

### 2. Zero-Perms Detection May Be Incomplete

Current check: `can_restrict_members` OR `can_delete_messages`. If either is True → not zero-perms.

Your screenshot shows all OFF. Telegram maps:
- "Ban Users" → `can_restrict_members`
- "Delete Messages" → `can_delete_messages`

So the check is correct. An admin with both OFF is zero-perms.

### 3. Possible Edge: Other Permission Attributes

Telegram also has: `can_pin_messages`, `can_change_info`, `can_invite_users`, `can_manage_chat`, etc. We only check restrict + delete. An admin with e.g. only `can_pin_messages` would be zero-perms (no restrict, no delete) — correct. No change needed.

---

## Proposed Changes (Minimal, Defensive)

### Option A: No Code Changes — Verify Setup Only

If the logic is correct, the failure may be:
1. Bot missing `can_promote_members` in the group
2. A different bug (e.g. the grants `or {}` bug we just fixed)

**Action:** Confirm bot has all three: delete messages, restrict users, **add new admins**.

### Option B: Harden Zero-Perms Detection (Low Risk)

Expand `_is_admin_with_zero_permissions` to be more explicit and future-proof:

```python
def _is_admin_with_zero_permissions(member) -> bool:
    """True if admin with no meaningful moderation power. Treated as regular member."""
    if member.status != "administrator":
        return False
    if not isinstance(member, ChatMemberAdministrator):
        return False
    # Must have NEITHER restrict nor delete to be "zero perms"
    if getattr(member, "can_restrict_members", False):
        return False
    if getattr(member, "can_delete_messages", False):
        return False
    return True
```

This is logically identical to current code — just clearer. **No behavior change.**

### Option C: Add Diagnostic Logging (Medium Risk)

When `_demote_zero_perms_admin` fails, log the exact reason (creator vs real admin vs API error). Helps debug "immune" reports.

**Risk:** More log noise. **Benefit:** Easier troubleshooting.

### Option D: Fail-Safe — Do Not Touch Grants/State

**Critical:** The previous break was the `context.bot_data.get("stfu_grants") or {}` bug. We fixed it with `setdefault`. **Do not modify** any grants, bot_data, or state logic. Zero-perms changes are isolated to `permissions.py` and the restrict call sites.

---

## Audit Checklist — Every Restrict Path

| # | File:Line | restrict_chat_member | _demote_zero_perms_admin before? |
|---|-----------|----------------------|-----------------------------------|
| 1 | handlers/stfu.py:90 | unmute | ✅ line 85 |
| 2 | handlers/stfu.py:359,367 | mute | ✅ line 354 |
| 3 | handlers/fool.py:97 | fool mute | ✅ line 94 |
| 4 | handlers/reputation.py:83 | low-rep restrict | ✅ line 80 |
| 5 | handlers/reputation.py:96 | low-rep unrestrict | ✅ line 93 |
| 6 | handlers/reputation.py:195 | based/cunt restrict | ✅ line 192 |
| 7 | handlers/reputation.py:208 | based/cunt unrestrict | ✅ line 205 |
| 8 | handlers/reputation.py:322 | edict restrict | ✅ line 319 |
| 9 | handlers/reputation.py:335 | edict unrestrict | ✅ line 332 |
| 10 | spam.py:194 | low-rep auto-restrict | ✅ line 191 |
| 11 | spam.py:373 | text spam mute | ✅ line 370 |
| 12 | spam.py:481 | text spam bulk mute | ✅ line 479 |
| 13 | spam.py:551 | media flood mute | ✅ line 549 |
| 14 | spam.py:194 (NSFW) | NSFW mute | ✅ line 191 |

**All 14 restrict paths have demote-before-restrict.** ✅

---

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking redeem/grants again | Low | Do not touch grants, state, or bot_data |
| Demote fails (bot lacks can_promote_members) | Medium | Document in README; add log when demote fails |
| Zero-perms admin still immune | Low | Logic is correct; verify bot permissions |
| Regression in permission checks | Low | Changes limited to permissions.py; no new call sites |

---

## Confidence Level

| Aspect | Confidence | Notes |
|--------|------------|-------|
| Zero-perms detection logic | **95%** | Matches Telegram API; screenshot confirms |
| Demote-before-restrict coverage | **100%** | All 14 paths audited |
| Sender permission checks | **95%** | _has_moderation_rights, _is_real_admin, _can_exile all handle zero-perms |
| No regression to grants/state | **100%** | Plan explicitly avoids those areas |
| Bot permission requirement | **90%** | can_promote_members is required; user must ensure |

---

## Recommended Actions

1. **Verify bot permissions** in the target group: delete messages, restrict users, **add new admins**.
2. **No code changes** if setup is correct — current implementation should work.
3. **Optional:** Add INFO log when `_demote_zero_perms_admin` fails with reason (creator vs real admin vs API error) for easier debugging.
4. **Optional:** Expand `_is_admin_with_zero_permissions` docstring to reference "Regular User" style roles for clarity.

---

## Summary

The zero-perms admin treatment is **already implemented**. The likely causes of "immune" behavior are:
1. Bot missing `can_promote_members` (demote fails)
2. The grants bug we fixed (unrelated to zero-perms)

**No structural code changes are required.** Verify bot permissions first.
