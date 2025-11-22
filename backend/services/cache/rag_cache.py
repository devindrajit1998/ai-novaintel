"""
RAG-specific caching for queries, embeddings, and context.
"""
import hashlib
from typing import Optional, List, Dict, Any
from services.cache.cache_manager import cache_manager
from utils.config import settings


class RAGCache:
    """Caching layer for RAG operations."""
    
    def __init__(self):
        self.cache = cache_manager
    
    def _hash_query(self, query: str, project_id: Optional[int] = None) -> str:
        """Create a hash key for a query."""
        key_parts = [query]
        if project_id:
            key_parts.append(str(project_id))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_query_results(
        self,
        query: str,
        project_id: Optional[int] = None,
        top_k: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached query results."""
        if not self.cache.is_available():
            return None
        
        cache_key = f"rag:query:{self._hash_query(query, project_id)}:topk:{top_k}"
        return self.cache.get(cache_key)
    
    def set_query_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        project_id: Optional[int] = None,
        top_k: int = 5,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache query results."""
        if not self.cache.is_available():
            return False
        
        cache_key = f"rag:query:{self._hash_query(query, project_id)}:topk:{top_k}"
        ttl = ttl or settings.CACHE_TTL
        return self.cache.set(cache_key, results, ttl)
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        if not self.cache.is_available():
            return None
        
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"rag:embedding:{text_hash}"
        return self.cache.get(cache_key)
    
    def set_embedding(
        self,
        text: str,
        embedding: List[float],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache embedding for text."""
        if not self.cache.is_available():
            return False
        
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"rag:embedding:{text_hash}"
        ttl = ttl or settings.EMBEDDING_CACHE_TTL
        return self.cache.set(cache_key, embedding, ttl)
    
    def get_chat_response(
        self,
        query: str,
        project_id: int,
        conversation_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached chat response."""
        if not self.cache.is_available():
            return None
        
        query_hash = self._hash_query(query, project_id)
        cache_key = f"rag:chat:{query_hash}:conv:{conversation_hash}"
        return self.cache.get(cache_key)
    
    def set_chat_response(
        self,
        query: str,
        project_id: int,
        conversation_hash: str,
        response: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache chat response."""
        if not self.cache.is_available():
            return False
        
        query_hash = self._hash_query(query, project_id)
        cache_key = f"rag:chat:{query_hash}:conv:{conversation_hash}"
        ttl = ttl or settings.CACHE_TTL
        return self.cache.set(cache_key, response, ttl)
    
    def invalidate_project(self, project_id: int):
        """Invalidate all RAG cache for a project."""
        self.cache.invalidate_project(project_id)
    
    def invalidate_document(self, rfp_document_id: int, project_id: int):
        """Invalidate cache for a specific document."""
        patterns = [
            f"rag:query:*:project:{project_id}:doc:{rfp_document_id}",
            f"rag:context:*:project:{project_id}:doc:{rfp_document_id}",
        ]
        for pattern in patterns:
            self.cache.delete_pattern(pattern)

# Global instance
rag_cache = RAGCache()

