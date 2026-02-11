"""API helpers: serialize MongoDB docs for JSON."""
from datetime import datetime
from typing import Any, List, Dict


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime fields to ISO strings for JSON."""
    if not doc:
        return doc
    out = dict(doc)
    for key in ("created_at", "updated_at", "timestamp", "last_updated", "deleted_at"):
        if key in out and out[key] is not None and hasattr(out[key], "isoformat"):
            out[key] = out[key].isoformat()
    return out


def serialize_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Serialize a list of MongoDB-like docs."""
    return [serialize_doc(d) for d in docs]
