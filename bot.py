"""Tengri bot entry point."""
import logging
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from telegram import Update
from telegram.error import Conflict
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from grants import _load_stfu_grants
from handlers import (
    _handle_help_callback,
    cmd_grant_stfu,
    cmd_privileged_peasants,
    cmd_revoke_stfu,
    cmd_save_grants,
    cmd_stfu,
    cmd_stfuproof,
    cmd_tengriguideme,
    cmd_unstfu,
)
from spam import MessageBucket, handle_message_or_media


def load_env() -> tuple[str, int]:
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    group_raw = os.getenv("TELEGRAM_GROUP")
    if not token:
        raise ValueError("Missing TELEGRAM_TOKEN in .env")
    if not group_raw:
        raise ValueError("Missing TELEGRAM_GROUP in .env")
    try:
        group_id = int(group_raw)
    except ValueError as exc:
        raise ValueError("TELEGRAM_GROUP must be an integer chat ID") from exc
    return token, group_id


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    token, group_id = load_env()

    app = ApplicationBuilder().token(token).build()
    app.bot_data["target_group"] = group_id
    app.bot_data["spam_state"] = defaultdict(lambda: defaultdict(MessageBucket))
    app.bot_data["media_flood_state"] = defaultdict(lambda: MessageBucket())
    state_file = os.getenv("STATE_FILE", "stfu_grants.json")
    app.bot_data["state_file"] = state_file
    app.bot_data["stfu_grants"] = _load_stfu_grants(state_file)
    app.bot_data["username_cache"] = {}
    app.bot_data["stfuproof_immunity"] = {}
    app.bot_data["stfuproof_cooldown"] = {}
    app.bot_data["stfuproof_duration_overrides"] = {}

    app.add_handler(MessageHandler(filters.UpdateType.MESSAGE & ~filters.COMMAND, handle_message_or_media))
    app.add_handler(CommandHandler("unstfu", cmd_unstfu))
    app.add_handler(CommandHandler("stfu", cmd_stfu))
    app.add_handler(CommandHandler("grant_stfu", cmd_grant_stfu))
    app.add_handler(CommandHandler("revoke_stfu", cmd_revoke_stfu))
    app.add_handler(CommandHandler("save_grants", cmd_save_grants))
    app.add_handler(CommandHandler("tengriguideme", cmd_tengriguideme))
    app.add_handler(CallbackQueryHandler(_handle_help_callback, pattern=r"^(help:(stfu|unstfu)|cmd:(privileged_peasants|holycowshithindupajeetarmor))$"))
    app.add_handler(CommandHandler("privileged_peasants", cmd_privileged_peasants))
    app.add_handler(CommandHandler("holycowshithindupajeetarmor", cmd_stfuproof))

    def on_error(_update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        if context.error and isinstance(context.error, Conflict):
            logging.getLogger(__name__).error(
                "Telegram 409 Conflict: another instance is already polling (Docker or another 'python bot.py'). "
                "This process is exiting so only one instance runs."
            )
            sys.exit(1)
        logging.getLogger(__name__).exception("Unhandled error")

    app.add_error_handler(on_error)

    print("Anti-spam bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
