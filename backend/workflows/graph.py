"""
LangGraph workflow for multi-agent presales pipeline.
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from workflows.state import WorkflowState, create_initial_state
from workflows.agents import (
    rfp_analyzer_agent,
    challenge_extractor_agent,
    discovery_question_agent,
    value_proposition_agent,
    case_study_matcher_agent,
    proposal_builder_agent
)

def rfp_analyzer_node(state: WorkflowState) -> Dict[str, Any]:
    """RFP Analyzer Agent node."""
    print(f"  [RFP Analyzer] Starting...")
    updates = {"current_step": "rfp_analyzer"}
    
    try:
        # Get RFP text if not in state
        rfp_text = state.get("rfp_text")
        if not rfp_text:
            # Try to get from state context (passed from workflow manager)
            rfp_text = state.get("rfp_text", "")
        
        print(f"  [RFP Analyzer] RFP text length: {len(rfp_text) if rfp_text else 0}")
        
        # Run analyzer
        result = rfp_analyzer_agent.analyze(
            rfp_text=rfp_text,
            retrieved_context=state.get("retrieved_context"),
            project_id=state["project_id"]
        )
        
        print(f"  [RFP Analyzer] Result: {list(result.keys()) if result else 'None'}")
        
        if result.get("error"):
            print(f"  [RFP Analyzer] ❌ Error: {result['error']}")
            updates["errors"] = [f"RFP Analyzer: {result['error']}"]
        else:
            print(f"  [RFP Analyzer] ✓ Success - Summary: {len(str(result.get('rfp_summary', ''))) if result.get('rfp_summary') else 0} chars")
            updates.update({
                "rfp_summary": result.get("rfp_summary"),
                "context_overview": result.get("context_overview"),
                "business_objectives": result.get("business_objectives"),
                "project_scope": result.get("project_scope"),
                "execution_log": [{
                    "step": "rfp_analyzer",
                    "status": "success",
                    "output": "RFP analyzed successfully"
                }]
            })
    except Exception as e:
        print(f"  [RFP Analyzer] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        updates["errors"] = [f"RFP Analyzer error: {str(e)}"]
        updates["execution_log"] = [{
            "step": "rfp_analyzer",
            "status": "error",
            "error": str(e)
        }]
    
    return updates

def challenge_extractor_node(state: WorkflowState) -> Dict[str, Any]:
    """Challenge Extractor Agent node."""
    # Check if challenges task is enabled
    selected_tasks = state.get("selected_tasks", {})
    if not selected_tasks.get("challenges", True):
        print(f"  [Challenge Extractor] Skipped (not selected)")
        return {"current_step": "challenge_extractor", "challenges": []}
    
    print(f"  [Challenge Extractor] Starting...")
    updates = {"current_step": "challenge_extractor"}
    
    try:
        rfp_summary = state.get("rfp_summary", "")
        business_objectives = state.get("business_objectives", [])
        print(f"  [Challenge Extractor] RFP Summary: {len(rfp_summary) if rfp_summary else 0} chars, Objectives: {len(business_objectives) if business_objectives else 0}")
        
        result = challenge_extractor_agent.extract_challenges(
            rfp_summary=rfp_summary,
            business_objectives=business_objectives
        )
        
        print(f"  [Challenge Extractor] Result: {list(result.keys()) if result else 'None'}")
        
        if result.get("error"):
            print(f"  [Challenge Extractor] ❌ Error: {result['error']}")
            updates["errors"] = [f"Challenge Extractor: {result['error']}"]
        else:
            challenges = result.get("challenges", [])
            print(f"  [Challenge Extractor] ✓ Success - Challenges: {len(challenges) if challenges else 0}")
            updates.update({
                "challenges": challenges,
                "execution_log": [{
                    "step": "challenge_extractor",
                    "status": "success",
                    "challenges_count": len(challenges) if challenges else 0
                }]
            })
    except Exception as e:
        print(f"  [Challenge Extractor] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        updates["errors"] = [f"Challenge Extractor error: {str(e)}"]
        updates["execution_log"] = [{
            "step": "challenge_extractor",
            "status": "error",
            "error": str(e)
        }]
    
    return updates

def discovery_question_node(state: WorkflowState) -> Dict[str, Any]:
    """Discovery Question Agent node."""
    # Check if questions task is enabled
    selected_tasks = state.get("selected_tasks", {})
    if not selected_tasks.get("questions", True):
        print(f"  [Discovery Question] Skipped (not selected)")
        return {"discovery_questions": {}}
    
    print(f"  [Discovery Question] Starting...")
    updates = {}
    
    try:
        challenges = state.get("challenges", [])
        print(f"  [Discovery Question] Challenges available: {len(challenges) if challenges else 0}")
        
        result = discovery_question_agent.generate_questions(
            challenges=challenges
        )
        
        print(f"  [Discovery Question] Result: {list(result.keys()) if result else 'None'}")
        
        if result.get("error"):
            print(f"  [Discovery Question] ❌ Error: {result['error']}")
            updates["errors"] = [f"Discovery Question: {result['error']}"]
        else:
            questions = result.get("discovery_questions", {})
            questions_count = sum(len(q) for q in questions.values()) if questions else 0
            print(f"  [Discovery Question] ✓ Success - Questions generated: {questions_count}")
            updates.update({
                "discovery_questions": questions,
                "execution_log": [{
                    "step": "discovery_question",
                    "status": "success",
                    "questions_count": questions_count
                }]
            })
    except Exception as e:
        print(f"  [Discovery Question] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        updates["errors"] = [f"Discovery Question error: {str(e)}"]
        updates["execution_log"] = [{
            "step": "discovery_question",
            "status": "error",
            "error": str(e)
        }]
    
    return updates

def value_proposition_node(state: WorkflowState) -> Dict[str, Any]:
    """Value Proposition Agent node."""
    print(f"  [Value Proposition] Starting...")
    updates = {}
    
    try:
        challenges = state.get("challenges", [])
        rfp_summary = state.get("rfp_summary", "")
        print(f"  [Value Proposition] Challenges: {len(challenges) if challenges else 0}, RFP Summary: {len(rfp_summary) if rfp_summary else 0} chars")
        
        result = value_proposition_agent.generate_value_propositions(
            challenges=challenges,
            rfp_summary=rfp_summary
        )
        
        print(f"  [Value Proposition] Result: {list(result.keys()) if result else 'None'}")
        
        if result.get("error"):
            print(f"  [Value Proposition] ❌ Error: {result['error']}")
            updates["errors"] = [f"Value Proposition: {result['error']}"]
        else:
            value_props = result.get("value_propositions", [])
            print(f"  [Value Proposition] ✓ Success - Value propositions: {len(value_props) if value_props else 0}")
            updates.update({
                "value_propositions": value_props,
                "execution_log": [{
                    "step": "value_proposition",
                    "status": "success",
                    "value_props_count": len(value_props) if value_props else 0
                }]
            })
    except Exception as e:
        print(f"  [Value Proposition] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        updates["errors"] = [f"Value Proposition error: {str(e)}"]
        updates["execution_log"] = [{
            "step": "value_proposition",
            "status": "error",
            "error": str(e)
        }]
    
    return updates

def case_study_matcher_node(state: WorkflowState) -> Dict[str, Any]:
    """Case Study Matcher Agent node."""
    # Check if cases task is enabled
    selected_tasks = state.get("selected_tasks", {})
    if not selected_tasks.get("cases", True):
        print(f"  [Case Study Matcher] Skipped (not selected)")
        return {"matching_case_studies": []}
    
    print(f"  [Case Study Matcher] Starting...")
    updates = {}
    
    try:
        challenges = state.get("challenges", [])
        print(f"  [Case Study Matcher] Challenges available: {len(challenges) if challenges else 0}")
        
        # Get db from state if available, otherwise create new session
        from db.database import SessionLocal
        db = SessionLocal()
        try:
            result = case_study_matcher_agent.match_case_studies(
                challenges=challenges,
                db=db,
                top_k=3
            )
            
            print(f"  [Case Study Matcher] Result: {list(result.keys()) if result else 'None'}")
            
            if result.get("error"):
                print(f"  [Case Study Matcher] ❌ Error: {result['error']}")
                updates["errors"] = [f"Case Study Matcher: {result['error']}"]
            else:
                case_studies = result.get("matching_case_studies", [])
                print(f"  [Case Study Matcher] ✓ Success - Case studies matched: {len(case_studies) if case_studies else 0}")
                updates.update({
                    "matching_case_studies": case_studies,
                    "execution_log": [{
                        "step": "case_study_matcher",
                        "status": "success",
                        "case_studies_count": len(case_studies) if case_studies else 0
                    }]
                })
        finally:
            db.close()
    except Exception as e:
        print(f"  [Case Study Matcher] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        updates["errors"] = [f"Case Study Matcher error: {str(e)}"]
        updates["execution_log"] = [{
            "step": "case_study_matcher",
            "status": "error",
            "error": str(e)
        }]
    
    return updates

def proposal_builder_node(state: WorkflowState) -> Dict[str, Any]:
    """Proposal Builder Agent node."""
    # Check if proposal task is enabled
    selected_tasks = state.get("selected_tasks", {})
    if not selected_tasks.get("proposal", True):
        print(f"  [Proposal Builder] Skipped (not selected)")
        return {"current_step": "proposal_builder", "proposal_draft": None}
    
    print(f"  [Proposal Builder] Starting...")
    # This runs sequentially after parallel nodes, so it's safe to update current_step
    updates = {"current_step": "proposal_builder"}
    
    try:
        rfp_summary = state.get("rfp_summary", "")
        challenges = state.get("challenges", [])
        value_propositions = state.get("value_propositions", [])
        case_studies = state.get("matching_case_studies", [])
        
        print(f"  [Proposal Builder] Inputs - Summary: {len(rfp_summary) if rfp_summary else 0} chars, "
              f"Challenges: {len(challenges) if challenges else 0}, "
              f"Value Props: {len(value_propositions) if value_propositions else 0}, "
              f"Case Studies: {len(case_studies) if case_studies else 0}")
        
        result = proposal_builder_agent.build_proposal(
            rfp_summary=rfp_summary,
            challenges=challenges,
            value_propositions=value_propositions,
            case_studies=case_studies
        )
        
        print(f"  [Proposal Builder] Result: {list(result.keys()) if result else 'None'}")
        
        if result.get("error"):
            print(f"  [Proposal Builder] ❌ Error: {result['error']}")
            updates["errors"] = [f"Proposal Builder: {result['error']}"]
        else:
            proposal_draft = result.get("proposal_draft")
            print(f"  [Proposal Builder] ✓ Success - Proposal draft: {'Created' if proposal_draft else 'Not created'}")
            updates.update({
                "proposal_draft": proposal_draft,
                "execution_log": [{
                    "step": "proposal_builder",
                    "status": "success",
                    "output": "Proposal draft created"
                }]
            })
    except Exception as e:
        print(f"  [Proposal Builder] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        updates["errors"] = [f"Proposal Builder error: {str(e)}"]
        updates["execution_log"] = [{
            "step": "proposal_builder",
            "status": "error",
            "error": str(e)
        }]
    
    return updates

def should_run_challenges(state: WorkflowState) -> str:
    """Conditional edge: check if challenges should run."""
    selected_tasks = state.get("selected_tasks", {})
    if selected_tasks.get("challenges", True):
        return "challenge_extractor"
    return "proposal_builder"  # Skip to proposal if challenges not selected

def create_workflow_graph() -> StateGraph:
    """Create the LangGraph workflow."""
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("rfp_analyzer", rfp_analyzer_node)
    workflow.add_node("challenge_extractor", challenge_extractor_node)
    workflow.add_node("discovery_question", discovery_question_node)
    workflow.add_node("value_proposition", value_proposition_node)
    workflow.add_node("case_study_matcher", case_study_matcher_node)
    workflow.add_node("proposal_builder", proposal_builder_node)
    
    # Define edges (workflow order)
    workflow.set_entry_point("rfp_analyzer")
    # RFP analyzer always runs, then conditionally go to challenge extractor or proposal builder
    workflow.add_conditional_edges(
        "rfp_analyzer",
        should_run_challenges,
        {
            "challenge_extractor": "challenge_extractor",
            "proposal_builder": "proposal_builder"
        }
    )
    # After challenge extractor, run parallel tasks (they check internally if enabled)
    workflow.add_edge("challenge_extractor", "discovery_question")
    workflow.add_edge("challenge_extractor", "value_proposition")
    workflow.add_edge("challenge_extractor", "case_study_matcher")
    # All parallel tasks converge to proposal builder
    workflow.add_edge("discovery_question", "proposal_builder")
    workflow.add_edge("value_proposition", "proposal_builder")
    workflow.add_edge("case_study_matcher", "proposal_builder")
    workflow.add_edge("proposal_builder", END)
    
    return workflow.compile()

# Global workflow instance
workflow_graph = create_workflow_graph()

