import os
from supabase import create_client, Client
from typing import Optional, Dict, Any

class SupabaseManager:
    def __init__(self):
        self.url: str = os.environ.get("SUPABASE_URL", "")
        self.key: str = os.environ.get("SUPABASE_KEY", "")
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                print("Supabase client initialized.")
            except Exception as e:
                print(f"Failed to initialize Supabase client: {e}")
        else:
            print("Supabase credentials not found. Cloud features will be disabled.")

    def is_enabled(self) -> bool:
        return self.client is not None

    def upload_file(self, file_path: str, bucket: str, destination_path: str) -> Optional[str]:
        """Uploads a file to Supabase Storage and returns the public URL."""
        if not self.client:
            return None
        
        try:
            with open(file_path, 'rb') as f:
                self.client.storage.from_(bucket).upload(
                    file=f,
                    path=destination_path,
                    file_options={"content-type": "audio/wav", "upsert": "true"}
                )
            
            return self.client.storage.from_(bucket).get_public_url(destination_path)
        except Exception as e:
            print(f"Supabase upload error: {e}")
            return None

    def save_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves project metadata to the 'projects' table."""
        if not self.client:
            return {"status": "error", "message": "Supabase not configured"}
            
        try:
            # Upsert project based on ID
            response = self.client.table("projects").upsert(project_data).execute()
            return {"status": "success", "data": response.data}
        except Exception as e:
            print(f"Supabase DB error: {e}")
            return {"status": "error", "message": str(e)}

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Retrieves a project by ID."""
        if not self.client:
            return {"status": "error", "message": "Supabase not configured"}
            
        try:
            response = self.client.table("projects").select("*").eq("id", project_id).execute()
            if response.data:
                return {"status": "success", "data": response.data[0]}
            else:
                return {"status": "error", "message": "Project not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
