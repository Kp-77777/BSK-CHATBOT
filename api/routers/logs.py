"""Logs endpoint: view upload/delete activity."""
from fastapi import APIRouter, Query

from api.schemas import LogListResponse, LogEntry
from api.utils import serialize_docs
from core.db_manager import get_all_logs

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("", response_model=LogListResponse)
def view_logs(
    department: str | None = Query(None, description="Filter by department"),
    service: str | None = Query(None, description="Filter by service"),
    action: str | None = Query(None, description="Filter by action: upload, delete"),
):
    """View upload/delete activity logs."""
    raw = get_all_logs()
    if department:
        raw = [r for r in raw if r.get("department") == department]
    if service:
        raw = [r for r in raw if r.get("service") == service]
    if action:
        raw = [r for r in raw if r.get("action") == action]
    serialized = serialize_docs(raw)
    entries = [
        LogEntry(
            timestamp=e.get("timestamp"),
            department=e.get("department"),
            service=e.get("service"),
            document_name=e.get("document_name"),
            document_type=e.get("document_type"),
            action=e.get("action"),
        )
        for e in serialized
    ]
    return LogListResponse(logs=entries)
