from ..client import client
from ..cache import get_cached_me, set_cached_me
from ..utils import log_and_format_error, format_entity
from telethon import functions

async def get_me() -> str:
    """
    Get information about the current user.
    """
    try:
        cached = get_cached_me()
        if cached:
            return str(format_entity(cached))
            
        me = await client.get_me()
        set_cached_me(me)
        return str(format_entity(me))
    except Exception as e:
        return log_and_format_error("get_me", e)

async def update_profile(first_name: str = None, last_name: str = None, about: str = None) -> str:
    """
    Update profile information.
    """
    try:
        if first_name or last_name:
            await client(functions.account.UpdateProfileRequest(
                first_name=first_name,
                last_name=last_name,
                about=about
            ))
        return "Profile updated."
    except Exception as e:
        return log_and_format_error("update_profile", e)
