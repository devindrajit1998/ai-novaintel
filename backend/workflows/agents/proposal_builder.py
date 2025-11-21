"""
Proposal Builder Agent - Drafts complete proposal sections.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from utils.config import settings
from utils.llm_factory import get_llm

class ProposalBuilderAgent:
    """Agent that builds proposal drafts."""
    
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM."""
        try:
            self.llm = get_llm(provider=settings.LLM_PROVIDER, temperature=0.2)
            if self.llm:
                print(f"✓ Proposal Builder Agent initialized with {settings.LLM_PROVIDER}")
            else:
                print(f"⚠ Proposal Builder Agent: LLM not available")
        except Exception as e:
            print(f"⚠ Error initializing Proposal Builder Agent: {e}")
            import traceback
            traceback.print_exc()
            self.llm = None
    
    def build_proposal(
        self,
        rfp_summary: str,
        challenges: List[Dict[str, Any]],
        value_propositions: List[str],
        case_studies: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build proposal draft with all sections.
        
        Args:
            rfp_summary: RFP summary
            challenges: List of challenges
            value_propositions: List of value propositions
            case_studies: List of matched case studies
        
        Returns:
            dict with proposal_draft sections
        """
        if not self.llm:
            return {
                "proposal_draft": None,
                "error": "LLM not initialized"
            }
        
        challenges_text = ""
        if challenges:
            challenges_text = "\n".join([
                f"- {ch.get('description', '')}"
                for ch in challenges
            ])
        
        value_props_text = "\n".join([f"- {vp}" for vp in value_propositions]) if value_propositions else "None"
        
        case_studies_text = ""
        if case_studies:
            case_studies_text = "\n".join([
                f"- {cs.get('title', '')}: {cs.get('impact', '')}"
                for cs in case_studies
            ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert proposal writer. Create a comprehensive proposal draft with:
1. Executive Summary
2. Understanding Client Challenges
3. Proposed Solution
4. Benefits & Value Propositions
5. Case Studies & Success Stories
6. Implementation Approach

Write professionally, clearly, and focus on client value."""),
            ("user", """Create a proposal draft based on:

RFP Summary:
{rfp_summary}

Client Challenges:
{challenges}

Value Propositions:
{value_propositions}

Relevant Case Studies:
{case_studies}

Provide proposal in JSON format:
{{
    "executive_summary": "Executive summary text",
    "client_challenges": "Section on understanding challenges",
    "proposed_solution": "Our solution approach",
    "benefits_value": "Benefits and value propositions",
    "case_studies": "Case studies section",
    "implementation_approach": "How we will implement"
}}""")
        ])
        
        try:
            # Check if Gemini service is available
            from utils.gemini_service import gemini_service
            if not gemini_service.is_available():
                return {
                    "proposal_draft": None,
                    "error": "Gemini API key not configured"
                }
            
            chain = prompt | self.llm
            response = chain.invoke({
                "rfp_summary": rfp_summary or "No summary available",
                "challenges": challenges_text or "No challenges identified",
                "value_propositions": value_props_text,
                "case_studies": case_studies_text or "No case studies available"
            })
            
            # Check for errors in response
            if hasattr(response, 'error') and response.error:
                return {
                    "proposal_draft": None,
                    "error": response.error
                }
            
            # Parse JSON response
            import json
            import re
            
            # Get content from response
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            if not content:
                return {
                    "proposal_draft": None,
                    "error": "Empty response from LLM"
                }
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    proposal_draft = result
                except json.JSONDecodeError as e:
                    # JSON parsing failed, use fallback
                    print(f"⚠ Failed to parse JSON from proposal response: {e}")
                    proposal_draft = {
                        "executive_summary": content[:500] if content else "Executive summary",
                        "client_challenges": "Client challenges section",
                        "proposed_solution": "Proposed solution",
                        "benefits_value": value_props_text,
                        "case_studies": case_studies_text or "Case studies",
                        "implementation_approach": "Implementation approach"
                    }
            else:
                # No JSON found, create structure from content
                proposal_draft = {
                    "executive_summary": content[:500] if content else "Executive summary",
                    "client_challenges": challenges_text or "Client challenges section",
                    "proposed_solution": "Proposed solution based on RFP requirements",
                    "benefits_value": value_props_text or "Benefits and value propositions",
                    "case_studies": case_studies_text or "Case studies",
                    "implementation_approach": "Implementation approach"
                }
            
            return {
                "proposal_draft": proposal_draft,
                "error": None
            }
        
        except Exception as e:
            import traceback
            print(f"⚠ Proposal Builder error: {e}")
            traceback.print_exc()
            return {
                "proposal_draft": None,
                "error": f"Proposal generation failed: {str(e)}"
            }

# Global instance
proposal_builder_agent = ProposalBuilderAgent()

