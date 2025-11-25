"""
Embedding generation service using OpenAI (recommended) or Hugging Face (free fallback).
"""
from typing import List, Optional
from utils.config import settings
from services.cache.rag_cache import rag_cache

class EmbeddingService:
    """Service for generating embeddings with caching. Supports OpenAI and HuggingFace."""
    
    def __init__(self):
        self.embedding_model = None
        self.embedding_dimension = None
        self.provider = None
        self.cache = rag_cache
        self._initialize()
    
    def _initialize(self):
        """Initialize embedding model - Supports OpenAI (best quality) or HuggingFace (free)."""
        embedding_provider = getattr(settings, 'EMBEDDING_PROVIDER', 'openai').lower()
        
        # Try OpenAI first if configured
        if embedding_provider == 'openai' and settings.OPENAI_API_KEY:
            try:
                from llama_index.embeddings.openai import OpenAIEmbedding
                
                model_name = getattr(settings, 'EMBEDDING_MODEL', 'text-embedding-3-large')
                
                # Initialize OpenAI embeddings
                self.embedding_model = OpenAIEmbedding(
                    model=model_name,
                    api_key=settings.OPENAI_API_KEY
                )
                self.provider = "openai"
                
                # Set dimension based on model
                if "3-large" in model_name:
                    self.embedding_dimension = 3072
                elif "3-small" in model_name:
                    self.embedding_dimension = 1536
                else:
                    self.embedding_dimension = 1536  # Default for ada-002
                
                print(f"[OK] Embedding service initialized: OpenAI ({model_name}) - {self.embedding_dimension}d")
                return
            except ImportError as e:
                print(f"[WARNING] OpenAI embedding dependencies not found: {e}")
                print("   Install: pip install llama-index-embeddings-openai")
            except Exception as e:
                print(f"[WARNING] Failed to initialize OpenAI embeddings: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback to HuggingFace (free)
        # Note: This initialization might take time if models need to be downloaded
        # We catch exceptions to avoid blocking server startup
        try:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            
            embedding_model_name = getattr(settings, 'EMBEDDING_MODEL', 'sentence-transformers/all-mpnet-base-v2')
            
            # Fallback chain: mpnet -> MiniLM if mpnet fails
            models_to_try = [
                embedding_model_name,
                'sentence-transformers/all-mpnet-base-v2',  # Better quality, 768d
                'sentence-transformers/all-MiniLM-L6-v2'   # Fallback: smaller, faster
            ]
            
            for model_name in models_to_try:
                try:
                    # Try to initialize - if this blocks, we'll catch and continue
                    self.embedding_model = HuggingFaceEmbedding(
                        model_name=model_name
                    )
                    self.provider = "huggingface"
                    # HuggingFace models are typically 384d or 768d
                    if "mpnet" in model_name.lower():
                        self.embedding_dimension = 768
                    else:
                        self.embedding_dimension = 384
                    print(f"[OK] Embedding service initialized: HuggingFace ({model_name}) - {self.embedding_dimension}d")
                    break
                except Exception as e:
                    if model_name == models_to_try[-1]:
                        # Last model failed, but don't raise - just set to None
                        print(f"[WARNING] Failed to load any HuggingFace model: {e}")
                        self.embedding_model = None
                        break
                    print(f"[INFO] Failed to load {model_name}, trying next model...")
                    continue
                    
        except ImportError as e:
            print(f"[WARNING] Missing HuggingFace dependencies: {e}")
            print("   Run: pip install llama-index-embeddings-huggingface sentence-transformers")
            self.embedding_model = None
        except Exception as e:
            # Catch any other exceptions to prevent blocking server startup
            print(f"[WARNING] Error initializing embeddings (non-blocking): {e}")
            self.embedding_model = None
    
    def get_embedding_dimension(self) -> Optional[int]:
        """Get the dimension of embeddings."""
        return self.embedding_dimension
    
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
        try:
            if self.provider == "openai":
                # OpenAI embeddings
                embedding = self.embedding_model.get_query_embedding(text)
            else:
                # HuggingFace embeddings
                embedding = self.embedding_model.get_query_embedding(text)
        except Exception as e:
            print(f"[ERROR] Failed to generate embedding: {e}")
            raise
        
        # Cache it
        if use_cache and embedding:
            self.cache.set_embedding(text, embedding)
        
        return embedding
    
    def get_embeddings(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """Get embeddings for multiple texts with caching and batching."""
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
        
        # Generate embeddings for uncached texts in batches
        if texts_to_embed:
            text_list = [text for _, text in texts_to_embed]
            
            try:
                # Batch processing - OpenAI handles batching automatically
                if self.provider == "openai":
                    # OpenAI can handle larger batches
                    batch_size = 100
                    new_embeddings = []
                    for i in range(0, len(text_list), batch_size):
                        batch = text_list[i:i+batch_size]
                        batch_embeddings = self.embedding_model.get_text_embedding_batch(batch)
                        new_embeddings.extend(batch_embeddings)
                else:
                    # HuggingFace batching
                    batch_size = 32
                    new_embeddings = []
                    for i in range(0, len(text_list), batch_size):
                        batch = text_list[i:i+batch_size]
                        batch_embeddings = self.embedding_model.get_text_embedding_batch(batch)
                        new_embeddings.extend(batch_embeddings)
                
                # Cache and store new embeddings
                for (i, text), embedding in zip(texts_to_embed, new_embeddings):
                    if use_cache and embedding:
                        self.cache.set_embedding(text, embedding)
                    embeddings.append((i, embedding))
            except Exception as e:
                print(f"[ERROR] Failed to generate batch embeddings: {e}")
                raise
        
        # Sort by original index and return
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]

# Global instance
embedding_service = EmbeddingService()

