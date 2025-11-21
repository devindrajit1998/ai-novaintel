from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from db.database import get_db
from models.user import User
from models.case_study_document import CaseStudyDocument, ProcessingStatus
from utils.dependencies import get_current_user
from services.case_study_trainer import case_study_trainer
from utils.config import settings
import os
import uuid
from pathlib import Path

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_case_study_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a case study document (PDF/DOCX) for training."""
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.docx']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )
    
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR) / "case_studies"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}{file_ext}"
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create document record
    document = CaseStudyDocument(
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file_ext.lstrip('.'),
        processing_status=ProcessingStatus.PENDING.value
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document in background
    def process_document(doc_id: int):
        from db.database import SessionLocal
        db_session = SessionLocal()
        try:
            doc = db_session.query(CaseStudyDocument).filter(
                CaseStudyDocument.id == doc_id
            ).first()
            if doc:
                case_study_trainer.process_case_study_document(doc, db_session)
        finally:
            db_session.close()
    
    background_tasks.add_task(process_document, document.id)
    
    return {
        "success": True,
        "message": "Document uploaded, processing started",
        "document_id": document.id,
        "processing_status": document.processing_status or ProcessingStatus.PENDING.value
    }

@router.get("/list")
async def list_case_study_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all case study documents uploaded by the user."""
    documents = db.query(CaseStudyDocument).filter(
        CaseStudyDocument.user_id == current_user.id
    ).order_by(CaseStudyDocument.created_at.desc()).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "processing_status": doc.processing_status if doc.processing_status else "pending",
            "error_message": doc.error_message,
            "case_study_id": doc.case_study_id,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat()
        }
        for doc in documents
    ]

@router.delete("/{document_id}")
async def delete_case_study_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a case study document."""
    document = db.query(CaseStudyDocument).filter(
        CaseStudyDocument.id == document_id,
        CaseStudyDocument.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    db.delete(document)
    db.commit()
    
    return {"success": True, "message": "Document deleted successfully"}

@router.get("/status/{document_id}")
async def get_document_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get processing status of a case study document."""
    document = db.query(CaseStudyDocument).filter(
        CaseStudyDocument.id == document_id,
        CaseStudyDocument.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "id": document.id,
        "processing_status": document.processing_status if document.processing_status else "pending",
        "error_message": document.error_message,
        "case_study_id": document.case_study_id
    }
