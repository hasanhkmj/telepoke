import os
import logging
import httpx
from telethon import events
from dotenv import load_dotenv

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

async def handle_new_message(event):
    """
    Event handler for new incoming messages.
    """
    try:
        # Extra safety check for incoming
        if event.out:
            return

        message = event.message
        sender = await event.get_sender()
        chat = await event.get_chat()
        
        sender_name = "Unknown"
        if sender:
            # Telethon entities have different name attributes
            sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'Unknown')
            if getattr(sender, 'last_name', None):
                sender_name += f" {sender.last_name}"
        
        chat_title = getattr(chat, 'title', 'Private Chat')
        
        logger.debug(f"Processing message from {sender_name} in {chat_title}")

        # Construct payload with clear identifier
        header = f"📩 [TELEGRAM MESSAGE]\nFrom: {sender_name}\nChat: {chat_title} (ID: {chat.id})"
        content = message.text or "[Media/Non-text message]"
        
        full_text = f"{header}\n\n{content}"

        data = {
            "message": full_text,
            "sender": sender_name,
            "chat_id": chat.id,
            "timestamp": message.date.isoformat() if message.date else ""
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
