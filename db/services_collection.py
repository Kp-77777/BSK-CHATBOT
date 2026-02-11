from .mongo_client import services_collection

class ServicesRepo:
    """
    Repository for accessing the 'services' collection in MongoDB.
    """
    @staticmethod
    def get_services():
        """
        Retrieve all services entries.
        """
        services = list(services_collection.find({}, {"_id": 0}))
        return services

    @staticmethod
    def add_service(department: str, service: str):
        """
        Add a new service entry.
        """
        entry = {"department": department, "service": service}
        services_collection.insert_one(entry)


# --- Compatibility adapter functions ---
from datetime import datetime
from bson import ObjectId

def upsert_service(department, service):
    """Insert or return existing service, return its _id (string)."""
    svc = services_collection.find_one({"department": department, "service": service})
    if not svc:
        entry = {
            "department": department,
            "service": service,
            "status": "Inactive",
            "last_updated": datetime.now(),
            "pdfs": []
        }
        res = services_collection.insert_one(entry)
        return str(res.inserted_id)
    return str(svc.get("_id"))


def add_pdf_to_service(service_id, pdf_id, pdf_name):
    try:
        services_collection.update_one(
            {"_id": ObjectId(service_id)},
            {
                "$push": {"pdfs": {"pdf_id": pdf_id, "pdf_name": pdf_name, "upload_time": datetime.now()}},
                "$set": {"status": "Active", "last_updated": datetime.now()}
            }
        )
    except Exception:
        # best-effort: try to match by string id if ObjectId conversion fails
        services_collection.update_one(
            {"service_id": service_id},
            {
                "$push": {"pdfs": {"pdf_id": pdf_id, "pdf_name": pdf_name, "upload_time": datetime.utcnow()}},
                "$set": {"status": "Active", "last_updated": datetime.now()}
            },
            upsert=True
        )


def remove_pdf_from_service(service_id, pdf_id):
    try:
        services_collection.update_one({"_id": ObjectId(service_id)}, {"$pull": {"pdfs": {"pdf_id": pdf_id}}, "$set": {"last_updated": datetime.now()}})
        svc = services_collection.find_one({"_id": ObjectId(service_id)})
        if svc and len(svc.get("pdfs", [])) == 0:
            services_collection.update_one({"_id": ObjectId(service_id)}, {"$set": {"status": "Inactive"}})
    except Exception:
        services_collection.update_one({"service_id": service_id}, {"$pull": {"pdfs": {"pdf_id": pdf_id}}, "$set": {"last_updated": datetime.now()}})
        svc = services_collection.find_one({"service_id": service_id})
        if svc and len(svc.get("pdfs", [])) == 0:
            services_collection.update_one({"service_id": service_id}, {"$set": {"status": "Inactive"}})


def fetch_all_services():
    return list(services_collection.find({}, {"_id": 1, "department": 1, "service": 1, "status": 1, "last_updated": 1, "pdfs": 1}))
