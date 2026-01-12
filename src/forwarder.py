import os
import logging
import httpx
import time
import asyncio
from telethon import events, functions
from dotenv import load_dotenv
from telethon.tl.types import PeerNotifySettings
from .cache import get_cached_mute_status, set_cached_mute_status

load_dotenv()
logger = logging.getLogger("telegram_forwarder")

# Configuration
WEBHOOK_URL = "https://poke.com/api/v1/inbound-sms/webhook"
POKE_API_KEY = os.getenv("POKE_API_KEY")

async def forward_to_poke(message_data: dict):
    if not POKE_API_KEY:
        logger.warning("POKE_API_KEY not set. Cannot forward message.")
        return

    target_url = os.getenv("POKE_WEBHOOK_URL", WEBHOOK_URL)
    
    headers = {
        "Authorization": f"Bearer {POKE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use non-blocking async client
    async with httpx.AsyncClient() as http_client:
        try:
            logger.debug(f"Forwarding to {target_url}...")
            response = await http_client.post(
                target_url, 
                json=message_data, 
                headers=headers, 
                timeout=5.0
            )
            if response.is_error:
                logger.error(f"Poke Webhook Error: {response.status_code} - {response.text}")
            else:
                logger.info(f"Forwarded message to Poke (Status: {response.status_code})")
                
        except Exception as e:
            logger.error(f"Failed to forward message to Poke: {e}")

# --- Helper ---

async def is_chat_muted(client, peer):
    """
    Checks if a chat/channel is muted.
    Uses cache to avoid rate limits.
    """
    try:
        if peer.id:
            cached = get_cached_mute_status(peer.id)
            if cached is not None:
                return cached

        # Fetch fresh settings
        # Use GetNotifySettingsRequest as client.get_notify_settings does not exist
        # Add timeout to prevent hanging
        try:
             settings = await asyncio.wait_for(
                 client(functions.account.GetNotifySettingsRequest(peer=peer)),
                 timeout=5.0
             )
        except asyncio.TimeoutError:
             logger.warning(f"Timeout checking mute status for {peer.id}. Assuming NOT muted.")
             return False

        is_muted = False
        if isinstance(settings, PeerNotifySettings):
            logger.debug(f"Notify Settings for {peer.id}: mute_until={settings.mute_until}, silent={getattr(settings, 'silent', 'N/A')}, type={type(settings).__name__}")
            
            # Check 'silent' or 'mute_until'
            # mute_until is a timestamp until which notifications are off.
            # If it is in the future, it is muted.
            if settings.mute_until:
                import datetime
                # mute_until is usually a future timestamp (int or datetime)
                # If int, it's a unix timestamp. If datetime, it's TZ aware.
                # However, Telethon usually returns datetime.datetime
                # But sometimes it sends a large int for "forever".
                
                now = datetime.datetime.now(datetime.timezone.utc)
                
                if isinstance(settings.mute_until, int):
                     # 2147483647 is often used for "Forever"
                     if settings.mute_until > time.time():
                         is_muted = True
                
                elif hasattr(settings.mute_until, 'timestamp'):
                    if settings.mute_until > now:
                        is_muted = True
            
            # settings.silent might be true for channels
            if getattr(settings, 'silent', False):
                is_muted = True
        else:
             logger.debug(f"Notify Settings for {peer.id}: {settings} (Type: {type(settings).__name__})")

        if peer.id:
            set_cached_mute_status(peer.id, is_muted)
            
        return is_muted

    except Exception as e:
        logger.error(f"Error checking mute status: {e}")
        return False

async def handle_new_message(event):
    """
    Event handler for new incoming messages.
    """
    try:
        # Extra safety check for incoming
        if event.out:
            return
            
        logger.debug("Handling incoming message event...")

        message = event.message
        sender = await event.get_sender()
        chat = await event.get_chat()
        
        # --- Mute Check ---
        if await is_chat_muted(event.client, chat):
            logger.debug(f"Skipping message from {getattr(chat, 'title', 'Chat')} (Muted)")
            return
        
        sender_name = "Unknown"
        if sender:
            # Telethon entities have different name attributes
            sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'Unknown')
            if getattr(sender, 'last_name', None):
                sender_name += f" {sender.last_name}"
        
        chat_title = getattr(chat, 'title', 'Private Chat')
        
        # Determine Chat Type
        chat_type = "private"
        if event.is_group:
            chat_type = "group"
            if getattr(chat, 'megagroup', False):
                chat_type = "supergroup"
        elif event.is_channel:
            chat_type = "channel"
            
        logger.debug(f"Processing message from {sender_name} in {chat_title} ({chat_type})")

        # Construct payload with clear identifier
        header = f"📩 [TELEGRAM MESSAGE]\nFrom: {sender_name}\nChat: {chat_title} (ID: {chat.id})\nType: {chat_type.upper()}"
        content = message.text or "[Media/Non-text message]"
        
        full_text = f"{header}\n\n{content}"

        data = {
            "message": full_text,
            "sender": sender_name,
            "chat_id": chat.id,
            "chat_title": chat_title,
            "chat_type": chat_type,
            "timestamp": message.date.isoformat() if message.date else "",
            "message_id": message.id
        }
        
        # Fire forwarding task
        await forward_to_poke(data)
        
    except Exception as e:
        logger.error(f"Error handling incoming message: {e}")

def setup_forwarder(client):
    """
    Registers the forwarder event listener on the client.
    """
    logger.info("Setting up Telegram Forwarder...")
    logger.debug("Registering event handler for NEW MESSAGES (Incoming)...")
    
    # Listen for NewMessage events that are incoming
    # We remove incoming=True from constructor and check inside to be sure we catch EVERYTHING for debug
    client.add_event_handler(handle_new_message, events.NewMessage())
    
    logger.info("Telegram Forwarder is active.")
    logger.debug("Handler registered.")
