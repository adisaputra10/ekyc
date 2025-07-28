import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Elasticsearch Configuration
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
    ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
    ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "document_validation")
    
    # Application Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    
    # Validation thresholds
    CONFIDENCE_THRESHOLD = 0.8
    SIMILARITY_THRESHOLD = 0.75
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        if not cls.ELASTICSEARCH_PASSWORD:
            raise ValueError("ELASTICSEARCH_PASSWORD is required")
        return True
