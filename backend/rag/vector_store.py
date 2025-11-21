"""
Vector database integration using Chroma.
"""
from typing import List, Optional, Dict, Any
from utils.config import settings
import chromadb
from chromadb.config import Settings as ChromaSettings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

class VectorStoreManager:
    """Manage vector database connections and operations."""
    
    def __init__(self):
        self.chroma_client = None
        self.vector_store = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Chroma vector database."""
        try:
            if settings.VECTOR_DB_TYPE == "chroma":
                import os
                from pathlib import Path
                
                # Resolve path relative to backend directory
                chroma_path = Path(settings.CHROMA_PERSIST_DIR)
                if not chroma_path.is_absolute():
                    # If relative, make it relative to backend directory
                    backend_dir = Path(__file__).parent.parent
                    chroma_path = backend_dir / chroma_path
                
                # Ensure directory exists
                chroma_path.mkdir(parents=True, exist_ok=True)
                
                # Initialize Chroma client
                self.chroma_client = chromadb.PersistentClient(
                    path=str(chroma_path)
                )
                
                # Create or get collection
                collection = self.chroma_client.get_or_create_collection(
                    name="novaintel_documents",
                    metadata={"hnsw:space": "cosine"}
                )
                
                # Create LlamaIndex vector store
                self.vector_store = ChromaVectorStore(chroma_collection=collection)
                
                print(f"[OK] Chroma vector store initialized: {chroma_path}")
            else:
                print(f"[WARNING] Vector DB type '{settings.VECTOR_DB_TYPE}' not implemented")
                print("   Please set VECTOR_DB_TYPE=chroma in your .env file")
        except ImportError as e:
            print(f"[ERROR] Missing Chroma dependencies: {e}")
            print("   Run: pip install chromadb llama-index-vector-stores-chroma")
            self.vector_store = None
        except Exception as e:
            print(f"[ERROR] Error initializing vector store: {e}")
            import traceback
            traceback.print_exc()
            self.vector_store = None
    
    def get_vector_store(self):
        """Get the vector store instance."""
        return self.vector_store
    
    def is_available(self) -> bool:
        """Check if vector store is available."""
        return self.vector_store is not None
    
    def delete_by_ids(self, ids: List[str]) -> bool:
        """Delete vectors by IDs."""
        if not self.is_available() or settings.VECTOR_DB_TYPE != "chroma":
            return False
        
        try:
            collection = self.chroma_client.get_collection("novaintel_documents")
            collection.delete(ids=ids)
            return True
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False
    
    def delete_by_metadata_filter(self, filter_dict: Dict[str, Any]) -> bool:
        """Delete vectors by metadata filter."""
        if not self.is_available() or settings.VECTOR_DB_TYPE != "chroma":
            return False
        
        try:
            collection = self.chroma_client.get_collection("novaintel_documents")
            # Convert filter dict to Chroma format
            where = filter_dict
            collection.delete(where=where)
            return True
        except Exception as e:
            print(f"Error deleting vectors by filter: {e}")
            return False

# Global instance
vector_store_manager = VectorStoreManager()
