"""
Challenge Extractor Agent - Generates business/technical challenges from RFP.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from utils.config import settings
from utils.llm_factory import get_llm

class ChallengeExtractorAgent:
    """Agent that extracts challenges from RFP analysis."""
    
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM."""
        try:
            self.llm = get_llm(provider=settings.LLM_PROVIDER, temperature=0.2)
            print(f"✓ Challenge Extractor Agent initialized with {settings.LLM_PROVIDER}")
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at identifying business and technical challenges from RFP documents.
Extract challenges that the client is facing or needs to address.
For each challenge, provide:
- Challenge description
- Type (Business/Technical/Compliance/Operational)
- Impact/Importance
- Potential solution direction"""),
            ("user", """Based on the following RFP summary, identify the key challenges:

RFP Summary:
{rfp_summary}

Business Objectives:
{objectives}

Provide challenges in JSON format:
{{
    "challenges": [
        {{
            "description": "Challenge description",
            "type": "Business|Technical|Compliance|Operational",
            "impact": "High|Medium|Low",
            "category": "Specific category",
            "solution_direction": "Brief solution hint"
        }},
        ...
    ]
}}""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "rfp_summary": rfp_summary or "No summary available",
                "objectives": objectives_text or "No objectives specified"
            })
            
            # Parse JSON response
            import json
            import re
            
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                challenges = result.get("challenges", [])
            else:
                # Fallback: create simple challenges from text
                challenges = [
                    {
                        "description": content[:200],
                        "type": "Business",
                        "impact": "High",
                        "category": "General",
                        "solution_direction": "To be determined"
                    }
                ]
            
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

