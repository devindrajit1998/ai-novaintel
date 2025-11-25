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
    auto_index: bool = True,  # Auto-build index by default
    auto_analyze: bool = False,  # Auto-run workflow (optional, for quick proposal)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an RFP document for a project.
    
    Args:
        project_id: Project ID
        file: RFP file to upload
        auto_index: Automatically build RAG index after upload (default: True)
        auto_analyze: Automatically run full workflow including proposal (default: False)
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
    
    index_result = None
    workflow_result = None
    
    # Auto-build index if enabled
    if auto_index:
        try:
            from rag.index_builder import index_builder
            print(f"[UPLOAD] Auto-building index for RFP document {rfp_doc.id}...")
            index_result = index_builder.build_index_from_file(
                file_path=storage_path,
                file_type=file_ext[1:],
                project_id=project_id,
                rfp_document_id=rfp_doc.id,
                db=db
            )
            if index_result and index_result.get('success'):
                print(f"[UPLOAD] ✓ Index built successfully: {index_result.get('chunk_count', 0)} chunks")
            else:
                error_msg = index_result.get('error') if index_result else "Unknown error"
                print(f"[UPLOAD] ⚠ Index build failed: {error_msg}")
                index_result = {"success": False, "error": error_msg}
        except Exception as e:
            print(f"[UPLOAD] ⚠ Error during auto-index: {e}")
            import traceback
            traceback.print_exc()
            index_result = {"success": False, "error": str(e)}
    else:
        index_result = None
    
    # Auto-run workflow if enabled (requires successful indexing)
    # Run in background to avoid blocking the HTTP request
    if auto_analyze and auto_index and index_result and index_result.get('success'):
        try:
            from fastapi import BackgroundTasks
            from workflows.workflow_manager import workflow_manager
            print(f"[UPLOAD] Scheduling workflow to run in background for project {project_id}...")
            
            # Extract rfp_document_id BEFORE starting the background thread
            rfp_document_id = rfp_doc.id  # Get the ID while we still have the main session

            def run_workflow_background():
                """Run workflow in background with its own database session."""
                import time
                # Wait a moment to ensure the main request's DB session is closed
                time.sleep(0.5)
                
                try:
                    # Get a completely new DB session for background task
                    from db.database import SessionLocal
                    background_db = SessionLocal()
                    try:
                        # Add this check first
                        from utils.gemini_service import gemini_service
                        if not gemini_service.is_available():
                            print(f"[UPLOAD] ❌ ERROR: Gemini API key not configured!")
                            print(f"[UPLOAD] Set GEMINI_API_KEY in your .env file")
                            return
                        
                        print(f"[UPLOAD] ✓ Gemini service is available, starting workflow...")
                        
                        # Use the rfp_document_id we extracted earlier, not rfp_doc.id
                        workflow_result = workflow_manager.run_workflow(
                            project_id=project_id,
                            rfp_document_id=rfp_document_id,  # Use the extracted ID, not rfp_doc.id
                            db=background_db,
                            selected_tasks={
                                "challenges": True,
                                "questions": True,
                                "cases": True,
                                "proposal": True  # Always include proposal in quick mode
                            }
                        )
                        if workflow_result.get('success'):
                            print(f"[UPLOAD] ✓ Workflow completed successfully in background")
                        else:
                            print(f"[UPLOAD] ⚠ Workflow failed in background: {workflow_result.get('error')}")
                    except Exception as workflow_error:
                        print(f"[UPLOAD] ⚠ Workflow execution error: {workflow_error}")
                        import traceback
                        traceback.print_exc()
                    finally:
                        try:
                            background_db.close()
                        except Exception as close_error:
                            print(f"[UPLOAD] ⚠ Error closing background DB session: {close_error}")
                except Exception as e:
                    print(f"[UPLOAD] ⚠ Error in background workflow setup: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Run workflow in background (non-blocking)
            import threading
            thread = threading.Thread(target=run_workflow_background, daemon=True)
            thread.start()
            print(f"[UPLOAD] ✓ Background thread started (thread_id: {thread.ident}, alive: {thread.is_alive()})")
            
            # Return immediately - workflow is running in background
            workflow_result = {"success": True, "status": "running", "message": "Workflow started in background"}
            print(f"[UPLOAD] ✓ Workflow started in background thread")
        except Exception as e:
            print(f"[UPLOAD] ⚠ Error starting background workflow: {e}")
            import traceback
            traceback.print_exc()
            workflow_result = {"success": False, "error": str(e), "status": "failed"}
    else:
        workflow_result = None
    
    # Determine if workflow is running or completed
    workflow_running = workflow_result and workflow_result.get('status') == "running"
    workflow_completed = workflow_result and workflow_result.get('success') and workflow_result.get('status') != "running"
    
    return {
        "id": rfp_doc.id,
        "filename": rfp_doc.original_filename,
        "file_size": rfp_doc.file_size,
        "file_type": rfp_doc.file_type,
        "uploaded_at": rfp_doc.uploaded_at,
        "rfp_document_id": rfp_doc.id,
        "indexed": index_result.get('success') if index_result else False,
        "analyzed": workflow_completed,
        "analyzing": workflow_running,  # New field to indicate workflow is running
        "proposal_ready": workflow_completed,
        "message": (
            "File uploaded and proposal generated successfully!" if workflow_completed
            else "File uploaded and analysis started! This may take 60-90 seconds." if workflow_running
            else "File uploaded and indexed successfully!" if (index_result and index_result.get('success'))
            else "File uploaded successfully. Use /rag/build-index to create searchable index."
        )
    }

@router.post("/company-logo")
async def upload_company_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a company logo image."""
    # Validate file type (only images)
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    file_ext = get_file_extension(file.filename)
    allowed_image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
    
    if file_ext not in allowed_image_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only image files are allowed. Supported formats: {', '.join(allowed_image_extensions)}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Check file size (max 5MB for logos)
    max_logo_size = 5 * 1024 * 1024  # 5MB
    if file_size > max_logo_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of 5MB"
        )
    
    # Create logos directory
    logos_dir = UPLOAD_DIR / "company_logos"
    logos_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    unique_filename = f"user_{current_user.id}_{uuid.uuid4()}{file_ext}"
    logo_path = logos_dir / unique_filename
    
    # Save file
    with open(logo_path, "wb") as f:
        f.write(file_content)
    
    # Update user's company_logo field
    current_user.company_logo = f"/uploads/company_logos/{unique_filename}"
    db.commit()
    db.refresh(current_user)
    
    # Return relative path that can be used to access the logo
    # The frontend will construct the full URL
    logo_url = f"/uploads/company_logos/{unique_filename}"
    
    return {
        "success": True,
        "message": "Logo uploaded successfully",
        "logo_url": logo_url,
        "file_path": str(logo_path)
    }

