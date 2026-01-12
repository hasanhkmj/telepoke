from typing import Union, Optional
from ..client import client
from ..cache import (
    get_or_fetch_entity, 
    get_cached_dialogs, 
    set_cached_dialogs, 
    LIST_TTL
)
from ..utils import log_and_format_error
import time
from telethon import functions
from telethon.tl.types import Chat, Channel

async def get_chats(page: int = 1, page_size: int = 20) -> str:
    """
    Get a paginated list of chats.
    Args:
        page: Page number (1-indexed).
        page_size: Number of chats per page.
    """
    try:
        # Determine strict requirements
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        # Check cache validity and coverage
        cached_data = get_cached_dialogs(end_index)
        
        if cached_data:
             dialogs = cached_data
        else:
            # Cache miss or partial cache
            limit = max(100, end_index + 20)
            dialogs = await client.get_dialogs(limit=limit)
            set_cached_dialogs(dialogs)

        # Slice
        chats = dialogs[start_index:end_index]
        
        if not chats and start_index >= len(dialogs):
             return "Page out of range."

        lines = []
        for dialog in chats:
            entity = dialog.entity
            chat_id = entity.id
            title = getattr(entity, "title", None) or getattr(entity, "first_name", "Unknown")
            lines.append(f"Chat ID: {chat_id}, Title: {title}, Unread: {dialog.unread_count}")
        
        if not lines:
             return "No chats found."
             
        return "\n".join(lines)
    except Exception as e:
        return log_and_format_error("get_chats", e)

async def get_chat(chat_id: Union[int, str]) -> str:
    """
    Get details about a specific chat.
    Args:
        chat_id: ID or username.
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        
        title = getattr(entity, "title", None) or getattr(entity, "first_name", "Unknown")
        chat_type = "User"
        if isinstance(entity, Chat): chat_type = "Group"
        elif isinstance(entity, Channel): chat_type = "Channel/Supergroup"
        
        username = getattr(entity, "username", "None")
        
        return f"ID: {entity.id}\nTitle: {title}\nType: {chat_type}\nUsername: {username}"
    except Exception as e:
        return log_and_format_error("get_chat", e, chat_id=chat_id)

async def join_chat_by_link(link: str) -> str:
    """
    Join a chat by invite link.
    """
    try:
        if "/" in link:
            hash_part = link.split("/")[-1]
            if hash_part.startswith("+"):
                hash_part = hash_part[1:]
        else:
            hash_part = link

        result = await client(functions.messages.ImportChatInviteRequest(hash=hash_part))
        if result and hasattr(result, "chats") and result.chats:
            chat_title = getattr(result.chats[0], "title", "Unknown Chat")
            return f"Successfully joined chat: {chat_title}"
        return "Joined chat via invite hash."
    except Exception as e:
        return log_and_format_error("join_chat_by_link", e)

async def leave_chat(chat_id: Union[int, str]) -> str:
    """
    Leave a chat or channel.
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        
        if isinstance(entity, Channel):
             await client(functions.channels.LeaveChannelRequest(entity))
        else:
             await client(functions.messages.DeleteChatUserRequest(chat_id=chat_id, user_id="me"))
             
        return f"Left chat {chat_id}."
    except Exception as e:
        return log_and_format_error("leave_chat", e, chat_id=chat_id)

async def get_unread_chats(limit: int = 10) -> str:
    """
    Get a list of chats with unread messages.
    Args:
        limit: Maximum number of unread chats to return (default: 10).
    """
    try:
        # Fetch dialogs (chats)
        # We fetch a bit more than limit to ensure we find enough unread ones if they are scattered
        dialogs = await client.get_dialogs(limit=limit * 5)
        
        unread_chats = []
        for d in dialogs:
            # Check for unread count or unread mark (manual)
            # Safely check for unread_mark as it might not be exposed on all Dialog wrappers
            # We check both the wrapper 'd' and the underlying 'd.dialog' if possible
            is_unread = d.unread_count > 0
            
            if not is_unread:
                is_unread = getattr(d, 'unread_mark', False)
                
            if not is_unread and hasattr(d, 'dialog'):
                is_unread = getattr(d.dialog, 'unread_mark', False)

            if is_unread:
                entity = d.entity
                chat_title = getattr(entity, "title", None) or getattr(entity, "first_name", "Unknown")
                unread_chats.append(f"Chat: {chat_title} (ID: {entity.id}) - Unread: {d.unread_count}")
                
                if len(unread_chats) >= limit:
                    break
        
        if not unread_chats:
            return "No unread chats found."
            
        return "\n".join(unread_chats)

    except Exception as e:
        return log_and_format_error("get_unread_chats", e)

async def mute_chat(chat_id: Union[int, str], duration_seconds: int = 0) -> str:
    """
    Mute a chat or channel.
    Args:
        chat_id: ID or username.
        duration_seconds: Duration in seconds. 0 means forever (default).
    """
    try:
        from telethon.tl.types import InputNotifyPeer, PeerNotifySettings
        import datetime
        
        entity = await get_or_fetch_entity(chat_id)
        
        # Calculate mute_until
        if duration_seconds > 0:
            mute_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=duration_seconds)
        else:
            # Forever (2038)
            mute_until = datetime.datetime(2038, 1, 1, tzinfo=datetime.timezone.utc)

        # Update settings
        # We assume 'peer' needs to be wrapped properly, often client.get_input_entity helps
        # But UpdateNotifySettingsRequest takes 'peer' as InputNotifyPeer
        
        # Telethon's convenience method might be easier but let's use Request for control
        # Actually client(...) takes InputPeer usually. 
        # But UpdateNotifySettingsRequest takes 'peer' of type InputNotifyPeer.
        
        # Let's try to construct InputNotifyPeer
        # InputNotifyPeer(peer) where peer is InputPeer
        
        input_peer = await client.get_input_entity(entity)
        
        await client(functions.account.UpdateNotifySettingsRequest(
            peer=InputNotifyPeer(input_peer),
            settings=PeerNotifySettings(
                show_previews=False, # Optional, strictly we just want to mute
                # silent=True, # usage depends on context (e.g. sending silent message)
                mute_until=mute_until
            )
        ))
        
        # Update cache immediately so it reflects
        from ..cache import set_cached_mute_status
        set_cached_mute_status(entity.id, True)

        duration_str = "forever" if duration_seconds == 0 else f"for {duration_seconds} seconds"
        return f"Muted chat {chat_id} {duration_str}."
        
    except Exception as e:
        return log_and_format_error("mute_chat", e, chat_id=chat_id)

async def unmute_chat(chat_id: Union[int, str]) -> str:
    """
    Unmute a chat or channel.
    Args:
        chat_id: ID or username.
    """
    try:
        from telethon.tl.types import InputNotifyPeer, PeerNotifySettings
        import datetime
        
        entity = await get_or_fetch_entity(chat_id)
        
        # 0 timestamp usually means unmuted in Telegram
        mute_until = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
        
        input_peer = await client.get_input_entity(entity)
        
        await client(functions.account.UpdateNotifySettingsRequest(
            peer=InputNotifyPeer(input_peer),
            settings=PeerNotifySettings(
                mute_until=mute_until
            )
        ))
        
        # Update cache
        from ..cache import set_cached_mute_status
        set_cached_mute_status(entity.id, False)
        
        return f"Unmuted chat {chat_id}."
        
    except Exception as e:
        return log_and_format_error("unmute_chat", e, chat_id=chat_id)
