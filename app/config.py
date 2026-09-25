import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google Cloud Configuration
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    google_cloud_bucket: str = os.getenv("GOOGLE_CLOUD_BUCKET", "")
    google_application_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Redis Configuration
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    
    # Cache Configuration
    cache_expiration_hours: int = int(os.getenv("CACHE_EXPIRATION_HOURS", "24"))
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Vertex AI Configuration
    vertex_ai_location: str = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    
    class Config:
        env_file = ".env"


settings = Settings()

