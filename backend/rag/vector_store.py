"""
Vector database integration with support for Chroma, Qdrant, and Pinecone.
"""
from typing import List, Optional, Dict, Any
from utils.config import settings
import sys

class VectorStoreManager:
    """Manage vector database connections and operations."""
    
    def __init__(self):
        self.chroma_client = None
        self.qdrant_client = None
        self.pinecone_client = None
        self.vector_store = None
        self.collection_name = "novaintel_documents"
        self._initialize()
    
    def _get_embedding_dimension(self, timeout: float = 2.0) -> Optional[int]:
        """Get the embedding dimension from the embedding service (non-blocking)."""
        try:
            from rag.embedding_service import embedding_service
            if not embedding_service.is_available():
                return None
            
            # Try to get dimension - if it blocks, we'll catch and skip
            # Note: This is a best-effort check, if it hangs we'll just skip it
            test_embedding = embedding_service.get_embedding("test", use_cache=False)
            return len(test_embedding) if test_embedding else None
        except Exception as e:
            # Silently skip if embedding service isn't ready or blocks
            # This prevents blocking during server startup
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
        """Initialize vector database based on VECTOR_DB_TYPE."""
        vector_db_type = settings.VECTOR_DB_TYPE.lower()
        
        if vector_db_type == "chroma":
            self._initialize_chroma()
        elif vector_db_type == "qdrant":
            self._initialize_qdrant()
        elif vector_db_type == "pinecone":
            self._initialize_pinecone()
        else:
            print(f"[WARNING] Unknown vector DB type '{vector_db_type}', defaulting to Chroma", file=sys.stderr, flush=True)
            self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize Chroma vector database."""
        try:
            import chromadb
            from llama_index.vector_stores.chroma import ChromaVectorStore
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
            
            # Skip embedding dimension check during startup to avoid blocking
            # Dimension will be checked when actually needed (when adding vectors)
            expected_dim = None
            
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
                    print(f"[OK] Created Chroma collection with dimension {expected_dim}", file=sys.stderr, flush=True)
                else:
                    print(f"[OK] Created Chroma collection", file=sys.stderr, flush=True)
            else:
                print(f"[OK] Using existing Chroma collection", file=sys.stderr, flush=True)
            
            # Create LlamaIndex vector store
            self.vector_store = ChromaVectorStore(chroma_collection=collection)
            
            print(f"[OK] Chroma vector store initialized: {chroma_path}", file=sys.stderr, flush=True)
        except ImportError as e:
            print(f"[ERROR] Missing Chroma dependencies: {e}", file=sys.stderr, flush=True)
            print("   Run: pip install chromadb llama-index-vector-stores-chroma", file=sys.stderr, flush=True)
            self.vector_store = None
        except Exception as e:
            print(f"[ERROR] Error initializing Chroma vector store: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.vector_store = None
    
    def _initialize_qdrant(self):
        """Initialize Qdrant vector database."""
        try:
            from llama_index.vector_stores.qdrant import QdrantVectorStore
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            # Initialize Qdrant client
            if settings.QDRANT_API_KEY:
                # Qdrant Cloud
                client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )
            else:
                # Local Qdrant
                client = QdrantClient(url=settings.QDRANT_URL)
            
            # Get expected embedding dimension (skip if not available to avoid blocking)
            expected_dim = 1536  # Default dimension
            try:
                dim = self._get_embedding_dimension(timeout=1.0)
                if dim:
                    expected_dim = dim
            except Exception:
                pass  # Use default if check blocks
            
            # Check if collection exists
            try:
                collection_info = client.get_collection(self.collection_name)
                print(f"[OK] Using existing Qdrant collection: {self.collection_name}", file=sys.stderr, flush=True)
            except:
                # Create collection if it doesn't exist
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=expected_dim,
                        distance=models.Distance.COSINE
                    )
                )
                print(f"[OK] Created Qdrant collection '{self.collection_name}' with dimension {expected_dim}", file=sys.stderr, flush=True)
            
            # Create LlamaIndex vector store
            self.vector_store = QdrantVectorStore(
                client=client,
                collection_name=self.collection_name
            )
            
            self.qdrant_client = client
            print(f"[OK] Qdrant vector store initialized: {settings.QDRANT_URL}", file=sys.stderr, flush=True)
        except ImportError as e:
            print(f"[ERROR] Missing Qdrant dependencies: {e}", file=sys.stderr, flush=True)
            print("   Run: pip install qdrant-client llama-index-vector-stores-qdrant", file=sys.stderr, flush=True)
            self.vector_store = None
        except Exception as e:
            print(f"[ERROR] Error initializing Qdrant vector store: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.vector_store = None
    
    def _initialize_pinecone(self):
        """Initialize Pinecone vector database."""
        try:
            from llama_index.vector_stores.pinecone import PineconeVectorStore
            from pinecone import Pinecone, ServerlessSpec
            import os
            
            if not settings.PINECONE_API_KEY:
                raise ValueError("PINECONE_API_KEY is required for Pinecone")
            
            # Initialize Pinecone client
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Get expected embedding dimension (skip if not available to avoid blocking)
            expected_dim = 1536  # Default dimension
            try:
                dim = self._get_embedding_dimension(timeout=1.0)
                if dim:
                    expected_dim = dim
            except Exception:
                pass  # Use default if check blocks
            
            # Check if index exists
            index_name = settings.PINECONE_INDEX_NAME
            existing_indexes = [idx.name for idx in pc.list_indexes()]
            
            if index_name not in existing_indexes:
                # Create index if it doesn't exist
                pc.create_index(
                    name=index_name,
                    dimension=expected_dim,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )
                print(f"[OK] Created Pinecone index '{index_name}' with dimension {expected_dim}", file=sys.stderr, flush=True)
            else:
                print(f"[OK] Using existing Pinecone index: {index_name}", file=sys.stderr, flush=True)
            
            # Get index
            index = pc.Index(index_name)
            
            # Create LlamaIndex vector store
            self.vector_store = PineconeVectorStore(
                pinecone_index=index,
                index_name=index_name
            )
            
            self.pinecone_client = pc
            print(f"[OK] Pinecone vector store initialized: {index_name}", file=sys.stderr, flush=True)
        except ImportError as e:
            print(f"[ERROR] Missing Pinecone dependencies: {e}", file=sys.stderr, flush=True)
            print("   Run: pip install pinecone-client llama-index-vector-stores-pinecone", file=sys.stderr, flush=True)
            self.vector_store = None
        except Exception as e:
            print(f"[ERROR] Error initializing Pinecone vector store: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.vector_store = None
    
    def recreate_collection(self) -> bool:
        """
        Recreate the collection (useful after embedding model change).
        WARNING: This will delete all existing vectors!
        """
        if settings.VECTOR_DB_TYPE != "chroma" or not self.chroma_client:
            return False
        
        try:
            from llama_index.vector_stores.chroma import ChromaVectorStore
            
            # Delete existing collection
            try:
                self.chroma_client.delete_collection(name=self.collection_name)
                print(f"[INFO] Deleted existing collection: {self.collection_name}", file=sys.stderr, flush=True)
            except:
                pass  # Collection might not exist
            
            # Get expected dimension (skip if not available to avoid blocking)
            expected_dim = None
            try:
                expected_dim = self._get_embedding_dimension(timeout=1.0)
            except Exception:
                pass  # Skip dimension check if it blocks
            
            # Create new collection
            collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Recreate vector store
            self.vector_store = ChromaVectorStore(chroma_collection=collection)
            
            if expected_dim:
                print(f"[OK] Recreated collection with dimension {expected_dim}", file=sys.stderr, flush=True)
            else:
                print(f"[OK] Recreated collection", file=sys.stderr, flush=True)
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to recreate collection: {e}", file=sys.stderr, flush=True)
            return False
    
    def get_vector_store(self):
        """Get the vector store instance."""
        return self.vector_store
    
    def is_available(self) -> bool:
        """Check if vector store is available."""
        return self.vector_store is not None
    
    def delete_by_ids(self, ids: List[str]) -> bool:
        """Delete vectors by IDs."""
        if not self.is_available():
            return False
        
        try:
            if settings.VECTOR_DB_TYPE == "chroma" and self.chroma_client:
                collection = self.chroma_client.get_collection("novaintel_documents")
                collection.delete(ids=ids)
                return True
            elif settings.VECTOR_DB_TYPE == "qdrant" and self.qdrant_client:
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=ids
                )
                return True
            elif settings.VECTOR_DB_TYPE == "pinecone" and self.pinecone_client:
                index = self.pinecone_client.Index(settings.PINECONE_INDEX_NAME)
                index.delete(ids=ids)
                return True
            return False
        except Exception as e:
            print(f"Error deleting vectors: {e}", file=sys.stderr, flush=True)
            return False
    
    def delete_by_metadata_filter(self, filter_dict: Dict[str, Any]) -> bool:
        """Delete vectors by metadata filter."""
        if not self.is_available():
            return False
        
        try:
            if settings.VECTOR_DB_TYPE == "chroma" and self.chroma_client:
                collection = self.chroma_client.get_collection("novaintel_documents")
                # Convert filter dict to Chroma format
                where = filter_dict
                collection.delete(where=where)
                return True
            elif settings.VECTOR_DB_TYPE == "qdrant" and self.qdrant_client:
                # Qdrant uses filter expressions
                from qdrant_client.http import models
                filter_expr = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filter_dict.items()
                    ]
                )
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.FilterSelector(filter=filter_expr)
                )
                return True
            elif settings.VECTOR_DB_TYPE == "pinecone" and self.pinecone_client:
                # Pinecone delete by metadata filter
                index = self.pinecone_client.Index(settings.PINECONE_INDEX_NAME)
                index.delete(filter=filter_dict)
                return True
            return False
        except Exception as e:
            print(f"Error deleting vectors by filter: {e}", file=sys.stderr, flush=True)
            return False

# Global instance
vector_store_manager = VectorStoreManager()
