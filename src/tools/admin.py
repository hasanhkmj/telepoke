from typing import Union, Optional
from ..client import client
from ..cache import get_or_fetch_entity
from ..utils import log_and_format_error
from telethon import functions
from telethon.tl.types import ChatAdminRights, ChatBannedRights

async def promote_admin(group_id: Union[int, str], user_id: Union[int, str]) -> str:
    """
    Promote a user to admin in a group/channel.
    """
    try:
        chat = await get_or_fetch_entity(group_id)
        user = await get_or_fetch_entity(user_id)

        # Default full rights
        admin_rights = ChatAdminRights(
            change_info=True, post_messages=True, edit_messages=True,
            delete_messages=True, ban_users=True, invite_users=True,
            pin_messages=True, add_admins=False, anonymous=False,
            manage_call=True, other=True
        )

        await client(functions.channels.EditAdminRequest(
            channel=chat, user_id=user, admin_rights=admin_rights, rank="Admin"
        ))
        return f"Promoted {user_id} to admin in {group_id}."
    except Exception as e:
        return log_and_format_error("promote_admin", e, group_id=group_id)

async def ban_user(chat_id: Union[int, str], user_id: Union[int, str]) -> str:
    """
    Ban a user from a group or channel.
    """
    try:
        chat = await get_or_fetch_entity(chat_id)
        user = await get_or_fetch_entity(user_id)

        banned_rights = ChatBannedRights(
            until_date=None, view_messages=True, send_messages=True,
            send_media=True, send_stickers=True, send_gifs=True,
            send_games=True, send_inline=True, embed_links=True,
            send_polls=True, change_info=True, invite_users=True,
            pin_messages=True
        )

        await client(functions.channels.EditBannedRequest(
            channel=chat, participant=user, banned_rights=banned_rights
        ))
        return f"Banned {user_id} from {chat_id}."
    except Exception as e:
        return log_and_format_error("ban_user", e)

async def create_group(title: str, users: list[str]) -> str:
     """
     Create a new basic group with users methods.
     Args:
        title: Group title
        users: List of usernames or IDs to include
     """
     try:
         user_entities = []
         for u in users:
             entity = await get_or_fetch_entity(u)
             user_entities.append(entity)
             
         result = await client(functions.messages.CreateChatRequest(
             users=user_entities,
             title=title
         ))
         return f"Created group '{title}'."
     except Exception as e:
         return log_and_format_error("create_group", e)
