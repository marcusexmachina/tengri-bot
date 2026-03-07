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


def _load_reputation() -> dict:
    """Returns {(chat_id, user_id): points}. Default 100 if not present."""
    path = _state_path("STATE_FILE", "reputation.json")
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load reputation from %s: %s", path, e)
        return {}
    if not isinstance(raw, list):
        return {}
    result = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            cid = int(item["chat_id"])
            uid = int(item["user_id"])
            pts = int(item.get("points", 100))
        except (KeyError, TypeError, ValueError):
            continue
        result[(cid, uid)] = pts
    return result


def _save_reputation(reputation: dict) -> None:
    path = _state_path("STATE_FILE", "reputation.json")
    if not path:
        return
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        payload = [{"chat_id": cid, "user_id": uid, "points": pts} for (cid, uid), pts in reputation.items()]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        logger.warning("Failed to save reputation to %s: %s", path, e)


def _load_reputation_votes() -> list:
    """Returns list of {chat_id, voter_id, target_id, command, at}. Prune old on load."""
    import time
    path = _state_path("STATE_FILE", "reputation_votes.json")
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load reputation_votes from %s: %s", path, e)
        return []
    if not isinstance(raw, list):
        return []
    from config import REPUTATION_COOLDOWN_SECONDS
    now = time.time()
    cutoff = now - REPUTATION_COOLDOWN_SECONDS
    return [v for v in raw if isinstance(v, dict) and v.get("at", 0) > cutoff]


def _save_reputation_votes(votes: list) -> None:
    path = _state_path("STATE_FILE", "reputation_votes.json")
    if not path:
        return
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(votes, f, indent=2)
    except OSError as e:
        logger.warning("Failed to save reputation_votes to %s: %s", path, e)


def _load_acquired_stfu() -> set:
    """Returns set of (chat_id, user_id) who have ever acquired STFU via the flow."""
    path = _state_path("STATE_FILE", "acquired_stfu.json")
    if not path or not os.path.isfile(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load acquired_stfu from %s: %s", path, e)
        return set()
    if not isinstance(raw, list):
        return set()
    result = set()
    for item in raw:
        if isinstance(item, dict):
            try:
                result.add((int(item["chat_id"]), int(item["user_id"])))
            except (KeyError, TypeError, ValueError):
                pass
        elif isinstance(item, list) and len(item) == 2:
            try:
                result.add((int(item[0]), int(item[1])))
            except (TypeError, ValueError):
                pass
    return result


def _save_acquired_stfu(acquired: set) -> None:
    path = _state_path("STATE_FILE", "acquired_stfu.json")
    if not path:
        return
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        payload = [{"chat_id": cid, "user_id": uid} for (cid, uid) in acquired]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        logger.warning("Failed to save acquired_stfu to %s: %s", path, e)


def _load_acquire_pending() -> dict:
    """Load pending STFU password sessions. Drops expired entries. Returns {user_id: entry}."""
    import time
    path = _state_path("STATE_FILE", "acquire_pending.json")
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load acquire_pending from %s: %s", path, e)
        return {}
    if not isinstance(raw, list):
        return {}
    ACQUIRE_PENDING_EXPIRE_SECONDS = 600  # same as handlers.acquire_stfu
    now = time.time()
    cutoff = now - ACQUIRE_PENDING_EXPIRE_SECONDS
    result = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            uid = int(item["user_id"])
            created_at = float(item["created_at"])
            if created_at < cutoff:
                continue
            result[uid] = {
                "password": str(item.get("password", "")),
                "target_group": int(item["target_group"]),
                "created_at": created_at,
                "last_char_message_id": None,
                "target_length": 0,
                "completed": True,
            }
        except (KeyError, TypeError, ValueError):
            continue
    return result


def _load_dm_started_users() -> set[int]:
    """Load user IDs who have completed first /start in DM. Used to show minimal vs full menu."""
    path = _state_path("STATE_FILE", "dm_started_users.json")
    if not path or not os.path.isfile(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load dm_started_users from %s: %s", path, e)
        return set()
    if not isinstance(raw, list):
        return set()
    return {int(x) for x in raw if isinstance(x, (int, str)) and str(x).isdigit()}


def _save_dm_started_users(user_ids: set[int]) -> None:
    path = _state_path("STATE_FILE", "dm_started_users.json")
    if not path:
        return
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(user_ids), f, indent=2)
    except OSError as e:
        logger.warning("Failed to save dm_started_users to %s: %s", path, e)


def _save_acquire_pending(pending: dict) -> None:
    """Persist pending STFU password sessions. Call after add/update/delete."""
    path = _state_path("STATE_FILE", "acquire_pending.json")
    if not path:
        return
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        payload = [
            {
                "user_id": uid,
                "password": entry.get("password", ""),
                "target_group": entry.get("target_group"),
                "created_at": entry.get("created_at", 0),
            }
            for uid, entry in pending.items()
            if isinstance(entry, dict) and entry.get("password") and entry.get("target_group")
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        logger.warning("Failed to save acquire_pending to %s: %s", path, e)
