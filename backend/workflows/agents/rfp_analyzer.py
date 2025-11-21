"""
RFP Analyzer Agent - Extracts summary, business context, objectives, and scope.
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from utils.config import settings
from utils.llm_factory import get_llm
from rag.retriever import retriever

class RFPAnalyzerAgent:
    """Agent that analyzes RFP documents."""
    
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM."""
        try:
            self.llm = get_llm(provider=settings.LLM_PROVIDER, temperature=0.1)
            print(f"✓ RFP Analyzer Agent initialized with {settings.LLM_PROVIDER}")
        except Exception as e:
            print(f"Error initializing RFP Analyzer Agent: {e}")
    
    def analyze(
        self,
        rfp_text: str,
        retrieved_context: str = None,
        project_id: int = None
    ) -> Dict[str, Any]:
        """
        Analyze RFP and extract key information.
        
        Args:
            rfp_text: The RFP document text
            retrieved_context: Optional retrieved context from RAG
            project_id: Optional project ID for RAG retrieval
        
        Returns:
            dict with rfp_summary, context_overview, business_objectives, project_scope
        """
        if not self.llm:
            return {
                "rfp_summary": None,
                "context_overview": None,
                "business_objectives": [],
                "project_scope": None,
                "error": "LLM not initialized"
            }
        
        # Retrieve additional context if needed
        if not retrieved_context and project_id:
            try:
                nodes = retriever.retrieve(
                    query="What is this project about? What are the main objectives?",
                    project_id=project_id,
                    top_k=3
                )
                if nodes:
                    retrieved_context = "\n\n".join([
                        node.node.get_content() for node in nodes
                    ])
            except Exception as e:
                print(f"Error retrieving context: {e}")
        
        # Build prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert RFP analyst. Analyze the RFP document and extract:
1. Executive Summary (2-3 paragraphs)
2. Business Context Overview
3. Key Business Objectives (list)
4. Project Scope (detailed description)

Be concise, accurate, and focus on actionable insights."""),
            ("user", """Analyze the following RFP document:

RFP Document:
{rfp_text}

{context_section}

Provide your analysis in the following JSON format:
{{
    "rfp_summary": "Executive summary (2-3 paragraphs)",
    "context_overview": "Business context and background",
    "business_objectives": ["objective1", "objective2", ...],
    "project_scope": "Detailed project scope description"
}}""")
        ])
        
        context_section = ""
        if retrieved_context:
            context_section = f"\nAdditional Context:\n{retrieved_context}"
        
        try:
            print(f"    [RFP Analyzer] Invoking LLM with {len(rfp_text)} chars of RFP text...")
            chain = prompt | self.llm
            response = chain.invoke({
                "rfp_text": rfp_text[:10000],  # Limit text length
                "context_section": context_section
            })
            
            print(f"    [RFP Analyzer] LLM response received: {type(response)}")
            
            # Parse response (assuming JSON format)
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            else:
                content = str(response)
            
            print(f"    [RFP Analyzer] Response content length: {len(content) if content else 0} chars")
            print(f"    [RFP Analyzer] Response preview: {content[:200] if content else 'None'}...")
            
            # Try to extract JSON from response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    print(f"    [RFP Analyzer] ✓ Successfully parsed JSON response")
                except json.JSONDecodeError as e:
                    print(f"    [RFP Analyzer] ⚠️  JSON parse error: {e}, using fallback")
                    result = {
                        "rfp_summary": content[:500] if content else None,
                        "context_overview": "Extracted from RFP",
                        "business_objectives": [],
                        "project_scope": content[500:1500] if len(content) > 500 else content
                    }
            else:
                print(f"    [RFP Analyzer] ⚠️  No JSON found in response, using fallback")
                # Fallback: parse manually
                result = {
                    "rfp_summary": content[:500] if content else None,
                    "context_overview": "Extracted from RFP",
                    "business_objectives": [],
                    "project_scope": content[500:1500] if len(content) > 500 else content
                }
            
            final_result = {
                "rfp_summary": result.get("rfp_summary"),
                "context_overview": result.get("context_overview"),
                "business_objectives": result.get("business_objectives", []),
                "project_scope": result.get("project_scope"),
                "error": None
            }
            
            print(f"    [RFP Analyzer] Final result - Summary: {len(str(final_result.get('rfp_summary'))) if final_result.get('rfp_summary') else 0} chars, "
                  f"Objectives: {len(final_result.get('business_objectives', []))}")
            
            return final_result
        
        except Exception as e:
            print(f"    [RFP Analyzer] ❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "rfp_summary": None,
                "context_overview": None,
                "business_objectives": [],
                "project_scope": None,
                "error": str(e)
            }

# Global instance
rfp_analyzer_agent = RFPAnalyzerAgent()

