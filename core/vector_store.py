"""
Vector store management using embedded Chroma (local, no external service)
"""
import os
from typing import List, Dict, Optional
import chromadb
from models.embeddings import get_embeddings
from config.settings import VECTOR_STORE_CONFIG, MODEL_CONFIG, EMBEDDING_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)


class OllamaEmbeddingFunction:
    """Chroma embedding function wrapper for Ollama embeddings."""
    def __init__(self, embeddings, model_name: Optional[str] = None):
        self.embeddings = embeddings
        # Keep default aligned with settings.py, but allow override when needed.
        self.model_name = model_name or MODEL_CONFIG.get("embedding_model", EMBEDDING_MODEL)

    def __call__(self, input):
        # Chroma expects parameter name "input"
        texts = input if isinstance(input, list) else [input]
        return self.embeddings.embed_documents(texts)

    def name(self):
        # Chroma expects embedding_function.name() callable
        return self.model_name


class ChromaVectorStore:
    """Manages embedded Chroma vector store operations (local, persistent)."""
    
    def __init__(self):
        self.embeddings = get_embeddings()
        embedding_model = MODEL_CONFIG.get("embedding_model", EMBEDDING_MODEL)
        self.embedding_function = OllamaEmbeddingFunction(self.embeddings, model_name=embedding_model)
        self.client = None
        self.collection = None
        self.persist_directory = VECTOR_STORE_CONFIG.get("persist_directory", "./db/chroma")
        self.collection_name = VECTOR_STORE_CONFIG.get("collection_name", "bsk_documents")
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize Chroma client with local persistence."""
        try:
            # Ensure persist directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            logger.info(f"Chroma persist directory ensured: {self.persist_directory}")
            
            # Initialize Chroma client with persistent storage (new API)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function
            )
            
            logger.info(f"✓ Chroma vector store initialized successfully with collection: {self.collection_name}")
            logger.info(f"  Persist directory: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chroma vector store: {e}")
            raise
    
    def add_documents(self, documents: List[Dict], ids: List[str]) -> bool:
        """
        Add documents to Chroma.
        
        Args:
            documents: List of document objects with page_content and metadata
            ids: List of unique IDs for each document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.collection:
                logger.error("Chroma collection not available")
                return False
            
            # Prepare documents for Chroma
            texts = []
            metadatas = []
            
            for doc in documents:
                texts.append(doc.page_content if hasattr(doc, 'page_content') else doc.get('page_content', ''))
                metadatas.append(doc.metadata if hasattr(doc, 'metadata') else doc.get('metadata', {}))
            
            # Add to collection
            self.collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"✓ Added {len(documents)} documents to Chroma collection")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to Chroma: {e}")
            return False
    
    def query(self, query_text: str, k: int = 4, where: Optional[Dict] = None) -> List[Dict]:
        """
        Query documents from Chroma.
        
        Args:
            query_text: Query text
            k: Number of results to return
            where: Optional filter conditions
            
        Returns:
            List of matching documents with scores
        """
        try:
            if not self.collection:
                logger.error("Chroma collection not available")
                return []
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=k,
                where=where
            )
            
            # Format results
            documents = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    doc = {
                        'id': doc_id,
                        'content': results['documents'][0][i] if results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    }
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error querying Chroma: {e}")
            return []
    
    def delete_by_filter(self, where: Dict) -> bool:
        """
        Delete documents matching a filter.
        
        Args:
            where: Filter condition (e.g., {"filename": "document.pdf"})
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.collection:
                logger.error("Chroma collection not available")
                return False
            
            # Get documents matching filter first
            results = self.collection.get(where=where)
            ids_to_delete = results.get('ids', [])
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"✓ Deleted {len(ids_to_delete)} documents from Chroma matching filter: {where}")
                return True
            else:
                logger.warning(f"No documents found matching filter: {where}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting documents from Chroma: {e}")
            return False
    
    def get_all_filenames(self) -> List[str]:
        """
        Get all unique filenames in the collection.
        
        Returns:
            List of filenames
        """
        try:
            if not self.collection:
                return []
            
            # Get all documents
            all_docs = self.collection.get()
            
            filenames = set()
            if all_docs.get('metadatas'):
                for metadata in all_docs['metadatas']:
                    if 'filename' in metadata:
                        filenames.add(metadata['filename'])
            
            return sorted(list(filenames))
            
        except Exception as e:
            logger.error(f"Error getting filenames from Chroma: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """
        Get collection statistics.
        
        Returns:
            Dict with collection stats
        """
        try:
            if not self.collection:
                return {"available": False, "total_documents": 0}
            
            all_docs = self.collection.get()
            total_docs = len(all_docs.get('ids', []))
            
            filenames = self.get_all_filenames()
            
            return {
                "available": True,
                "total_documents": total_docs,
                "unique_files": len(filenames),
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting Chroma stats: {e}")
            return {"available": False, "total_documents": 0, "error": str(e)}
    
    def persist(self):
        """Persist the collection to disk."""
        try:
            if self.client:
                self.client.persist()
                logger.info("✓ Chroma collection persisted to disk")
        except Exception as e:
            logger.warning(f"Could not explicitly persist Chroma (may persist automatically): {e}")
    
    def is_available(self) -> bool:
        """Check if Chroma client and collection are initialized."""
        return self.client is not None and self.collection is not None

    def get_retriever(self):
        """Get a retriever for the Chroma collection."""
        if not self.is_available():
            return None
        
        try:
            # Create a simple wrapper retriever for Chroma
            # This retrieves documents using Chroma's query functionality
            class ChromaRetriever:
                def __init__(self, collection, embeddings, k=4):
                    self.collection = collection
                    self.embeddings = embeddings
                    self.k = k
                
                def invoke(self, query_text):
                    """Retrieve similar documents using embeddings."""
                    # Get embeddings for query
                    query_embedding = self.embeddings.embed_query(query_text)
                    
                    # Create a Document-like object for Chroma query results
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=self.k
                    )
                    
                    # Convert results to Document-like objects
                    documents = []
                    if results and results.get('ids') and len(results['ids']) > 0:
                        for i, doc_id in enumerate(results['ids'][0]):
                            # Create a simple Document wrapper
                            doc = type('Document', (), {
                                'page_content': results['documents'][0][i] if results.get('documents') else '',
                                'metadata': results['metadatas'][0][i] if results.get('metadatas') else {}
                            })()
                            documents.append(doc)
                    
                    return documents
            
            # Use k from config, default to 4
            k = VECTOR_STORE_CONFIG.get("k", 4)
            retriever = ChromaRetriever(self.collection, self.embeddings, k=k)
            return retriever
            
        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            return None

# Global instance
vector_store_manager = ChromaVectorStore()
