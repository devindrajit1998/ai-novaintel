"""
Entity extraction for knowledge graph construction.
Extracts entities (companies, industries, technologies, challenges, solutions) from documents.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from utils.llm_factory import get_llm
from utils.model_router import TaskType
import sys


class Entity(BaseModel):
    """Represents an entity in the knowledge graph."""
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type: 'company', 'industry', 'technology', 'challenge', 'solution', 'metric'")
    description: Optional[str] = Field(None, description="Entity description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Relationship(BaseModel):
    """Represents a relationship between entities."""
    source: str = Field(description="Source entity name")
    target: str = Field(description="Target entity name")
    relationship_type: str = Field(description="Relationship type: 'uses', 'solves', 'addresses', 'related_to', 'in_industry'")
    strength: float = Field(description="Relationship strength (0-1)")
    description: Optional[str] = Field(None, description="Relationship description")


class EntityExtractionOutput(BaseModel):
    """Output from entity extraction."""
    entities: List[Entity] = Field(description="List of extracted entities")
    relationships: List[Relationship] = Field(description="List of extracted relationships")


class EntityExtractor:
    """Extract entities and relationships from text documents."""
    
    def __init__(self):
        """Initialize entity extractor."""
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM."""
        try:
            # Use Claude or GPT-4o for complex reasoning
            self.llm = get_llm(
                provider=None,
                temperature=0.1,
                task_type=TaskType.COMPLEX_REASONING
            )
            print("[OK] Entity Extractor initialized", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[WARNING] Entity Extractor initialization failed: {e}", file=sys.stderr, flush=True)
            self.llm = None
    
    def extract_entities(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships from text.
        
        Args:
            text: Text to extract entities from
            context: Optional context (e.g., document type, industry)
        
        Returns:
            dict with 'entities' and 'relationships'
        """
        if not self.llm:
            return {
                "entities": [],
                "relationships": [],
                "error": "LLM not initialized"
            }
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=EntityExtractionOutput)
        format_instructions = output_parser.get_format_instructions()
        
        context_section = ""
        if context:
            context_section = f"\nContext: {context}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting entities and relationships from business documents.
Extract:
1. Entities: companies, industries, technologies, challenges, solutions, metrics
2. Relationships: how entities relate to each other (uses, solves, addresses, related_to, in_industry)

Focus on business-relevant entities and relationships that would help with case study matching.

{format_instructions}"""),
            ("user", """Extract entities and relationships from the following text:

{text}
{context_section}

Provide entities and relationships in the specified JSON format.""")
        ])
        
        try:
            chain = prompt | self.llm | output_parser
            response = chain.invoke({
                "text": text[:5000],  # Limit text length
                "context_section": context_section,
                "format_instructions": format_instructions
            })
            
            if isinstance(response, EntityExtractionOutput):
                return {
                    "entities": [entity.model_dump() for entity in response.entities],
                    "relationships": [rel.model_dump() for rel in response.relationships],
                    "error": None
                }
            elif isinstance(response, dict):
                return response
            else:
                return {
                    "entities": [],
                    "relationships": [],
                    "error": "Failed to parse response"
                }
        except Exception as e:
            print(f"[WARNING] Entity extraction failed: {e}", file=sys.stderr, flush=True)
            return {
                "entities": [],
                "relationships": [],
                "error": str(e)
            }


# Global instance
entity_extractor = EntityExtractor()

