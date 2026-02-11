"""
Enhanced Chat service for managing chat operations with UUID-based chat IDs.
Storage: MongoDB (chat_history collection).
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from core.db_manager import (
    chat_create,
    chat_get_by_id,
    chat_update_title,
    chat_append_message,
    chat_get_messages,
    chat_delete,
    chat_get_all,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    """Service for managing chat operations with UUID-based IDs (MongoDB backend)."""

    def create_new_chat(self, custom_id: Optional[str] = None) -> str:
        """Create a new chat session with UUID."""
        try:
            new_chat_id = custom_id if custom_id else str(uuid.uuid4())
            existing = chat_get_by_id(new_chat_id)
            while existing:
                new_chat_id = str(uuid.uuid4())
                existing = chat_get_by_id(new_chat_id)
            if not chat_create(new_chat_id, title="New Chat"):
                logger.error("Failed to create chat in MongoDB")
                return str(uuid.uuid4())
            logger.info(f"Created new chat with UUID: {new_chat_id}")
            return new_chat_id
        except Exception as e:
            logger.error(f"Error creating new chat: {e}")
            return str(uuid.uuid4())

    def get_chat_by_id(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific chat by its ID."""
        try:
            return chat_get_by_id(chat_id)
        except Exception as e:
            logger.error(f"Error getting chat {chat_id}: {e}")
            return None

    def update_chat_title(self, chat_id: str, first_message: str) -> bool:
        """Update chat title based on first user message."""
        try:
            title = first_message.strip()
            if len(title) > 30:
                title = title[:27] + "..."
            ok = chat_update_title(chat_id, title)
            if ok:
                logger.info(f"Updated chat {chat_id} title: {title}")
            return ok
        except Exception as e:
            logger.error(f"Error updating chat title for {chat_id}: {e}")
            return False

    def save_message_to_chat(self, chat_id: str, role: str, content: str) -> bool:
        """Save a message to the specified chat."""
        try:
            ok = chat_append_message(chat_id, role, content)
            if ok:
                logger.info(f"Saved message to chat {chat_id}")
            return ok
        except Exception as e:
            logger.error(f"Error saving message to chat {chat_id}: {e}")
            return False

    def get_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get all messages from a specific chat."""
        try:
            return chat_get_messages(chat_id)
        except Exception as e:
            logger.error(f"Error getting messages for chat {chat_id}: {e}")
            return []

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a specific chat from history."""
        try:
            ok = chat_delete(chat_id)
            if ok:
                logger.info(f"Deleted chat {chat_id}")
            return ok
        except Exception as e:
            logger.error(f"Error deleting chat {chat_id}: {e}")
            return False

    def get_all_chats(self) -> Dict[str, Any]:
        """Get all chats, sorted by last updated. Returns dict keyed by chat_id for compatibility."""
        try:
            docs = chat_get_all(sort_by_updated=True)
            return {d["chat_id"]: d for d in docs}
        except Exception as e:
            logger.error(f"Error getting all chats: {e}")
            return {}

    def get_chat_summary(self, chat_id: str) -> Dict[str, Any]:
        """Get summary information about a chat."""
        try:
            chat = chat_get_by_id(chat_id)
            if not chat:
                return {}
            messages = chat.get("messages", [])
            return {
                "id": chat_id,
                "title": chat.get("title", "Untitled Chat"),
                "created_at": chat.get("created_at"),
                "updated_at": chat.get("updated_at"),
                "message_count": chat.get("message_count", len(messages)),
                "has_messages": len(messages) > 0,
            }
        except Exception as e:
            logger.error(f"Error getting chat summary for {chat_id}: {e}")
            return {}

    def cleanup_empty_chats(self) -> int:
        """Remove chats that have no messages."""
        try:
            docs = chat_get_all(sort_by_updated=False)
            removed = 0
            for d in docs:
                if (d.get("message_count") or 0) == 0:
                    if chat_delete(d["chat_id"]):
                        removed += 1
            if removed:
                logger.info(f"Cleaned up {removed} empty chats")
            return removed
        except Exception as e:
            logger.error(f"Error during chat cleanup: {e}")
            return 0


# Global enhanced chat service instance
chat_service = ChatService()
