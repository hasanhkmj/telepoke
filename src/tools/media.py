import os
from typing import Union, Optional
from ..client import client
from ..cache import get_or_fetch_entity
from ..utils import log_and_format_error
from telethon import functions

async def send_file(chat_id: Union[int, str], file_path: str, caption: str = "") -> str:
    """
    Send a file (photo, document, video) to a chat.
    Args:
        chat_id: ID or username.
        file_path: Absolute path to the file.
        caption: Optional caption.
    """
    try:
        if not os.path.isfile(file_path):
             return f"File not found: {file_path}"
             
        entity = await get_or_fetch_entity(chat_id)
        await client.send_file(entity, file_path, caption=caption)
        return f"File sent to {chat_id}."
    except Exception as e:
        return log_and_format_error("send_file", e, chat_id=chat_id)

async def send_voice_note(chat_id: Union[int, str], file_path: str, caption: str = "") -> str:
    """
    Send an audio file as a voice note.
    Args:
        chat_id: ID or username.
        file_path: Absolute path to the audio file (ogg, mp3, etc).
    """
    try:
        if not os.path.isfile(file_path):
             return f"File not found: {file_path}"
             
        entity = await get_or_fetch_entity(chat_id)
        await client.send_file(entity, file_path, caption=caption, voice_note=True)
        return f"Voice note sent to {chat_id}."
    except Exception as e:
        return log_and_format_error("send_voice_note", e, chat_id=chat_id)

async def download_media(chat_id: Union[int, str], message_id: int, save_path: str) -> str:
    """
    Download media from a specific message.
    Args:
        chat_id: ID or username.
        message_id: ID of the message containing media.
        save_path: Directory or full path to save the file.
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        message = await client.get_messages(entity, ids=message_id)
        
        if not message or not message.media:
             return "No media found in this message."
             
        path = await client.download_media(message, file=save_path)
        return f"Media saved to: {path}"
    except Exception as e:
        return log_and_format_error("download_media", e, chat_id=chat_id)
