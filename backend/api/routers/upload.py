from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
from datetime import datetime
from db.database import get_db
from models.user import User
from models.project import Project
from models.rfp_document import RFPDocument  # Fixed: import from correct module
from utils.dependencies import get_current_user
from utils.config import settings

router = APIRouter()

# Ensure upload directory exists (fallback)
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def get_file_extension(filename: str) -> str:
    """Get file extension."""
    return Path(filename).suffix.lower()

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = get_file_extension(filename)
    return ext in settings.allowed_extensions_list

@router.post("/rfp")
async def upload_rfp(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an RFP document for a project."""
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
    
    # Validate file
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions_list)}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Check file size
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / (1024*1024)}MB"
        )
    
    # Generate unique filename
    file_ext = get_file_extension(file.filename)
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Create project-specific directory
    project_dir = UPLOAD_DIR / f"project_{project_id}"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Upload to local storage
    local_file_path = project_dir / unique_filename
    with open(local_file_path, "wb") as f:
        f.write(file_content)
    storage_path = str(local_file_path)
    
    # Create database record
    rfp_doc = RFPDocument(
        project_id=project_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=storage_path,
        file_size=file_size,
        file_type=file_ext[1:]  # Remove the dot
    )
    
    db.add(rfp_doc)
    db.commit()
    db.refresh(rfp_doc)
    
    # Optionally build index automatically (can be done async in production)
    # For now, index building is done via /rag/build-index endpoint
    
    return {
        "id": rfp_doc.id,
        "filename": rfp_doc.original_filename,
        "file_size": rfp_doc.file_size,
        "file_type": rfp_doc.file_type,
        "uploaded_at": rfp_doc.uploaded_at,
        "message": "File uploaded successfully. Use /rag/build-index to create searchable index.",
        "rfp_document_id": rfp_doc.id
    }

