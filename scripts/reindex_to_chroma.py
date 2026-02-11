"""
Reindex Documents from MongoDB to Chroma
Populates the Chroma vector store from existing MongoDB documents
"""
import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
from db.mongo_client import get_db
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from datetime import datetime

# Load environment variables
load_dotenv()

# Import after loading env
from core.vector_store import vector_store_manager
from utils.logger import get_logger

logger = get_logger(__name__)

def reindex_chroma(skip_existing: bool = True):
    """
    Reindex all documents from MongoDB into Chroma.
    
    Args:
        skip_existing: If True, skip documents already in Chroma
    """
    try:
        # Connect to MongoDB
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DB_NAME", "bsk_assistant")
        
        logger.info(f"Connecting to MongoDB: {mongo_uri}")
        db = get_db()
        documents_collection = db["documents"]
        
        # Get all documents from MongoDB
        active_docs = list(documents_collection.find({}))
        
        if not active_docs:
            logger.warning("No active documents found in MongoDB")
            return True
        
        logger.info(f"Found {len(active_docs)} active documents in MongoDB")
        
        # Get list of documents already in Chroma
        existing_files = set(vector_store_manager.get_all_filenames()) if skip_existing else set()
        
        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", 1000)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 350))
        )
        
        # Process each document
        reindexed_count = 0
        skipped_count = 0
        error_count = 0
        
        for doc in active_docs:
            filename = doc.get("filename") or doc.get("pdf_name", "unknown")
            
            # Skip if already exists
            if skip_existing and filename in existing_files:
                logger.info(f"⊘ Skipping (already in Chroma): {filename}")
                skipped_count += 1
                continue
            
            try:
                # For now, we assume the full text is stored or available
                # In a real scenario, you might need to fetch from original file
                text_content = doc.get("text_content", "")
                
                if not text_content:
                    logger.warning(f"⚠ No text content for: {filename}")
                    error_count += 1
                    continue
                
                # Create document
                doc_obj = Document(
                    page_content=text_content,
                    metadata={
                        "filename": filename,
                        "department": doc.get("department", ""),
                        "service": doc.get("service", ""),
                        "document_type": doc.get("document_type", ""),
                        "status": "Active",
                        "date_time": doc.get("created_at", datetime.now()).isoformat()
                    }
                )
                
                # Split into chunks
                chunks = text_splitter.split_documents([doc_obj])
                
                if not chunks:
                    logger.warning(f"⚠ No chunks created for: {filename}")
                    error_count += 1
                    continue
                
                # Create chunk IDs
                chunk_ids = [f"{filename}_{i+1}" for i in range(len(chunks))]
                
                # Add to Chroma
                success = vector_store_manager.add_documents(chunks, ids=chunk_ids)
                
                if success:
                    logger.info(f"✓ Reindexed: {filename} ({len(chunks)} chunks)")
                    reindexed_count += 1
                else:
                    logger.error(f"✗ Failed to add chunks for: {filename}")
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"✗ Error processing {filename}: {e}")
                error_count += 1
        
        # Persist Chroma
        vector_store_manager.persist()
        
        logger.info("=" * 60)
        logger.info("Reindexing Complete:")
        logger.info(f"  Reindexed: {reindexed_count}")
        logger.info(f"  Skipped: {skipped_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reindex documents from MongoDB to Chroma")
    parser.add_argument("--replace", action="store_true", help="Replace existing documents (don't skip)")
    
    args = parser.parse_args()
    
    success = reindex_chroma(skip_existing=not args.replace)
    sys.exit(0 if success else 1)
