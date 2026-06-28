"""Chat/conversation CRUD — create, load, update, delete chats, batch message saving."""

import uuid
from datetime import datetime, timezone
from auth import get_supabase


def load_chats(user_id: str) -> dict:
    """Load all conversations for a user from Supabase, ordered by most recent update."""
    supabase = get_supabase()
    try:
        result = supabase.table("conversations").select(
            "id, title, created_at, updated_at, pinned"
        ).eq("user_id", user_id).order("updated_at", desc=True).execute()
    except Exception:
        return {}
    chats = {}
    for row in result.data or []:
        chats[row["id"]] = {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "pinned": row.get("pinned", False),
            "messages": [],
        }
    return chats


def create_chat(user_id: str, title: str = "New Chat") -> str:
    """Create a new conversation in Supabase and return its UUID."""
    supabase = get_supabase()
    cid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("conversations").insert({
            "id": cid,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "pinned": False,
        }).execute()
    except Exception:
        pass
    return cid


def update_chat(chat_id: str, user_id: str, data: dict) -> bool:
    """Update a conversation's fields (title, pinned, etc.) in Supabase."""
    supabase = get_supabase()
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("conversations").update(data).eq("id", chat_id).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False


def delete_chat(chat_id: str, user_id: str):
    """Delete a conversation and all its messages from Supabase."""
    supabase = get_supabase()
    try:
        supabase.table("messages").delete().eq("conversation_id", chat_id).eq("user_id", user_id).execute()
        supabase.table("conversations").delete().eq("id", chat_id).eq("user_id", user_id).execute()
    except Exception:
        pass


def load_messages(chat_id: str) -> list:
    """Load all messages for a conversation, ordered by creation time."""
    supabase = get_supabase()
    try:
        result = supabase.table("messages").select("*").eq("conversation_id", chat_id).order("created_at").execute()
        return [{
            "role": m["role"],
            "content": m["content"],
            "timestamp": m.get("timestamp", ""),
        } for m in result.data or []]
    except Exception:
        return []


def save_message(chat_id: str, user_id: str, role: str, content: str, timestamp: str = "") -> bool:
    """Insert a single message into Supabase."""
    supabase = get_supabase()
    try:
        supabase.table("messages").insert({
            "conversation_id": chat_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return True
    except Exception:
        return False


def save_messages_batch(chat_id: str, user_id: str, messages: list[dict]) -> bool:
    """Insert multiple messages in a single PostgREST call for efficiency."""
    supabase = get_supabase()
    try:
        now = datetime.now(timezone.utc).isoformat()
        records = []
        for msg in messages:
            records.append({
                "conversation_id": chat_id,
                "user_id": user_id,
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg.get("timestamp", ""),
                "created_at": now,
            })
        if records:
            supabase.table("messages").insert(records).execute()
        return True
    except Exception:
        return False


def sync_chat(chat_id: str, user_id: str, title: str = None) -> bool:
    """Touch the updated_at timestamp (and optionally update title) for a conversation."""
    if not chat_id:
        return False
    supabase = get_supabase()
    data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if title:
        data["title"] = title
    try:
        supabase.table("conversations").update(data).eq("id", chat_id).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False
