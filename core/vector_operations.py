"""
Vector database operations for managing documents in Chroma (embedded local)
"""
import os
import tempfile
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from core.vector_store import vector_store_manager
from utils.logger import get_logger
import re

logger = get_logger(__name__)

class VectorDBOperations:
    """Operations for managing documents in Chroma vector store."""
    
    def __init__(self):
        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", 1000)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 350))
        )

    def clean_pdf_text(self, text: str) -> str:
        """Clean and normalize extracted PDF text.

        - Fix hyphenation at line breaks
        - Normalize newlines and whitespace
        - Remove non-printable characters
        """
        if not text:
            return ""

        # Normalize CRLF to LF
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove hyphenation where words are split at line breaks
        text = re.sub(r"-\n\s*", "", text)

        # Collapse multiple newlines to at most two
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Collapse multiple spaces/tabs
        text = re.sub(r"[ \t]{2,}", " ", text)

        # Remove non-printable characters except newline
        text = ''.join(ch for ch in text if ch.isprintable() or ch == '\n')

        # Strip leading/trailing whitespace
        return text.strip()

    def add_pdf_to_vectorstore(self, uploaded_file, filename: str, department: str = "", service: str = "", document_type: str = "") -> Dict:
        """
        Add a PDF file to Chroma and sync to MongoDB.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            filename: Name of the file
            department: Department name for this document
            service: Service name for this document
            document_type: Type of document (FAQ, Policy, etc.)
            
        Returns:
            Dict with operation status and details
        """
        try:
            # Check if vector store is available
            if not vector_store_manager.is_available():
                return {
                    "success": False,
                    "message": "Vector store is not available. Please check system configuration.",
                    "chunks_added": 0
                }
            
            # Check for duplicate filename in Chroma
            existing_docs = self.list_documents()
            if filename in existing_docs:
                return {
                    "success": False,
                    "message": f"Document '{filename}' already exists. Please delete it first or use a different name.",
                    "chunks_added": 0
                }
            
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name
            
            try:
                # Load PDF using PyMuPDFLoader
                from langchain_community.document_loaders import PyMuPDFLoader
                loader = PyMuPDFLoader(temp_file_path)
                docs = loader.load()
                
                if not docs:
                    return {"success": False, "message": "Failed to load document. It may be empty.", "chunks_added": 0}
                
                # Merge all pages into a single text string
                full_text = "\n".join([doc.page_content for doc in docs])
                
                # Clean the extracted text
                cleaned_text = self.clean_pdf_text(full_text)
                if not cleaned_text.strip():
                    return {"success": False, "message": "Cleaned document text is empty.", "chunks_added": 0}

                # Create a single document for splitting
                merged_doc = Document(page_content=cleaned_text, metadata={"source": filename, "filename": filename})
                
                # Split into chunks
                chunks = self.text_splitter.split_documents([merged_doc])
                if not chunks:
                    return {"success": False, "message": "Failed to create chunks from the document.", "chunks_added": 0}
                
                # Create IDs for each chunk using filename and index
                chunk_ids = [f"{filename}_{i+1}" for i in range(len(chunks))]
                
                from datetime import datetime
                upload_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Enrich chunks with metadata
                for chunk in chunks:
                    chunk.metadata["filename"] = filename
                    chunk.metadata["source"] = filename
                    chunk.metadata["department"] = department
                    chunk.metadata["service"] = service
                    chunk.metadata["document_type"] = document_type
                    chunk.metadata["status"] = "Active"
                    chunk.metadata["add_modify"] = "Add"
                    chunk.metadata["date_time"] = upload_timestamp
                
                # Add chunks to Chroma
                success = vector_store_manager.add_documents(chunks, ids=chunk_ids)
                
                if not success:
                    return {
                        "success": False,
                        "message": "Failed to add documents to Chroma.",
                        "chunks_added": 0
                    }
                
                # Persist Chroma collection
                vector_store_manager.persist()
                
                logger.info(f"✓ Successfully added {len(chunks)} chunks for {filename} to Chroma")
                
                return {
                    "success": True,
                    "message": f"Successfully added '{filename}' to vector store ({len(chunks)} chunks).",
                    "chunks_added": len(chunks),
                    "chroma_ids": chunk_ids  # Return IDs for Mongo sync
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error adding {filename} to Chroma: {e}")
            return {"success": False, "message": f"An error occurred: {str(e)}", "chunks_added": 0}

    def list_documents(self) -> List[str]:
        """
        List all unique document filenames in Chroma.
        
        Returns:
            List of filenames
        """
        try:
            if not vector_store_manager.is_available():
                logger.warning("Vector store not available.")
                return []
            
            return vector_store_manager.get_all_filenames()
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []

    def delete_document_by_filename(self, filename: str) -> Dict:
        """
        Delete all chunks of a document from Chroma by filename.
        
        Args:
            filename: Name of the file to delete
         
        Returns:
            Dict with operation status and details.
        """
        try:
            if not vector_store_manager.is_available():
                return {"success": False, "message": "Vector store is not available.", "chunks_deleted": 0}
            
            # Delete from Chroma using filter
            success = vector_store_manager.delete_by_filter({"filename": filename})
            
            if success:
                # Persist changes
                vector_store_manager.persist()
                
                logger.info(f"✓ Deleted all chunks for filename: {filename}")
                return {
                    "success": True, 
                    "message": f"Successfully deleted '{filename}' from vector store.",
                    "chunks_deleted": -1  # Unknown exact count, but successful
                }
            else:
                return {
                    "success": False, 
                    "message": f"No document found with filename: '{filename}'",
                    "chunks_deleted": 0
                }
                
        except Exception as e:
            logger.error(f"Error deleting document '{filename}' from Chroma: {e}")
            return {"success": False, "message": f"An error occurred: {str(e)}", "chunks_deleted": 0}
    
    def get_document_stats(self) -> Dict:
        """
        Get vector store statistics (Chroma).
        
        Returns:
            Dict with stats
        """
        try:
            if not vector_store_manager.is_available():
                return {
                    "available": False,
                    "total_documents": 0
                }

            stats = vector_store_manager.get_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {
                "available": False,
                "total_documents": 0,
                "error": str(e)
            }


# Global instance for legacy imports
vector_db_operations = VectorDBOperations()
