import json
import os
import shutil
from datetime import datetime
from pathlib import Path

PROJECTS_DIR = "projects"

class ProjectManager:
    def __init__(self):
        if not os.path.exists(PROJECTS_DIR):
            os.makedirs(PROJECTS_DIR)

    def save_project(self, project_data):
        """
        Saves project state to a JSON file or Supabase.
        """
        try:
            # Check for Cloud Flag
            if os.environ.get("USE_CLOUD_PROCESSING") == "true":
                from cloud.supabase_client import SupabaseManager
                sb = SupabaseManager()
                if sb.is_enabled():
                    # Ensure ID exists
                    project_name = project_data.get("name", "Untitled Project")
                    safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                    project_id = safe_name.replace(" ", "_").lower()
                    project_data["id"] = project_id
                    project_data["updated_at"] = datetime.now().isoformat()
                    
                    return sb.save_project(project_data)

            # Local Fallback
            project_name = project_data.get("name", "Untitled Project")
            # Sanitize filename
            safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            project_id = safe_name.replace(" ", "_").lower()
            
            # Create project folder
            project_path = os.path.join(PROJECTS_DIR, project_id)
            if not os.path.exists(project_path):
                os.makedirs(project_path)
            
            # Save metadata
            project_data["id"] = project_id
            project_data["updated_at"] = datetime.now().isoformat()
            
            metadata_path = os.path.join(project_path, "project.json")
            with open(metadata_path, "w") as f:
                json.dump(project_data, f, indent=4)
                
            return {"status": "success", "project_id": project_id, "message": "Project saved successfully"}
        except Exception as e:
            print(f"Error saving project: {e}")
            return {"status": "error", "message": str(e)}

    def list_projects(self):
        """Lists all saved projects."""
        try:
            # Check for Cloud Flag
            if os.environ.get("USE_CLOUD_PROCESSING") == "true":
                from cloud.supabase_client import SupabaseManager
                sb = SupabaseManager()
                if sb.is_enabled():
                    # This is a bit hacky, SupabaseManager needs a list_projects method
                    # For now, we'll just return local projects or implement list in SupabaseManager
                    # Let's assume we add list_projects to SupabaseManager
                    return sb.list_projects() 

            projects = []
            if os.path.exists(PROJECTS_DIR):
                for dirname in os.listdir(PROJECTS_DIR):
                    project_path = os.path.join(PROJECTS_DIR, dirname)
                    metadata_path = os.path.join(project_path, "project.json")
                    
                    if os.path.exists(metadata_path):
                        with open(metadata_path, "r") as f:
                            data = json.load(f)
                            projects.append({
                                "id": data.get("id"),
                                "name": data.get("name"),
                                "updated_at": data.get("updated_at")
                            })
            return projects
        except Exception as e:
            print(f"Error listing projects: {e}")
            return []

    def load_project(self, project_id):
        """Loads a specific project."""
        try:
            # Check for Cloud Flag
            if os.environ.get("USE_CLOUD_PROCESSING") == "true":
                from cloud.supabase_client import SupabaseManager
                sb = SupabaseManager()
                if sb.is_enabled():
                    return sb.get_project(project_id)

            project_path = os.path.join(PROJECTS_DIR, project_id)
            metadata_path = os.path.join(project_path, "project.json")
            
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    data = json.load(f)
                    return {"status": "success", "data": data}
            else:
                return {"status": "error", "message": "Project not found"}
        except Exception as e:
            print(f"Error loading project: {e}")
            return {"status": "error", "message": str(e)}
