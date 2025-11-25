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
        
        # Format challenges - handle both dict and string formats
        challenges_text = ""
        if challenges:
            if isinstance(challenges, list) and len(challenges) > 0:
                if isinstance(challenges[0], dict):
                    challenges_text = "\n".join([
                        f"- {ch.get('challenge', ch.get('description', ''))}"
                        for ch in challenges
                    ])
                else:
                    challenges_text = "\n".join([f"- {ch}" for ch in challenges])
            else:
                challenges_text = str(challenges)
        
        # Format value propositions
        value_props_text = "\n".join([f"- {vp}" for vp in value_propositions]) if value_propositions else "None"
        
        # Format case studies
        case_studies_text = ""
        if case_studies:
            if isinstance(case_studies, list) and len(case_studies) > 0:
                if isinstance(case_studies[0], dict):
                    case_studies_text = "\n".join([
                        f"- {cs.get('title', '')}: {cs.get('impact', '')}"
                        for cs in case_studies
                    ])
                else:
                    case_studies_text = "\n".join([f"- {cs}" for cs in case_studies])
            else:
                case_studies_text = str(case_studies)
        
        # Ensure we have at least RFP summary to work with
        if not rfp_summary or len(rfp_summary.strip()) == 0:
            rfp_summary = "The client has requested a proposal for their project needs. Based on the RFP document, we will provide a comprehensive solution."
        
        # If we have no challenges or value props, the proposal builder should still work
        # It will create a general proposal based on the RFP summary
        if not challenges_text:
            challenges_text = "General business and technical requirements from the RFP"
        if not value_props_text or value_props_text == "None":
            value_props_text = "Our solution will address the key requirements outlined in the RFP"
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=ProposalDraftOutput)
        
        # Simple format instructions without JSON schema to avoid template parsing issues
        # Use escaped curly braces to prevent LangChain from treating JSON field names as template variables
        format_instructions_simple = """Return your response as a valid JSON object with these string fields:
- executive_summary: Executive Summary (1️⃣)
- understanding_client_needs: Understanding of Client Needs (2️⃣)
- proposed_solution: Proposed Solution (3️⃣)
- solution_architecture: Solution Architecture & Technology Stack (4️⃣)
- business_value_use_cases: Business Value & Use Cases (5️⃣)
- benefits_roi: Benefits & ROI Justification (6️⃣)
- implementation_roadmap: Implementation Roadmap & Timeline (7️⃣)
- change_management_training: Change Management & Training Strategy (8️⃣)
- security_compliance: Security, Compliance & Data Governance (9️⃣)
- case_studies_credentials: Case Studies & Delivery Credentials (🔟)
- commercial_model: Commercial Model & Licensing Options (1️⃣1️⃣)
- risks_assumptions: Risks, Assumptions & Mitigation (1️⃣2️⃣)
- next_steps_cta: Next Steps & Call-to-Action (1️⃣3️⃣)

Each section should:
- Start with a short business impact statement
- Connect features to measurable business KPIs
- Include quantitative improvements where possible
- Use business language that executives understand

Example: {{"executive_summary": "...", "understanding_client_needs": "...", ...}}"""
        
        system_prompt = get_few_shot_proposal_builder_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + """

Create a comprehensive proposal draft following the 13-section structure.
Each section must start with a business impact statement and connect features to measurable KPIs.
Use quantitative improvements and business language throughout.
"""),
            ("user", """Create a proposal draft based on:

RFP Summary:
{rfp_summary}

Client Challenges:
{challenges}

Value Propositions:
{value_propositions}

Relevant Case Studies:
{case_studies}

{format_instructions}

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
                "format_instructions": format_instructions_simple
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
                print(f"  [Proposal Builder] ✓ Parsed Pydantic model successfully")
            elif isinstance(response, dict):
                proposal_draft = response
                print(f"  [Proposal Builder] ✓ Parsed dict response successfully")
            else:
                # Fallback - create a basic proposal structure with 13 sections
                print(f"  [Proposal Builder] ⚠ Unexpected response type: {type(response)}, creating fallback proposal")
                content = str(response)
                proposal_draft = {
                    "executive_summary": content[:500] if content and len(content) > 10 else "Executive summary based on RFP requirements",
                    "understanding_client_needs": challenges_text or "Understanding of client needs and requirements",
                    "proposed_solution": "Comprehensive solution approach tailored to RFP requirements",
                    "solution_architecture": "Solution architecture and technology stack details",
                    "business_value_use_cases": value_props_text or "Business value and use cases",
                    "benefits_roi": "Benefits and ROI justification",
                    "implementation_roadmap": "Implementation roadmap and timeline",
                    "change_management_training": "Change management and training strategy",
                    "security_compliance": "Security, compliance and data governance",
                    "case_studies_credentials": case_studies_text or "Case studies and delivery credentials",
                    "commercial_model": "Commercial model and licensing options",
                    "risks_assumptions": "Risks, assumptions and mitigation",
                    "next_steps_cta": "Next steps and call-to-action"
                }
            
            # Validate proposal_draft has content
            if not proposal_draft or not isinstance(proposal_draft, dict):
                print(f"  [Proposal Builder] ⚠ Invalid proposal_draft, creating minimal proposal")
                proposal_draft = {
                    "executive_summary": f"Executive summary for the project based on the RFP document",
                    "understanding_client_needs": challenges_text or "Client needs and requirements",
                    "proposed_solution": "Proposed solution addressing the RFP requirements",
                    "solution_architecture": "Solution architecture and technology stack",
                    "business_value_use_cases": value_props_text or "Business value and use cases",
                    "benefits_roi": "Benefits and ROI justification",
                    "implementation_roadmap": "Implementation roadmap and timeline",
                    "change_management_training": "Change management and training strategy",
                    "security_compliance": "Security, compliance and data governance",
                    "case_studies_credentials": case_studies_text or "Case studies and delivery credentials",
                    "commercial_model": "Commercial model and licensing options",
                    "risks_assumptions": "Risks, assumptions and mitigation",
                    "next_steps_cta": "Next steps and call-to-action"
                }
            
            # Ensure all required fields exist (13-section structure)
            required_fields = [
                "executive_summary", "understanding_client_needs", "proposed_solution",
                "solution_architecture", "business_value_use_cases", "benefits_roi",
                "implementation_roadmap", "change_management_training", "security_compliance",
                "case_studies_credentials", "commercial_model", "risks_assumptions", "next_steps_cta"
            ]
            for field in required_fields:
                if field not in proposal_draft or not proposal_draft[field]:
                    # Create a meaningful default based on field name
                    field_display = field.replace('_', ' ').title()
                    proposal_draft[field] = f"{field_display} section - to be completed based on RFP requirements"
            
            print(f"  [Proposal Builder] ✓ Proposal draft validated with {len(proposal_draft)} sections")
            
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

