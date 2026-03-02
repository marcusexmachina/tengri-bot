# Tengri Bot — Modularization Plan

## Current State

- **bot.py**: ~1,555 lines — monolithic, all logic in one file
- **Dependencies**: `python-telegram-bot`, `python-dotenv`
- **Entry point**: `python bot.py` or Docker

---

## Proposed Module Structure

```
tengri-bot/
├── bot.py                 # Entry point, ~80 lines (load env, wire handlers, run)
├── config.py              # Constants and configuration
├── responses.py           # ALL bot responses — single source of truth for every reply
├── utils.py               # Shared utilities (duration parsing, scheduling, formatting)
├── permissions.py          # Mod/admin checks, ChatPermissions helpers
├── resolvers.py           # User resolution (reply, @mention, username cache)
├── spam.py                # Text spam + media flood detection
├── grants.py              # STFU grant persistence (load/save JSON)
├── handlers/
│   ├── __init__.py        # Export all handlers for clean imports
│   ├── stfu.py            # /stfu, /unstfu, /grant_stfu, /revoke_stfu, /save_grants
│   ├── privileged_peasants.py
│   ├── stfuproof.py       # /holycowshithindupajeetarmor
│   └── tengriguideme.py   # /tengriguideme + callback handler
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
├── README.md
└── MODULARIZATION_PLAN.md
```

---

## Module Breakdown

### 1. `config.py` (~50 lines)

**Contents:**
- `SPAM_THRESHOLD`, `MEDIA_FLOOD_THRESHOLD`, `REPEAT_WINDOW_SECONDS`
- `MUTE_SECONDS`, `BULK_DELETE_CHUNK`, `NOTIFICATION_AUTO_DELETE_SECONDS`
- `DELEGATE_STFU_*`, `ADMIN_STFU_*`, `STFU_MAX_TARGETS`
- `STFUPROOF_DEFAULT_SECONDS`, `STFUPROOF_COOLDOWN_SECONDS`
- `SPAM_CATCHUP_SECONDS`, `MAX_TEMP_RESTRICT_SECONDS`, `TELEGRAM_MIN_RESTRICT_SECONDS`
- `_DURATION_UNITS` dict

**Dependencies:** None (pure config)

---

### 2. `responses.py` — ALL Bot Responses (~350–400 lines)

**Purpose:** Single source of truth for every bot reply. Handlers import from here only — no hardcoded strings. Designed for rotating responses: each response type is a list; use `random.choice()` when sending. Easy to add new variants later.

**Structure:**
- Each response type = list of strings (or templates with `{placeholder}`)
- Helper: `get_response(key: str, **kwargs) -> str` — returns `random.choice(LIST).format(**kwargs)` for that key
- Handlers call `responses.get_response("spam_warning", mention=user.mention_html())` etc.

**Complete catalog of response types (all must live here):**

