"""
Script to ingest training data into the vector database.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag.index_builder import index_builder
from rag.document_processor import document_processor
from db.database import SessionLocal
from models.rfp_document import RFPDocument
from models.project import Project
from models.user import User

def ingest_documents(data_dir: str, user_email: str = "admin@novaintel.com"):
    """
    Ingest documents from a directory into the vector database.
    
    Args:
        data_dir: Directory containing PDF/DOCX files
        user_email: Email of user to associate documents with
    """
    db = SessionLocal()
    
    try:
        # Get or create admin user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"Creating user: {user_email}")
            from utils.security import get_password_hash
            user = User(
                email=user_email,
                full_name="Admin User",
                hashed_password=get_password_hash("admin123"),  # Change this!
                is_active=True,
                email_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create a training project
        project = Project(
            name="Training Data",
            client_name="Internal",
            industry="Training",
            region="Global",
            project_type="training",
            owner_id=user.id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Process all files in directory
        data_path = Path(data_dir)
        supported_extensions = ['.pdf', '.docx']
        
        for file_path in data_path.rglob('*'):
            if file_path.suffix.lower() in supported_extensions:
                print(f"Processing: {file_path}")
                
                # Create RFP document record
                rfp_doc = RFPDocument(
                    project_id=project.id,
                    filename=file_path.name,
                    original_filename=file_path.name,
                    file_path=str(file_path),
                    file_size=file_path.stat().st_size,
                    file_type=file_path.suffix[1:]  # Remove dot
                )
                db.add(rfp_doc)
                db.commit()
                db.refresh(rfp_doc)
                
                # Build index
                result = index_builder.build_index_from_file(
                    file_path=str(file_path),
                    file_type=file_path.suffix,
                    project_id=project.id,
                    rfp_document_id=rfp_doc.id,
                    db=db
                )
                
                if result.get('success'):
                    print(f"✓ Indexed: {file_path.name}")
                else:
                    print(f"✗ Failed: {file_path.name} - {result.get('error')}")
        
        print(f"\n✓ Ingestion complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_data.py <data_directory> [user_email]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    user_email = sys.argv[2] if len(sys.argv) > 2 else "admin@novaintel.com"
    
    ingest_documents(data_dir, user_email)

