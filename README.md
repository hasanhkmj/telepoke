# Telepoke (Telegram FastMCP Server)

A FastMCP server implementation that provides Telegram functionality (messaging, contacts, admin tools) to MCP clients.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) (for dependency management)
- Python 3.10+
- Telegram API ID and Hash (from https://my.telegram.org)

## Setup

1. **Clone/Navigate to directory:**
   ```bash
   cd telepoke
   ```

2. **Environment Configuration:**
   Create a `.env` file (if not already present) with your Telegram credentials:
   ```env
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_SESSION_STRING=your_session_string  # Optional: for existing sessions
   MCP_API_KEY=your_secure_key # Optional: to secure the MCP server
   ```

3. **Install Dependencies:**
   ```bash
   uv sync
   ```

## Running the Server

Start the MCP server using `uv`:

```bash
uv run -m src.server
```
Or directly:
```bash
python src/server.py
```

The server will start on `http://0.0.0.0:8000`.

## Available Tools

- **Messaging**: `send_message`, `get_messages`, `list_inline_buttons`, `press_inline_button`
- **Chats**: `get_chats`, `get_chat`, `join_chat_by_link`, `leave_chat`
- **Contacts**: `list_contacts`, `search_contacts`
- **Admin**: `promote_admin`, `ban_user`, `create_group`
- **Profile**: `get_me`, `update_profile`
- **Interactions**: `react_to_message`, `mark_read`, `send_typing_action`
- **Media**: `send_file`, `send_voice_note`, `download_media`

## Architecture

- Built with `fastmcp` and `telethon`.
- Uses a lazy-loaded singleton Telegram client (`src/client.py`) to handle authentication and connection.
