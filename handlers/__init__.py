"""Command handlers for Tengri bot."""

from handlers.acquire_stfu import cmd_redeem
from handlers.doxx import cmd_doxx, cmd_doxxed, cmd_revoke_doxx
from handlers.exile import cmd_exile
from handlers.fool import cmd_fool, cmd_unfool
from handlers.mock import cmd_mock, cmd_unmock
from handlers.privileged_peasants import cmd_privileged_peasants
from handlers.reputation import (
    cmd_based,
    cmd_cunt,
    cmd_edictoftengri,
    cmd_howbasedami,
    cmd_howbasediseveryone,
    cmd_retag_user,
    cmd_shieldnull,
)
from handlers.stfu import (
    cmd_grant_stfu,
    cmd_revoke_stfu,
    cmd_save_grants,
    cmd_stfu,
    cmd_unstfu,
)
from handlers.stfuproof import cmd_stfuproof
from handlers.tengriguideme import _handle_help_callback, cmd_start, cmd_tengriguideme
from handlers.translate import cmd_translate

__all__ = [
    "cmd_mock",
    "cmd_unmock",
    "cmd_translate",
    "cmd_unstfu",
    "cmd_stfu",
    "cmd_grant_stfu",
    "cmd_revoke_stfu",
    "cmd_save_grants",
    "cmd_start",
    "cmd_tengriguideme",
    "_handle_help_callback",
    "cmd_privileged_peasants",
    "cmd_stfuproof",
    "cmd_doxxed",
    "cmd_doxx",
    "cmd_revoke_doxx",
    "cmd_fool",
    "cmd_unfool",
    "cmd_exile",
    "cmd_based",
    "cmd_cunt",
    "cmd_howbasedami",
    "cmd_howbasediseveryone",
    "cmd_edictoftengri",
    "cmd_redeem",
    "cmd_retag_user",
    "cmd_shieldnull",
]
