
from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import UploadFile, HTTPException
import os
import re
from typing import List, Dict
import uuid

class BlobDB:
    def __init__(self):
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not conn_str:
            raise ValueError("Azure Storage connection string not found")
        self.service_client = BlobServiceClient.from_connection_string(conn_str)
        self.container_name = "roundtable"
        self.max_file_size = 5 * 1024 * 1024  # 5MB in bytes
        self.allowed_extensions = {'.txt', '.md', '.pdf'}

    async def _validate_file(self, file: UploadFile, filename: str) -> None:
        """Validate file size, name and type."""
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset position
        
        if size > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {self.max_file_size/1024/1024}MB"
            )

        # # Validate filename - only alphanumeric characters, hyphens, and underscores
        # if not re.match(r'^[\w\-\. ]+$', filename):
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Filename contains invalid characters. Only alphanumeric characters, hyphens, and underscores are allowed."
        #     )

        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )

    async def upload_file(self, file: UploadFile, user_id: str, participant_id:str) -> Dict:
        """Upload a file to Azure Blob Storage."""
        try:
            # Generate a unique ID for the file
            file_id = str(uuid.uuid4())
            
            # Get original filename and extension
            original_filename = file.filename
            ext = os.path.splitext(original_filename)[1].lower()
            
            # Create a clean filename
            clean_filename = f"{file_id}{ext}"
            
            # Validate the file
            await self._validate_file(file, original_filename)
            
            # Ensure container exists
            container_client = self.service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()

            # Create blob path
            blob_path = f"{user_id}/{participant_id}/knowledge/{clean_filename}"
            blob_client = container_client.get_blob_client(blob_path)

            # Set content settings based on file type
            content_settings = ContentSettings(
                content_type='application/pdf' if ext == '.pdf' else 'text/plain'
            )

            # Upload the file
            await blob_client.upload_blob(file.file, content_settings=content_settings)

            return {
                "file_id": file_id,
                "participant_id": participant_id,
                "user_id": user_id,
                "name": original_filename,
                "clean_name": clean_filename,
                "user_id": user_id,
                "path": blob_path,
                "size": file.file.tell(),
                "type": ext[1:]  # Remove the dot from extension
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    async def delete_file(self, user_id: str, participant_id:str, file_path: str) -> None:
        """Delete a file from Azure Blob Storage."""
        try:
            container_client = self.service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(f"{user_id}/{participant_id}/knowledge/{file_path}")
            
            # Check if blob exists before deleting
            if not await blob_client.exists():
                raise HTTPException(status_code=404, detail="File not found")
                
            await blob_client.delete_blob()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    async def list_files(self, user_id: str, participant_id:str) -> List[Dict]:
        """List all files for a user."""
        try:
            container_client = self.service_client.get_container_client(self.container_name)
            files = []
            
            # List all blobs in the user's directory
            async for blob in container_client.list_blobs(name_starts_with=f"{user_id}/{participant_id}/knowledge/"):
                blob_name = blob.name.split('/')[-1]  # Get filename from path
                file_id = os.path.splitext(blob_name)[0]  # Remove extension to get ID
                
                files.append({
                    "id": file_id,
                    "name": blob_name,
                    "path": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "type": os.path.splitext(blob_name)[1][1:]  # Get extension without dot
                })
                
            return files
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

# Create a singleton instance
blob_db = BlobDB()