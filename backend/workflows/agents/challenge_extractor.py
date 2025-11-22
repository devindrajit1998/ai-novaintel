"""
Challenge Extractor Agent - Generates business/technical challenges from RFP.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from utils.config import settings
from utils.llm_factory import get_llm
from utils.model_router import TaskType
from workflows.schemas.output_schemas import ChallengesOutput
from workflows.prompts.prompt_templates import get_few_shot_challenge_extractor_prompt

class ChallengeExtractorAgent:
    """Agent that extracts challenges from RFP analysis."""
    
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM with intelligent routing."""
        try:
            # Use Claude for complex reasoning tasks
            self.llm = get_llm(
                provider=None,  # Auto-select
                temperature=0.2,
                task_type=TaskType.COMPLEX_REASONING,  # Challenge extraction requires reasoning
                prefer_provider=settings.LLM_PROVIDER if settings.LLM_PROVIDER in ["claude", "openai"] else None
            )
            print(f"✓ Challenge Extractor Agent initialized with intelligent routing")
        except Exception as e:
            print(f"Error initializing Challenge Extractor Agent: {e}")
    
    def extract_challenges(
        self,
        rfp_summary: str,
        business_objectives: List[str] = None
    ) -> Dict[str, Any]:
        """
        Extract business and technical challenges.
        
        Args:
            rfp_summary: Summary from RFP Analyzer
            business_objectives: List of business objectives
        
        Returns:
            dict with challenges list
        """
        if not self.llm:
            return {
                "challenges": [],
                "error": "LLM not initialized"
            }
        
        objectives_text = ""
        if business_objectives:
            objectives_text = "\n".join([f"- {obj}" for obj in business_objectives])
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=ChallengesOutput)
        format_instructions = output_parser.get_format_instructions()
        system_prompt = get_few_shot_challenge_extractor_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{system_prompt}

For each challenge, provide:
- Challenge description
- Type (Business/Technical/Compliance/Operational)
- Impact/Importance (High/Medium/Low)
- Category (optional)

{format_instructions}"""),
            ("user", """Based on the following RFP summary, identify the key challenges:

RFP Summary:
{rfp_summary}

Business Objectives:
{objectives}

Provide challenges in the specified JSON format.""")
        ])
        
        try:
            chain = prompt | self.llm | output_parser
            response = chain.invoke({
                "rfp_summary": rfp_summary or "No summary available",
                "objectives": objectives_text or "No objectives specified",
                "format_instructions": format_instructions
            })
            
            # Response is already parsed as Pydantic model
            if isinstance(response, ChallengesOutput):
                challenges = [challenge.model_dump() for challenge in response.challenges]
            elif isinstance(response, dict):
                challenges = response.get("challenges", [])
            else:
                # Fallback
                challenges = []
            
            return {
                "challenges": challenges,
                "error": None
            }
        
        except Exception as e:
            return {
                "challenges": [],
                "error": str(e)
            }

# Global instance
challenge_extractor_agent = ChallengeExtractorAgent()

