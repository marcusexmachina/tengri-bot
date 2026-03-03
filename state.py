"""Persistence for fool_marked, doxx_grants, doxx_hashes."""
import json
import logging
import os

logger = logging.getLogger(__name__)


def _state_path(base: str, name: str) -> str:
    """Derive path from STATE_FILE dir, e.g. /app/data/stfu_grants.json -> /app/data/fool_marked.json."""
    state_file = os.getenv("STATE_FILE", "stfu_grants.json")
    parent = os.path.dirname(os.path.abspath(state_file))
    return os.path.join(parent, name) if parent else name


def _load_fool_marked() -> set[int]:
    """Load marked user IDs. Returns set of user_id."""
    path = _state_path("STATE_FILE", "fool_marked.json")
    if not path or not os.path.isfile(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load fool_marked from %s: %s", path, e)
        return set()
    if not isinstance(raw, list):
        return set()
    return {int(x) for x in raw if isinstance(x, (int, str)) and str(x).isdigit()}


def _save_fool_marked(user_ids: set[int]) -> None:
    path = _state_path("STATE_FILE", "fool_marked.json")
    if not path:
        return
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(user_ids), f, indent=2)
    except OSError as e:
        logger.warning("Failed to save fool_marked to %s: %s", path, e)


def _load_doxx_grants() -> dict:
    """Returns {(chat_id, user_id): {granted_by, expires_at}}."""
    path = _state_path("STATE_FILE", "doxx_grants.json")
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load doxx_grants from %s: %s", path, e)
        return {}
    if not isinstance(raw, list):
        return {}
    import time
    now = time.time()
    grants = {}
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
        if expires_at > now:
            grants[(cid, uid)] = {"granted_by": granted_by, "expires_at": expires_at}
    return grants


def _save_doxx_grants(grants: dict) -> None:
    path = _state_path("STATE_FILE", "doxx_grants.json")
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
        logger.warning("Failed to save doxx_grants to %s: %s", path, e)


def _load_doxx_hashes() -> set[str]:
    """Load stored content hashes. Returns set of hex strings."""
    path = _state_path("STATE_FILE", "doxx_hashes.json")
    if not path or not os.path.isfile(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load doxx_hashes from %s: %s", path, e)
        return set()
    if isinstance(raw, list):
        return {str(h) for h in raw if isinstance(h, str) and len(h) == 64}
    if isinstance(raw, dict) and "hashes" in raw:
        return {str(h) for h in raw["hashes"] if isinstance(h, str) and len(h) == 64}
    return set()


def _save_doxx_hashes(hashes: set[str]) -> None:
    path = _state_path("STATE_FILE", "doxx_hashes.json")
    if not path:
        return
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(hashes), f, indent=2)
    except OSError as e:
        logger.warning("Failed to save doxx_hashes to %s: %s", path, e)
