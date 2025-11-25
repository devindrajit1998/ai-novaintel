"""
Value Proposition Agent - Creates value propositions mapped to challenges.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from utils.config import settings
from utils.llm_factory import get_llm
from utils.model_router import TaskType
from workflows.schemas.output_schemas import ValuePropositionsOutput
from workflows.prompts.prompt_templates import get_few_shot_value_proposition_prompt

class ValuePropositionAgent:
    """Agent that generates value propositions."""
    
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM with intelligent routing."""
        try:
            # Use Claude for creative tasks
            self.llm = get_llm(
                provider=None,  # Auto-select
                temperature=0.2,
                task_type=TaskType.CREATIVE,  # Value props require creativity
                prefer_provider=settings.LLM_PROVIDER if settings.LLM_PROVIDER in ["claude", "openai"] else None
            )
            print(f"✓ Value Proposition Agent initialized with intelligent routing")
        except Exception as e:
            print(f"Error initializing Value Proposition Agent: {e}")
    
    def generate_value_propositions(
        self,
        challenges: List[Dict[str, Any]],
        rfp_summary: str = None
    ) -> Dict[str, Any]:
        """
        Generate value propositions aligned with challenges.
        
        Args:
            challenges: List of challenges
            rfp_summary: Optional RFP summary for context
        
        Returns:
            dict with value_propositions list
        """
        if not self.llm:
            return {
                "value_propositions": [],
                "error": "LLM not initialized"
            }
        
        challenges_text = ""
        if challenges:
            challenges_text = "\n".join([
                f"- {ch.get('description', '')} (Impact: {ch.get('impact', 'Unknown')})"
                for ch in challenges
            ])
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=ValuePropositionsOutput)
        
        # Simple format instructions without JSON schema to avoid template parsing issues
        # Use escaped curly braces to prevent LangChain from treating JSON field names as template variables
        format_instructions_simple = """Return your response as a valid JSON object with a value_propositions array of strings.

Example: {{"value_propositions": ["Value prop 1", "Value prop 2", ...]}}"""
        
        system_prompt = get_few_shot_value_proposition_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + """

Each value proposition should be:
- Specific and measurable
- Aligned with client challenges
- Focused on business outcomes
- Quantifiable where possible (e.g., "45% reduction in operational costs")

Generate 5-8 value propositions.
"""),
            ("user", """Based on these challenges, create value propositions:

Challenges:
{challenges}

RFP Context:
{rfp_summary}

{format_instructions}

Provide value propositions in the specified JSON format.""")
        ])
        
        try:
            chain = prompt | self.llm | output_parser
            response = chain.invoke({
                "challenges": challenges_text or "No challenges identified",
                "rfp_summary": rfp_summary or "No summary available",
                "format_instructions": format_instructions_simple
            })
            
            # Response is already parsed as Pydantic model
            if isinstance(response, ValuePropositionsOutput):
                value_props = response.value_propositions
            elif isinstance(response, dict):
                value_props = response.get("value_propositions", [])
            else:
                # Fallback: extract from text
                content = str(response)
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                value_props = lines[:5]  # Take first 5 lines
            
            return {
                "value_propositions": value_props,
                "error": None
            }
        
        except Exception as e:
            return {
                "value_propositions": [],
                "error": str(e)
            }

# Global instance
value_proposition_agent = ValuePropositionAgent()

