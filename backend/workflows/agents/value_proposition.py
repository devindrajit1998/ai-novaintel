"""
Value Proposition Agent - Creates value propositions mapped to challenges.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from utils.config import settings
from utils.llm_factory import get_llm

class ValuePropositionAgent:
    """Agent that generates value propositions."""
    
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM."""
        try:
            self.llm = get_llm(provider=settings.LLM_PROVIDER, temperature=0.2)
            print(f"✓ Value Proposition Agent initialized with {settings.LLM_PROVIDER}")
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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at crafting compelling value propositions for presales.
Create value propositions that directly address client challenges and demonstrate clear business value.
Each value proposition should be:
- Specific and measurable
- Aligned with client challenges
- Focused on business outcomes
- Quantifiable where possible"""),
            ("user", """Based on these challenges, create value propositions:

Challenges:
{challenges}

RFP Context:
{rfp_summary}

Generate value propositions in JSON format:
{{
    "value_propositions": [
        "Value prop 1 (e.g., 45% reduction in operational costs)",
        "Value prop 2 (e.g., 99.9% uptime SLA)",
        ...
    ]
}}""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "challenges": challenges_text or "No challenges identified",
                "rfp_summary": rfp_summary or "No summary available"
            })
            
            # Parse JSON response
            import json
            import re
            
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                value_props = result.get("value_propositions", [])
            else:
                # Fallback: extract from text
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

