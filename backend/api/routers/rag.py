"""
RAG API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from models.project import Project
from models.rfp_document import RFPDocument
from api.schemas.rag import (
    BuildIndexRequest,
    BuildIndexResponse,
    QueryRequest,
    QueryResponse,
    ChatRequest,
    ChatResponse
)
from utils.dependencies import get_current_user
from rag.index_builder import index_builder
from rag.retriever import retriever
from rag.chat_service import chat_service
from pathlib import Path

router = APIRouter()

@router.post("/build-index", response_model=BuildIndexResponse)
async def build_index(
    request: BuildIndexRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Build vector index for an RFP document.
    """
    print(f"Building index for RFP document {request.rfp_document_id}, user {current_user.id} ({current_user.email})")
    
    # Get RFP document
    rfp_doc = db.query(RFPDocument).filter(
        RFPDocument.id == request.rfp_document_id
    ).first()
    
    if not rfp_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RFP document not found: {request.rfp_document_id}"
        )
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == rfp_doc.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        # Check if project exists but belongs to different user
        project_exists = db.query(Project).filter(
            Project.id == rfp_doc.project_id
        ).first()
        
        if project_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Project {rfp_doc.project_id} does not belong to user {current_user.id}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {rfp_doc.project_id}"
            )
    
    # Check if file exists
    file_path = Path(rfp_doc.file_path)
    if not file_path.exists():
        return BuildIndexResponse(
            success=False,
            error=f"File not found: {rfp_doc.file_path}"
        )
    
    # Check vector store availability before building index
    from rag.vector_store import vector_store_manager
    if not vector_store_manager.is_available():
        return BuildIndexResponse(
            success=False,
            error="Vector store not available. Please ensure Chroma dependencies are installed (pip install chromadb llama-index-vector-stores-chroma) and restart the backend server."
        )
    
    # Check embedding service availability
    from rag.embedding_service import embedding_service
    if not embedding_service.is_available():
        return BuildIndexResponse(
            success=False,
            error="Embedding service not available. Please ensure HuggingFace dependencies are installed (pip install llama-index-embeddings-huggingface sentence-transformers) and restart the backend server."
        )
    
    # Build index
    result = index_builder.build_index_from_file(
        file_path=str(file_path),
        file_type=rfp_doc.file_type,
        project_id=rfp_doc.project_id,
        rfp_document_id=rfp_doc.id,
        db=db
    )
    
    return BuildIndexResponse(**result)

@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Query the RAG system to retrieve relevant context.
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        # Check if project exists but belongs to different user
        project_exists = db.query(Project).filter(
            Project.id == request.project_id
        ).first()
        
        if project_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Project {request.project_id} does not belong to user {current_user.id}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {request.project_id}"
            )
    
    # Retrieve nodes
    try:
        nodes = retriever.get_nodes_with_metadata(
            query=request.query,
            project_id=request.project_id,
            top_k=request.top_k
        )
        
        return QueryResponse(
            success=True,
            results=nodes,
            query=request.query
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            results=[],
            query=request.query,
            error=str(e)
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_rfp(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with RFP document using RAG.
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        # Check if project exists but belongs to different user
        project_exists = db.query(Project).filter(
            Project.id == request.project_id
        ).first()
        
        if project_exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Project {request.project_id} does not belong to user {current_user.id}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {request.project_id}"
            )
    
    # Chat with RFP
    try:
        result = chat_service.chat(
            query=request.query,
            project_id=request.project_id,
            conversation_history=request.conversation_history,
            top_k=request.top_k
        )
        
        # Ensure result has all required fields
        if 'query' not in result:
            result['query'] = request.query
        if 'sources' not in result:
            result['sources'] = []
        if 'context_used' not in result:
            result['context_used'] = 0
        
        return ChatResponse(**result)
    except Exception as e:
        # Return a valid ChatResponse even on unexpected errors
        return ChatResponse(
            success=False,
            error=f"Unexpected error: {str(e)}",
            answer=None,
            sources=[],
            context_used=0,
            query=request.query
        )

@router.get("/status/{project_id}")
async def get_rag_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get RAG status for a project - check if index is built and ready.
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check RFP documents
    rfp_docs = db.query(RFPDocument).filter(
        RFPDocument.project_id == project_id
    ).all()
    
    # Check if any have been indexed (have extracted_text)
    indexed_docs = [doc for doc in rfp_docs if doc.extracted_text]
    
    # Check insights
    from models.insights import Insights
    insights = db.query(Insights).filter(
        Insights.project_id == project_id
    ).first()
    
    return {
        "project_id": project_id,
        "rfp_documents_count": len(rfp_docs),
        "indexed_documents_count": len(indexed_docs),
        "has_insights": insights is not None,
        "next_steps": {
            "build_index": len(rfp_docs) > 0 and len(indexed_docs) == 0,
            "run_agents": len(indexed_docs) > 0 and insights is None,
            "ready": insights is not None
        },
        "message": (
            "Ready to generate insights" if insights
            else "Run /agents/run-all to generate insights" if indexed_docs
            else "Upload RFP and build index first" if rfp_docs
            else "Upload an RFP document first"
        )
    }

