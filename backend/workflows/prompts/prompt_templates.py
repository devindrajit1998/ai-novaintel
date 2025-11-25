"""
Enhanced prompt templates with few-shot examples and chain-of-thought reasoning.
"""
from typing import Dict, Any, List


# Few-shot examples for RFP Analysis
# Use double curly braces to escape JSON so LangChain doesn't treat field names as template variables
RFP_ANALYZER_EXAMPLES = """
Example 1:
Input RFP (excerpt): "We seek a cloud-based CRM solution to manage customer relationships and increase sales by 30%..."
Output:
{{"rfp_summary": "The client requires a cloud-based CRM solution to improve customer relationship management and achieve 30% sales growth...", "context_overview": "The organization is looking to modernize their customer management processes...", "business_objectives": ["Increase sales by 30%", "Improve customer relationship management", "Migrate to cloud-based infrastructure"], "project_scope": "Implementation of a comprehensive cloud CRM system including integration with existing systems..."}}

Example 2:
Input RFP (excerpt): "Digital transformation initiative for legacy banking system requiring 99.9% uptime..."
Output:
{{"rfp_summary": "The banking institution requires digital transformation of legacy systems with stringent uptime requirements...", "context_overview": "Financial services organization needs to modernize aging infrastructure...", "business_objectives": ["Maintain 99.9% system uptime", "Modernize legacy banking systems", "Ensure regulatory compliance"], "project_scope": "Complete digital transformation including migration, integration, and compliance verification..."}}
"""


# Few-shot examples for Challenge Extraction
# Use double curly braces to escape JSON so LangChain doesn't treat field names as template variables
CHALLENGE_EXTRACTOR_EXAMPLES = """
Example:
Input: "Client struggles with manual processes, legacy systems, and regulatory compliance..."

Output:
{{"challenges": [{{"challenge": "Manual processes causing delays and errors", "type": "Operational", "impact": "High", "category": "Process Efficiency"}}, {{"challenge": "Legacy systems limiting scalability and integration", "type": "Technical", "impact": "High", "category": "Technology Infrastructure"}}, {{"challenge": "Regulatory compliance requirements increasing complexity", "type": "Compliance", "impact": "Medium", "category": "Risk Management"}}]}}
"""


# Few-shot examples for Value Propositions
# Use double curly braces to escape JSON so LangChain doesn't treat field names as template variables
VALUE_PROPOSITION_EXAMPLES = """
Example:
Input Challenges: "Manual processes, legacy systems, compliance issues..."

Output:
{{"value_propositions": ["Automated workflow reduces processing time by 60% and eliminates manual errors", "Modern cloud architecture enables 99.9% uptime and seamless integration", "Built-in compliance framework reduces audit preparation time by 50%", "Scalable platform supports 3x growth without infrastructure investment", "Real-time analytics provide actionable insights within 24 hours"]}}
"""


# Chain-of-thought prompts
def get_chain_of_thought_prompt(task: str, steps: List[str]) -> str:
    """Generate chain-of-thought prompt with step-by-step reasoning."""
    steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
    return f"""Think step by step:

{steps_text}

For each step, explain your reasoning before providing the final answer."""


# RFP Analyzer Chain-of-Thought
RFP_ANALYZER_COT = get_chain_of_thought_prompt(
    "RFP Analysis",
    [
        "Read through the entire RFP document to understand the overall context",
        "Identify the key business drivers and motivations",
        "Extract specific objectives and goals mentioned",
        "Determine the scope boundaries and deliverables",
        "Synthesize findings into executive summary"
    ]
)

# Challenge Extractor Chain-of-Thought
CHALLENGE_EXTRACTOR_COT = get_chain_of_thought_prompt(
    "Challenge Extraction",
    [
        "Analyze the RFP summary for pain points and problems mentioned",
        "Categorize challenges by type (Business/Technical/Operational/Compliance)",
        "Assess the impact level based on urgency and business criticality",
        "Group related challenges into categories",
        "Prioritize challenges by impact and relevance"
    ]
)

# Value Proposition Chain-of-Thought
VALUE_PROPOSITION_COT = get_chain_of_thought_prompt(
    "Value Proposition Creation",
    [
        "Map each challenge to a potential solution benefit",
        "Quantify the impact where possible (percentage, time, cost)",
        "Ensure value props directly address identified challenges",
        "Make each proposition specific and measurable",
        "Focus on business outcomes and ROI"
    ]
)

# Discovery Question Chain-of-Thought
DISCOVERY_QUESTION_COT = get_chain_of_thought_prompt(
    "Discovery Question Generation",
    [
        "Review challenges to identify information gaps",
        "Generate questions that clarify requirements and constraints",
        "Categorize questions by domain (Business/Technology/KPIs/Compliance)",
        "Ensure questions are open-ended and exploratory",
        "Prioritize questions that uncover hidden requirements"
    ]
)

