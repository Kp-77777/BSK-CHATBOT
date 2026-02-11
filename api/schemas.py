"""Pydantic schemas for BSK FastAPI."""
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field


# ----- Health -----
class HealthResponse(BaseModel):
    message: str = "BSK Chatbot API is running"
    version: str = "1.0.0"
    status: str = "healthy"


# ----- Chat -----
class ChatCreateResponse(BaseModel):
    chat_id: str
    created_at: str
    title: str = "New Chat"
    message_count: int = 0


class ChatQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    chat_id: Optional[str] = None


class SourceInfo(BaseModel):
    document_id: Optional[str] = None
    filename: Optional[str] = None
    snippet: Optional[str] = None


class ChatQueryResponse(BaseModel):
    chat_id: str
    answer: str
    confidence: Optional[float] = None
    sources: Optional[List[SourceInfo]] = None


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None
    seq: Optional[int] = None


class ChatHistoryResponse(BaseModel):
    chat_id: str
    messages: List[ChatMessage]
    title: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatDeleteResponse(BaseModel):
    chat_id: str
    status: str = "deleted"
    deleted_at: str


# ----- Documents -----
class DocumentUploadMetadata(BaseModel):
    department: str = ""
    service: str = ""
    doc_type: str = ""


class DocumentItem(BaseModel):
    filename: str
    department: Optional[str] = None
    service: Optional[str] = None
    document_type: Optional[str] = None
    created_at: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentItem]


class DocumentUploadResponse(BaseModel):
    filename: str
    status: str = "indexed"
    chunks: int
    created_at: str


class DocumentDeleteResponse(BaseModel):
    filename: str
    status: str = "deleted"
    deleted_at: str


# ----- Services -----
class ServiceItem(BaseModel):
    department: str
    service: str
    status: Optional[str] = None
    last_updated: Optional[str] = None


class ServiceListResponse(BaseModel):
    services: List[ServiceItem]


class ServiceCreateRequest(BaseModel):
    department: str = Field(..., min_length=1)
    service: str = Field(..., min_length=1)
    status: str = "Inactive"


class ServiceCreateResponse(BaseModel):
    department: str
    service: str
    status: str
    created_at: Optional[str] = None
    last_updated: Optional[str] = None


# ----- Logs -----
class LogEntry(BaseModel):
    timestamp: Optional[str] = None
    department: Optional[str] = None
    service: Optional[str] = None
    document_name: Optional[str] = None
    document_type: Optional[str] = None
    action: Optional[str] = None


class LogListResponse(BaseModel):
    logs: List[LogEntry]
