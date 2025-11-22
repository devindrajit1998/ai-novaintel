"""
Reranking service for improving retrieval relevance using cross-encoder models.
Supports Cohere Rerank (best quality) and BGE-Reranker (open-source).
"""
from typing import List, Dict, Any, Optional
from utils.config import settings
import sys

class RerankingService:
    """Service for reranking retrieval results to improve relevance."""
    
    def __init__(self):
        self.reranker = None
        self.provider = None
        self._initialize()
    
    def _initialize(self):
        """Initialize reranking model - Cohere (best) or BGE-Reranker (open-source)."""
        # Try Cohere first if API key available
        if settings.COHERE_API_KEY:
            try:
                import cohere
                self.reranker = cohere.Client(api_key=settings.COHERE_API_KEY)
                self.provider = "cohere"
                print("[OK] Reranking service initialized: Cohere Rerank")
                return
            except ImportError:
                print("[WARNING] Cohere package not installed. Install: pip install cohere")
            except Exception as e:
                print(f"[WARNING] Failed to initialize Cohere reranker: {e}")
        
        # Fallback to BGE-Reranker (open-source)
        try:
            from sentence_transformers import CrossEncoder
            # Use BGE reranker model
            model_name = "BAAI/bge-reranker-base"  # Can upgrade to "BAAI/bge-reranker-large"
            self.reranker = CrossEncoder(model_name)
            self.provider = "bge"
            print(f"[OK] Reranking service initialized: BGE-Reranker ({model_name})")
        except ImportError:
            print("[WARNING] sentence-transformers not available for reranking")
            print("   Install: pip install sentence-transformers")
            self.reranker = None
        except Exception as e:
            print(f"[WARNING] Failed to initialize BGE reranker: {e}")
            self.reranker = None
    
    def is_available(self) -> bool:
        """Check if reranking service is available."""
        return self.reranker is not None
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: The search query
            documents: List of dicts with 'text' and optionally 'score', 'metadata'
            top_k: Number of top results to return (None = return all)
        
        Returns:
            Reranked list of documents with 'text', 'rerank_score', 'metadata'
        """
        if not self.is_available():
            return documents  # Return as-is if reranking unavailable
        
        if not documents:
            return []
        
        try:
            if self.provider == "cohere":
                return self._rerank_cohere(query, documents, top_k)
            elif self.provider == "bge":
                return self._rerank_bge(query, documents, top_k)
            else:
                return documents
        except Exception as e:
            print(f"[ERROR] Reranking failed: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return documents  # Return original on error
    
    def _rerank_cohere(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Rerank using Cohere API."""
        # Extract texts
        doc_texts = [doc.get('text', '') for doc in documents]
        
        # Cohere rerank API
        if top_k:
            results = self.reranker.rerank(
                model="rerank-english-v3.0",  # Best model
                query=query,
                documents=doc_texts,
                top_n=top_k,
                return_documents=False
            )
        else:
            results = self.reranker.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=doc_texts,
                top_n=len(doc_texts),
                return_documents=False
            )
        
        # Map results back to original documents
        reranked = []
        for result in results:
            original_idx = result.index
            original_doc = documents[original_idx]
            
            reranked.append({
                'text': original_doc.get('text', ''),
                'rerank_score': result.relevance_score,
                'score': original_doc.get('score', 0.0),  # Original score
                'metadata': original_doc.get('metadata', {}),
                **{k: v for k, v in original_doc.items() if k not in ['text', 'score', 'metadata']}
            })
        
        return reranked
    
    def _rerank_bge(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Rerank using BGE-Reranker (local model)."""
        # Create query-document pairs
        pairs = [[query, doc.get('text', '')] for doc in documents]
        
        # Get rerank scores
        scores = self.reranker.predict(pairs)
        
        # Combine with original documents
        scored_docs = []
        for doc, score in zip(documents, scores):
            scored_docs.append({
                'text': doc.get('text', ''),
                'rerank_score': float(score),
                'score': doc.get('score', 0.0),
                'metadata': doc.get('metadata', {}),
                **{k: v for k, v in doc.items() if k not in ['text', 'score', 'metadata']}
            })
        
        # Sort by rerank score (descending)
        scored_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        # Return top_k if specified
        if top_k:
            return scored_docs[:top_k]
        
        return scored_docs

# Global instance
reranking_service = RerankingService()

