"""Chat endpoints: create, query, get history, delete."""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import (
    ChatCreateResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    ChatHistoryResponse,
    ChatDeleteResponse,
    ChatMessage,
)
from services.chat_service import chat_service
from core.rag_engine import rag_engine

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatCreateResponse)
def create_chat():
    """Create a new chat session."""
    chat_id = chat_service.create_new_chat()
    chat = chat_service.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=500, detail="Failed to create chat")
    created_at = chat.get("created_at", datetime.now(timezone.utc).isoformat())
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()
    return ChatCreateResponse(
        chat_id=chat_id,
        created_at=created_at,
        title=chat.get("title", "New Chat"),
        message_count=chat.get("message_count", 0),
    )


@router.post("/query", response_model=ChatQueryResponse)
def chat_query(body: ChatQueryRequest):
    """Send user query and get RAG-based response (non-streaming)."""
    query = body.query.strip()
    chat_id = body.chat_id
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    if not chat_id:
        chat_id = chat_service.create_new_chat()
    chat_service.save_message_to_chat(chat_id, "user", query)
    chat = chat_service.get_chat_by_id(chat_id)
    if chat and (chat.get("message_count") or 0) == 1:
        chat_service.update_chat_title(chat_id, query)
    full_answer = ""
    for chunk in rag_engine.process_query(query, chat_id=chat_id):
        full_answer += chunk
    chat_service.save_message_to_chat(chat_id, "Virtual Assistant", full_answer)
    return ChatQueryResponse(
        chat_id=chat_id,
        answer=full_answer,
        confidence=None,
        sources=[],
    )


@router.get("/{chat_id}", response_model=ChatHistoryResponse)
def get_chat_history(chat_id: str):
    """Fetch full chat history by ID."""
    chat = chat_service.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = [
        ChatMessage(
            role=m.get("role", ""),
            content=m.get("content", ""),
            timestamp=m.get("timestamp"),
            seq=m.get("seq"),
        )
        for m in chat.get("messages", [])
    ]
    return ChatHistoryResponse(
        chat_id=chat_id,
        messages=messages,
        title=chat.get("title"),
        created_at=chat.get("created_at"),
        updated_at=chat.get("updated_at"),
    )


@router.delete("/{chat_id}", response_model=ChatDeleteResponse)
def delete_chat(chat_id: str):
    """Delete a chat session and its history."""
    if not chat_service.delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatDeleteResponse(
        chat_id=chat_id,
        status="deleted",
        deleted_at=datetime.now(timezone.utc).isoformat(),
    )