| Key | Used in | Placeholders | Notes |
|-----|---------|--------------|-------|
| `spam_warning` | Spam/media flood | `{mention}` | Already rotating |
| `admin_check_fail` | Various | — | Already rotating |
| `not_admin_unmute` | cmd_unstfu | `{mention}` | Already rotating |
| `not_admin_mute` | cmd_stfu | `{mention}` | Already rotating |
| `no_target_unmute` | cmd_unstfu | — | Already rotating |
| `no_target_mute` | cmd_stfu | — | Already rotating |
| `unmute_fail` | cmd_unstfu | — | Already rotating |
| `mute_fail` | cmd_stfu | — | Already rotating |
| `unmute_success` | cmd_unstfu | `{mention}` | Already rotating |
| `mute_success` | cmd_stfu | `{mention}` | Already rotating |
| `wrong_chat` | All handlers | `{chat_id}` | Move from inline; add variants |
| `wrong_chat_stfu` | cmd_stfu | `{chat_id}` | Slightly different text |
| `unmute_basic_group` | cmd_unstfu | — | Move from inline |
| `mute_basic_group` | cmd_stfu | — | Move from inline |
| `grant_stfu_mod_only` | cmd_grant_stfu | `{mention}` | Move from inline |
| `grant_stfu_no_target` | cmd_grant_stfu | — | Move from inline |
| `revoke_stfu_mod_only` | cmd_revoke_stfu | `{mention}` | Move from inline |
| `revoke_stfu_no_target` | cmd_revoke_stfu | — | Move from inline |
| `revoke_stfu_all_done` | cmd_revoke_stfu | `{count}` | Move from inline |
| `revoke_stfu_all_empty` | cmd_revoke_stfu | — | Move from inline |
| `revoke_stfu_user_done` | cmd_revoke_stfu | `{mention}` | Move from inline |
| `revoke_stfu_user_empty` | cmd_revoke_stfu | — | Move from inline |
| `save_grants_mod_only` | cmd_save_grants | `{mention}` | Move from inline |
| `save_grants_done` | cmd_save_grants | `{count}` | Move from inline |
| `stfuproof_cooldown` | cmd_stfuproof | `{seconds}` | Move from inline |
| `stfuproof_self` | cmd_stfuproof | `{time_str}` | Move from inline |
| `stfuproof_other` | cmd_stfuproof | `{mention}`, `{time_str}` | Move from inline |
| `tengriguideme_dm_fail` | cmd_tengriguideme | — | Move from inline |
| `tengriguideme_group_reply` | cmd_tengriguideme | — | Already `GROUP_HEARMY_PRAYERS_REPLIES` |
| `tengriguideme_panel_text` | cmd_tengriguideme (DM) | — | Move from inline |
| `tengriguideme_cmd_privileged` | Callback | — | Move from inline |
| `tengriguideme_cmd_armor` | Callback | — | Move from inline |
| `tengriguideme_help_stfu` | Callback | — | Multi-line HTML; move from inline |
| `tengriguideme_help_unstfu` | Callback | — | Multi-line HTML; move from inline |
| `privileged_peasants_empty` | cmd_privileged_peasants | — | Move from inline |
| `privileged_peasants_header` | cmd_privileged_peasants | — | "PRIVILEGED PEASANTS" |
| `stfu_immune_single` | cmd_stfu | `{mention}`, `{time_left}` | Move from inline |
| `stfu_immune_multi` | cmd_stfu | `{skipped_list}` | Move from inline |
| `stfu_muted_multi` | cmd_stfu | `{muted}`, `{skipped}`, `{failed}` | Composite; may stay in handler |
| `grant_stfu_done` | cmd_grant_stfu | `{target}`, `{sender}`, `{hours}` | Move from inline |

**Implementation pattern:**
```python
# responses.py
import random

RESPONSES = {
    "spam_warning": SPAM_WARNING_MESSAGES,  # existing list
    "wrong_chat": [
        "This bot only runs in one group. Your current chat ID is <code>{chat_id}</code>. Set TELEGRAM_GROUP in .env to use me here.",
        "Wrong chat, idiot. Chat ID: <code>{chat_id}</code>. Fix your .env.",
        # ... add more variants
    ],
    # ...
}

def get_response(key: str, **kwargs) -> str:
    options = RESPONSES.get(key, [""])
    template = random.choice(options) if isinstance(options, list) else options
    return template.format(**kwargs) if kwargs else template
```

**Dependencies:** None (pure data + helper)

**Handlers:** Import `get_response` and use it for every reply. No string literals in handler code.

---

### 3. `utils.py` (~80 lines)

**Contents:**
- `_parse_duration_spec(spec: str) -> int | None`
- `_extract_duration_from_message(message, target_user) -> int | None`
- `_job_delete_message(context)` — JobQueue callback
- `_delete_message_after(bot, chat_id, message_id, seconds)` — fallback
- `_schedule_notification_delete(context, chat_id, message_id)`
- `_format_time_left(seconds: float) -> str`

**Dependencies:** `config`, `telegram.ext`

---

### 4. `permissions.py` (~50 lines)

**Contents:**
- `_has_moderation_rights(member) -> bool`
- `_full_permissions() -> ChatPermissions`
- `_mute_permissions() -> ChatPermissions`

**Dependencies:** `telegram`

---

### 5. `resolvers.py` (~100 lines)

**Contents:**
- `_update_username_cache(context, chat_id, user)`
- `_get_target_user_from_message(message, context) -> User | None`
- `_get_target_users_from_message(message, context) -> list[User]`

**Dependencies:** `telegram`, `config` (STFU_MAX_TARGETS)

---

### 6. `spam.py` (~200 lines)

