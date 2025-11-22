"""
Document processing and chunking using LlamaIndex with advanced strategies.
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from llama_index.core import Document, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode
from utils.text_extractor import TextExtractor
from rag.embedding_service import embedding_service
from utils.config import settings
from services.rag.chunking_strategy import ChunkingStrategyFactory, ChunkingStrategy

class DocumentProcessor:
    """Process documents for RAG pipeline with advanced chunking."""
    
    def __init__(self, chunking_strategy: str = "fixed", **chunking_kwargs):
        """
        Initialize document processor.
        
        Args:
            chunking_strategy: "fixed", "semantic", "hierarchical", or "adaptive"
            **chunking_kwargs: Strategy-specific parameters
        """
        self.text_extractor = TextExtractor()
        self.chunk_size = 500  # tokens (default, may be overridden by strategy)
        self.chunk_overlap = 50  # tokens
        
        # Initialize chunking strategy
        try:
            self.chunking_strategy: ChunkingStrategy = ChunkingStrategyFactory.create(
                strategy_type=chunking_strategy,
                **chunking_kwargs
            )
            self.strategy_type = chunking_strategy
        except Exception as e:
            print(f"[WARNING] Failed to create {chunking_strategy} chunking strategy: {e}")
            print("   Falling back to fixed-size chunking")
            self.chunking_strategy = ChunkingStrategyFactory.create("fixed")
            self.strategy_type = "fixed"
        
        # Legacy node parser for backward compatibility
        self.node_parser = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separator=" "
        )
        
        # Set embedding model in Settings
        if embedding_service.is_available():
            Settings.embed_model = embedding_service.get_embedding_model()
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Extract text from file.
        
        Returns:
            dict with 'text', 'page_count', 'metadata', 'success'
        """
        return self.text_extractor.extract_text(file_path, file_type)
    
    def create_document(self, text: str, metadata: Optional[Dict] = None) -> Document:
        """
        Create a LlamaIndex Document from text.
        
        Args:
            text: The text content
            metadata: Optional metadata dictionary
        
        Returns:
            Document instance
        """
        doc_metadata = metadata or {}
        return Document(text=text, metadata=doc_metadata)
    
    def chunk_document(self, document: Document) -> List[BaseNode]:
        """
        Chunk a document into nodes using the configured strategy.
        
        Args:
            document: LlamaIndex Document
        
        Returns:
            List of nodes (chunks)
        """
        # Use the configured chunking strategy
        nodes = self.chunking_strategy.chunk(document)
        return nodes
    
    def process_file(
        self,
        file_path: str,
        file_type: str,
        project_id: int,
        rfp_document_id: int
    ) -> Dict[str, Any]:
        """
        Process a file: extract text, create document, and chunk it.
        
        Args:
            file_path: Path to the file
            file_type: File extension (pdf, docx)
            project_id: Project ID for metadata
            rfp_document_id: RFP document ID for metadata
        
        Returns:
            dict with 'document', 'nodes', 'extraction_result'
        """
        # Extract text
        extraction_result = self.extract_text_from_file(file_path, file_type)
        
        if not extraction_result.get('success'):
            return {
                'success': False,
                'error': extraction_result.get('error', 'Text extraction failed'),
                'document': None,
                'nodes': []
            }
        
        # Clean text
        text = self.text_extractor.clean_text(extraction_result['text'])
        
        if not text:
            return {
                'success': False,
                'error': 'No text extracted from file',
                'document': None,
                'nodes': []
            }
        
        # Create document with metadata
        metadata = {
            'project_id': project_id,
            'rfp_document_id': rfp_document_id,
            'file_type': file_type,
            'file_path': file_path,
            'page_count': extraction_result.get('page_count'),
            **extraction_result.get('metadata', {})
        }
        
        document = self.create_document(text, metadata)
        
        # Chunk document
        nodes = self.chunk_document(document)
        
        # Add metadata to each node
        for i, node in enumerate(nodes):
            node.metadata.update({
                'chunk_index': i,
                'total_chunks': len(nodes),
                **metadata
            })
        
        return {
            'success': True,
            'document': document,
            'nodes': nodes,
            'extraction_result': extraction_result,
            'chunk_count': len(nodes)
        }

# Global instance
document_processor = DocumentProcessor()

