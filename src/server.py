# src/server.py
import os
import logging
from fastmcp import FastMCP
from dotenv import load_dotenv
from .tools import messages, chats, contacts, admin, profile, media, interactions
from .client import client
from .auth import TelegramOAuthProvider

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("server").setLevel(logging.DEBUG)
logging.getLogger("telegram_client").setLevel(logging.DEBUG)

logger = logging.getLogger("server")

# Load Config
load_dotenv()

# Initialize FastMCP with lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def server_lifespan(server: FastMCP):
    await client.connect()
    yield
    await client.disconnect()

# Authentication — OAuth 2.1 with legacy static token fallback
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "https://textdonna.com/telegram")
auth_provider = TelegramOAuthProvider(base_url=MCP_BASE_URL)

mcp = FastMCP("Telegram", lifespan=server_lifespan, auth=auth_provider)

# Register Tools

# Interactive & Media Tools
mcp.tool()(media.send_file)
mcp.tool()(media.send_voice_note)
mcp.tool()(media.download_media)

mcp.tool()(interactions.react_to_message)
mcp.tool()(interactions.mark_read)
mcp.tool()(interactions.send_typing_action)
mcp.tool()(interactions.get_message_context)

# Message Tools
mcp.tool()(messages.get_messages)
mcp.tool()(messages.send_message)
mcp.tool()(messages.list_inline_buttons)
mcp.tool()(messages.press_inline_button)

# Chat Tools
mcp.tool()(chats.get_chats)
mcp.tool()(chats.get_chat)
mcp.tool()(chats.join_chat_by_link)
mcp.tool()(chats.leave_chat)
mcp.tool()(chats.get_unread_chats)
mcp.tool()(chats.mute_chat)
mcp.tool()(chats.unmute_chat)

# Contact Tools
mcp.tool()(contacts.list_contacts)
mcp.tool()(contacts.search_contacts)
mcp.tool()(contacts.get_direct_chat_by_contact)

# Admin Tools
mcp.tool()(admin.promote_admin)
mcp.tool()(admin.ban_user)
mcp.tool()(admin.create_group)

# Profile Tools
mcp.tool()(profile.get_me)
mcp.tool()(profile.update_profile)

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 4444
    print(f"Starting Telegram FastMCP Server on {host}:{port}")
    mcp.run(transport="http", host=host, port=port, stateless_http=True)
