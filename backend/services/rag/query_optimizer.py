"""
Query optimization for RAG: expansion, reranking, and hybrid search.
"""
from typing import List, Dict, Any, Optional, Tuple
from utils.gemini_service import gemini_service
from rag.embedding_service import embedding_service


class QueryExpander:
    """Expand queries with synonyms and related terms."""
    
    def __init__(self):
        self.llm = gemini_service
    
    def expand(self, query: str, max_expansions: int = 3) -> List[str]:
        """
        Expand query with related terms.
        
        Args:
            query: Original query
            max_expansions: Maximum number of expansion terms
        
        Returns:
            List of expanded query variations
        """
        if not self.llm.is_available():
            return [query]
        
        prompt = f"""Given the following query, generate {max_expansions} alternative phrasings or related terms that would help find the same information.

Query: {query}

Generate alternative phrasings that:
1. Use synonyms or related terms
2. Maintain the same intent
3. Are concise (1-5 words each)

Return only the alternative phrasings, one per line, without numbering or bullets."""

        try:
            result = self.llm.generate_content(prompt, temperature=0.3)
            if result.get("error"):
                return [query]
            
            content = result.get("content", "")
            if not content:
                return [query]
            
            # Parse expansions
            expansions = [
                line.strip()
                for line in content.split('\n')
                if line.strip() and len(line.strip()) < 100
            ]
            
            # Limit and add original
            expansions = expansions[:max_expansions]
            return [query] + expansions
        
        except Exception as e:
            print(f"[WARNING] Query expansion failed: {e}")
            return [query]


class QueryReranker:
    """Rerank retrieved results using cross-encoder models."""
    
    def __init__(self):
        self.reranker = None
        self._initialize()
    
    def _initialize(self):
        """Initialize reranker model."""
        try:
            from sentence_transformers import CrossEncoder
            # Use a lightweight cross-encoder for reranking
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            print("[OK] Query reranker initialized")
        except ImportError:
            print("[WARNING] sentence-transformers not available for reranking")
            self.reranker = None
        except Exception as e:
            print(f"[WARNING] Failed to initialize reranker: {e}")
            self.reranker = None
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: Query string
            documents: List of dicts with 'text' and optionally 'score'
            top_k: Return top K results (None for all)
        
        Returns:
            Reranked list of documents
        """
        if not self.reranker or not documents:
            return documents
        
        try:
            # Prepare pairs for reranking
            pairs = [(query, doc.get('text', '')) for doc in documents]
            
            # Get reranking scores
            scores = self.reranker.predict(pairs)
            
            # Combine with original documents
            reranked = []
            for doc, score in zip(documents, scores):
                doc_copy = doc.copy()
                doc_copy['rerank_score'] = float(score)
                reranked.append(doc_copy)
            
            # Sort by rerank score (descending)
            reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # Return top_k if specified
            if top_k:
                return reranked[:top_k]
            
            return reranked
        
        except Exception as e:
            print(f"[WARNING] Reranking failed: {e}")
            return documents


class HybridSearcher:
    """Hybrid search combining keyword (BM25) and semantic search."""
    
    def __init__(self):
        self.bm25_index = None
        self._initialize()
    
    def _initialize(self):
        """Initialize BM25 index."""
        try:
            from rank_bm25 import BM25Okapi
            # We'll build this dynamically per query
            self.bm25_available = True
        except ImportError:
            print("[WARNING] rank-bm25 not available. Install with: pip install rank-bm25")
            self.bm25_available = False
    
    def hybrid_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        semantic_scores: List[float],
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Combine keyword (BM25) and semantic scores.
        
        Args:
            query: Query string
            documents: List of documents with 'text'
            semantic_scores: Semantic similarity scores
            alpha: Weight for semantic (1-alpha for BM25)
        
        Returns:
            Documents with combined scores
        """
        if not self.bm25_available or not documents:
            # Return with semantic scores only
            for doc, score in zip(documents, semantic_scores):
                doc['hybrid_score'] = score
            return documents
        
        try:
            from rank_bm25 import BM25Okapi
            
            # Build BM25 index
            texts = [doc.get('text', '') for doc in documents]
            tokenized_texts = [text.lower().split() for text in texts]
            bm25 = BM25Okapi(tokenized_texts)
            
            # Get BM25 scores
            tokenized_query = query.lower().split()
            bm25_scores = bm25.get_scores(tokenized_query)
            
            # Normalize scores to [0, 1]
            if max(bm25_scores) > 0:
                bm25_scores = [s / max(bm25_scores) for s in bm25_scores]
            if max(semantic_scores) > 0:
                semantic_scores_norm = [s / max(semantic_scores) for s in semantic_scores]
            else:
                semantic_scores_norm = semantic_scores
            
            # Combine scores
            results = []
            for doc, bm25_score, sem_score in zip(documents, bm25_scores, semantic_scores_norm):
                hybrid_score = alpha * sem_score + (1 - alpha) * bm25_score
                doc_copy = doc.copy()
                doc_copy['hybrid_score'] = hybrid_score
                doc_copy['bm25_score'] = bm25_score
                doc_copy['semantic_score'] = sem_score
                results.append(doc_copy)
            
            # Sort by hybrid score
            results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            return results
        
        except Exception as e:
            print(f"[WARNING] Hybrid search failed: {e}")
            # Fallback to semantic only
            for doc, score in zip(documents, semantic_scores):
                doc['hybrid_score'] = score
            return documents


class QueryOptimizer:
    """Main query optimizer combining all techniques."""
    
    def __init__(self):
        self.expander = QueryExpander()
        self.reranker = QueryReranker()
        self.hybrid_searcher = HybridSearcher()
    
    def optimize_query(self, query: str, use_expansion: bool = True) -> List[str]:
        """
        Optimize query with expansion.
        
        Args:
            query: Original query
            use_expansion: Whether to expand the query
        
        Returns:
            List of query variations
        """
        if use_expansion:
            return self.expander.expand(query)
        return [query]
    
    def optimize_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        use_reranking: bool = True,
        use_hybrid: bool = False,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Optimize retrieval results.
        
        Args:
            query: Original query
            results: Retrieved results with 'text' and 'score'
            use_reranking: Whether to rerank results
            use_hybrid: Whether to use hybrid search (requires semantic scores)
            top_k: Return top K results
        
        Returns:
            Optimized results
        """
        if not results:
            return results
        
        # Apply reranking if enabled
        if use_reranking and self.reranker.reranker:
            results = self.reranker.rerank(query, results, top_k)
        
        # Apply hybrid search if enabled (requires semantic scores)
        if use_hybrid and 'score' in results[0]:
            semantic_scores = [r.get('score', 0.0) for r in results]
            results = self.hybrid_searcher.hybrid_search(query, results, semantic_scores)
        
        # Return top_k
        if top_k:
            return results[:top_k]
        
        return results

# Global instance
query_optimizer = QueryOptimizer()

