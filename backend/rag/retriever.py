"""
Retrieval system for RAG pipeline with caching and query optimization.
"""
from typing import List, Optional, Dict, Any
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.retrievers import VectorIndexRetriever
from rag.vector_store import vector_store_manager
from rag.embedding_service import embedding_service
from services.cache.rag_cache import rag_cache
from services.rag.query_optimizer import query_optimizer

class Retriever:
    """Retrieve relevant context from vector store with caching."""
    
    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.vector_store = vector_store_manager.get_vector_store()
        self.cache = rag_cache
    
    def get_index(self) -> Optional[VectorStoreIndex]:
        """Get or create vector store index."""
        if not self.vector_store:
            return None
        
        try:
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=storage_context
            )
            return index
        except Exception as e:
            print(f"Error creating index: {e}")
            return None
    
    def retrieve(
        self,
        query: str,
        project_id: Optional[int] = None,
        top_k: Optional[int] = None,
        use_cache: bool = True,
        use_query_expansion: bool = False,
        use_reranking: bool = True,
        use_hybrid: bool = False
    ) -> List[NodeWithScore]:
        """
        Retrieve relevant nodes for a query with caching and optimization.
        
        Args:
            query: Query string
            project_id: Optional project ID to filter results
            top_k: Number of results to return (defaults to self.top_k)
            use_cache: Whether to use cache
            use_query_expansion: Whether to expand query
            use_reranking: Whether to rerank results
            use_hybrid: Whether to use hybrid search
        
        Returns:
            List of nodes with scores
        """
        if not vector_store_manager.is_available():
            return []
        
        if not embedding_service.is_available():
            return []
        
        top_k = top_k or self.top_k
        
        # Try cache first (only if not using optimization)
        if use_cache and not (use_query_expansion or use_reranking or use_hybrid):
            cached_results = self.cache.get_query_results(query, project_id, top_k)
            if cached_results is not None:
                # Convert cached dicts back to NodeWithScore objects
                from llama_index.core.schema import TextNode
                nodes = []
                for result in cached_results:
                    node = TextNode(
                        text=result['text'],
                        metadata=result.get('metadata', {})
                    )
                    node_with_score = NodeWithScore(node=node, score=result.get('score', 0.0))
                    nodes.append(node_with_score)
                return nodes
        
        # Optimize query if expansion enabled
        queries = [query]
        if use_query_expansion:
            queries = query_optimizer.optimize_query(query, use_expansion=True)
        
        try:
            index = self.get_index()
            if not index:
                return []
            
            # Retrieve for all query variations
            all_nodes = []
            for q in queries:
                retriever = VectorIndexRetriever(
                    index=index,
                    similarity_top_k=top_k * 2 if len(queries) > 1 else top_k  # Get more if multiple queries
                )
                
                query_bundle = QueryBundle(query_str=q)
                nodes = retriever.retrieve(query_bundle)
                all_nodes.extend(nodes)
            
            # Filter by project_id if provided
            if project_id:
                all_nodes = [
                    node for node in all_nodes
                    if node.node.metadata.get('project_id') == project_id
                ]
            
            # Remove duplicates (by node ID or text)
            seen = set()
            unique_nodes = []
            for node in all_nodes:
                node_id = node.node.node_id if hasattr(node.node, 'node_id') else None
                node_text = node.node.get_content()[:100]  # First 100 chars as identifier
                identifier = node_id or node_text
                
                if identifier not in seen:
                    seen.add(identifier)
                    unique_nodes.append(node)
            
            # Convert to dict format for optimization
            results_dict = [
                {
                    'text': node.node.get_content(),
                    'score': node.score if hasattr(node, 'score') else 0.0,
                    'metadata': node.node.metadata,
                    'node': node  # Keep original for conversion back
                }
                for node in unique_nodes
            ]
            
            # Apply optimization (reranking, hybrid)
            if use_reranking or use_hybrid:
                # Use centralized reranking service if available
                if use_reranking:
                    try:
                        from services.rag.reranking_service import reranking_service
                        if reranking_service.is_available():
                            # Rerank before hybrid search
                            results_dict = reranking_service.rerank(query, results_dict, top_k=None)
                    except Exception as e:
                        print(f"[WARNING] Reranking service failed: {e}")
                
                # Apply hybrid search if enabled (with RRF)
                if use_hybrid and results_dict:
                    # Extract semantic scores
                    semantic_scores = [r.get('rerank_score') or r.get('score', 0.0) for r in results_dict]
                    # Use hybrid searcher directly with RRF
                    from services.rag.query_optimizer import query_optimizer
                    results_dict = query_optimizer.hybrid_searcher.hybrid_search(
                        query,
                        results_dict,
                        semantic_scores,
                        use_rrf=True  # Use Reciprocal Rank Fusion
                    )
                elif use_reranking:
                    # Just apply top_k after reranking
                    if top_k:
                        results_dict = results_dict[:top_k]
            else:
                # Sort by score and take top_k
                results_dict.sort(key=lambda x: x.get('score', 0.0), reverse=True)
                results_dict = results_dict[:top_k]
            
            # Convert back to NodeWithScore
            nodes = []
            for result in results_dict:
                if 'node' in result:
                    # Update score if reranked
                    node = result['node']
                    if 'rerank_score' in result:
                        node.score = result['rerank_score']
                    elif 'hybrid_score' in result:
                        node.score = result['hybrid_score']
                    nodes.append(node)
                else:
                    # Reconstruct node
                    from llama_index.core.schema import TextNode
                    text_node = TextNode(
                        text=result['text'],
                        metadata=result.get('metadata', {})
                    )
                    score = result.get('rerank_score') or result.get('hybrid_score') or result.get('score', 0.0)
                    node_with_score = NodeWithScore(node=text_node, score=score)
                    nodes.append(node_with_score)
            
            # Cache results (only if not using optimization)
            if use_cache and not (use_query_expansion or use_reranking or use_hybrid):
                cache_data = [
                    {
                        'text': node.node.get_content(),
                        'score': node.score if hasattr(node, 'score') else 0.0,
                        'metadata': node.node.metadata
                    }
                    for node in nodes
                ]
                self.cache.set_query_results(query, cache_data, project_id, top_k)
            
            return nodes
        
        except Exception as e:
            print(f"Error retrieving nodes: {e}")
            return []
    
    def get_context(
        self,
        query: str,
        project_id: Optional[int] = None,
        top_k: Optional[int] = None
    ) -> str:
        """
        Get context string from retrieved nodes.
        
        Args:
            query: Query string
            project_id: Optional project ID to filter results
            top_k: Number of results to return
        
        Returns:
            Combined context string
        """
        nodes = self.retrieve(query, project_id, top_k)
        
        if not nodes:
            return ""
        
        # Combine node texts
        context_parts = []
        for i, node in enumerate(nodes, 1):
            text = node.node.get_content()
            score = node.score if hasattr(node, 'score') else None
            context_parts.append(f"[Context {i}]{text}")
        
        return "\n\n".join(context_parts)
    
    def get_nodes_with_metadata(
        self,
        query: str,
        project_id: Optional[int] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get retrieved nodes with metadata.
        
        Returns:
            List of dicts with 'text', 'score', 'metadata'
        """
        nodes = self.retrieve(query, project_id, top_k)
        
        result = []
        for node in nodes:
            result.append({
                'text': node.node.get_content(),
                'score': node.score if hasattr(node, 'score') else None,
                'metadata': node.node.metadata
            })
        
        return result

# Global instance
retriever = Retriever(top_k=5)

