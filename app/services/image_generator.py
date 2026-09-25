import base64
import io
from typing import Optional, Tuple
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from PIL import Image
from app.config import settings


class VertexAIImageGenerator:
    """Service for generating images using Vertex AI Imagen 2"""
    
    def __init__(self):
        self.project_id = settings.google_cloud_project
        self.location = settings.vertex_ai_location
        self.model_name = "imagegeneration@006"  # Imagen 2 model
        
        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)
        
    def generate_image(
        self, 
        prompt: str, 
        style: Optional[str] = None, 
        aspect_ratio: str = "1:1"
    ) -> Tuple[bytes, str]:
        """
        Generate an image using Vertex AI Imagen 2
        
        Args:
            prompt: Text prompt for image generation
            style: Style of the image (optional)
            aspect_ratio: Aspect ratio of the image
            
        Returns:
            Tuple of (image_bytes, image_format)
        """
        try:
            # Prepare the prompt with style if provided
            full_prompt = prompt
            if style:
                full_prompt = f"{prompt}, {style} style"
            
            # Map aspect ratio to Vertex AI format
            aspect_ratio_map = {
                "1:1": "1:1",
                "16:9": "16:9",
                "9:16": "9:16",
                "4:3": "4:3",
                "3:4": "3:4"
            }
            
            vertex_aspect_ratio = aspect_ratio_map.get(aspect_ratio, "1:1")
            
            # Create prediction request
            endpoint = aiplatform.Endpoint(
                endpoint_name=f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_name}"
            )
            
            # Prepare the request parameters
            instances = [
                {
                    "prompt": full_prompt,
                    "sampleCount": 1,
                    "aspectRatio": vertex_aspect_ratio,
                    "safetyFilterLevel": "block_some",
                    "personGeneration": "allow_adult"
                }
            ]
            
            # Make prediction
            response = endpoint.predict(instances=instances)
            
            # Extract image data from response
            if response.predictions:
                prediction = response.predictions[0]
                if "bytesBase64Encoded" in prediction:
                    image_bytes = base64.b64decode(prediction["bytesBase64Encoded"])
                    return image_bytes, "png"
                else:
                    raise ValueError("No image data in response")
            else:
                raise ValueError("No predictions in response")
                
        except Exception as e:
            raise Exception(f"Failed to generate image: {str(e)}")
    
    def _validate_image(self, image_bytes: bytes) -> bool:
        """
        Validate that the generated image is valid
        
        Args:
            image_bytes: Image data in bytes
            
        Returns:
            True if valid, False otherwise
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Check if image has valid dimensions
            width, height = image.size
            return width > 0 and height > 0
        except Exception:
            return False

