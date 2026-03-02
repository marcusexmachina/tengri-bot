# Tengri Anti-Spam Bot

Telegram anti-spam and moderation bot for a single group. Features:

- **Spam detection** — Repetitive text (3+ in 2 min) or GIF/sticker floods (5+ in 2 min): deletes messages, mutes 1 min, warns
- **/stfu and /unstfu** — Mute/unmute users (admins or delegated users)
- **Armor** — `/holycowshithindupajeetarmor` grants 60s immunity to /stfu
- **Help panel** — `/tengriguideme` sends commands and usage to your DM

**Full documentation:** [DOCUMENTATION.md](DOCUMENTATION.md) — all commands, setup, and troubleshooting.

## Setup

1. Create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Install dependencies (includes optional `job-queue` for reliable 20s auto-deletes):
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in:
   - `TELEGRAM_TOKEN=...` (from [@BotFather](https://t.me/BotFather))
   - `TELEGRAM_GROUP=...` (target group chat ID)
   - Optional: `STATE_FILE=...` (default: `stfu_grants.json` in current directory)

## Run (local)

`python bot.py`

## Run with Docker Compose

1. Copy `.env.example` to `.env` and ensure it has:
   - `TELEGRAM_TOKEN=...`
   - `TELEGRAM_GROUP=...`
2. Build and start the bot (a volume is used so `/stfu` grants persist across restarts):
   - `docker compose up -d --build`
3. View logs:
   - `docker compose logs -f`
4. Stop the bot:
   - `docker compose down`

## Notes

- The bot must be admin in the target group with **delete messages** and **restrict users** (required for spam cleanup, /stfu, /unstfu, and for auto-deleting bot notifications and commands after 20 seconds).
- Spam detection triggers when the same user sends the same normalized text 3 times within 120 seconds.
- Bot notifications and /stfu, /unstfu command messages are automatically deleted after 20 seconds. If they are not disappearing, check the bot has "can delete messages" and check logs for `Auto-delete failed` warnings.
- Only **one** instance of the bot should run per token at a time. If you use Docker Compose, avoid also running `python bot.py` directly on the host simultaneously.

### Persisting /stfu grants

- Grants for `/stfu` (who can use the mute command) are stored in a JSON file so they survive restarts.
- **Env:** Set `STATE_FILE` to the path (e.g. `./data/stfu_grants.json` locally, or `/app/data/stfu_grants.json` in Docker). Default is `stfu_grants.json` in the current directory.
- **Docker:** The Compose file sets `STATE_FILE=/app/data/stfu_grants.json` and mounts a volume at `/app/data`, so grants persist across container restarts.
- **First deploy:** The first time you run with this persistence, the state file does not exist yet. After the first restart, in-memory grants from the previous run are gone. Either re-grant with `/grant_stfu` for those users once, or create the state file manually before starting: a JSON array of `{"chat_id": <int>, "user_id": <int>, "granted_by": <int>, "expires_at": <float>}` at `STATE_FILE`. From then on, grants are saved on every change and restored on startup. Mods can run `/save_grants` before a restart to flush the current in-memory state to disk.

### Finding and stopping the other instance (409 Conflict)

If you see "409 Conflict" or "only one bot instance can poll", another process is already using the token. Use one of these:

- **If the other instance is Docker:**  
  `docker compose ps` then `docker compose down`
- **If the other instance is a local `python bot.py`:**  
  `pgrep -f "python bot.py"` to see PIDs, then `pkill -f "python bot.py"` to stop them (or close the terminal that’s running the bot).
- **Run only one:** Use either Docker **or** local `python bot.py`, not both. When you start the bot, any duplicate process that hits 409 will exit automatically so one instance remains.
