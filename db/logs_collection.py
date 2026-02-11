from datetime import datetime
from .mongo_client import logs_collection

class LogRepo:
    """
    Repository for accessing the 'logs' collection in MongoDB.
    """
    @staticmethod
    def add_log(action: str, filename: str):
        """
        Insert a new log entry with the current timestamp, action, and filename.
        """
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "filename": filename
        }
        logs_collection.insert_one(log_entry)

    @staticmethod
    def get_recent_logs(limit: int = 50):
        """
        Retrieve recent log entries sorted by timestamp descending.
        """
        cursor = logs_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return list(cursor)


# Compatibility adapters
def add_log(action: str, department: str, service: str, document_name: str, details=None):
    entry = {
        "action": action,
        "department": department,
        "service": service,
        "document_name": document_name,
        "timestamp": datetime.now(),
        "details": details
    }
    logs_collection.insert_one(entry)


def fetch_logs(limit=100):
    return list(logs_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
