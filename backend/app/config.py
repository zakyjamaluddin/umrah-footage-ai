import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Umrah Footage AI Indexer"
    API_V1_STR: str = "/api"
    
    # API Keys & Configurations
    GEMINI_API_KEY: Optional[str] = None
    COMPOSIO_API_KEY: Optional[str] = None
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    
    # Polling & Worker Settings
    POLLING_INTERVAL_MINUTES: int = 5
    AUTO_POLLING_ENABLED: bool = True
    
    # Storage Paths
    DATABASE_PATH: str = "data/metadata.db"
    STORAGE_DIR: str = "data/storage"
    CHROMA_PERSIST_DIR: str = "data/chroma"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Ensure directories exist
os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
