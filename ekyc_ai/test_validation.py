import asyncio
import os
from document_validator import DocumentValidator

async def test_validation():
    """Test script to validate documents in the workspace"""
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for test files
    ktp_file = None
    akta_file = None
    
    for file in os.listdir(current_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')) and 'ktp' in file.lower():
            ktp_file = os.path.join(current_dir, file)
        elif file.lower().endswith('.pdf') and 'akta' in file.lower():
            akta_file = os.path.join(current_dir, file)
    
    # Check existing files
    existing_files = []
    for file in ['ktp.png', 'akta.pdf']:
        if os.path.exists(os.path.join(current_dir, file)):
            existing_files.append(os.path.join(current_dir, file))
    
    print("=== Document Validation Test ===")
    print(f"Current directory: {current_dir}")
    print(f"Available files: {os.listdir(current_dir)}")
    
    if not existing_files:
        print("No KTP or Akta files found in current directory")
        print("Expected files: ktp.png, akta.pdf")
        return
    
    try:
        # Initialize validator
        print("\nInitializing validator...")
        validator = DocumentValidator()
        print("✓ Validator initialized successfully")
        
        # Test individual validations
        for file_path in existing_files:
            filename = os.path.basename(file_path)
            print(f"\n--- Testing {filename} ---")
            
            try:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    result = validator.validate_ktp(file_path)
                    print(f"✓ KTP validation completed")
                    print(f"  Valid: {result.get('validation_result', {}).get('valid', False)}")
                    print(f"  Confidence: {result.get('validation_result', {}).get('confidence_score', 0)}")
                elif filename.lower().endswith('.pdf'):
                    result = validator.validate_akta(file_path)
                    print(f"✓ Akta validation completed")
                    print(f"  Valid: {result.get('validation_result', {}).get('valid', False)}")
                    print(f"  Confidence: {result.get('validation_result', {}).get('confidence_score', 0)}")
                
            except Exception as e:
                print(f"✗ Error validating {filename}: {str(e)}")
        
        # Test comprehensive validation if both files exist
        ktp_path = os.path.join(current_dir, 'ktp.png')
        akta_path = os.path.join(current_dir, 'akta.pdf')
        
        if os.path.exists(ktp_path) and os.path.exists(akta_path):
            print(f"\n--- Testing Comprehensive Validation ---")
            try:
                result = validator.validate_documents(ktp_path, akta_path)
                print(f"✓ Comprehensive validation completed")
                report = result.get('comprehensive_report', {})
                print(f"  Overall Status: {report.get('overall_status', 'Unknown')}")
                print(f"  Overall Confidence: {report.get('overall_confidence', 0)}")
                print(f"  Risk Level: {report.get('risk_assessment', {}).get('level', 'Unknown')}")
                
            except Exception as e:
                print(f"✗ Error in comprehensive validation: {str(e)}")
    
    except Exception as e:
        print(f"✗ Failed to initialize validator: {str(e)}")
        print("\nPlease make sure:")
        print("1. .env file is configured with OPENAI_API_KEY and ELASTICSEARCH_PASSWORD")
        print("2. Elasticsearch is running on localhost:9200")
        print("3. All required packages are installed (pip install -r requirements.txt)")

def main():
    """Main test function"""
    print("Starting document validation test...")
    asyncio.run(test_validation())

if __name__ == "__main__":
    main()
