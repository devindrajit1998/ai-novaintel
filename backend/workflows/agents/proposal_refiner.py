"""
Proposal Refiner Agent - Reviews and refines proposals for quality.
Implements multi-pass generation: draft → review → refine workflow.
"""
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from utils.llm_factory import get_llm
from utils.model_router import TaskType
from workflows.schemas.output_schemas import ProposalDraftOutput
from pydantic import BaseModel, Field


class ProposalQualityScore(BaseModel):
    """Quality score for proposal sections."""
    overall_score: float = Field(description="Overall quality score (0-100)")
    clarity_score: float = Field(description="Clarity score (0-100)")
    completeness_score: float = Field(description="Completeness score (0-100)")
    relevance_score: float = Field(description="Relevance score (0-100)")
    professionalism_score: float = Field(description="Professionalism score (0-100)")
    weak_sections: List[str] = Field(default_factory=list, description="List of weak section names")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class ProposalRefinerAgent:
    """Agent that refines proposals for quality."""
    
    def __init__(self):
        self.review_llm = None
        self.refine_llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLMs for review and refinement."""
        try:
            # Use Claude or GPT-4o for review (complex reasoning)
            self.review_llm = get_llm(
                provider=None,
                temperature=0.1,
                task_type=TaskType.COMPLEX_REASONING
            )
            # Use GPT-4o or Claude for refinement (high quality)
            self.refine_llm = get_llm(
                provider=None,
                temperature=0.2,
                task_type=TaskType.REFINEMENT
            )
            print(f"✓ Proposal Refiner Agent initialized")
        except Exception as e:
            print(f"Error initializing Proposal Refiner Agent: {e}")
            self.review_llm = None
            self.refine_llm = None
    
    def review_proposal(
        self,
        proposal_draft: Dict[str, Any],
        rfp_summary: str,
        challenges: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Review proposal and provide quality scores and suggestions.
        
        Args:
            proposal_draft: Draft proposal from ProposalBuilder
            rfp_summary: RFP summary for context
            challenges: Client challenges for relevance checking
        
        Returns:
            dict with quality scores, weak sections, and suggestions
        """
        if not self.review_llm:
            return {
                "overall_score": 70.0,
                "weak_sections": [],
                "suggestions": [],
                "error": "Review LLM not initialized"
            }
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=ProposalQualityScore)
        format_instructions = output_parser.get_format_instructions()
        
        challenges_text = ""
        if challenges:
            challenges_text = "\n".join([f"- {ch.get('challenge', ch.get('description', ''))}" for ch in challenges])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert proposal reviewer. Evaluate the proposal quality on:
1. Clarity: Is the language clear and understandable?
2. Completeness: Are all key sections present and thorough?
3. Relevance: Does it address the client's challenges?
4. Professionalism: Is the tone professional and polished?

Provide specific scores (0-100) for each dimension and identify weak sections.

{format_instructions}"""),
            ("user", """Review the following proposal draft:

RFP Summary:
{rfp_summary}

Client Challenges:
{challenges}

Proposal Draft:
{proposal_draft}

Provide quality scores and improvement suggestions in the specified JSON format.""")
        ])
        
        try:
            chain = prompt | self.review_llm | output_parser
            response = chain.invoke({
                "rfp_summary": rfp_summary or "No summary available",
                "challenges": challenges_text or "No challenges specified",
                "proposal_draft": self._format_proposal_for_review(proposal_draft),
                "format_instructions": format_instructions
            })
            
            if isinstance(response, ProposalQualityScore):
                return response.model_dump()
            elif isinstance(response, dict):
                return response
            else:
                return {
                    "overall_score": 70.0,
                    "weak_sections": [],
                    "suggestions": ["Proposal needs review"],
                    "error": "Failed to parse review response"
                }
        except Exception as e:
            print(f"[WARNING] Proposal review failed: {e}")
            return {
                "overall_score": 70.0,
                "weak_sections": [],
                "suggestions": [],
                "error": str(e)
            }
    
    def refine_proposal(
        self,
        proposal_draft: Dict[str, Any],
        review_results: Dict[str, Any],
        rfp_summary: str,
        max_iterations: int = 2
    ) -> Dict[str, Any]:
        """
        Refine proposal based on review feedback.
        
        Args:
            proposal_draft: Original draft proposal
            review_results: Review scores and suggestions
            rfp_summary: RFP summary for context
            max_iterations: Maximum refinement iterations
        
        Returns:
            Refined proposal draft
        """
        if not self.refine_llm:
            return proposal_draft
        
        # If score is high enough, return as-is
        overall_score = review_results.get("overall_score", 70.0)
        if overall_score >= 85.0:
            print(f"[Proposal Refiner] Quality score {overall_score:.1f} is acceptable, skipping refinement")
            return proposal_draft
        
        # Refine weak sections
        weak_sections = review_results.get("weak_sections", [])
        suggestions = review_results.get("suggestions", [])
        
        if not weak_sections and not suggestions:
            return proposal_draft
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=ProposalDraftOutput)
        format_instructions = output_parser.get_format_instructions()
        
        suggestions_text = "\n".join([f"- {s}" for s in suggestions])
        weak_sections_text = ", ".join(weak_sections) if weak_sections else "None"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert proposal writer. Refine the proposal based on review feedback.
Focus on improving weak sections while maintaining the overall structure.
Make the language clearer, more professional, and more relevant to client needs.

{format_instructions}"""),
            ("user", """Refine the following proposal based on review feedback:

Original Proposal:
{proposal_draft}

RFP Summary:
{rfp_summary}

Review Feedback:
Overall Score: {overall_score}/100
Weak Sections: {weak_sections}
Suggestions:
{suggestions}

Provide the refined proposal in the specified JSON format. Focus on improving weak sections.""")
        ])
        
        try:
            chain = prompt | self.refine_llm | output_parser
            response = chain.invoke({
                "proposal_draft": self._format_proposal_for_review(proposal_draft),
                "rfp_summary": rfp_summary or "No summary available",
                "overall_score": overall_score,
                "weak_sections": weak_sections_text,
                "suggestions": suggestions_text,
                "format_instructions": format_instructions
            })
            
            if isinstance(response, ProposalDraftOutput):
                return response.model_dump()
            elif isinstance(response, dict):
                return response
            else:
                return proposal_draft  # Return original on error
        except Exception as e:
            print(f"[WARNING] Proposal refinement failed: {e}")
            return proposal_draft
    
    def _format_proposal_for_review(self, proposal_draft: Dict[str, Any]) -> str:
        """Format proposal for review."""
        sections = []
        for key, value in proposal_draft.items():
            if key != "error" and value:
                section_name = key.replace("_", " ").title()
                sections.append(f"{section_name}:\n{value}")
        return "\n\n".join(sections)


# Global instance
proposal_refiner_agent = ProposalRefinerAgent()