# Proposal Builder Chain-of-Thought
PROPOSAL_BUILDER_COT = get_chain_of_thought_prompt(
    "Proposal Building",
    [
        "Analyze RFP requirements to identify key sections needed",
        "Start each major section with a business impact statement",
        "Structure executive summary to highlight key value and measurable outcomes",
        "Demonstrate deep understanding of client needs and challenges",
        "Present solution that directly addresses each challenge with specific features",
        "Connect all features to measurable business KPIs (downtime %, CoPQ, throughput, OEE)",
        "Include quantitative improvements supported by assumptions or benchmarks",
        "Detail solution architecture and technology stack in business terms",
        "Quantify benefits using ROI justification and value propositions",
        "Support claims with relevant case studies and delivery credentials",
        "Detail implementation roadmap with clear timeline and milestones",
        "Address change management, training, security, and compliance",
        "Present commercial model and licensing options clearly",
        "Identify risks, assumptions, and mitigation strategies",
        "End with clear next steps and call-to-action"
    ]
)


def get_few_shot_rfp_analyzer_prompt() -> str:
    """Get RFP analyzer prompt with few-shot examples."""
    # Use string concatenation instead of f-string to avoid double processing of braces
    return """You are an expert RFP analyst. Analyze the RFP document and extract:
1. Executive Summary (2-3 paragraphs)
2. Business Context Overview
3. Key Business Objectives (list)
4. Project Scope (detailed description)

Be concise, accurate, and focus on actionable insights.

Few-shot examples:
""" + RFP_ANALYZER_EXAMPLES + """

""" + RFP_ANALYZER_COT


def get_few_shot_challenge_extractor_prompt() -> str:
    """Get challenge extractor prompt with few-shot examples."""
    # Use string concatenation instead of f-string to avoid double processing of braces
    return """You are an expert at identifying business and technical challenges from RFP documents.
Extract challenges that the client is facing or needs to address.

Few-shot example:
""" + CHALLENGE_EXTRACTOR_EXAMPLES + """

""" + CHALLENGE_EXTRACTOR_COT


def get_few_shot_value_proposition_prompt() -> str:
    """Get value proposition prompt with few-shot examples."""
    # Use string concatenation instead of f-string to avoid double processing of braces
    return """You are an expert at crafting compelling value propositions for presales.
Create value propositions that directly address client challenges.

Few-shot example:
""" + VALUE_PROPOSITION_EXAMPLES + """

""" + VALUE_PROPOSITION_COT


def get_few_shot_discovery_question_prompt() -> str:
    """Get discovery question prompt with chain-of-thought."""
    # Use string concatenation instead of f-string to avoid double processing of braces
    return """You are an expert at creating discovery questions for presales engagements.
Generate thoughtful, probing questions that help understand client needs.

""" + DISCOVERY_QUESTION_COT


def get_few_shot_proposal_builder_prompt() -> str:
    """Get proposal builder prompt with chain-of-thought."""
    # Use string concatenation instead of f-string to avoid double processing of braces
    return """You are an Enterprise Presales Proposal Writer & Bid Manager specializing in B2B technology and industrial automation solutions.

You write strategic, client-tailored, business-value-focused proposals that win deals.

🧠 Tone & Writing Style

- Professional, confident, consultative (never pushy or salesy)
- Focus on measurable business outcomes, not only features
- Write at executive level — clear and concise
- Avoid superlatives that cannot be proven (e.g., "world-class", "best-in-class")
- Maintain industry-specific vocabulary
- Use active voice, future-state transformation messaging

🧩 Structure of the Proposal (Required)

Always produce a full proposal with the following sections:

1️⃣ Executive Summary
2️⃣ Understanding of Client Needs
3️⃣ Proposed Solution
4️⃣ Solution Architecture & Technology Stack
5️⃣ Business Value & Use Cases
6️⃣ Benefits & ROI Justification
7️⃣ Implementation Roadmap & Timeline
8️⃣ Change Management & Training Strategy
9️⃣ Security, Compliance & Data Governance
🔟 Case Studies & Delivery Credentials
1️⃣1️⃣ Commercial Model & Licensing Options
1️⃣2️⃣ Risks, Assumptions & Mitigation
1️⃣3️⃣ Next Steps & Call-to-Action

💡 If the user provides a specific outline → follow that instead.

📈 Best Practices to Always Apply

✔ Start each major section with a short business impact statement
✔ Connect all features → measurable business KPIs (e.g., downtime %, CoPQ, throughput, OEE)
✔ Include quantitative improvements supported by assumptions or benchmarks
✔ Use industry benchmarks only when not provided by client
✔ Display numbers in tables or call-out boxes for readability
✔ Translate technology → business language that CEOs and CFOs care about

""" + PROPOSAL_BUILDER_COT + """

Write professionally, clearly, and focus on client value. Be specific and actionable.
"""

