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
        self.collection_name = "novaintel_documents"
        self._initialize()
    
    def _get_embedding_dimension(self) -> Optional[int]:
        """Get the embedding dimension from the embedding service."""
        try:
            from rag.embedding_service import embedding_service
            if not embedding_service.is_available():
                return None
            
            # Get a test embedding to determine dimension
            test_embedding = embedding_service.get_embedding("test", use_cache=False)
            return len(test_embedding) if test_embedding else None
        except Exception as e:
            print(f"[WARNING] Could not determine embedding dimension: {e}")
            return None
    
    def _check_and_fix_collection_dimension(self, collection, expected_dim: Optional[int]) -> bool:
        """
        Check if collection dimension matches expected dimension.
        If not, delete and recreate the collection.
        
        Returns:
            True if collection is valid or was recreated, False otherwise
        """
        if expected_dim is None:
            return True  # Can't verify, assume OK
        
        try:
            # Try to get collection metadata to check dimension
            # Chroma doesn't directly expose dimension in metadata, so we'll try to add a test vector
            try:
                # Try to peek at collection - if it has items, check one
                count = collection.count()
                if count > 0:
                    # Get a sample to check dimension
                    sample = collection.get(limit=1)
                    if sample and 'embeddings' in sample and len(sample['embeddings']) > 0:
                        existing_dim = len(sample['embeddings'][0])
                        if existing_dim != expected_dim:
                            print(f"[WARNING] Collection dimension mismatch: {existing_dim} != {expected_dim}")
                            print(f"   Deleting old collection and creating new one with dimension {expected_dim}")
                            # Delete the collection
                            self.chroma_client.delete_collection(name=self.collection_name)
                            return False  # Need to recreate
            except Exception as e:
                # Collection might be empty or have issues, try to recreate
                print(f"[INFO] Collection check failed: {e}, will recreate if needed")
                try:
                    self.chroma_client.delete_collection(name=self.collection_name)
                except:
                    pass  # Collection might not exist
                return False  # Need to recreate
            
            return True  # Collection is valid
        except Exception as e:
            print(f"[WARNING] Error checking collection dimension: {e}")
            return True  # Assume OK to avoid breaking
    
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
                
                # Get expected embedding dimension
                expected_dim = self._get_embedding_dimension()
                
                # Try to get existing collection
                collection = None
                try:
                    collection = self.chroma_client.get_collection(name=self.collection_name)
                    # Check if dimension matches
                    if not self._check_and_fix_collection_dimension(collection, expected_dim):
                        collection = None  # Need to recreate
                except:
                    # Collection doesn't exist, will create new one
                    pass
                
                # Create or recreate collection if needed
                if collection is None:
                    collection = self.chroma_client.create_collection(
                        name=self.collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                    if expected_dim:
                        print(f"[OK] Created Chroma collection with dimension {expected_dim}")
                    else:
                        print(f"[OK] Created Chroma collection")
                else:
                    print(f"[OK] Using existing Chroma collection")
                
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
    
    def recreate_collection(self) -> bool:
        """
        Recreate the collection (useful after embedding model change).
        WARNING: This will delete all existing vectors!
        """
        if not self.chroma_client or settings.VECTOR_DB_TYPE != "chroma":
            return False
        
        try:
            # Delete existing collection
            try:
                self.chroma_client.delete_collection(name=self.collection_name)
                print(f"[INFO] Deleted existing collection: {self.collection_name}")
            except:
                pass  # Collection might not exist
            
            # Get expected dimension
            expected_dim = self._get_embedding_dimension()
            
            # Create new collection
            collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Recreate vector store
            self.vector_store = ChromaVectorStore(chroma_collection=collection)
            
            if expected_dim:
                print(f"[OK] Recreated collection with dimension {expected_dim}")
            else:
                print(f"[OK] Recreated collection")
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to recreate collection: {e}")
            return False
    
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
