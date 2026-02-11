"""Service endpoints: list, add."""
from datetime import datetime, timezone
from fastapi import APIRouter

from api.schemas import ServiceListResponse, ServiceItem, ServiceCreateRequest, ServiceCreateResponse
from api.utils import serialize_docs
from core.db_manager import get_all_services, add_service, upsert_service

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=ServiceListResponse)
def list_services():
    """Get all departments and their services."""
    raw = get_all_services()
    serialized = serialize_docs(raw)
    items = [
        ServiceItem(
            department=s.get("department", ""),
            service=s.get("service", ""),
            status=s.get("status"),
            last_updated=s.get("last_updated"),
        )
        for s in serialized
    ]
    return ServiceListResponse(services=items)


@router.post("", response_model=ServiceCreateResponse)
def add_service_endpoint(body: ServiceCreateRequest):
    """Add a new department or service."""
    add_service(body.department, body.service)
    upsert_service(body.department, body.service, body.status)
    now = datetime.now(timezone.utc).isoformat()
    return ServiceCreateResponse(
        department=body.department,
        service=body.service,
        status=body.status,
        created_at=now,
        last_updated=now,
    )
