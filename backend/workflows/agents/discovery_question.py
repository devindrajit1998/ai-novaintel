"""
Discovery Question Agent - Generates categorized discovery questions.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from utils.config import settings
from utils.llm_factory import get_llm
from utils.model_router import TaskType
from workflows.schemas.output_schemas import DiscoveryQuestionsOutput
from workflows.prompts.prompt_templates import get_few_shot_discovery_question_prompt

class DiscoveryQuestionAgent:
    """Agent that generates discovery questions."""
    
    def __init__(self):
        self.llm = None
        self.categories = ["Business", "Technology", "KPIs", "Compliance"]
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM with intelligent routing."""
        try:
            # Use Gemini Flash for fast generation (questions are straightforward)
            self.llm = get_llm(
                provider=None,  # Auto-select
                temperature=0.3,
                task_type=TaskType.FAST_GENERATION,  # Fast generation
                prefer_provider=settings.LLM_PROVIDER
            )
            print(f"✓ Discovery Question Agent initialized with intelligent routing")
        except Exception as e:
            print(f"Error initializing Discovery Question Agent: {e}")
    
    def generate_questions(
        self,
        challenges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate discovery questions categorized by type.
        
        Args:
            challenges: List of challenges from Challenge Extractor
        
        Returns:
            dict with discovery_questions by category
        """
        if not self.llm:
            return {
                "discovery_questions": {},
                "error": "LLM not initialized"
            }
        
        challenges_text = ""
        if challenges:
            challenges_text = "\n".join([
                f"- {ch.get('description', '')} (Type: {ch.get('type', 'Unknown')})"
                for ch in challenges
            ])
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=DiscoveryQuestionsOutput)
        format_instructions = output_parser.get_format_instructions()
        system_prompt = get_few_shot_discovery_question_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{system_prompt}

Organize questions by category: Business, Technology, KPIs, Compliance, and Other.
Generate 3-5 questions per category.

{format_instructions}"""),
            ("user", """Based on these challenges, generate discovery questions:

Challenges:
{challenges}

Provide questions in the specified JSON format.""")
        ])
        
        try:
            chain = prompt | self.llm | output_parser
            response = chain.invoke({
                "challenges": challenges_text or "No challenges identified",
                "format_instructions": format_instructions
            })
            
            # Response is already parsed as Pydantic model
            if isinstance(response, DiscoveryQuestionsOutput):
                questions = {
                    "Business": response.business_questions,
                    "Technology": response.technical_questions,
                    "KPIs": response.kpi_questions,
                    "Compliance": response.compliance_questions,
                    "Other": response.other_questions
                }
            elif isinstance(response, dict):
                questions = {
                    "Business": response.get("business_questions", []),
                    "Technology": response.get("technical_questions", []),
                    "KPIs": response.get("kpi_questions", []),
                    "Compliance": response.get("compliance_questions", []),
                    "Other": response.get("other_questions", [])
                }
            else:
                # Fallback
                questions = {
                    "Business": ["What are your primary business objectives?"],
                    "Technology": ["What is your current technology stack?"],
                    "KPIs": ["What metrics do you track?"],
                    "Compliance": ["What compliance requirements must be met?"],
                    "Other": []
                }
            
            return {
                "discovery_questions": questions,
                "error": None
            }
        
        except Exception as e:
            return {
                "discovery_questions": {},
                "error": str(e)
            }

# Global instance
discovery_question_agent = DiscoveryQuestionAgent()

