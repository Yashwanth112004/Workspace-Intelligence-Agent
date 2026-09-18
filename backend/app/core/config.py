import os
from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Workspace Intelligence Agent (WIA)"
    VERSION: str = "0.1.1"
    API_V1_STR: str = "/api/v1"
    
    # Storage
    DATA_DIR: str = os.getenv("WIA_DATA_DIR", os.path.expanduser("~/.wia/data"))
    REPOS_DIR: str = os.getenv("WIA_REPOS_DIR", os.path.join(os.getenv("WIA_DATA_DIR", os.path.expanduser("~/.wia/data")), "repos"))

    
    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", None)
    
    # NVIDIA NIM Primary LLM Provider
    NVIDIA_NIM_API_KEY: Optional[str] = os.getenv("NVIDIA_NIM_API_KEY", os.getenv("NVIDIA_API_KEY", None))
    NVIDIA_API_KEY: Optional[str] = os.getenv("NVIDIA_API_KEY", None)
    NVIDIA_NIM_BASE_URL: str = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_NIM_MODEL: str = os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.3-70b-instruct")

    NVIDIA_NIM_EMBEDDING_MODEL: Optional[str] = os.getenv("NVIDIA_NIM_EMBEDDING_MODEL", None)
    
    # Alternative LLM Providers (optional)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "nvidia") # nvidia, openai, anthropic, gemini
    
    # Vector Search & Local Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()

# Ensure data directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.REPOS_DIR, exist_ok=True)
