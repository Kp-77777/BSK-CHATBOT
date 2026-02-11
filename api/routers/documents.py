"""Document endpoints: upload, list, delete."""
from datetime import datetime, timezone
import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from api.schemas import (
    DocumentListResponse,
    DocumentItem,
    DocumentUploadResponse,
    DocumentDeleteResponse,
)
from api.utils import serialize_docs
from core.vector_operations import vector_db_operations
from core.db_manager import (
    add_document,
    delete_document,
    get_all_documents,
    find_document,
    upsert_service,
    log_action,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    department: str = Form(""),
    service: str = Form(""),
    doc_type: str = Form(""),
):
    """Upload document with department & service metadata."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF file required")
    contents = await file.read()
    max_size_bytes = 50 * 1024 * 1024  # 50 MB
    if len(contents) > max_size_bytes:
        raise HTTPException(status_code=413, detail="PDF file too large (max 50 MB)")
    # vector_db_operations.add_pdf_to_vectorstore expects a file-like object with .getvalue()
    class FileLike:
        def getvalue(self):
            return contents
    # Ensure filename is unique: if a document with the same filename exists, append a short suffix
    final_filename = file.filename
    try:
        if find_document(file.filename):
            base, ext = os.path.splitext(file.filename)
            suffix = uuid.uuid4().hex[:8]
            final_filename = f"{base}_{suffix}{ext}"
    except Exception:
        # If any DB check fails, fall back to original filename
        final_filename = file.filename

    result = vector_db_operations.add_pdf_to_vectorstore(
        FileLike(), final_filename, department, service, doc_type
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Upload failed"),
        )
    add_document(final_filename, department, service, doc_type)
    if department and service:
        upsert_service(department, service, "Active")
    log_action(department or "Unassigned", service or "Unassigned", final_filename, doc_type or "Unknown", "upload")
    return DocumentUploadResponse(
        filename=final_filename,
        status="indexed",
        chunks=result.get("chunks_added", 0),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("", response_model=DocumentListResponse)
def list_documents():
    """List documents for dashboard and filtering."""
    docs = get_all_documents()
    serialized = serialize_docs(docs)
    items = [
        DocumentItem(
            filename=d.get("filename", ""),
            department=d.get("department"),
            service=d.get("service"),
            document_type=d.get("document_type"),
            created_at=d.get("created_at"),
        )
        for d in serialized
    ]
    return DocumentListResponse(documents=items)


@router.delete("/{filename:path}", response_model=DocumentDeleteResponse)
def delete_document_endpoint(filename: str):
    """Delete document from system and vector DB."""
    doc = find_document(filename)
    result = vector_db_operations.delete_document_by_filename(filename)
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Document not found or delete failed"),
        )
    delete_document(filename)
    if doc:
        log_action(
            doc.get("department") or "Unassigned",
            doc.get("service") or "Unassigned",
            filename,
            doc.get("document_type") or "Unknown",
            "delete",
        )
    return DocumentDeleteResponse(
        filename=filename,
        status="deleted",
        deleted_at=datetime.now(timezone.utc).isoformat(),
    )
