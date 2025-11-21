"""
Discovery Question Agent - Generates categorized discovery questions.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from utils.config import settings
from utils.llm_factory import get_llm

class DiscoveryQuestionAgent:
    """Agent that generates discovery questions."""
    
    def __init__(self):
        self.llm = None
        self.categories = ["Business", "Technology", "KPIs", "Compliance"]
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM."""
        try:
            self.llm = get_llm(provider=settings.LLM_PROVIDER, temperature=0.3)
            print(f"✓ Discovery Question Agent initialized with {settings.LLM_PROVIDER}")
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating discovery questions for presales engagements.
Generate thoughtful, probing questions that help understand client needs, pain points, and requirements.
Organize questions by category: Business, Technology, KPIs, Compliance."""),
            ("user", """Based on these challenges, generate discovery questions:

Challenges:
{challenges}

Generate 3-5 questions per category. Provide in JSON format:
{{
    "Business": ["question1", "question2", ...],
    "Technology": ["question1", "question2", ...],
    "KPIs": ["question1", "question2", ...],
    "Compliance": ["question1", "question2", ...]
}}""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "challenges": challenges_text or "No challenges identified"
            })
            
            # Parse JSON response
            import json
            import re
            
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                questions = {
                    cat: result.get(cat, [])
                    for cat in self.categories
                }
            else:
                # Fallback: create default questions
                questions = {
                    "Business": ["What are your primary business objectives?"],
                    "Technology": ["What is your current technology stack?"],
                    "KPIs": ["What metrics do you track?"],
                    "Compliance": ["What compliance requirements must be met?"]
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

