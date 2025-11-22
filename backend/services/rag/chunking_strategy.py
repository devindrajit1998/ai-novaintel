"""
Advanced chunking strategies for RAG document processing.
"""
from typing import List, Dict, Any, Optional
from llama_index.core import Document
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
    MarkdownNodeParser,
    CodeSplitter
)
from llama_index.core.schema import BaseNode, TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from rag.embedding_service import embedding_service


class ChunkingStrategy:
    """Base class for chunking strategies."""
    
    def chunk(self, document: Document) -> List[BaseNode]:
        """Chunk a document into nodes."""
        raise NotImplementedError


class FixedSizeChunker(ChunkingStrategy):
    """Fixed-size chunking (current default)."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=" "
        )
    
    def chunk(self, document: Document) -> List[BaseNode]:
        """Chunk using fixed size."""
        return self.parser.get_nodes_from_documents([document])


class SemanticChunker(ChunkingStrategy):
    """Semantic chunking - chunks by meaning using embeddings."""
    
    def __init__(
        self,
        buffer_size: int = 1,
        breakpoint_percentile_threshold: float = 95,
        chunk_size: int = 500
    ):
        """
        Args:
            buffer_size: Number of sentences to look back when computing breakpoint
            breakpoint_percentile_threshold: Percentile threshold for semantic similarity
            chunk_size: Max chunk size in tokens
        """
        self.buffer_size = buffer_size
        self.breakpoint_percentile_threshold = breakpoint_percentile_threshold
        self.chunk_size = chunk_size
        
        # Get embedding model
        embed_model = embedding_service.get_embedding_model()
        if not embed_model:
            raise ValueError("Embedding service not available for semantic chunking")
        
        try:
            self.parser = SemanticSplitterNodeParser(
                buffer_size=buffer_size,
                breakpoint_percentile_threshold=breakpoint_percentile_threshold,
                embed_model=embed_model
            )
        except Exception as e:
            print(f"[WARNING] Semantic chunking not available: {e}")
            print("   Falling back to fixed-size chunking")
            self.parser = SentenceSplitter(chunk_size=chunk_size)
    
    def chunk(self, document: Document) -> List[BaseNode]:
        """Chunk using semantic similarity."""
        try:
            return self.parser.get_nodes_from_documents([document])
        except Exception as e:
            print(f"[WARNING] Semantic chunking failed: {e}, using fallback")
            # Fallback to fixed-size
            fallback = SentenceSplitter(chunk_size=self.chunk_size)
            return fallback.get_nodes_from_documents([document])


class HierarchicalChunker(ChunkingStrategy):
    """Hierarchical chunking - creates parent-child relationships."""
    
    def __init__(self, chunk_sizes: List[int] = [2048, 512, 128], chunk_overlap: int = 50):
        """
        Args:
            chunk_sizes: List of chunk sizes from largest to smallest
            chunk_overlap: Overlap between chunks
        """
        self.chunk_sizes = chunk_sizes
        self.chunk_overlap = chunk_overlap
        self.parsers = [
            SentenceSplitter(chunk_size=size, chunk_overlap=chunk_overlap)
            for size in chunk_sizes
        ]
    
    def chunk(self, document: Document) -> List[BaseNode]:
        """Create hierarchical chunks."""
        all_nodes = []
        
        # Create chunks at each level
        for parser in self.parsers:
            nodes = parser.get_nodes_from_documents([document])
            
            # Add level metadata
            for node in nodes:
                if not hasattr(node, 'metadata'):
                    node.metadata = {}
                node.metadata['chunk_level'] = self.chunk_sizes.index(parser.chunk_size)
                node.metadata['chunk_size'] = parser.chunk_size
            
            all_nodes.extend(nodes)
        
        return all_nodes


class AdaptiveChunker(ChunkingStrategy):
    """Adaptive chunking - adjusts size based on content structure."""
    
    def __init__(
        self,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1000,
        preferred_chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.preferred_chunk_size = preferred_chunk_size
        self.chunk_overlap = chunk_overlap
        self.base_parser = SentenceSplitter(
            chunk_size=preferred_chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """Detect document sections (headers, paragraphs)."""
        sections = []
        lines = text.split('\n')
        current_section = {'title': '', 'content': [], 'start': 0}
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Detect headers (lines that are short and end without period)
            if (len(line_stripped) < 100 and 
                not line_stripped.endswith('.') and 
                line_stripped and
                i > 0):
                # Save previous section
                if current_section['content']:
                    current_section['content'] = '\n'.join(current_section['content'])
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line_stripped,
                    'content': [],
                    'start': i
                }
            else:
                current_section['content'].append(line)
        
        # Add last section
        if current_section['content']:
            current_section['content'] = '\n'.join(current_section['content'])
            sections.append(current_section)
        
        return sections
    
    def chunk(self, document: Document) -> List[BaseNode]:
        """Chunk adaptively based on content structure."""
        text = document.get_content()
        sections = self._detect_sections(text)
        
        nodes = []
        
        for section in sections:
            section_text = f"{section['title']}\n{section['content']}" if section['title'] else section['content']
            section_doc = Document(text=section_text, metadata=document.metadata.copy())
            
            # Determine chunk size based on section length
            section_length = len(section_text.split())
            if section_length < self.min_chunk_size:
                # Small section - use smaller chunks
                chunk_size = min(self.min_chunk_size, section_length)
            elif section_length > self.max_chunk_size:
                # Large section - use preferred size
                chunk_size = self.preferred_chunk_size
            else:
                # Medium section - use section length
                chunk_size = min(section_length, self.max_chunk_size)
            
            # Create parser with adaptive size
            parser = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            
            section_nodes = parser.get_nodes_from_documents([section_doc])
            
            # Add section metadata
            for node in section_nodes:
                if not hasattr(node, 'metadata'):
                    node.metadata = {}
                node.metadata['section_title'] = section['title']
                node.metadata['adaptive_chunk_size'] = chunk_size
            
            nodes.extend(section_nodes)
        
        return nodes if nodes else self.base_parser.get_nodes_from_documents([document])


class ChunkingStrategyFactory:
    """Factory for creating chunking strategies."""
    
    @staticmethod
    def create(strategy_type: str = "fixed", **kwargs) -> ChunkingStrategy:
        """
        Create a chunking strategy.
        
        Args:
            strategy_type: "fixed", "semantic", "hierarchical", or "adaptive"
            **kwargs: Strategy-specific parameters
        """
        if strategy_type == "fixed":
            return FixedSizeChunker(
                chunk_size=kwargs.get('chunk_size', 500),
                chunk_overlap=kwargs.get('chunk_overlap', 50)
            )
        elif strategy_type == "semantic":
            return SemanticChunker(
                buffer_size=kwargs.get('buffer_size', 1),
                breakpoint_percentile_threshold=kwargs.get('breakpoint_percentile_threshold', 95),
                chunk_size=kwargs.get('chunk_size', 500)
            )
        elif strategy_type == "hierarchical":
            return HierarchicalChunker(
                chunk_sizes=kwargs.get('chunk_sizes', [2048, 512, 128]),
                chunk_overlap=kwargs.get('chunk_overlap', 50)
            )
        elif strategy_type == "adaptive":
            return AdaptiveChunker(
                min_chunk_size=kwargs.get('min_chunk_size', 200),
                max_chunk_size=kwargs.get('max_chunk_size', 1000),
                preferred_chunk_size=kwargs.get('preferred_chunk_size', 500),
                chunk_overlap=kwargs.get('chunk_overlap', 50)
            )
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy_type}")

