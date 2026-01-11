from typing import Union, Optional
from ..client import client
from ..cache import (
    get_or_fetch_entity,
    get_cached_contacts,
    set_cached_contacts,
    get_cached_dialogs,
    set_cached_dialogs,
    cache_entity
)
from ..utils import log_and_format_error, format_entity
from telethon import functions

async def list_contacts() -> str:
    """
    List all contacts.
    """
    try:
        cached_contacts = get_cached_contacts()
        if cached_contacts:
            contacts = cached_contacts
        else:
            contacts = await client(functions.contacts.GetContactsRequest(hash=0))
            # Cache individual users from the contacts list for entity lookups
            for user in contacts.users:
                cache_entity(user.id, user)
            set_cached_contacts(contacts)

        if not contacts.users:
            return "No contacts found."

        lines = []
        for user in contacts.users:
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            lines.append(f"ID: {user.id} | Name: {name} | Phone: {user.phone or 'N/A'}")
        
        return "\n".join(lines)
    except Exception as e:
        return log_and_format_error("list_contacts", e)

async def search_contacts(query: str, limit: int = 10) -> str:
    """
    Search for contacts or users on Telegram.
    Checks local contacts cache first.
    """
    try:
        # 1. Search local cache first
        local_results = []
        cached_contacts = get_cached_contacts()
        if cached_contacts:
            q_lower = query.lower()
            for user in cached_contacts.users:
                name = f"{user.first_name or ''} {user.last_name or ''}".strip().lower()
                username = (user.username or "").lower()
                if q_lower in name or q_lower in username:
                     local_results.append(format_entity(user))
        
        if local_results:
             return f"Found in Contacts:\n" + "\n".join([str(r) for r in local_results[:limit]])

        # 2. Global Search
        result = await client(functions.contacts.SearchRequest(
            q=query, limit=limit
        ))
        
        lines = []
        for user in result.users:
             lines.append(str(format_entity(user)))
             cache_entity(user.id, user)
             
        for chat in result.chats:
             lines.append(str(format_entity(chat)))
             cache_entity(chat.id, chat)

        return "\n".join(lines) if lines else "No results found."
    except Exception as e:
        return log_and_format_error("search_contacts", e)

async def get_direct_chat_by_contact(contact_id: Union[int, str]) -> str:
    """
    Find the direct chat (dialog) with a specific contact.
    """
    try:
        # Resolve contact first
        contact = await get_or_fetch_entity(contact_id)
        target_id = contact.id
        
        # Check cached dialogs
        cached_dialogs = get_cached_dialogs(limit=100) # Check recent
        if cached_dialogs:
            for d in cached_dialogs:
                if d.entity.id == target_id:
                     return f"Found Cached Dialog | ID: {d.entity.id} | Title: {getattr(d.entity, 'first_name', 'Unknown')}"
        
        # If not in cache, we technically should fetch fresh dialogs or just try to get_entity
        # returning the entity info is enough to start a chat usually
        return f"Chat Info: ID={contact.id}. You can use 'get_messages' with this ID."
    except Exception as e:
        return log_and_format_error("get_direct_chat_by_contact", e)
