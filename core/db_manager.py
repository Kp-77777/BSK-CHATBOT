"""
MongoDB database manager for BSK 2.0 v2
Handles documents, services, and logs with auto-initialization.
"""

from datetime import datetime, timezone
from db.mongo_client import get_db

db = get_db()

documents_collection = db["documents"]
services_collection = db["services"]
logs_collection = db["logs"]
chat_history_collection = db["chat_history"]


# ======================================================
# AUTO-INITIALIZATION: Create indexes and seed services
# ======================================================

def initialize_collections():
    """Initialize collections with indexes and seed services on startup."""
    try:
        # Create indexes
        documents_collection.create_index([("filename", 1)])
        documents_collection.create_index([("department", 1), ("service", 1)])
        
        services_collection.create_index([("department", 1), ("service", 1)], unique=True)
        
        logs_collection.create_index([("timestamp", -1)])
        logs_collection.create_index([("department", 1), ("service", 1)])
        
        chat_history_collection.create_index([("chat_id", 1)], unique=True)
        chat_history_collection.create_index([("updated_at", -1)])
        
        # Seed services collection if empty
        if services_collection.count_documents({}) == 0:
            from config.departments_services import DEPARTMENTS_SERVICES
            
            services_to_insert = []
            for dept, services in DEPARTMENTS_SERVICES.items():
                for service in services:
                    services_to_insert.append({
                        "department": dept,
                        "service": service,
                        "status": "Inactive",
                        "last_updated": None,
                        "created_at": datetime.now(timezone.utc)
                    })
            
            if services_to_insert:
                services_collection.insert_many(services_to_insert)
                import logging
                logging.getLogger(__name__).info("Seeded %s services into MongoDB", len(services_to_insert))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Error initializing collections: %s", e)


# NOTE: Initialization is called explicitly during app startup.


# ======================================================
# DOCUMENTS COLLECTION
# ======================================================

def add_document(filename: str, department: str, service: str, document_type: str = ""):
    """Add a document record."""
    documents_collection.insert_one({
        "filename": filename,
        "department": department,
        "service": service,
        "document_type": document_type,
        "created_at": datetime.now(timezone.utc),
    })


def delete_document(filename: str):
    """Delete a document record."""
    # Find which department/service pairs are affected by this filename
    docs = list(documents_collection.find({"filename": filename}, {"department": 1, "service": 1}))
    affected = set()
    for d in docs:
        dept = d.get("department")
        serv = d.get("service")
        if dept and serv:
            affected.add((dept, serv))

    # Delete the documents
    documents_collection.delete_many({"filename": filename})

    # For each affected service, if no documents remain, mark it Inactive
    for dept, serv in affected:
        try:
            count = get_document_count_for_service(dept, serv)
            if count == 0:
                update_service_status(dept, serv, "Inactive")
        except Exception:
            # If anything goes wrong here, continue without failing the delete
            continue


def find_document(filename: str):
    """Find a document by filename."""
    return documents_collection.find_one({"filename": filename})


def get_all_documents():
    """Get all documents."""
    return list(documents_collection.find({}, {"_id": 0}))


def get_documents_by_department_service(department: str, service: str):
    """Get all documents for a specific department and service."""
    return list(documents_collection.find(
        {"department": department, "service": service},
        {"_id": 0}
    ))


def update_document(filename: str, department: str = None, service: str = None, document_type: str = None):
    """Update document metadata."""
    update_fields = {}
    if department:
        update_fields["department"] = department
    if service:
        update_fields["service"] = service
    if document_type:
        update_fields["document_type"] = document_type
    if update_fields:
        documents_collection.update_one(
            {"filename": filename},
            {"$set": update_fields}
        )


# ======================================================
# SERVICES COLLECTION
# ======================================================

