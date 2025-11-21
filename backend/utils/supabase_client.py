"""
Supabase Client - Database, Auth, and Storage integration.
"""
from typing import Optional, Dict, Any
from supabase import create_client, Client
from utils.config import settings
import os

class SupabaseManager:
    """Manage Supabase connections for database, auth, and storage."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.admin_client: Optional[Client] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Supabase clients."""
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                # Regular client (anon key)
                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                print("✓ Supabase client initialized")
                
                # Admin client (service key) if available
                if settings.SUPABASE_SERVICE_KEY:
                    self.admin_client = create_client(
                        settings.SUPABASE_URL,
                        settings.SUPABASE_SERVICE_KEY
                    )
                    print("✓ Supabase admin client initialized")
            except Exception as e:
                print(f"✗ Error initializing Supabase: {e}")
        else:
            print("⚠ Supabase credentials not configured")
    
    def get_client(self) -> Optional[Client]:
        """Get regular Supabase client."""
        return self.client
    
    def get_admin_client(self) -> Optional[Client]:
        """Get admin Supabase client."""
        return self.admin_client or self.client
    
    def is_available(self) -> bool:
        """Check if Supabase is available."""
        return self.client is not None
    
    def get_database_url(self) -> str:
        """Get PostgreSQL connection string from Supabase URL."""
        if not settings.SUPABASE_URL:
            return ""
        
        # Extract connection details from Supabase URL
        # Format: https://[project-ref].supabase.co
        url = settings.SUPABASE_URL.replace("https://", "").replace("http://", "")
        project_ref = url.split(".")[0]
        
        # Construct PostgreSQL connection string
        # Note: This requires the database password from Supabase dashboard
        # For now, return empty and use Supabase client directly
        return ""
    
    def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_content: bytes,
        content_type: str = "application/pdf"
    ) -> Dict[str, Any]:
        """
        Upload file to Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            file_path: Path in bucket
            file_content: File content as bytes
            content_type: MIME type
        
        Returns:
            dict with 'success', 'path', 'error' keys
        """
        if not self.is_available():
            return {
                "success": False,
                "path": None,
                "error": "Supabase not available"
            }
        
        try:
            response = self.client.storage.from_(bucket).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(file_path)
            
            return {
                "success": True,
                "path": file_path,
                "public_url": public_url.data if hasattr(public_url, 'data') else str(public_url),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "path": None,
                "error": str(e)
            }
    
    def get_file_url(self, bucket: str, file_path: str) -> str:
        """Get public URL for a file."""
        if not self.is_available():
            return ""
        
        try:
            response = self.client.storage.from_(bucket).get_public_url(file_path)
            return response.data if hasattr(response, 'data') else str(response)
        except:
            return ""
    
    def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete file from Supabase Storage."""
        if not self.is_available():
            return False
        
        try:
            self.client.storage.from_(bucket).remove([file_path])
            return True
        except:
            return False

# Global instance
supabase_manager = SupabaseManager()

