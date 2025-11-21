"""
Retrieval system for RAG pipeline.
"""
from typing import List, Optional, Dict, Any
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.retrievers import VectorIndexRetriever
from rag.vector_store import vector_store_manager
from rag.embedding_service import embedding_service

class Retriever:
    """Retrieve relevant context from vector store."""
    
    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.vector_store = vector_store_manager.get_vector_store()
    
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
        top_k: Optional[int] = None
    ) -> List[NodeWithScore]:
        """
        Retrieve relevant nodes for a query.
        
        Args:
            query: Query string
            project_id: Optional project ID to filter results
            top_k: Number of results to return (defaults to self.top_k)
        
        Returns:
            List of nodes with scores
        """
        if not vector_store_manager.is_available():
            return []
        
        if not embedding_service.is_available():
            return []
        
        top_k = top_k or self.top_k
        
        try:
            index = self.get_index()
            if not index:
                return []
            
            # Create retriever
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=top_k
            )
            
            # Retrieve nodes
            query_bundle = QueryBundle(query_str=query)
            nodes = retriever.retrieve(query_bundle)
            
            # Filter by project_id if provided
            if project_id:
                nodes = [
                    node for node in nodes
                    if node.node.metadata.get('project_id') == project_id
                ]
            
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

