"""
Embedding generation service using Hugging Face (free) or OpenAI.
"""
from typing import List
from utils.config import settings
from services.cache.rag_cache import rag_cache

class EmbeddingService:
    """Service for generating embeddings with caching."""
    
    def __init__(self):
        self.embedding_model = None
        self.cache = rag_cache
        self._initialize()
    
    def _initialize(self):
        """Initialize embedding model - Upgraded to better quality."""
        try:
            # Use Hugging Face embeddings - upgraded to better model
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            from utils.config import settings
            
            # Try to get model from config, default to upgraded model
            embedding_model_name = getattr(settings, 'EMBEDDING_MODEL', 'sentence-transformers/all-mpnet-base-v2')
            
            # Fallback chain: mpnet -> MiniLM if mpnet fails
            models_to_try = [
                embedding_model_name,
                'sentence-transformers/all-mpnet-base-v2',  # Better quality, 768d
                'sentence-transformers/all-MiniLM-L6-v2'   # Fallback: smaller, faster
            ]
            
            for model_name in models_to_try:
                try:
                    self.embedding_model = HuggingFaceEmbedding(
                        model_name=model_name
                    )
                    print(f"[OK] Embedding service initialized: HuggingFace ({model_name})")
                    break
                except Exception as e:
                    if model_name == models_to_try[-1]:
                        raise e
                    print(f"[INFO] Failed to load {model_name}, trying next model...")
                    continue
                    
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
    
    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """Get embedding for a single text with caching."""
        if not self.is_available():
            raise ValueError("Embedding service not available")
        
        # Try cache first
        if use_cache:
            cached = self.cache.get_embedding(text)
            if cached is not None:
                return cached
        
        # Generate embedding
        embedding = self.embedding_model.get_query_embedding(text)
        
        # Cache it
        if use_cache and embedding:
            self.cache.set_embedding(text, embedding)
        
        return embedding
    
    def get_embeddings(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """Get embeddings for multiple texts with caching."""
        if not self.is_available():
            raise ValueError("Embedding service not available")
        
        embeddings = []
        texts_to_embed = []
        text_indices = []
        
        # Check cache for each text
        if use_cache:
            for i, text in enumerate(texts):
                cached = self.cache.get_embedding(text)
                if cached is not None:
                    embeddings.append((i, cached))
                else:
                    texts_to_embed.append((i, text))
        else:
            texts_to_embed = [(i, text) for i, text in enumerate(texts)]
        
        # Generate embeddings for uncached texts
        if texts_to_embed:
            text_list = [text for _, text in texts_to_embed]
            new_embeddings = self.embedding_model.get_text_embedding_batch(text_list)
            
            # Cache and store new embeddings
            for (i, text), embedding in zip(texts_to_embed, new_embeddings):
                if use_cache:
                    self.cache.set_embedding(text, embedding)
                embeddings.append((i, embedding))
        
        # Sort by original index and return
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]

# Global instance
embedding_service = EmbeddingService()

