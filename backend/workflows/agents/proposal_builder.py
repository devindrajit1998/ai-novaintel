"""
Proposal Builder Agent - Drafts complete proposal sections.
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from utils.config import settings
from utils.llm_factory import get_llm
from utils.model_router import TaskType
from workflows.schemas.output_schemas import ProposalDraftOutput
from workflows.prompts.prompt_templates import get_few_shot_proposal_builder_prompt
from workflows.agents.proposal_refiner import proposal_refiner_agent

class ProposalBuilderAgent:
    """Agent that builds proposal drafts."""
    
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM with intelligent routing."""
        try:
            # Use GPT-4o or Claude for high-quality proposal generation
            self.llm = get_llm(
                provider=None,  # Auto-select
                temperature=0.2,
                task_type=TaskType.HIGH_QUALITY,  # High-quality output
                prefer_provider=settings.LLM_PROVIDER if settings.LLM_PROVIDER in ["openai", "claude"] else None
            )
            if self.llm:
                print(f"✓ Proposal Builder Agent initialized with intelligent routing")
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
        case_studies: List[Dict[str, Any]] = None,
        use_refinement: bool = True,
        max_refinement_iterations: int = 2
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
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=ProposalDraftOutput)
        format_instructions = output_parser.get_format_instructions()
        system_prompt = get_few_shot_proposal_builder_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{system_prompt}

Create a comprehensive proposal draft with:
1. Executive Summary (2-3 paragraphs)
2. Understanding Client Challenges (show you understand their pain points)
3. Proposed Solution (detailed solution approach)
4. Benefits & Value Propositions (clear business value)
5. Case Studies & Success Stories (relevant examples)
6. Implementation Approach (how you will deliver)

{format_instructions}"""),
            ("user", """Create a proposal draft based on:

RFP Summary:
{rfp_summary}

Client Challenges:
{challenges}

Value Propositions:
{value_propositions}

Relevant Case Studies:
{case_studies}

Provide proposal in the specified JSON format.""")
        ])
        
        try:
            # Check if Gemini service is available
            from utils.gemini_service import gemini_service
            if not gemini_service.is_available():
                return {
                    "proposal_draft": None,
                    "error": "Gemini API key not configured"
                }
            
            chain = prompt | self.llm | output_parser
            response = chain.invoke({
                "rfp_summary": rfp_summary or "No summary available",
                "challenges": challenges_text or "No challenges identified",
                "value_propositions": value_props_text,
                "case_studies": case_studies_text or "No case studies available",
                "format_instructions": format_instructions
            })
            
            # Check for errors in response
            if hasattr(response, 'error') and response.error:
                return {
                    "proposal_draft": None,
                    "error": response.error
                }
            
            # Response is already parsed as Pydantic model
            if isinstance(response, ProposalDraftOutput):
                proposal_draft = response.model_dump()
            elif isinstance(response, dict):
                proposal_draft = response
            else:
                # Fallback
                content = str(response)
                proposal_draft = {
                    "executive_summary": content[:500] if content else "Executive summary",
                    "client_challenges": challenges_text or "Client challenges section",
                    "proposed_solution": "Proposed solution based on RFP requirements",
                    "benefits_value": value_props_text or "Benefits and value propositions",
                    "case_studies": case_studies_text or "Case studies",
                    "implementation_approach": "Implementation approach"
                }
            
            # Apply refinement if enabled
            refinement_results = None
            if use_refinement and proposal_draft:
                print(f"  [Proposal Builder] Starting refinement (max {max_refinement_iterations} iterations)...")
                try:
                    # Review proposal
                    review_results = proposal_refiner_agent.review_proposal(
                        proposal_draft=proposal_draft,
                        rfp_summary=rfp_summary or "No summary available",
                        challenges=challenges or []
                    )
                    
                    initial_score = review_results.get("overall_score", 70.0)
                    print(f"  [Proposal Builder] Initial quality score: {initial_score:.1f}/100")
                    
                    # Refine if score is below threshold
                    if initial_score < 85.0 and max_refinement_iterations > 0:
                        refined_draft = proposal_draft
                        for iteration in range(max_refinement_iterations):
                            print(f"  [Proposal Builder] Refinement iteration {iteration + 1}/{max_refinement_iterations}...")
                            
                            refined_draft = proposal_refiner_agent.refine_proposal(
                                proposal_draft=refined_draft,
                                review_results=review_results,
                                rfp_summary=rfp_summary or "No summary available",
                                max_iterations=1
                            )
                            
                            # Review refined draft
                            review_results = proposal_refiner_agent.review_proposal(
                                proposal_draft=refined_draft,
                                rfp_summary=rfp_summary or "No summary available",
                                challenges=challenges or []
                            )
                            
                            refined_score = review_results.get("overall_score", 70.0)
                            print(f"  [Proposal Builder] Refined quality score: {refined_score:.1f}/100")
                            
                            # Stop if score is good enough or not improving
                            if refined_score >= 85.0 or refined_score <= initial_score:
                                break
                            
                            initial_score = refined_score
                        
                        proposal_draft = refined_draft
                        refinement_results = {
                            "initial_score": review_results.get("overall_score", 70.0),
                            "final_score": review_results.get("overall_score", 70.0),
                            "iterations": iteration + 1 if 'iteration' in locals() else 0
                        }
                    else:
                        refinement_results = {
                            "initial_score": initial_score,
                            "final_score": initial_score,
                            "iterations": 0,
                            "message": "Quality score already acceptable"
                        }
                except Exception as e:
                    print(f"  [WARNING] Refinement failed: {e}")
                    refinement_results = {"error": str(e)}
            
            return {
                "proposal_draft": proposal_draft,
                "refinement_results": refinement_results,
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

