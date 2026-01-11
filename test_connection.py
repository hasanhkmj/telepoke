import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_connection")

async def test_telegram_connection():
    load_dotenv()
    
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_string = os.getenv("TELEGRAM_SESSION_STRING")
    
    if not api_id or not api_hash:
        logger.error("❌ Missing TELEGRAM_API_ID or TELEGRAM_API_HASH")
        return

    logger.info(f"Using API_ID: {api_id}")
    
    client = None
    try:
        print("1. Initializing Client...")
        if session_string:
            print("   Using StringSession")
            client = TelegramClient(StringSession(session_string), int(api_id), api_hash)
        else:
            print("   Using File Session (telegram_session)")
            client = TelegramClient("telegram_session", int(api_id), api_hash)
            
        print("2. Connecting...")
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Client is NOT authorized. Session might be invalid or expired.")
        else:
            me = await client.get_me()
            print(f"✅ Connected successfully as: {me.first_name} (ID: {me.id})")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            await client.disconnect()
            print("3. Disconnected.")

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())
