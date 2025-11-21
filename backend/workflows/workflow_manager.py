"""
Workflow manager for executing and managing multi-agent workflows.
"""
from typing import Dict, Any, Optional
from workflows.graph import workflow_graph
from workflows.state import create_initial_state, WorkflowState
from db.database import get_db
from models.rfp_document import RFPDocument
from models.project import Project
from models.insights import Insights
from sqlalchemy.orm import Session

class WorkflowManager:
    """Manages workflow execution and state."""
    
    def __init__(self):
        self.workflow = workflow_graph
        self.active_states: Dict[str, WorkflowState] = {}
        self.project_states: Dict[int, str] = {}  # Map project_id to state_id
    
    def run_workflow(
        self,
        project_id: int,
        rfp_document_id: int,
        db: Session,
        selected_tasks: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete workflow.
        
        Args:
            project_id: Project ID
            rfp_document_id: RFP document ID
            db: Database session
        
        Returns:
            dict with workflow results
        """
        import sys
        sys.stdout.flush()  # Force flush output
        
        print(f"\n{'='*60}", flush=True)
        print(f"WORKFLOW MANAGER: Starting workflow execution", flush=True)
        print(f"Project ID: {project_id}", flush=True)
        print(f"RFP Document ID: {rfp_document_id}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        # Get RFP document
        rfp_doc = db.query(RFPDocument).filter(
            RFPDocument.id == rfp_document_id
        ).first()
        
        if not rfp_doc:
            print(f"❌ RFP document {rfp_document_id} not found")
            return {
                "success": False,
                "error": "RFP document not found"
            }
        
        print(f"✓ RFP document found: {rfp_doc.filename}")
        
        # Get RFP text
        rfp_text = rfp_doc.extracted_text
        if not rfp_text:
            print(f"❌ RFP document has no extracted text")
            return {
                "success": False,
                "error": "RFP document has no extracted text. Please build index first."
            }
        
        print(f"✓ RFP text extracted: {len(rfp_text)} characters")
        
        # Create initial state
        initial_state = create_initial_state(
            project_id=project_id,
            rfp_document_id=rfp_document_id,
            rfp_text=rfp_text,
            retrieved_context=None,
            selected_tasks=selected_tasks
        )
        
        # Store state
        state_id = f"{project_id}_{rfp_document_id}"
        self.active_states[state_id] = initial_state
        self.project_states[project_id] = state_id  # Map project to state
        print(f"✓ Initial state created: {state_id}")
        
        try:
            print(f"\n{'='*60}")
            print(f"🚀 STARTING WORKFLOW EXECUTION")
            print(f"{'='*60}")
            print(f"Workflow will execute the following steps:")
            print(f"  1. RFP Analyzer - Analyze RFP document")
            print(f"  2. Challenge Extractor - Extract business challenges")
            print(f"  3. Discovery Question Agent - Generate discovery questions (parallel)")
            print(f"  4. Value Proposition Agent - Generate value propositions (parallel)")
            print(f"  5. Case Study Matcher - Match relevant case studies (parallel)")
            print(f"  6. Proposal Builder - Build proposal draft")
            print(f"{'='*60}\n")
            
            # Run workflow
            final_state = self.workflow.invoke(initial_state)
            
            print(f"\n{'='*60}")
            print(f"✓ WORKFLOW EXECUTION COMPLETED")
            print(f"{'='*60}\n")
            
            # Debug: Print final state keys and values
            print(f"\n{'='*60}")
            print(f"FINAL STATE DEBUG")
            print(f"{'='*60}")
            print(f"RFP Summary: {bool(final_state.get('rfp_summary'))} ({len(str(final_state.get('rfp_summary', ''))) if final_state.get('rfp_summary') else 0} chars)")
            print(f"Challenges: {final_state.get('challenges')} (type: {type(final_state.get('challenges'))})")
            print(f"Value Propositions: {final_state.get('value_propositions')} (type: {type(final_state.get('value_propositions'))})")
            print(f"Discovery Questions: {final_state.get('discovery_questions')} (type: {type(final_state.get('discovery_questions'))})")
            print(f"Case Studies: {final_state.get('matching_case_studies')} (type: {type(final_state.get('matching_case_studies'))})")
            print(f"Proposal Draft: {bool(final_state.get('proposal_draft'))}")
            print(f"Errors: {final_state.get('errors', [])}")
            print(f"Execution Log: {len(final_state.get('execution_log', []))} entries")
            if final_state.get('execution_log'):
                for log_entry in final_state.get('execution_log', []):
                    print(f"  - {log_entry.get('step', 'unknown')}: {log_entry.get('status', 'unknown')}")
            print(f"{'='*60}\n")
            
            # Update stored state
            self.active_states[state_id] = final_state
            
            # Save insights to database
            print(f"💾 Saving insights to database...")
            self._save_insights(final_state, db)
            print(f"✓ Insights saved successfully")
            
            # Handle None values properly - .get() returns None if key exists with None value
            challenges = final_state.get("challenges") or []
            value_propositions = final_state.get("value_propositions") or []
            matching_case_studies = final_state.get("matching_case_studies") or []
            
            summary = {
                "rfp_summary": final_state.get("rfp_summary"),
                "challenges_count": len(challenges) if isinstance(challenges, list) else 0,
                "value_propositions_count": len(value_propositions) if isinstance(value_propositions, list) else 0,
                "case_studies_count": len(matching_case_studies) if isinstance(matching_case_studies, list) else 0,
                "proposal_created": final_state.get("proposal_draft") is not None
            }
            
            print(f"\n{'='*60}")
            print(f"✅ WORKFLOW COMPLETED SUCCESSFULLY")
            print(f"{'='*60}")
            print(f"📊 GENERATED INSIGHTS SUMMARY:")
            print(f"  • RFP Summary: {'✓ Generated' if summary['rfp_summary'] else '✗ Not generated'}")
            print(f"  • Challenges Extracted: {summary['challenges_count']}")
            print(f"  • Value Propositions: {summary['value_propositions_count']}")
            print(f"  • Case Studies Matched: {summary['case_studies_count']}")
            print(f"  • Proposal Draft: {'✓ Created' if summary['proposal_created'] else '✗ Not created'}")
            
            # Show errors if any
            errors = final_state.get('errors', [])
            if errors:
                print(f"\n⚠️  ERRORS ENCOUNTERED ({len(errors)}):")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error}")
            else:
                print(f"\n✓ No errors encountered")
            
            print(f"{'='*60}")
            print(f"🎉 Workflow execution finished! Insights saved to database.")
            print(f"{'='*60}\n")
            
            return {
                "success": True,
                "state_id": state_id,
                "state": final_state,
                "summary": summary
            }
        
        except Exception as e:
            print(f"\n❌ WORKFLOW ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "state_id": state_id
            }
    
    def get_state(self, state_id: str) -> Optional[WorkflowState]:
        """Get workflow state by state_id."""
        return self.active_states.get(state_id)
    
    def get_state_by_project(self, project_id: int) -> Optional[WorkflowState]:
        """Get workflow state by project_id."""
        state_id = self.project_states.get(project_id)
        if state_id:
            return self.active_states.get(state_id)
        return None
    
    def _save_insights(self, state: WorkflowState, db: Session):
        """Save workflow results to Insights table."""
        try:
            project_id = state["project_id"]
            
            # Check user's auto-save setting
            from models.project import Project
            from models.user import User
            project = db.query(Project).filter(Project.id == project_id).first()
            if project and project.owner_id:
                user = db.query(User).filter(User.id == project.owner_id).first()
                if user and user.auto_save_insights is False:
                    print(f"\n  ⏭️  Auto-save insights is disabled for user {user.id}. Skipping save.")
                    return
            
            print(f"\n  💾 Saving insights for project {project_id}...")
            
            # Debug: Print what we're trying to save
            print(f"  📋 Data to save:")
            print(f"    - RFP Summary: {type(state.get('rfp_summary'))} = {str(state.get('rfp_summary'))[:100] if state.get('rfp_summary') else 'None'}...")
            print(f"    - Challenges: {type(state.get('challenges'))} = {len(state.get('challenges')) if isinstance(state.get('challenges'), list) else 'None/Not a list'}")
            print(f"    - Value Propositions: {type(state.get('value_propositions'))} = {len(state.get('value_propositions')) if isinstance(state.get('value_propositions'), list) else 'None/Not a list'}")
            print(f"    - Discovery Questions: {type(state.get('discovery_questions'))} = {state.get('discovery_questions')}")
            print(f"    - Business Objectives: {type(state.get('business_objectives'))} = {state.get('business_objectives')}")
            
            # Check if insights already exist
            insights = db.query(Insights).filter(
                Insights.project_id == project_id
            ).first()
            
            if not insights:
                print(f"  ➕ Creating new insights record...")
                insights = Insights(project_id=project_id)
                db.add(insights)
            else:
                print(f"  🔄 Updating existing insights record (ID: {insights.id})...")
            
            # Update insights - SQLAlchemy JSON columns handle serialization automatically
            rfp_summary = state.get("rfp_summary")
            insights.executive_summary = rfp_summary if rfp_summary else None
            
            challenges = state.get("challenges")
            if challenges:
                # Ensure challenges is a list (SQLAlchemy JSON column will serialize it)
                if isinstance(challenges, list):
                    insights.challenges = challenges if challenges else None
                else:
                    print(f"  ⚠️  Challenges is not a list: {type(challenges)}, value: {challenges}")
                    insights.challenges = None
            else:
                insights.challenges = None
            
            value_propositions = state.get("value_propositions")
            if value_propositions:
                if isinstance(value_propositions, list):
                    insights.value_propositions = value_propositions if value_propositions else None
                else:
                    print(f"  ⚠️  Value propositions is not a list: {type(value_propositions)}, value: {value_propositions}")
                    insights.value_propositions = None
            else:
                insights.value_propositions = None
            
            discovery_questions = state.get("discovery_questions")
            if discovery_questions:
                if isinstance(discovery_questions, dict):
                    insights.discovery_questions = discovery_questions if discovery_questions else None
                else:
                    print(f"  ⚠️  Discovery questions is not a dict: {type(discovery_questions)}, value: {discovery_questions}")
                    insights.discovery_questions = None
            else:
                insights.discovery_questions = None
            
            business_objectives = state.get("business_objectives")
            if business_objectives:
                if isinstance(business_objectives, list):
                    insights.tags = business_objectives if business_objectives else None
                else:
                    print(f"  ⚠️  Business objectives is not a list: {type(business_objectives)}, value: {business_objectives}")
                    insights.tags = None
            else:
                insights.tags = None
            
            matching_case_studies = state.get("matching_case_studies")
            if matching_case_studies:
                if isinstance(matching_case_studies, list):
                    insights.matching_case_studies = matching_case_studies if matching_case_studies else None
                else:
                    print(f"  ⚠️  Matching case studies is not a list: {type(matching_case_studies)}, value: {matching_case_studies}")
                    insights.matching_case_studies = None
            else:
                insights.matching_case_studies = None
            
            insights.ai_model_used = state.get("ai_model_used", "gemini-2.0-flash")
            from datetime import datetime
            insights.analysis_timestamp = datetime.utcnow()
            
            print(f"\n  ✅ Final values before commit:")
            print(f"    - Executive summary: {len(str(insights.executive_summary)) if insights.executive_summary else 0} chars")
            print(f"    - Challenges: {len(insights.challenges) if insights.challenges and isinstance(insights.challenges, list) else 0}")
            print(f"    - Value propositions: {len(insights.value_propositions) if insights.value_propositions and isinstance(insights.value_propositions, list) else 0}")
            print(f"    - Discovery questions: {len(insights.discovery_questions) if insights.discovery_questions and isinstance(insights.discovery_questions, dict) else 0}")
            print(f"    - Matching case studies: {len(insights.matching_case_studies) if insights.matching_case_studies and isinstance(insights.matching_case_studies, list) else 0}")
            print(f"    - Tags: {len(insights.tags) if insights.tags and isinstance(insights.tags, list) else 0}")
            
            db.commit()
            db.refresh(insights)
            print(f"  ✓ Insights saved successfully (ID: {insights.id})\n")
        
        except Exception as e:
            print(f"  ❌ Error saving insights: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()

# Global instance
workflow_manager = WorkflowManager()

