"""
Index builder for RAG pipeline.
"""
from typing import List, Optional, Dict, Any
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import BaseNode
from rag.vector_store import vector_store_manager
from rag.document_processor import document_processor
from rag.embedding_service import embedding_service
from db.database import get_db
from models.rfp_document import RFPDocument
from sqlalchemy.orm import Session

class IndexBuilder:
    """Build and manage vector indexes."""
    
    def __init__(self):
        self.vector_store = vector_store_manager.get_vector_store()
    
    def build_index_from_file(
        self,
        file_path: str,
        file_type: str,
        project_id: int,
        rfp_document_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Build index from a file.
        
        Args:
            file_path: Path to the file
            file_type: File extension
            project_id: Project ID
            rfp_document_id: RFP document ID
            db: Database session
        
        Returns:
            dict with index information
        """
        if not vector_store_manager.is_available():
            return {
                'success': False,
                'error': 'Vector store not available. Please ensure Chroma dependencies are installed and the backend has been restarted.'
            }
        
        if not embedding_service.is_available():
            return {
                'success': False,
                'error': 'Embedding service not available. Please ensure HuggingFace dependencies are installed and the backend has been restarted.'
            }
        
        # Process file
        process_result = document_processor.process_file(
            file_path=file_path,
            file_type=file_type,
            project_id=project_id,
            rfp_document_id=rfp_document_id
        )
        
        if not process_result.get('success'):
            return process_result
        
        nodes: List[BaseNode] = process_result['nodes']
        
        if not nodes:
            return {
                'success': False,
                'error': 'No nodes generated from document'
            }
        
        try:
            # Create storage context
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            
            # Create index from nodes
            index = VectorStoreIndex(
                nodes=nodes,
                storage_context=storage_context,
                show_progress=True
            )
            
            # Update RFP document with extracted text
            rfp_doc = db.query(RFPDocument).filter(
                RFPDocument.id == rfp_document_id
            ).first()
            
            if rfp_doc:
                rfp_doc.extracted_text = process_result['document'].text
                rfp_doc.page_count = process_result['extraction_result'].get('page_count')
                db.commit()
            
            return {
                'success': True,
                'index_id': f"project_{project_id}_rfp_{rfp_document_id}",
                'chunk_count': len(nodes),
                'document_id': rfp_document_id,
                'message': f'Index built successfully with {len(nodes)} chunks'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Error building index: {str(e)}'
            }
    
    def delete_index_for_document(
        self,
        project_id: int,
        rfp_document_id: int
    ) -> bool:
        """
        Delete index for a specific document.
        
        Args:
            project_id: Project ID
            rfp_document_id: RFP document ID
        
        Returns:
            bool indicating success
        """
        if not vector_store_manager.is_available():
            return False
        
        try:
            # Delete vectors by metadata filter
            filter_dict = {
                'project_id': project_id,
                'rfp_document_id': rfp_document_id
            }
            return vector_store_manager.delete_by_metadata_filter(filter_dict)
        except Exception as e:
            print(f"Error deleting index: {e}")
            return False

# Global instance
index_builder = IndexBuilder()

