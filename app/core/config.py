import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # MongoDB settings
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "risk_assessment")
    
    # Omni server settings
    omni_base_url: str = os.getenv("OMNI_BASE_URL", "http://localhost:10240/v1")
    omni_api_key: str = os.getenv("OMNI_API_KEY", "mlx-omni-server")
    omni_model: str = os.getenv("OMNI_MODEL", "Qwen3-4B-8bit")
    
    # API settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    class Config:
        env_file = ".env"

settings = Settings()
