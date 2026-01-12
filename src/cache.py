import time
import logging
from typing import Optional, Any, Dict, Tuple
from .client import client

logger = logging.getLogger("telegram_cache")

# Caching Configuration
LIST_TTL = 60           # 1 minute for volatile lists (chats, contacts)
ENTITY_TTL = 300        # 5 minutes for stable entities (User/Chat)
MESSAGE_TTL = 10        # 10 seconds for message lists (debounce)
MUTE_TTL = 30           # 30 seconds for mute status (fast reaction)

# In-memory stores
_DIALOGS_CACHE: Dict[str, Any] = {"data": None, "timestamp": 0}
_CONTACTS_CACHE: Dict[str, Any] = {"data": None, "timestamp": 0}
_ENTITY_CACHE: Dict[int, Tuple[Any, float]] = {} 
_MESSAGES_CACHE: Dict[str, Tuple[str, float]] = {}
_ME_CACHE: Dict[str, Any] = {"data": None, "timestamp": 0}

# --- Entity Caching ---

def get_cached_me() -> Optional[Any]:
    """Helper to get cached 'me'."""
    if _ME_CACHE["data"] and (time.time() - _ME_CACHE["timestamp"] < ENTITY_TTL):
        return _ME_CACHE["data"]
    return None

def set_cached_me(me: Any) -> None:
    _ME_CACHE["data"] = me
    _ME_CACHE["timestamp"] = time.time()

def get_cached_entity(entity_id: int) -> Optional[Any]:
    """Helper to get entity from cache or None."""
    if entity_id in _ENTITY_CACHE:
        data, timestamp = _ENTITY_CACHE[entity_id]
        if time.time() - timestamp < ENTITY_TTL:
            return data
    return None

def cache_entity(entity_id: int, entity: Any) -> None:
    """Helper to cache entity."""
    current_time = time.time()
    _ENTITY_CACHE[entity_id] = (entity, current_time)
    if hasattr(entity, 'id'):
        _ENTITY_CACHE[entity.id] = (entity, current_time)

async def get_or_fetch_entity(entity_id: int, force_refresh: bool = False) -> Any:
    """
    Smart helper to get an entity.
    Checks cache first (unless force_refresh is True).
    If missing or expired, fetches from Telegram and caches it.
    """
    if not force_refresh:
        entity = get_cached_entity(entity_id)
        if entity:
            return entity

    logger.debug(f"Fetching fresh entity for ID {entity_id}...")
    try:
        entity = await client.get_entity(entity_id)
        cache_entity(entity_id, entity)
        return entity
    except Exception as e:
        logger.error(f"Failed to fetch entity {entity_id}: {e}")
        raise e

# --- List Caching ---

def get_cached_dialogs(limit: int) -> Optional[list]:
    current_time = time.time()
    cached_data = _DIALOGS_CACHE["data"]
    timestamp = _DIALOGS_CACHE["timestamp"]
    
    if cached_data and (current_time - timestamp < LIST_TTL):
        # We have a valid cache. 
        # CAUTION: If user requests 200 items but we only cached top 20, 
        # this simple check might need refinement. For now, we assume
        # the list header is usually consistent.
        if len(cached_data) >= limit:
            return cached_data[:limit]
    return None

def set_cached_dialogs(dialogs: list) -> None:
    _DIALOGS_CACHE["data"] = dialogs
    _DIALOGS_CACHE["timestamp"] = time.time()

def get_cached_contacts() -> Optional[list]:
    current_time = time.time()
    if _CONTACTS_CACHE["data"] and (current_time - _CONTACTS_CACHE["timestamp"] < LIST_TTL):
        return _CONTACTS_CACHE["data"]
    return None

def set_cached_contacts(contacts: list) -> None:
    _CONTACTS_CACHE["data"] = contacts
    _CONTACTS_CACHE["timestamp"] = time.time()

# --- Message Caching ---

def get_cached_messages(key: str) -> Optional[str]:
    if key in _MESSAGES_CACHE:
        data, timestamp = _MESSAGES_CACHE[key]
        if time.time() - timestamp < MESSAGE_TTL:
            return data
    return None

def set_cached_messages(key: str, content: str) -> None:
    _MESSAGES_CACHE[key] = (content, time.time())

# --- Mute Status Caching ---

_MUTE_STATUS_CACHE: Dict[int, Tuple[bool, float]] = {}

def get_cached_mute_status(peer_id: int) -> Optional[bool]:
    """
    Returns cached mute status (True/False) if valid, else None.
    """
    if peer_id in _MUTE_STATUS_CACHE:
        is_muted, timestamp = _MUTE_STATUS_CACHE[peer_id]
        if time.time() - timestamp < MUTE_TTL:
            return is_muted
    return None

def set_cached_mute_status(peer_id: int, is_muted: bool) -> None:
    _MUTE_STATUS_CACHE[peer_id] = (is_muted, time.time())
