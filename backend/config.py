"""
Configuration management for Survey Sensei backend
Loads environment variables and provides typed configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # OpenAI
    openai_api_key: str

    # Application
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    # OpenAI Model Configuration
    openai_model: str = "gpt-4o-mini"  # Cost-effective for development
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000

    # Embedding Configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Survey Configuration
    initial_questions_count: int = 3
    max_survey_questions: int = 10
    min_survey_questions: int = 5
    review_options_count: int = 3  # Number of natural language review options to generate

    # Vector Search Configuration
    similarity_threshold: float = 0.7
    max_similar_products: int = 5
    max_user_history: int = 10

    class Config:
        env_file = ".env.local"
        case_sensitive = False


# Global settings instance
settings = Settings()
