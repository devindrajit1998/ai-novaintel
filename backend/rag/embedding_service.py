"""
Embedding generation service using Hugging Face (free) or OpenAI.
"""
from typing import List
from utils.config import settings

class EmbeddingService:
    """Service for generating embeddings."""
    
    def __init__(self):
        self.embedding_model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize embedding model - Hugging Face only."""
        try:
            # Use Hugging Face embeddings (free)
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            
            self.embedding_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            print("[OK] Embedding service initialized: HuggingFace (all-MiniLM-L6-v2)")
        except ImportError as e:
            print(f"[ERROR] Missing HuggingFace dependencies: {e}")
            print("   Run: pip install llama-index-embeddings-huggingface sentence-transformers")
            self.embedding_model = None
        except Exception as e:
            print(f"[ERROR] Error initializing HuggingFace embeddings: {e}")
            import traceback
            traceback.print_exc()
            print("[WARNING] No embedding service available")
            self.embedding_model = None
    
    def get_embedding_model(self):
        """Get the embedding model instance."""
        return self.embedding_model
    
    def is_available(self) -> bool:
        """Check if embedding service is available."""
        return self.embedding_model is not None
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        if not self.is_available():
            raise ValueError("Embedding service not available")
        
        return self.embedding_model.get_query_embedding(text)
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        if not self.is_available():
            raise ValueError("Embedding service not available")
        
        return self.embedding_model.get_text_embedding_batch(texts)

# Global instance
embedding_service = EmbeddingService()

