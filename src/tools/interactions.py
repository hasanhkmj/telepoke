from typing import Union, Optional, List
from ..client import client
from ..cache import get_or_fetch_entity
from ..utils import log_and_format_error
from telethon import functions, types

async def react_to_message(chat_id: Union[int, str], message_id: int, emoji: str) -> str:
    """
    React to a message with an emoji.
    Args:
        chat_id: ID or username.
        message_id: ID of the message.
        emoji: Emoji string (e.g. "👍", "❤️").
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        
        # Use raw SendReactionRequest since helpers are missing/version-dependent
        await client(functions.messages.SendReactionRequest(
            peer=entity,
            msg_id=message_id,
            reaction=[types.ReactionEmoji(emoticon=emoji)]
        ))
        
        return f"Reacted {emoji} to message {message_id}."
    except Exception as e:
        return log_and_format_error("react_to_message", e, chat_id=chat_id)

async def mark_read(chat_id: Union[int, str]) -> str:
    """
    Mark a chat as read (clears unread count).
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        # send_read_acknowledge exists in client methods
        await client.send_read_acknowledge(entity)
        return f"Marked chat {chat_id} as read."
    except Exception as e:
        return log_and_format_error("mark_read", e)

async def send_typing_action(chat_id: Union[int, str], action: str = "typing") -> str:
    """
    Send a typing/uploading action.
    Args:
        chat_id: ID or username.
        action: 'typing', 'record_audio', 'upload_photo', 'upload_document', 'geo', 'contact'.
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        
        # Map simple strings to Telethon typing actions
        action_map = {
            "typing": types.SendMessageTypingAction(),
            "record_audio": types.SendMessageRecordAudioAction(),
            "upload_photo": types.SendMessageUploadPhotoAction(progress=0),
            "upload_document": types.SendMessageUploadDocumentAction(progress=0),
            "geo": types.SendMessageGeoLocationAction(),
            "contact": types.SendMessageChooseContactAction()
        }
        
        target_action = action_map.get(action.lower(), types.SendMessageTypingAction())
        
        # Use raw SetTypingRequest
        await client(functions.messages.SetTypingRequest(
            peer=entity,
            action=target_action
        ))
        
        return f"Sent action '{action}' to chat {chat_id}."
    except Exception as e:
        return log_and_format_error("send_typing_action", e)

async def get_message_context(chat_id: Union[int, str], message_id: int, count: int = 5) -> str:
    """
    Get context (messages before/after) for a specific message.
    Args:
        chat_id: ID or username.
        message_id: ID of the center message.
        count: Number of messages *each side* to retrieve.
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        
        history_before = await client.get_messages(entity, limit=count, max_id=message_id)
        history_after = await client.get_messages(entity, limit=count, min_id=message_id, reverse=True)
        center = await client.get_messages(entity, ids=message_id)
        
        formatted = []
        
        # Prepend before (reverse to make it chronological)
        for m in reversed(history_before):
             formatted.append(f"[{m.id}] {m.message or '<media>'}")
             
        if center:
             formatted.append(f"-> [{center.id}] {center.message or '<media>'} (TARGET)")
             
        for m in history_after:
             formatted.append(f"[{m.id}] {m.message or '<media>'}")
             
        return "\n".join(formatted)
    except Exception as e:
        return log_and_format_error("get_message_context", e)
