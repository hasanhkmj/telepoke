import os
import logging
import asyncio
import inspect
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("telegram_client")

class LazyClient:
    """
    A simple lazy wrapper around TelegramClient.
    It initializes the real client only when an attribute is accessed.
    """
    def __init__(self):
        self._client = None

    def _init_client(self):
        if self._client:
            return

        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        session_string = os.getenv("TELEGRAM_SESSION_STRING")
        session_name = os.getenv("TELEGRAM_SESSION_NAME", "telegram_session")
        
        # Ensure we use the current running loop or create a new one if none exists
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if not api_id or not api_hash:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")

        if session_string:
            logger.info("Initializing Telegram Client with StringSession")
            self._client = TelegramClient(StringSession(session_string), int(api_id), api_hash, loop=loop)
        else:
            logger.info(f"Initializing Telegram Client with File Session: {session_name}")
            self._client = TelegramClient(session_name, int(api_id), api_hash, loop=loop)

    def __getattr__(self, name):
        self._init_client()
        attr = getattr(self._client, name)
        
        if callable(attr):
            # Known synchronous methods that should NOT be wrapped
            sync_methods = {'add_event_handler', 'remove_event_handler', 'list_event_handlers', 'disconnect'}
            
            if inspect.iscoroutinefunction(attr) and name not in sync_methods:
                async def wrapper(*args, **kwargs):
                    if not self._client.is_connected():
                        await self._client.connect()
                    return await attr(*args, **kwargs)
                return wrapper
            else:
                # Synchronous method (e.g. add_event_handler)
                # We return it directly. 
                # Note: We don't auto-connect here because we can't await connect().
                # Assumption: Sync methods usually don't need active connection OR caller handles connection.
                return attr
            
        return attr

    async def __call__(self, *args, **kwargs):
        # Allow calling the client instance directly if needed (though rare for Telethon client itself)
        self._init_client()
        if not self._client.is_connected():
            await self._client.connect()
        return await self._client(*args, **kwargs)

# Global exported client instance
client = LazyClient()
