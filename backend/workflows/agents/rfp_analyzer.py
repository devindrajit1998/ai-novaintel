"""
RFP Analyzer Agent - Extracts summary, business context, objectives, and scope.
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from utils.config import settings
from utils.llm_factory import get_llm
from utils.model_router import TaskType
from rag.retriever import retriever
from workflows.schemas.output_schemas import RFPAnalysisOutput
from workflows.prompts.prompt_templates import get_few_shot_rfp_analyzer_prompt

class RFPAnalyzerAgent:
    """Agent that analyzes RFP documents."""
    
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM with intelligent routing."""
        try:
            # Use Claude or GPT-4o for analysis tasks (better reasoning)
            self.llm = get_llm(
                provider=None,  # Auto-select
                temperature=0.1,
                task_type=TaskType.ANALYSIS,
                prefer_provider=settings.LLM_PROVIDER if settings.LLM_PROVIDER in ["claude", "openai"] else None
            )
            print(f"✓ RFP Analyzer Agent initialized with intelligent routing")
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
        
        # Set up structured output parser
        output_parser = PydanticOutputParser(pydantic_object=RFPAnalysisOutput)
        
        # Create a simple format instruction without JSON schema examples to avoid template parsing issues
        # The PydanticOutputParser will handle the actual parsing, we just need to tell the LLM the structure
        # Use escaped curly braces to prevent LangChain from treating JSON field names as template variables
        format_instructions_simple = """Return your response as a valid JSON object with the following structure:
- rfp_summary: A 2-3 paragraph executive summary
- context_overview: Business context and background information
- business_objectives: An array of business objectives (strings)
- project_scope: Description of the project scope

Example format: {{"rfp_summary": "...", "context_overview": "...", "business_objectives": [...], "project_scope": "..."}}

Ensure the JSON is valid and properly formatted."""
        
        system_prompt = get_few_shot_rfp_analyzer_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", """Analyze the following RFP document:

RFP Document:
{rfp_text}

{context_section}

{format_instructions}

Provide your analysis in the specified JSON format.""")
        ])
        
        context_section = ""
        if retrieved_context:
            context_section = f"\nAdditional Context:\n{retrieved_context}"
        
        try:
            print(f"    [RFP Analyzer] Invoking LLM with {len(rfp_text)} chars of RFP text...")
            
            # Create chain with structured output
            chain = prompt | self.llm | output_parser
            
            response = chain.invoke({
                "rfp_text": rfp_text[:10000],  # Limit text length
                "context_section": context_section,
                "format_instructions": format_instructions_simple
            })
            
            print(f"    [RFP Analyzer] LLM response received: {type(response)}")
            
            # Response is already parsed as Pydantic model
            if isinstance(response, RFPAnalysisOutput):
                result = response.model_dump()
                print(f"    [RFP Analyzer] ✓ Successfully parsed structured response")
            else:
                # Fallback: convert dict to model
                if isinstance(response, dict):
                    result = RFPAnalysisOutput(**response).model_dump()
                else:
                    # Last resort fallback
                    content = str(response)
                    result = {
                        "rfp_summary": content[:500] if content else "",
                        "context_overview": "Extracted from RFP",
                        "business_objectives": [],
                        "project_scope": content[500:1500] if len(content) > 500 else content
                    }
            
            final_result = {
                "rfp_summary": result.get("rfp_summary", ""),
                "context_overview": result.get("context_overview", ""),
                "business_objectives": result.get("business_objectives", []),
                "project_scope": result.get("project_scope", ""),
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

