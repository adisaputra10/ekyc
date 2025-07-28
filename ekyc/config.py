"""
Configuration settings untuk eKYC application
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # LLM Provider Configuration
    llm_provider: str = os.getenv("LLM_PROVIDER", "deepseek")  # deepseek atau openai
    
    # DeepSeek Configuration
    deepseek_api_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # OpenAI Configuration (fallback)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Elasticsearch Configuration
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    elasticsearch_index: str = os.getenv("ELASTICSEARCH_INDEX", "document_vectors")
    elasticsearch_username: Optional[str] = os.getenv("ELASTICSEARCH_USERNAME")
    elasticsearch_password: Optional[str] = os.getenv("ELASTICSEARCH_PASSWORD")
    
    # Application Configuration
    app_name: str = "eKYC Document Analyzer with DeepSeek"
    app_version: str = "2.1.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # File Upload Configuration
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    allowed_extensions: list = [".pdf", ".jpg", ".jpeg", ".png", ".docx"]
    
    # Document Processing Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    
    # LangChain Configuration
    langchain_verbose: bool = os.getenv("LANGCHAIN_VERBOSE", "false").lower() == "true"
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "5"))
    
    # LLM Configuration
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1500"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Environment validation
def validate_environment():
    """Validate required environment variables"""
    errors = []
    
    if settings.llm_provider == "deepseek":
        if not settings.deepseek_api_key:
            errors.append("DEEPSEEK_API_KEY is required when using DeepSeek")
    elif settings.llm_provider == "openai":
        if not settings.openai_api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI")
    else:
        errors.append(f"Unsupported LLM_PROVIDER: {settings.llm_provider}. Use 'deepseek' or 'openai'")
    
    if errors:
        raise ValueError(f"Environment validation failed: {', '.join(errors)}")
    
    return True

# Development environment template
def create_env_template():
    """Create .env template file"""
    template = """
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=document_vectors
# ELASTICSEARCH_USERNAME=elastic
# ELASTICSEARCH_PASSWORD=your-password

# Application Configuration
DEBUG=true
MAX_FILE_SIZE=10485760
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_THRESHOLD=0.7

# LangChain Configuration
LANGCHAIN_VERBOSE=false
RETRIEVAL_K=5
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(template.strip())
        print("Created .env template file. Please update with your actual values.")
    else:
        print(".env file already exists.")

if __name__ == "__main__":
    create_env_template()
