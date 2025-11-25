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
    executive_summary: str = Field(description="Executive Summary section")
    understanding_client_needs: str = Field(description="Understanding of Client Needs section")
    proposed_solution: str = Field(description="Proposed Solution section")
    solution_architecture: str = Field(description="Solution Architecture & Technology Stack section")
    business_value_use_cases: str = Field(description="Business Value & Use Cases section")
    benefits_roi: str = Field(description="Benefits & ROI Justification section")
    implementation_roadmap: str = Field(description="Implementation Roadmap & Timeline section")
    change_management_training: str = Field(description="Change Management & Training Strategy section")
    security_compliance: str = Field(description="Security, Compliance & Data Governance section")
    case_studies_credentials: str = Field(description="Case Studies & Delivery Credentials section")
    commercial_model: str = Field(description="Commercial Model & Licensing Options section")
    risks_assumptions: str = Field(description="Risks, Assumptions & Mitigation section")
    next_steps_cta: str = Field(description="Next Steps & Call-to-Action section")


# Alternative format for sections-based proposals
class ProposalSectionsOutput(BaseModel):
    """Structured output with sections array."""
    sections: List[ProposalSectionOutput] = Field(description="List of proposal sections")

