# src/server.py
import os
import asyncio
from fastmcp import FastMCP
from dotenv import load_dotenv
from .tools import messages, chats, contacts, admin, profile, media, interactions
from .client import client
from .forwarder import setup_forwarder


# Load Config
load_dotenv()

# Initialize FastMCP with lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def server_lifespan(server: FastMCP):
    # Startup logic
    # print("Connecting Telegram Client for Forwarder...")
    await client.connect()
    setup_forwarder(client)
    # print("Telegram Forwarder Connected.")
    yield
    # Shutdown logic
    await client.disconnect()

# Authentication
try:
    from fastmcp.server.auth import StaticTokenVerifier
except ImportError:
    StaticTokenVerifier = None

# Get API Key from environment
api_key = os.getenv("MCP_API_KEY")

# Configure auth if key is present
auth_provider = None
if api_key and StaticTokenVerifier:
    # StaticTokenVerifier expects a dict of {token: user_info_dict}
    # We MUST provide 'client_id' as it is required by AccessToken
    auth_provider = StaticTokenVerifier(tokens={
        api_key: {
            "username": "admin", # Changed from 'user' to 'username' just in case, though verify_token uses 'client_id'
            "client_id": "telegram-mcp-server", 
            "scopes": ["admin"]
        }
    })

mcp = FastMCP("Telegram", lifespan=server_lifespan, auth=auth_provider)

# Register Tools

# Interactive & Media Tools (Phase 2)
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
    host = "0.0.0.0"
    port = 8000
    
    print(f"Starting Telegram FastMCP Server on {host}:{port}")
    
    # Initialize the Telegram Client in the background
    # We can't await here in top-level generally, but we can hook into Startup or run parallel
    # Ideally, FastMCP exposes a way to run async startup tasks.
    # Since we are using standard mcp.run, it blocks.
    # We will simply kick off the client connection in the background loop that FastMCP uses?
    # No, we need to ensure it runs.
    
    # We can define an on_startup hook if FastMCP supports it.
    # Current FastMCP version might not have a decorator for it in the README, 
    # but Uvicorn (underlying) does.
    # Safe approach: Just like client calls, we can rely on lazy load, 
    # BUT forwarder needs to be active.
    
    # Let's inspect if `client` can be started eagerly before mcp.run()
    # No, because that requires an async loop.
    
    # Workaround for keeping it simple:
    # We'll use the client's loop if it exists, or create one?
    # The clean way in FastMCP (which is FastAPI essentially) is:
    


    mcp.run(transport="http", host=host, port=port, stateless_http=True)
