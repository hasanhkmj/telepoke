from fastmcp import FastMCP, Context
from typing import Union, Optional
from ..client import client
from ..cache import get_or_fetch_entity, get_cached_messages, set_cached_messages, MESSAGE_TTL
from ..utils import get_sender_name, log_and_format_error
from telethon import functions

# We will attach these to the MCP instance in server.py, 
# but for modularity, we define the functions here.
# FastMCP doesn't strictly require decorators if we register manually, 
# but using a local FastMCP instance for decorators and then mounting might be cleaner
# OR we just define async functions and import them.
# The user wants "FastMCP", which usually implies using the decorators.
# Let's create a blueprint-like structure or just simple functions that we decorate in server.py?
# FastMCP doesn't have "Blueprints" yet. 
# Best practice: Create a module-level mcp instance? No, we want one server.
# We will define the functions and importing them in server.py to register them using mcp.tool().
# Actually, FastMCP supports mounting tools. 
# But to keep it simple and closer to the requested example:
# We can define `mcp` in `server.py` and import it here? Circular import risk.
# Better: Define functions, and in server.py: `mcp.tool()(imported_function)`.

async def get_messages(chat_id: Union[int, str], page: int = 1, page_size: int = 20) -> str:
    """
    Get paginated messages from a specific chat.
    Args:
        chat_id: The ID or username of the chat.
        page: Page number (1-indexed).
        page_size: Number of messages per page.
    """
    try:
        # Optimization: Check short-term message cache
        cache_key = f"{chat_id}_{page}_{page_size}"
        cached_content = get_cached_messages(cache_key)
        if cached_content:
            return cached_content

        # Optimization: Use smart entity cache
        entity = await get_or_fetch_entity(chat_id)
        
        offset = (page - 1) * page_size
        messages = await client.get_messages(entity, limit=page_size, add_offset=offset)
        if not messages:
            return "No messages found for this page."
        lines = []
        for msg in messages:
            sender_name = get_sender_name(msg)
            reply_info = ""
            if msg.reply_to and msg.reply_to.reply_to_msg_id:
                reply_info = f" | reply to {msg.reply_to.reply_to_msg_id}"
            lines.append(
                f"ID: {msg.id} | {sender_name} | Date: {msg.date}{reply_info} | Message: {msg.message}"
            )
        
        result = "\n".join(lines)
        # Cache the result
        set_cached_messages(cache_key, result)
        return result
    except Exception as e:
        return log_and_format_error("get_messages", e, chat_id=chat_id)

async def send_message(chat_id: Union[int, str], text: str) -> str:
    """
    Send a simplified text message.
    Args:
        chat_id: The ID or username of the chat.
        text: The message content.
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        await client.send_message(entity, text)
        return f"Message sent to {chat_id}."
    except Exception as e:
        return log_and_format_error("send_message", e, chat_id=chat_id)

async def list_inline_buttons(chat_id: Union[int, str], message_id: int) -> str:
    """
    List inline buttons for a specific message.
    Args:
        chat_id: The ID or username of the chat.
        message_id: The ID of the message with buttons.
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        message = await client.get_messages(entity, ids=message_id)
        
        if not message or not message.buttons:
            return "No buttons found."
            
        rows = []
        for i, row in enumerate(message.buttons):
            buttons = []
            for j, btn in enumerate(row):
                buttons.append(f"[{i},{j}] {btn.text}")
            rows.append(" | ".join(buttons))
            
        return "Buttons:\n" + "\n".join(rows)
    except Exception as e:
        return log_and_format_error("list_inline_buttons", e, chat_id=chat_id)

async def press_inline_button(chat_id: Union[int, str], message_id: int, row: int, col: int) -> str:
    """
    Press an inline button.
    Args:
        chat_id: The ID or username.
        message_id: The ID of the message.
        row: Row index (0-based).
        col: Column index (0-based).
    """
    try:
        entity = await get_or_fetch_entity(chat_id)
        message = await client.get_messages(entity, ids=message_id)
        
        if not message or not message.buttons:
            return "Message has no buttons."
            
        try:
            btn = message.buttons[row][col]
        except IndexError:
            return "Invalid button coordinates."
            
        await message.click(i=row, j=col)
        return f"Clicked button: {btn.text}"
    except Exception as e:
        return log_and_format_error("press_inline_button", e, chat_id=chat_id)
