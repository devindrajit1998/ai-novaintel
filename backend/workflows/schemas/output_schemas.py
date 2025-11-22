"""
Pydantic schemas for structured outputs from workflow agents.
These ensure consistent, validated outputs from all agents.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RFPAnalysisOutput(BaseModel):
    """Structured output from RFP Analyzer Agent."""
    rfp_summary: str = Field(description="Executive summary of the RFP (2-3 paragraphs)")
    context_overview: str = Field(description="Business context and background")
    business_objectives: List[str] = Field(description="List of key business objectives")
    project_scope: str = Field(description="Detailed project scope description")


class ChallengeOutput(BaseModel):
    """Single challenge output."""
    challenge: str = Field(description="Description of the challenge")
    type: str = Field(description="Type: 'business', 'technical', 'operational', or 'compliance'")
    impact: str = Field(description="Impact level: 'high', 'medium', or 'low'")
    category: Optional[str] = Field(None, description="Category of the challenge")


class ChallengesOutput(BaseModel):
    """Structured output from Challenge Extractor Agent."""
    challenges: List[ChallengeOutput] = Field(description="List of identified challenges")


class DiscoveryQuestionsOutput(BaseModel):
    """Structured output from Discovery Question Agent."""
    business_questions: List[str] = Field(default_factory=list, description="Business-related questions")
    technical_questions: List[str] = Field(default_factory=list, description="Technical questions")
    kpi_questions: List[str] = Field(default_factory=list, description="KPI and metrics questions")
    compliance_questions: List[str] = Field(default_factory=list, description="Compliance questions")
    other_questions: List[str] = Field(default_factory=list, description="Other categories")


class ValuePropositionsOutput(BaseModel):
    """Structured output from Value Proposition Agent."""
    value_propositions: List[str] = Field(description="List of value propositions")


class CaseStudyMatchOutput(BaseModel):
    """Matched case study output."""
    title: str = Field(description="Case study title")
    industry: str = Field(description="Industry")
    impact: str = Field(description="Impact description")
    description: Optional[str] = Field(None, description="Case study description")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    match_reason: Optional[str] = Field(None, description="Reason for matching")


class CaseStudiesOutput(BaseModel):
    """Structured output from Case Study Matcher Agent."""
    matching_case_studies: List[CaseStudyMatchOutput] = Field(description="List of matched case studies")


class ProposalSectionOutput(BaseModel):
    """Single proposal section output."""
    title: str = Field(description="Section title")
    content: str = Field(description="Section content")


class ProposalDraftOutput(BaseModel):
    """Structured output from Proposal Builder Agent."""
    executive_summary: str = Field(description="Executive summary")
    client_challenges: str = Field(description="Understanding client challenges section")
    proposed_solution: str = Field(description="Proposed solution section")
    benefits_value: str = Field(description="Benefits and value propositions section")
    case_studies: str = Field(description="Case studies and success stories section")
    implementation_approach: str = Field(description="Implementation approach section")


# Alternative format for sections-based proposals
class ProposalSectionsOutput(BaseModel):
    """Structured output with sections array."""
    sections: List[ProposalSectionOutput] = Field(description="List of proposal sections")

