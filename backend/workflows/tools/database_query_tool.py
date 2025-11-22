"""
Database query tool for agents to query internal database.
"""
from typing import Any, Dict, List, Optional
from workflows.tools.base_tool import BaseTool, ToolResult
from sqlalchemy.orm import Session
from db.database import SessionLocal
import sys


class DatabaseQueryTool(BaseTool):
    """Tool for querying internal database."""
    
    def __init__(self):
        """Initialize database query tool."""
        super().__init__(
            name="database_query",
            description="Query internal database for projects, proposals, case studies, insights, etc."
        )
        print("[OK] Database Query Tool initialized", file=sys.stderr, flush=True)
    
    def execute(
        self,
        query_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> ToolResult:
        """
        Execute database query.
        
        Args:
            query_type: "projects", "proposals", "case_studies", "insights", "rfp_documents"
            filters: Optional filters (e.g., {"project_id": 1, "status": "active"})
            limit: Maximum number of results
        
        Returns:
            ToolResult with query results
        """
        if not filters:
            filters = {}
        
        try:
            db = SessionLocal()
            try:
                if query_type == "projects":
                    result = self._query_projects(db, filters, limit)
                elif query_type == "proposals":
                    result = self._query_proposals(db, filters, limit)
                elif query_type == "case_studies":
                    result = self._query_case_studies(db, filters, limit)
                elif query_type == "insights":
                    result = self._query_insights(db, filters, limit)
                elif query_type == "rfp_documents":
                    result = self._query_rfp_documents(db, filters, limit)
                else:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Unknown query type: {query_type}"
                    )
                
                return ToolResult(
                    success=True,
                    result=result,
                    metadata={"query_type": query_type, "filters": filters}
                )
            finally:
                db.close()
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Database query failed: {str(e)}"
            )
    
    def _query_projects(self, db: Session, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Query projects."""
        from models.project import Project
        
        query = db.query(Project)
        
        if "project_id" in filters:
            query = query.filter(Project.id == filters["project_id"])
        if "user_id" in filters:
            query = query.filter(Project.owner_id == filters["user_id"])
        if "status" in filters:
            query = query.filter(Project.status == filters["status"])
        
        projects = query.limit(limit).all()
        
        return [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in projects
        ]
    
    def _query_proposals(self, db: Session, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Query proposals."""
        from models.proposal import Proposal
        
        query = db.query(Proposal)
        
        if "proposal_id" in filters:
            query = query.filter(Proposal.id == filters["proposal_id"])
        if "project_id" in filters:
            query = query.filter(Proposal.project_id == filters["project_id"])
        if "status" in filters:
            query = query.filter(Proposal.status == filters["status"])
        
        proposals = query.limit(limit).all()
        
        return [
            {
                "id": p.id,
                "project_id": p.project_id,
                "title": p.title,
                "status": p.status,
                "template_type": p.template_type
            }
            for p in proposals
        ]
    
    def _query_case_studies(self, db: Session, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Query case studies."""
        from models.case_study import CaseStudy
        
        query = db.query(CaseStudy)
        
        if "case_study_id" in filters:
            query = query.filter(CaseStudy.id == filters["case_study_id"])
        if "industry" in filters:
            query = query.filter(CaseStudy.industry == filters["industry"])
        if "indexed" in filters:
            query = query.filter(CaseStudy.indexed == filters["indexed"])
        
        case_studies = query.limit(limit).all()
        
        return [
            {
                "id": cs.id,
                "title": cs.title,
                "industry": cs.industry,
                "impact": cs.impact,
                "description": cs.description
            }
            for cs in case_studies
        ]
    
    def _query_insights(self, db: Session, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Query insights."""
        from models.insights import Insights
        
        query = db.query(Insights)
        
        if "insight_id" in filters:
            query = query.filter(Insights.id == filters["insight_id"])
        if "project_id" in filters:
            query = query.filter(Insights.project_id == filters["project_id"])
        
        insights = query.limit(limit).all()
        
        return [
            {
                "id": i.id,
                "project_id": i.project_id,
                "has_rfp_summary": bool(i.rfp_summary),
                "has_challenges": bool(i.challenges),
                "has_value_propositions": bool(i.value_propositions)
            }
            for i in insights
        ]
    
    def _query_rfp_documents(self, db: Session, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Query RFP documents."""
        from models.rfp_document import RFPDocument
        
        query = db.query(RFPDocument)
        
        if "rfp_document_id" in filters:
            query = query.filter(RFPDocument.id == filters["rfp_document_id"])
        if "project_id" in filters:
            query = query.filter(RFPDocument.project_id == filters["project_id"])
        if "processing_status" in filters:
            query = query.filter(RFPDocument.processing_status == filters["processing_status"])
        
        documents = query.limit(limit).all()
        
        return [
            {
                "id": d.id,
                "project_id": d.project_id,
                "filename": d.filename,
                "processing_status": d.processing_status,
                "indexed": d.indexed
            }
            for d in documents
        ]
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get JSON schema for parameters."""
        return {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["projects", "proposals", "case_studies", "insights", "rfp_documents"],
                    "description": "Type of data to query"
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters (e.g., {'project_id': 1, 'status': 'active'})",
                    "additionalProperties": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 10)",
                    "default": 10
                }
            },
            "required": ["query_type"]
        }


# Global instance
database_query_tool = DatabaseQueryTool()