**Contents:**
- `MessageBucket` dataclass
- `normalize_text(text: str) -> str`
- `handle_message_or_media(update, context)`
- `handle_message(update, context)` — text spam detection
- `handle_media_flood(update, context)` — GIF/sticker flood

**Dependencies:** `config`, `responses`, `utils`, `permissions`, `resolvers`

---

### 7. `grants.py` (~80 lines)

**Contents:**
- `_load_stfu_grants(path: str) -> dict`
- `_save_stfu_grants(path: str, grants: dict) -> None`

**Dependencies:** `config` (indirect), `json`, `os`, `logging`

---

### 8. `handlers/stfu.py` (~350 lines)

**Contents:**
- `cmd_unstfu`
- `cmd_stfu`
- `cmd_grant_stfu`
- `cmd_revoke_stfu`
- `cmd_save_grants`

**Dependencies:** `config`, `responses`, `utils`, `permissions`, `resolvers`, `grants`

---

### 9. `handlers/privileged_peasants.py` (~60 lines)

**Contents:**
- `cmd_privileged_peasants`

**Dependencies:** `config`, `utils`, `resolvers`

---

### 10. `handlers/stfuproof.py` (~100 lines)

**Contents:**
- `cmd_stfuproof` (alias: `/holycowshithindupajeetarmor`)

**Dependencies:** `config`, `utils`, `resolvers`

---

### 11. `handlers/tengriguideme.py` (~120 lines)

**Contents:**
- `cmd_tengriguideme`
- `_handle_help_callback`

**Dependencies:** `config`, `responses`, `utils`, `telegram`

---

### 12. `bot.py` (slim entry point, ~80 lines)

**Contents:**
- `load_env() -> tuple[str, int]`
- `main()` — build app, init bot_data, register handlers, run
- Imports from all handler modules

---

## Migration Steps (Order of Execution)

1. **Create `config.py`** — extract constants, update `bot.py` imports
2. **Create `responses.py`** — extract ALL response strings into one module; add `get_response()` helper; move every hardcoded string from handlers
3. **Create `utils.py`** — extract utilities, update imports
4. **Create `permissions.py`** — extract permission helpers
5. **Create `resolvers.py`** — extract user resolution
6. **Create `grants.py`** — extract load/save
7. **Create `spam.py`** — extract spam handlers
8. **Create `handlers/` package** — `__init__.py` first
9. **Create `handlers/stfu.py`** — extract stfu-related commands
10. **Create `handlers/privileged_peasants.py`**
11. **Create `handlers/stfuproof.py`**
12. **Create `handlers/tengriguideme.py`**
13. **Slim down `bot.py`** — keep only `load_env`, `main`, handler registration
14. **Run tests** — manual or automated (if any)
15. **Verify Docker build** — `docker compose up -d --build`

---

## Import Strategy

- Use **relative imports** within `handlers/` (e.g. `from ..utils import _schedule_notification_delete`)
- Use **absolute imports** from project root (e.g. `from config import STFU_MAX_TARGETS`)
- Avoid circular imports: `utils`, `config`, `responses` have no handler deps; handlers depend on them
- **responses.py** is the single place to add new rotating text — handlers never define reply strings

---

## Backward Compatibility

- **Entry point**: `python bot.py` remains unchanged
- **Dockerfile**: `CMD ["python", "bot.py"]` unchanged
- **Environment**: `.env` structure unchanged
- **Behavior**: No functional changes; only code organization

---

## Estimated Line Counts After Split

| File | Lines |
|------|-------|
| bot.py | ~80 |
| config.py | ~50 |
| responses.py | ~350–400 |
| utils.py | ~80 |
| permissions.py | ~50 |
| resolvers.py | ~100 |
| spam.py | ~200 |
| grants.py | ~80 |
| handlers/stfu.py | ~350 |
| handlers/privileged_peasants.py | ~60 |
| handlers/stfuproof.py | ~100 |
| handlers/tengriguideme.py | ~120 |
| **Total** | ~1,620 |

Largest files: `responses.py` (~350–400), `handlers/stfu.py` (~350). Both manageable.

---

## Add New Rotating Responses

To add new variants in the future:

1. Open **`responses.py`**
2. Find the response key (e.g. `wrong_chat`, `spam_warning`)
3. Append a new string to that list — it will be used automatically via `random.choice()`
4. Handlers never need changes — they call `get_response(key, **kwargs)` only
