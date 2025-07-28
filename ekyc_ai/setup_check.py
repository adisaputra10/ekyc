import os
import sys

def check_requirements():
    """Check if all required packages are installed"""
    print("=== Checking Requirements ===")
    
    required_packages = [
        'openai',
        'python-dotenv',
        'PyPDF2',
        'Pillow',
        'langchain',
        'langchain-openai',
        'langchain-community',
        'langchain-elasticsearch',
        'pypdf',
        'pdf2image',
        'pytesseract',
        'numpy',
        'cv2',
        'elasticsearch',
        'fastapi',
        'uvicorn',
        'pydantic',
        'easyocr'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                from PIL import Image
            else:
                __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All required packages are installed!")
        return True

def check_environment():
    """Check environment configuration"""
    print("\n=== Checking Environment Configuration ===")
    
    if not os.path.exists('.env'):
        print("✗ .env file not found")
        print("Copy .env.example to .env and configure it")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_env_vars = [
        'OPENAI_API_KEY',
        'ELASTICSEARCH_PASSWORD'
    ]
    
    missing_vars = []
    
    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            print(f"✗ {var} - NOT SET")
            missing_vars.append(var)
        else:
            print(f"✓ {var} - SET")
    
    if missing_vars:
        print(f"\nMissing environment variables: {', '.join(missing_vars)}")
        print("Please configure them in .env file")
        return False
    else:
        print("\n✓ All required environment variables are set!")
        return True

def check_elasticsearch():
    """Check Elasticsearch connection"""
    print("\n=== Checking Elasticsearch Connection ===")
    
    try:
        from elasticsearch import Elasticsearch
        from dotenv import load_dotenv
        load_dotenv()
        
        es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        es_user = os.getenv('ELASTICSEARCH_USERNAME', 'elastic')
        es_pass = os.getenv('ELASTICSEARCH_PASSWORD')
        
        if not es_pass:
            print("✗ Elasticsearch password not configured")
            return False
        
        es = Elasticsearch(
            [es_url],
            basic_auth=(es_user, es_pass),
            verify_certs=False,
            request_timeout=5
        )
        
        info = es.info()
        print(f"✓ Connected to Elasticsearch {info['version']['number']}")
        
        # Check cluster health
        health = es.cluster.health()
        print(f"✓ Cluster status: {health['status']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Elasticsearch connection failed: {str(e)}")
        print("Make sure Elasticsearch is running on localhost:9200")
        return False

def check_openai():
    """Check OpenAI API connection"""
    print("\n=== Checking OpenAI API Connection ===")
    
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("✗ OpenAI API key not configured")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Test connection"}],
            max_tokens=5
        )
        
        print("✓ OpenAI API connection successful")
        print(f"✓ Model: gpt-4o-mini available")
        
        return True
        
    except Exception as e:
        print(f"✗ OpenAI API connection failed: {str(e)}")
        print("Check your API key and internet connection")
        return False

def check_test_files():
    """Check if test files exist"""
    print("\n=== Checking Test Files ===")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    test_files = {
        'ktp.png': 'KTP image file',
        'akta.pdf': 'Akta PDF file'
    }
    
    found_files = 0
    
    for filename, description in test_files.items():
        filepath = os.path.join(current_dir, filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ {filename} - {description} ({file_size} bytes)")
            found_files += 1
        else:
            print(f"✗ {filename} - {description} NOT FOUND")
    
    if found_files == 0:
        print("\nNo test files found. Add ktp.png and akta.pdf to test validation.")
        return False
    else:
        print(f"\n✓ Found {found_files}/{len(test_files)} test files")
        return True

def main():
    """Main setup check function"""
    print("Document Validation System - Setup Check")
    print("=" * 50)
    
    checks = [
        ("Package Requirements", check_requirements),
        ("Environment Configuration", check_environment),
        ("Elasticsearch Connection", check_elasticsearch),
        ("OpenAI API Connection", check_openai),
        ("Test Files", check_test_files)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"✗ {check_name} check failed: {str(e)}")
            results[check_name] = False
    
    print("\n" + "=" * 50)
    print("SETUP CHECK SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: python test_validation.py")
        print("2. Or run API: python run_api.py")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Install packages: pip install -r requirements.txt")
        print("2. Configure .env file with your API keys")
        print("3. Start Elasticsearch server")
        print("4. Check your internet connection")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
