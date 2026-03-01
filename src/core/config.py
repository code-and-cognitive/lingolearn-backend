"""Configuration settings for LingoLearn API"""
import os
from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_TOKEN: str = "your-secret-api-token"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 1234
    DEBUG: bool = False
    
    # LLM Configuration (LMStudio)
    LLM_MODEL_ID: str = ""
    VISION_MODEL_ID: str = ""
    TTS_MODEL_ID: str = ""
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./lingolearn.db"
    
    # CORS Configuration - stored as string, converted to list
    ALLOWED_ORIGINS: Union[str, List[str]] = "*"
    
    # LangGraph Configuration
    LANGGRAPH_THREAD_TIMEOUT: int = 300

    # Google / OIDC Configuration
    # Accept both OIDC_GOOGLE_CLIENT_ID and legacy env names
    OIDC_GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # JWT settings for application tokens
    JWT_SECRET_KEY: str = "super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Model Parameters (Local LLM)
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string to list"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if v == "*":
                return "*"  # Keep as string, will be converted to list when needed
            return v
        return "*"
    
    def get_allowed_origins(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            if self.ALLOWED_ORIGINS == "*":
                return ["*"]
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS if isinstance(self.ALLOWED_ORIGINS, list) else ["*"]
    
    def get_llm_api_url(self) -> str:
        """Get the LLM API base URL"""
        return f"http://{self.API_HOST}:{self.API_PORT}/v1"
    
    def use_local_llm(self) -> bool:
        """Check if LLM is configured"""
        return bool(self.LLM_MODEL_ID)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
