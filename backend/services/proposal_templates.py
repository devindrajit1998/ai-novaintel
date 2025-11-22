"""
Proposal templates for different proposal types.
"""
from typing import List, Dict, Any, Optional
from workflows.agents.proposal_builder import proposal_builder_agent

class ProposalTemplates:
    """Proposal templates with predefined sections."""
    
    EXECUTIVE_TEMPLATE = [
        {
            "id": 1,
            "title": "Executive Summary",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Client Challenges",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Proposed Solution",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Key Benefits",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Next Steps",
            "content": "",
            "order": 5,
            "required": True
        }
    ]
    
    FULL_TEMPLATE = [
        {
            "id": 1,
            "title": "Introduction",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Understanding Client Challenges",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Proposed Solution",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Value Propositions",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Case Studies & Success Stories",
            "content": "",
            "order": 5,
            "required": False
        },
        {
            "id": 6,
            "title": "Benefits & ROI",
            "content": "",
            "order": 6,
            "required": True
        },
        {
            "id": 7,
            "title": "Implementation Approach",
            "content": "",
            "order": 7,
            "required": False
        },
        {
            "id": 8,
            "title": "Next Steps",
            "content": "",
            "order": 8,
            "required": True
        }
    ]
    
    ONE_PAGE_TEMPLATE = [
        {
            "id": 1,
            "title": "Overview",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Solution & Benefits",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Why Choose Us",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Call to Action",
            "content": "",
            "order": 4,
            "required": True
        }
    ]
    
    EXCLUSIVE_TEMPLATE = [
        {
            "id": 1,
            "title": "Executive Overview",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Unique Value Proposition",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Exclusive Solution Features",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Competitive Advantages",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Investment & ROI",
            "content": "",
            "order": 5,
            "required": True
        }
    ]
    
    SHORT_PITCH_TEMPLATE = [
        {
            "id": 1,
            "title": "The Challenge",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Our Solution",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Key Benefits",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Next Steps",
            "content": "",
            "order": 4,
            "required": True
        }
    ]
    
    EXECUTIVE_SUMMARY_TEMPLATE = [
        {
            "id": 1,
            "title": "Executive Summary",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Business Context",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Proposed Solution Overview",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Expected Outcomes",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Recommendation",
            "content": "",
            "order": 5,
            "required": True
        }
    ]
    
    TECHNICAL_APPENDIX_TEMPLATE = [
        {
            "id": 1,
            "title": "Technical Architecture",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "System Requirements",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Integration Details",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Security & Compliance",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Implementation Timeline",
            "content": "",
            "order": 5,
            "required": True
        },
        {
            "id": 6,
            "title": "Technical Specifications",
            "content": "",
            "order": 6,
            "required": False
        }
    ]
    
    # Industry-specific templates
    BFSI_TEMPLATE = [
        {
            "id": 1,
            "title": "Executive Summary",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Regulatory Compliance & Security",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Financial Challenges & Objectives",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Proposed Solution",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Risk Management & Mitigation",
            "content": "",
            "order": 5,
            "required": True
        },
        {
            "id": 6,
            "title": "ROI & Financial Impact",
            "content": "",
            "order": 6,
            "required": True
        },
        {
            "id": 7,
            "title": "Industry Case Studies",
            "content": "",
            "order": 7,
            "required": False
        },
        {
            "id": 8,
            "title": "Implementation & Integration",
            "content": "",
            "order": 8,
            "required": True
        }
    ]
    
    HEALTHCARE_TEMPLATE = [
        {
            "id": 1,
            "title": "Executive Summary",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "HIPAA Compliance & Data Security",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Patient Care Challenges",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Clinical Solution Overview",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Operational Efficiency Benefits",
            "content": "",
            "order": 5,
            "required": True
        },
        {
            "id": 6,
            "title": "Patient Outcomes & Quality Metrics",
            "content": "",
            "order": 6,
            "required": True
        },
        {
            "id": 7,
            "title": "Healthcare Industry References",
            "content": "",
            "order": 7,
            "required": False
        },
        {
            "id": 8,
            "title": "Implementation Timeline",
            "content": "",
            "order": 8,
            "required": True
        }
    ]
    
    RETAIL_TEMPLATE = [
        {
            "id": 1,
            "title": "Executive Summary",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Customer Experience Challenges",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Omnichannel Solution",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Revenue Growth Opportunities",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Inventory & Supply Chain Optimization",
            "content": "",
            "order": 5,
            "required": False
        },
        {
            "id": 6,
            "title": "Retail Success Stories",
            "content": "",
            "order": 6,
            "required": False
        },
        {
            "id": 7,
            "title": "Implementation & Rollout Plan",
            "content": "",
            "order": 7,
            "required": True
        }
    ]
    
    TECHNOLOGY_TEMPLATE = [
        {
            "id": 1,
            "title": "Executive Summary",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Technical Challenges & Requirements",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Technology Solution Architecture",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Scalability & Performance",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Integration & API Capabilities",
            "content": "",
            "order": 5,
            "required": True
        },
        {
            "id": 6,
            "title": "Innovation & Competitive Advantage",
            "content": "",
            "order": 6,
            "required": True
        },
        {
            "id": 7,
            "title": "Technical Case Studies",
            "content": "",
            "order": 7,
            "required": False
        },
        {
            "id": 8,
            "title": "Implementation Roadmap",
            "content": "",
            "order": 8,
            "required": True
        }
    ]
    
    MANUFACTURING_TEMPLATE = [
        {
            "id": 1,
            "title": "Executive Summary",
            "content": "",
            "order": 1,
            "required": True
        },
        {
            "id": 2,
            "title": "Operational Challenges",
            "content": "",
            "order": 2,
            "required": True
        },
        {
            "id": 3,
            "title": "Industry 4.0 Solution",
            "content": "",
            "order": 3,
            "required": True
        },
        {
            "id": 4,
            "title": "Productivity & Efficiency Gains",
            "content": "",
            "order": 4,
            "required": True
        },
        {
            "id": 5,
            "title": "Quality & Safety Improvements",
            "content": "",
            "order": 5,
            "required": True
        },
        {
            "id": 6,
            "title": "Supply Chain Optimization",
            "content": "",
            "order": 6,
            "required": False
        },
        {
            "id": 7,
            "title": "Manufacturing Success Stories",
            "content": "",
            "order": 7,
            "required": False
        },
        {
            "id": 8,
            "title": "Deployment Plan",
            "content": "",
            "order": 8,
            "required": True
        }
    ]
    
    @classmethod
    def get_template(cls, template_type: str, industry: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get template by type and industry.
        
        Args:
            template_type: "executive", "full", "one-page", or industry-specific
            industry: Optional industry for industry-specific templates
        
        Returns:
            List of section dictionaries
        """
        # Industry-specific templates
        industry_templates = {
            "bfsi": cls.BFSI_TEMPLATE,
            "financial": cls.BFSI_TEMPLATE,
            "banking": cls.BFSI_TEMPLATE,
            "healthcare": cls.HEALTHCARE_TEMPLATE,
            "medical": cls.HEALTHCARE_TEMPLATE,
            "retail": cls.RETAIL_TEMPLATE,
            "technology": cls.TECHNOLOGY_TEMPLATE,
            "tech": cls.TECHNOLOGY_TEMPLATE,
            "manufacturing": cls.MANUFACTURING_TEMPLATE,
            "manufacturing": cls.MANUFACTURING_TEMPLATE
        }
        
        # Check for industry-specific template first
        if industry:
            industry_lower = industry.lower()
            if industry_lower in industry_templates:
                return industry_templates[industry_lower].copy()
        
        # Generic templates
        templates = {
            "executive": cls.EXECUTIVE_TEMPLATE,
            "full": cls.FULL_TEMPLATE,
            "one-page": cls.ONE_PAGE_TEMPLATE,
            "exclusive": cls.EXCLUSIVE_TEMPLATE,
            "short-pitch": cls.SHORT_PITCH_TEMPLATE,
            "executive-summary": cls.EXECUTIVE_SUMMARY_TEMPLATE,
            "technical-appendix": cls.TECHNICAL_APPENDIX_TEMPLATE
        }
        
        # Also check if template_type is an industry
        if template_type.lower() in industry_templates:
            return industry_templates[template_type.lower()].copy()
        
        return templates.get(template_type.lower(), cls.FULL_TEMPLATE).copy()
    
    @classmethod
    def populate_from_insights(
        cls,
        template_type: str,
        insights: Dict[str, Any],
        use_ai: bool = True,
        proposal_tone: str = "professional",
        ai_response_style: str = "balanced",
        secure_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Populate template with insights data, optionally using AI for full content generation.
        
        Args:
            template_type: Template type
            insights: Insights dictionary with rfp_summary, challenges, etc.
            use_ai: If True, use AI to generate full content for each section
        
        Returns:
            Populated sections
        """
        sections = cls.get_template(template_type)
        
        if use_ai and proposal_builder_agent.llm:
            # Use AI to generate full content for each section
            rfp_summary = insights.get("rfp_summary", "") or insights.get("executive_summary", "")
            challenges = insights.get("challenges", [])
            value_propositions = insights.get("value_propositions", [])
            case_studies = insights.get("matching_case_studies", [])
            
            # Sanitize PII if secure mode is enabled
            if secure_mode:
                from utils.pii_sanitizer import PIISanitizer
                insights = PIISanitizer.sanitize_insights(insights)
                rfp_summary = PIISanitizer.sanitize_text(rfp_summary)
                # Sanitize challenges, value_propositions, case_studies
                challenges = PIISanitizer.sanitize_dict({"challenges": challenges}).get("challenges", challenges)
                value_propositions = [PIISanitizer.sanitize_text(vp) if isinstance(vp, str) else vp for vp in value_propositions]
                case_studies = PIISanitizer.sanitize_dict({"case_studies": case_studies}).get("case_studies", case_studies)
            
            # Generate content for each section using AI
            for section in sections:
                try:
                    section_content = cls._generate_section_content_ai(
                        section_title=section["title"],
                        rfp_summary=rfp_summary,
                        challenges=challenges,
                        value_propositions=value_propositions,
                        case_studies=case_studies,
                        proposal_tone=proposal_tone,
                        ai_response_style=ai_response_style
                    )
                    section["content"] = section_content
                except Exception as e:
                    print(f"Error generating AI content for section {section['title']}: {e}")
                    # Fallback to basic population
                    section["content"] = cls._populate_section_basic(section, insights)
        else:
            # Basic population without AI
            for section in sections:
                section["content"] = cls._populate_section_basic(section, insights)
        
        return sections
    
    @classmethod
    def _populate_section_basic(cls, section: Dict[str, Any], insights: Dict[str, Any]) -> str:
        """Basic section population without AI."""
        title_lower = section["title"].lower()
        
        if "summary" in title_lower or "overview" in title_lower or "introduction" in title_lower:
            return insights.get("rfp_summary", "") or insights.get("executive_summary", "")
        
        elif "challenge" in title_lower:
            challenges = insights.get("challenges", [])
            if challenges:
                content = "Key challenges identified:\n\n"
                for i, ch in enumerate(challenges[:5], 1):
                    desc = ch.get("description", "") if isinstance(ch, dict) else str(ch)
                    content += f"{i}. {desc}\n"
                return content
            return ""
        
        elif "solution" in title_lower:
            return insights.get("proposed_solution", "Our comprehensive solution addresses your key challenges...")
        
        elif "value" in title_lower or "benefit" in title_lower:
            value_props = insights.get("value_propositions", [])
            if value_props:
                return "\n".join([f"• {vp}" for vp in value_props[:5]])
            return "Significant value through improved efficiency and ROI."
        
        elif "case study" in title_lower or "success" in title_lower:
            case_studies = insights.get("matching_case_studies", [])
            if case_studies:
                content = ""
                for cs in case_studies[:3]:
                    title = cs.get("title", "") if isinstance(cs, dict) else str(cs)
                    impact = cs.get("impact", "") if isinstance(cs, dict) else ""
                    content += f"• {title}: {impact}\n"
                return content
            return "Relevant case studies available upon request."
        
        elif "next step" in title_lower or "action" in title_lower:
            return "We look forward to discussing how we can help achieve your objectives. Please contact us to schedule a detailed discussion."
        
        return ""
    
    @classmethod
    def _generate_section_content_ai(
        cls,
        section_title: str,
        rfp_summary: str,
        challenges: List[Dict[str, Any]],
        value_propositions: List[str],
        case_studies: List[Dict[str, Any]],
        proposal_tone: str = "professional",
        ai_response_style: str = "balanced"
    ) -> str:
        """Generate section content using AI."""
        from langchain.prompts import ChatPromptTemplate
        
        challenges_text = ""
        if challenges:
            challenges_text = "\n".join([
                f"- {ch.get('description', '')} (Type: {ch.get('type', 'Unknown')}, Impact: {ch.get('impact', 'Unknown')})"
                for ch in challenges[:10]
            ])
        
        value_props_text = "\n".join([f"- {vp}" for vp in value_propositions[:10]]) if value_propositions else "None"
        
        case_studies_text = ""
        if case_studies:
            case_studies_text = "\n".join([
                f"- {cs.get('title', '')}: {cs.get('impact', '')} - {cs.get('description', '')[:200]}"
                for cs in case_studies[:5]
            ])
        
        # Build tone instructions
        tone_instructions = {
            "professional": "Use a professional, formal tone. Be clear, concise, and business-focused.",
            "friendly": "Use a warm, approachable tone. Be conversational while maintaining professionalism.",
            "technical": "Use a technical, detailed tone. Include specific technical details and terminology.",
            "executive": "Use an executive-level tone. Focus on strategic value and high-level outcomes.",
            "consultative": "Use a consultative, advisory tone. Position as a trusted advisor and partner."
        }
        tone_instruction = tone_instructions.get(proposal_tone, tone_instructions["professional"])
        
        # Build response style instructions
        style_instructions = {
            "concise": "Be very concise. Write 1-2 short paragraphs. Focus on key points only.",
            "balanced": "Write 2-4 paragraphs. Provide a good balance of detail and brevity.",
            "detailed": "Write 3-5 detailed paragraphs. Provide comprehensive information and context."
        }
        style_instruction = style_instructions.get(ai_response_style, style_instructions["balanced"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert proposal writer. Write compelling proposal content that:
- Addresses client needs directly
- Uses specific data and insights
- Is clear and persuasive
- Focuses on business value
- Is appropriate for the section type

Tone: {tone_instruction}
Style: {style_instruction}

Write high-quality content following the tone and style guidelines above."""),
            ("user", """Write content for the proposal section: "{section_title}"

RFP Summary:
{rfp_summary}

Client Challenges:
{challenges}

Value Propositions:
{value_propositions}

Case Studies:
{case_studies}

Write professional, persuasive content for this section. Do not include the section title, only the content."""),
        ])
        
        try:
            chain = prompt | proposal_builder_agent.llm
            response = chain.invoke({
                "section_title": section_title,
                "rfp_summary": rfp_summary or "No summary available",
                "challenges": challenges_text or "No challenges identified",
                "value_propositions": value_props_text or "No value propositions",
                "case_studies": case_studies_text or "No case studies available"
            })
            
            content = response.content if hasattr(response, 'content') else str(response)
            # Clean up markdown formatting issues (remove ** from section titles, etc.)
            content = content.strip()
            # Remove ** from section titles if they appear in content
            import re
            # Fix patterns like **Title:** to Title:
            content = re.sub(r'\*\*([^*]+):\*\*', r'\1:', content)
            # Fix standalone **Title** to Title (but preserve intentional bold)
            # Only remove if it's at the start of a line or after a newline
            content = re.sub(r'(^|\n)\*\*([^*]+)\*\*(\s|$)', r'\1\2\3', content, flags=re.MULTILINE)
            return content
        except Exception as e:
            print(f"AI generation error: {e}")
            return cls._populate_section_basic(
                {"title": section_title},
                {
                    "rfp_summary": rfp_summary,
                    "challenges": challenges,
                    "value_propositions": value_propositions,
                    "matching_case_studies": case_studies
                }
            )

