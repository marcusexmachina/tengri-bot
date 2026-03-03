# Tengri Bot — Full Documentation

## Overview

**Tengri** is a Telegram anti-spam and moderation bot for a single group. It:

1. **Detects spam** — Repetitive identical text (3+ in 2 min) or GIF/sticker floods (5+ in 2 min), deletes messages, mutes the user for 1 minute, and sends a warning.
2. **Provides /stfu and /unstfu** — Mute and unmute users. Admins/mods can always use these; regular users can use them if granted by a mod.
3. **Armor (stfu-proof)** — Users can grant themselves or others immunity to /stfu for 60 seconds.
4. **Help panel** — `/tengriguideme` sends a private DM with commands and usage instructions.

---

## Requirements

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Bot must be **admin** in the target group with:
  - **Delete messages**
  - **Restrict members**

---

## Setup

### 1. Environment

Create a `.env` file:

```env
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_GROUP=-1001234567890
STATE_FILE=stfu_grants.json
```

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_TOKEN` | Yes | Bot token from BotFather |
| `TELEGRAM_GROUP` | Yes | Target group chat ID (integer). Use a bot like @userinfobot to get it. |
| `STATE_FILE` | No | Path for persisting /stfu grants. Default: `stfu_grants.json` |

### 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run

**Local:**
```bash
python bot.py
```

**Docker:**
```bash
docker compose up -d --build
```

---

## Commands Reference

### Everyone Can Use

| Command | Description |
|---------|--------------|
| `/tengriguideme` | Bot replies in group "check your DM", then sends a help panel to your DM with buttons for commands and usage. |
| `/privileged_peasants` | Lists users who currently have /stfu rights in this chat (with time left). |
| `/holycowshithindupajeetarmor` | Grant immunity to /stfu for 60 seconds. Self (no target) or on someone else (reply/@user). Cooldown: 60s per caster. |

### Mods/Admins Only

| Command | Description |
|---------|--------------|
| `/grant_stfu @user [duration]` | Grant /stfu rights to a user. Default 24h. Example: `/grant_stfu @alice 12h` |
| `/revoke_stfu @user` | Revoke /stfu from a user. |
| `/revoke_stfu all` | Revoke all /stfu grants in this chat. |
| `/save_grants` | Write current grants to disk. Run before restart to persist in-memory state. |

### Mods/Admins or Delegates (Users with /stfu Grant)

| Command | Description |
|---------|--------------|
| `/stfu [@user(s)] [duration]` | Mute user(s). Reply to their message or @mention. Duration: admin 1m–10m, delegate 1m–5m. Examples: `/stfu`, `/stfu @user 3m`, `/stfu @a @b 5m` |
| `/unstfu [@user(s)]` | Unmute user(s). Reply or @mention. |

---

## Command Details

### /tengriguideme

- **Where:** Run in the group.
- **Behavior:** Bot replies in group with a short message (e.g. "Hi, check your DM. I don't talk here.") that auto-deletes after 30 seconds. The full help panel is sent to your **private chat** with the bot.
- **DM panel:** Buttons for "Who has /stfu?", "Armor", "How to /stfu", "How to /unstfu". Tapping shows the command to copy or usage instructions.
- **Requirement:** You must have started a chat with the bot first (tap bot name → Message). Otherwise the bot will reply in group that it couldn't DM you.

### /stfu

- **Who can use:** Group admins/mods, or users with an active /stfu grant (delegates).
- **Target:** Reply to the user's message, or @mention them. Multiple users: `/stfu @a @b @c 3m`.
- **Duration:** Optional. Format: `1m`, `5m`, `10m`, `2h`, `1d`, etc. Admin default: 1m, max 10m. Delegate default: 1m, max 5m.
- **Immunity:** Users with active armor (from `/holycowshithindupajeetarmor`) cannot be muted — not even by admins.
- **Chat type:** Works only in **supergroups** (not basic groups).

### /unstfu

- **Who can use:** Same as /stfu (admins or delegates).
- **Target:** Reply or @mention. Multiple: `/unstfu @a @b`.
- **Chat type:** Supergroups only.

### /holycowshithindupajeetarmor (Armor)

- **Who can use:** Anyone.
- **Self-cast:** Run with no target — you get 60s immunity.
- **Cast on others:** Reply to someone or @mention — they get 60s immunity.
- **Cooldown:** 60 seconds per caster (you can't spam it).
- **Effect:** Immune users cannot be /stfu'd by anyone, including admins.

### /privileged_peasants

- **Who can use:** Anyone.
- **Output:** List of users with active /stfu grants and time remaining. Auto-deletes after 30s.

### /grant_stfu

- **Who can use:** Mods/admins only.
- **Target:** Reply or @mention. Example: `/grant_stfu @user 24h`.
- **Duration:** Default 24h. Max ~366 days.

### /revoke_stfu

- **Who can use:** Mods/admins only.
- **Target:** Reply, @mention, or `all` to revoke everyone in the chat.

### /save_grants

- **Who can use:** Mods/admins only.
- **Purpose:** Flush current in-memory grants to the state file. Useful before restarting the bot.

---

## Spam Detection

### Text Spam

- **Trigger:** Same user sends the **same normalized text** 3+ times within 120 seconds.
- **Action:** Delete all copies, mute user for 1 minute, send a random warning message.
- **Normalization:** Lowercase, collapse whitespace.

### Media Flood (GIF/Sticker)

- **Trigger:** Same user sends 5+ GIFs or stickers in succession within the same 120s window.
- **Action:** Same as text spam — delete, mute 1 min, warn.

---

## Persistence

### /stfu Grants

- Stored in a JSON file (`STATE_FILE`).
- Loaded at startup; saved on every grant/revoke (and via `/save_grants`).
- Format: `[{"chat_id": N, "user_id": N, "granted_by": N, "expires_at": FLOAT}, ...]`

### In-Memory Only

- **Armor (stfuproof):** Immunity and cooldown — lost on restart.
- **Username cache:** For @mention resolution — lost on restart.
- **Spam state:** Buckets — lost on restart.

---

## Auto-Delete

- Bot replies (warnings, command responses) are scheduled for deletion after **30 seconds**.
- Requires bot to have "delete messages" permission.
- If messages don't disappear, check logs for `Auto-delete failed`.

---

## Single Instance

- Only **one** bot instance per token can poll Telegram at a time.
- Running both `python bot.py` and Docker will cause 409 Conflict.
- The bot exits on 409 so you can restart with a single instance.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 409 Conflict | Stop all other instances (Docker or local). Use only one. |
| Bot can't DM me | Start a chat with the bot first (tap name → Message). |
| /stfu doesn't work | Ensure chat is a supergroup. Bot needs "restrict members". |
| Grants lost after restart | Set `STATE_FILE` and ensure the path is writable. Run `/save_grants` before restart. |
| Messages not auto-deleting | Bot needs "delete messages". Check logs for errors. |

---

## File Structure (Current)

```
tengri-bot/
├── bot.py           # Main entry (~1555 lines)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
├── README.md
├── DOCUMENTATION.md
└── MODULARIZATION_PLAN.md
```

See `MODULARIZATION_PLAN.md` for the planned modular structure.
