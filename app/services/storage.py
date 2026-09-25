import uuid
from datetime import datetime
from typing import Optional
from google.cloud import storage
from app.config import settings


class CloudStorageService:
    """Service for uploading images to Google Cloud Storage"""
    
    def __init__(self):
        self.project_id = settings.google_cloud_project
        self.bucket_name = settings.google_cloud_bucket
        
        # Initialize Cloud Storage client
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
    
    def upload_image(
        self, 
        image_data: bytes, 
        image_format: str = "png",
        folder: str = "generated-images"
    ) -> str:
        """
        Upload image to Cloud Storage and return public URL
        
        Args:
            image_data: Image data in bytes
            image_format: Image format (png, jpg, etc.)
            folder: Folder path in the bucket
            
        Returns:
            Public URL of the uploaded image
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{folder}/{timestamp}_{unique_id}.{image_format}"
            
            # Create blob and upload
            blob = self.bucket.blob(filename)
            blob.upload_from_string(
                image_data,
                content_type=f"image/{image_format}"
            )
            
            # Make the blob publicly accessible
            blob.make_public()
            
            # Return public URL
            return blob.public_url
            
        except Exception as e:
            raise Exception(f"Failed to upload image to storage: {str(e)}")
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete image from Cloud Storage
        
        Args:
            image_url: Public URL of the image to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract blob name from URL
            blob_name = self._extract_blob_name_from_url(image_url)
            if not blob_name:
                return False
            
            # Delete the blob
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
            
        except Exception:
            return False
    
    def _extract_blob_name_from_url(self, url: str) -> Optional[str]:
        """
        Extract blob name from public URL
        
        Args:
            url: Public URL of the image
            
        Returns:
            Blob name or None if extraction fails
        """
        try:
            # URL format: https://storage.googleapis.com/bucket-name/blob-name
            if f"storage.googleapis.com/{self.bucket_name}/" in url:
                return url.split(f"storage.googleapis.com/{self.bucket_name}/")[1]
            return None
        except Exception:
            return None
    
    def check_bucket_exists(self) -> bool:
        """
        Check if the configured bucket exists
        
        Returns:
            True if bucket exists, False otherwise
        """
        try:
            self.bucket.reload()
            return True
        except Exception:
            return False