def add_service(department: str, service: str):
    """Add a new service (defaults to Inactive)."""
    services_collection.update_one(
        {"department": department, "service": service},
        {
            "$setOnInsert": {
                "department": department,
                "service": service,
                "status": "Inactive",
                "last_updated": None,
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )


def upsert_service(department: str, service: str, status: str = None):
    """Upsert a service record (insert if missing, update if exists)."""
    update_data = {
        "department": department,
        "service": service
    }
    
    if status:
        update_data["status"] = status
    
    update_data["last_updated"] = datetime.now(timezone.utc)
    
    services_collection.update_one(
        {"department": department, "service": service},
        {
            "$set": update_data
        },
        upsert=True
    )


def get_all_services():
    """Get all services."""
    return list(services_collection.find({}, {"_id": 0}).sort("department", 1))


def get_services_by_department(department: str):
    """Get all services for a department."""
    return list(services_collection.find(
        {"department": department},
        {"_id": 0}
    ).sort("service", 1))


def update_service_status(department: str, service: str, status: str):
    """Update service status."""
    services_collection.update_one(
        {"department": department, "service": service},
        {
            "$set": {
                "status": status,
                "last_updated": datetime.now(timezone.utc)
            }
        }
    )


def get_document_count_for_service(department: str, service: str):
    """Count documents for a specific service."""
    return documents_collection.count_documents({
        "department": department,
        "service": service
    })


# ======================================================
# LOGS COLLECTION
# ======================================================

def log_action(department: str, service: str, document_name: str, document_type: str, action: str):
    """
    Log an action.
    action: 'upload', 'delete', etc.
    """
    try:
        logs_collection.insert_one({
            "timestamp": datetime.now(timezone.utc),
            "department": department or "Unassigned",
            "service": service or "Unassigned",
            "document_name": document_name,
            "document_type": document_type or "Unknown",
            "action": action
        })
    except Exception as e:
        import logging
        logging.error(f"Error logging action: {e}")


def get_all_logs():
    """Get all logs."""
    return list(logs_collection.find({}, {"_id": 0}).sort("timestamp", -1))


def get_logs_by_filename(filename: str):
    """Get all logs for a specific document."""
    return list(logs_collection.find(
        {"document_name": filename},
        {"_id": 0}
    ).sort("timestamp", -1))


def get_logs_by_department(department: str):
    """Get all logs for a department."""
    return list(logs_collection.find(
        {"department": department},
        {"_id": 0}
    ).sort("timestamp", -1))


def get_logs_by_department_service(department: str, service: str):
    """Get all logs for a department and service combination."""
    return list(logs_collection.find(
        {"department": department, "service": service},
        {"_id": 0}
    ).sort("timestamp", -1))


# ======================================================
# CHAT HISTORY COLLECTION (MongoDB)
# ======================================================

def chat_create(chat_id: str, title: str = "New Chat") -> bool:
    """Create a new chat session in MongoDB."""
    try:
        now = datetime.now(timezone.utc)
        chat_history_collection.insert_one({
            "chat_id": chat_id,
            "created_at": now,
            "updated_at": now,
            "title": title,
            "messages": [],
            "message_count": 0
        })
        return True
    except Exception as e:
        import logging
        logging.error(f"Error creating chat: {e}")
        return False


def chat_get_by_id(chat_id: str):
    """Get a chat by chat_id. Returns dict or None. Excludes _id for JSON serialization."""
    doc = chat_history_collection.find_one({"chat_id": chat_id}, {"_id": 0})
    if doc and "created_at" in doc:
        if hasattr(doc["created_at"], "isoformat"):
            doc["created_at"] = doc["created_at"].isoformat()
        if hasattr(doc["updated_at"], "isoformat"):
            doc["updated_at"] = doc["updated_at"].isoformat()
        for m in doc.get("messages", []):
            if "timestamp" in m and hasattr(m["timestamp"], "isoformat"):
                m["timestamp"] = m["timestamp"].isoformat()
    return doc


def chat_update_title(chat_id: str, title: str) -> bool:
    """Update chat title and updated_at."""
    try:
        chat_history_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}}
        )
        return True
    except Exception as e:
        import logging
        logging.error(f"Error updating chat title: {e}")
        return False


def chat_append_message(chat_id: str, role: str, content: str) -> bool:
    """Append a message to chat and update message_count and updated_at."""
    try:
        now = datetime.now(timezone.utc)
        message = {
            "seq": 0,  # will set via $inc or count
            "role": role,
            "content": content,
            "timestamp": now
        }
        # Get current count for seq
        chat = chat_history_collection.find_one({"chat_id": chat_id}, {"message_count": 1, "messages": 1})
        if not chat:
            return False
        next_seq = (chat.get("message_count") or 0) + 1
        message["seq"] = next_seq
        chat_history_collection.update_one(
            {"chat_id": chat_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": now, "message_count": next_seq}
            }
        )
        return True
    except Exception as e:
        import logging
        logging.error(f"Error appending message: {e}")
        return False


def chat_get_messages(chat_id: str):
    """Get messages list for a chat. Returns list of message dicts with serializable timestamps."""
    chat = chat_history_collection.find_one({"chat_id": chat_id}, {"_id": 0, "messages": 1})
    if not chat:
        return []
    messages = chat.get("messages", [])
    for m in messages:
        if "timestamp" in m and hasattr(m["timestamp"], "isoformat"):
            m["timestamp"] = m["timestamp"].isoformat()
    return messages


def chat_delete(chat_id: str) -> bool:
    """Delete a chat session."""
    try:
        result = chat_history_collection.delete_one({"chat_id": chat_id})
        return result.deleted_count > 0
    except Exception as e:
        import logging
        logging.error(f"Error deleting chat: {e}")
        return False


def chat_get_all(sort_by_updated: bool = True):
    """Get all chats. Returns list of chat docs (no _id), sorted by updated_at desc."""
    cursor = chat_history_collection.find({}, {"_id": 0})
    if sort_by_updated:
        cursor = cursor.sort("updated_at", -1)
    docs = list(cursor)
    for doc in docs:
        if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
            doc["created_at"] = doc["created_at"].isoformat()
        if "updated_at" in doc and hasattr(doc["updated_at"], "isoformat"):
            doc["updated_at"] = doc["updated_at"].isoformat()
    return docs
