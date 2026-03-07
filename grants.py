"""STFU grant persistence: load/save JSON."""
import json
import logging
import os
import time

logger = logging.getLogger(__name__)


def _load_stfu_grants(path: str) -> dict:
    """Load stfu_grants from JSON. Returns dict (chat_id, user_id) -> {granted_by, expires_at}."""
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load stfu_grants from %s: %s. Starting with empty grants.", path, e)
        return {}
    if not isinstance(raw, list):
        logger.warning("stfu_grants file %s has invalid format (expected list). Starting with empty grants.", path)
        return {}
    now = time.time()
    grants: dict[tuple[int, int], dict] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            cid = int(item["chat_id"])
            uid = int(item["user_id"])
            granted_by = int(item.get("granted_by", 0))
            expires_at = float(item.get("expires_at", 0))
        except (KeyError, TypeError, ValueError):
            continue
        if expires_at > 0 and expires_at < now:
            continue
        grants[(cid, uid)] = {"granted_by": granted_by, "expires_at": expires_at}
    return grants


def _save_stfu_grants(path: str, grants: dict) -> None:
    """Write stfu_grants to JSON."""
    if not path:
        return
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        payload = [
            {"chat_id": cid, "user_id": uid, "granted_by": g["granted_by"], "expires_at": g["expires_at"]}
            for (cid, uid), g in grants.items()
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        logger.warning("Failed to save stfu_grants to %s: %s", path, e)
