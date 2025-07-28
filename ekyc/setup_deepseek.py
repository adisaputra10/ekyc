"""
Setup script untuk konfigurasi lengkap DeepSeek environment
Membantu user mengkonfigurasi semua yang diperlukan untuk menggunakan DeepSeek
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'elasticsearch',
        'langchain',
        'langchain-community',
        'langchain-elasticsearch',
        'sentence-transformers',
        'faiss-cpu',
        'aiofiles',
        'python-multipart',
        'python-dotenv',
        'requests',
        'httpx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    print("✓ All dependencies installed")
    return True

def setup_env_file():
    """Setup .env file with DeepSeek configuration"""
    print("\nSetting up .env file...")
    
    env_path = Path(".env")
    
    if env_path.exists():
        print("✓ .env file already exists")
        
        # Read current content
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if DeepSeek config exists
        if "DEEPSEEK_API_KEY" in content:
            print("✓ DeepSeek configuration found in .env")
        else:
            print("⚠️  DeepSeek configuration not found in .env")
            print("Please add the following to your .env file:")
            print("\nLLM_PROVIDER=deepseek")
            print("DEEPSEEK_API_KEY=your-actual-deepseek-api-key")
            print("DEEPSEEK_MODEL=deepseek-chat")
    else:
        print("Creating .env file...")
        env_content = """# LLM Configuration
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key-here
DEEPSEEK_MODEL=deepseek-chat

# OpenAI Configuration (fallback)
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
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✓ .env file created")

def check_docker():
    """Check if Docker is available"""
    print("\nChecking Docker...")
    
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Docker is available")
            print(f"  Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker command failed")
            return False
    except FileNotFoundError:
        print("❌ Docker not found")
        print("Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
        return False

def check_elasticsearch():
    """Check if Elasticsearch is running"""
    print("\nChecking Elasticsearch...")
    
    try:
        import requests
        response = requests.get('http://localhost:9200', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Elasticsearch is running")
            print(f"  Version: {data.get('version', {}).get('number', 'unknown')}")
            return True
        else:
            print("❌ Elasticsearch not responding properly")
            return False
    except Exception:
        print("❌ Elasticsearch not running")
        print("Start Elasticsearch with: .\\scripts\\run_elasticsearch.ps1")
        return False

def validate_deepseek_config():
    """Validate DeepSeek configuration"""
    print("\nValidating DeepSeek configuration...")
    
    try:
        from config import settings, validate_environment
        
        print(f"LLM Provider: {settings.llm_provider}")
        print(f"DeepSeek Model: {settings.deepseek_model}")
        
        if settings.deepseek_api_key and settings.deepseek_api_key != "your-deepseek-api-key-here":
            print("✓ DeepSeek API key is set")
            
            # Test basic validation
            validate_environment()
            print("✓ Environment validation passed")
            return True
        else:
            print("❌ DeepSeek API key not set")
            print("Please set DEEPSEEK_API_KEY in your .env file")
            return False
            
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        return False

def show_usage_instructions():
    """Show usage instructions"""
    print("\n" + "=" * 60)
    print("DEEPSEEK SETUP COMPLETE!")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS:")
    print("\n1. Get DeepSeek API Key:")
    print("   - Visit: https://platform.deepseek.com/")
    print("   - Create account and get API key")
    print("   - Update DEEPSEEK_API_KEY in .env file")
    
    print("\n2. Start Elasticsearch:")
    print("   PowerShell: .\\scripts\\run_elasticsearch.ps1")
    print("   Or: docker-compose -f docker-compose.yml up -d")
    
    print("\n3. Test the setup:")
    print("   python test_deepseek_integration.py")
    
    print("\n4. Run the application:")
    print("   python main.py")
    print("   Or: uvicorn main:app --reload")
    
    print("\n5. Access the application:")
    print("   - FastAPI docs: http://localhost:8000/docs")
    print("   - Upload form: http://localhost:8000/")
    print("   - Streamlit UI: streamlit run streamlit_app.py")
    
    print("\n📚 AVAILABLE ENDPOINTS:")
    print("   - POST /upload-document - Upload and analyze documents")
    print("   - POST /rag/query - Ask questions about uploaded documents")
    print("   - POST /ai/chat - Chat with AI about documents")
    print("   - GET /health - Check system health")

def main():
    """Main setup function"""
    print("DeepSeek Environment Setup")
    print("=" * 50)
    
    # Check all components
    deps_ok = check_dependencies()
    setup_env_file()
    docker_ok = check_docker()
    es_ok = check_elasticsearch()
    config_ok = validate_deepseek_config()
    
    print("\n" + "=" * 50)
    print("SETUP SUMMARY:")
    print(f"Dependencies: {'✓ OK' if deps_ok else '❌ MISSING'}")
    print(f"Docker: {'✓ OK' if docker_ok else '❌ NOT AVAILABLE'}")
    print(f"Elasticsearch: {'✓ RUNNING' if es_ok else '❌ NOT RUNNING'}")
    print(f"DeepSeek Config: {'✓ VALID' if config_ok else '❌ INVALID'}")
    
    if all([deps_ok, docker_ok, config_ok]):
        print("\n🎉 Setup completed successfully!")
        if not es_ok:
            print("⚠️  Start Elasticsearch to complete the setup")
    else:
        print("\n⚠️  Some components need attention. Please fix the issues above.")
    
    show_usage_instructions()

if __name__ == "__main__":
    main()
