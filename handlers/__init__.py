"""Command handlers for Tengri bot."""
from handlers.privileged_peasants import cmd_privileged_peasants
from handlers.stfu import (
    cmd_grant_stfu,
    cmd_revoke_stfu,
    cmd_save_grants,
    cmd_stfu,
    cmd_unstfu,
)
from handlers.stfuproof import cmd_stfuproof
from handlers.tengriguideme import _handle_help_callback, cmd_tengriguideme

__all__ = [
    "cmd_unstfu",
    "cmd_stfu",
    "cmd_grant_stfu",
    "cmd_revoke_stfu",
    "cmd_save_grants",
    "cmd_tengriguideme",
    "_handle_help_callback",
    "cmd_privileged_peasants",
    "cmd_stfuproof",
]
