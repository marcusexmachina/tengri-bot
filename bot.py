"""Tengri bot entry point."""
import logging
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv
from telegram import BotCommand, BotCommandScopeAllChatAdministrators, BotCommandScopeDefault, Update
from telegram.error import Conflict
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from grants import _load_stfu_grants
from state import _load_acquire_pending, _load_acquired_stfu, _load_doxx_grants, _load_doxx_hashes, _load_dm_started_users, _load_fool_marked, _load_reputation, _load_reputation_votes
from handlers import (
    _handle_help_callback,
    cmd_redeem,
    cmd_doxx,
    cmd_doxxed,
    cmd_based,
    cmd_cunt,
    cmd_howbasedami,
    cmd_howbasediseveryone,
    cmd_edictoftengri,
    cmd_exile,
    cmd_fool,
    cmd_grant_stfu,
    cmd_privileged_peasants,
    cmd_revoke_doxx,
    cmd_revoke_stfu,
    cmd_save_grants,
    cmd_start,
    cmd_stfu,
    cmd_stfuproof,
    cmd_tengriguideme,
    cmd_unfool,
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

    async def _set_commands(application):
        # Default scope: everyone (group members, DMs) — common commands only
        common_commands = [
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
        await application.bot.set_my_commands(common_commands, scope=BotCommandScopeDefault())

        # Admin scope: only visible to chat administrators (group/supergroup)
        admin_commands = [
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
        await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeAllChatAdministrators())
    app = ApplicationBuilder().token(token).post_init(_set_commands).build()
    app.bot_data["target_group"] = group_id
    app.bot_data["spam_state"] = defaultdict(lambda: defaultdict(MessageBucket))
    app.bot_data["media_flood_state"] = defaultdict(lambda: MessageBucket())
    state_file = os.getenv("STATE_FILE", "stfu_grants.json")
    app.bot_data["state_file"] = state_file
    app.bot_data["stfu_grants"] = _load_stfu_grants(state_file)
    app.bot_data["fool_marked"] = _load_fool_marked()
    app.bot_data["doxx_grants"] = _load_doxx_grants()
    app.bot_data["doxx_hashes"] = _load_doxx_hashes()
    app.bot_data["acquired_stfu"] = _load_acquired_stfu()
    app.bot_data["acquire_pending"] = _load_acquire_pending()
    app.bot_data["reputation"] = _load_reputation()
    app.bot_data["reputation_votes"] = _load_reputation_votes()
    app.bot_data["dm_started_users"] = _load_dm_started_users()
    app.bot_data["username_cache"] = {}
    app.bot_data["stfuproof_immunity"] = {}
    app.bot_data["stfuproof_cooldown"] = {}
    app.bot_data["stfuproof_duration_overrides"] = {}

    app.add_handler(MessageHandler(filters.UpdateType.MESSAGE & ~filters.COMMAND, handle_message_or_media))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("unstfu", cmd_unstfu))
    app.add_handler(CommandHandler("stfu", cmd_stfu))
    app.add_handler(CommandHandler("grant_stfu", cmd_grant_stfu))
    app.add_handler(CommandHandler("revoke_stfu", cmd_revoke_stfu))
    app.add_handler(CommandHandler("save_grants", cmd_save_grants))
    app.add_handler(CommandHandler("doxxed", cmd_doxxed))
    app.add_handler(CommandHandler("doxx", cmd_doxx))
    app.add_handler(CommandHandler("revoke_doxx", cmd_revoke_doxx))
    app.add_handler(CommandHandler("fool", cmd_fool))
    app.add_handler(CommandHandler("unfool", cmd_unfool))
    app.add_handler(CommandHandler("exile", cmd_exile))
    app.add_handler(CommandHandler("based", cmd_based))
    app.add_handler(CommandHandler("cunt", cmd_cunt))
    app.add_handler(CommandHandler("howbasedami", cmd_howbasedami))
    app.add_handler(CommandHandler("howbasediseveryone", cmd_howbasediseveryone))
    app.add_handler(CommandHandler("edictoftengri", cmd_edictoftengri))
    app.add_handler(CommandHandler("tengriguideme", cmd_tengriguideme))
    app.add_handler(CommandHandler("redeem", cmd_redeem))
    # Match help:*, cmd:*, and acquire: callbacks. Flexible so new help/cmd buttons work without updating this.
    app.add_handler(
        CallbackQueryHandler(
            _handle_help_callback,
            pattern=r"^(help:[a-z_]+|cmd:[a-z_]+|acquire:(start|gen|timeleft|blocked))$",
        )
    )
    app.add_handler(CommandHandler("privileged_peasants", cmd_privileged_peasants))
    app.add_handler(CommandHandler("holycowshithindupajeetarmor", cmd_stfuproof))

    async def on_error(_update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
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
