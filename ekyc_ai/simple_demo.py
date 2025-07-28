#!/usr/bin/env python3
"""
Contoh penggunaan sederhana Document Validation System
"""

from document_validator import DocumentValidator
import os
import json

def main():
    print("🚀 Document Validation System - Simple Demo")
    print("=" * 60)
    
    # Check if documents exist
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ktp_file = os.path.join(current_dir, "ktp.png")
    akta_file = os.path.join(current_dir, "akta.pdf")
    
    if not os.path.exists(ktp_file):
        print(f"❌ KTP file not found: {ktp_file}")
        return
    
    if not os.path.exists(akta_file):
        print(f"❌ Akta file not found: {akta_file}")
        return
    
    print(f"✅ Found KTP file: {os.path.basename(ktp_file)}")
    print(f"✅ Found Akta file: {os.path.basename(akta_file)}")
    
    try:
        # Initialize validator
        print("\n🔧 Initializing validator...")
        validator = DocumentValidator()
        print("✅ Validator ready!")
        
        # Validate KTP
        print(f"\n📄 Validating KTP...")
        ktp_result = validator.validate_ktp(ktp_file)
        
        if ktp_result['success']:
            ktp_validation = ktp_result['validation_result']
            print(f"✅ KTP processed successfully")
            print(f"   Status: {'VALID' if ktp_validation.get('valid') else 'INVALID'}")
            print(f"   Confidence: {ktp_validation.get('confidence_score', 0)}%")
        else:
            print(f"❌ KTP validation failed: {ktp_result.get('error', 'Unknown error')}")
        
        # Validate Akta
        print(f"\n📄 Validating Akta...")
        akta_result = validator.validate_akta(akta_file)
        
        if akta_result['success']:
            akta_validation = akta_result['validation_result']
            print(f"✅ Akta processed successfully")
            print(f"   Status: {'VALID' if akta_validation.get('valid') else 'INVALID'}")
            print(f"   Confidence: {akta_validation.get('confidence_score', 0)}%")
        else:
            print(f"❌ Akta validation failed: {akta_result.get('error', 'Unknown error')}")
        
        # Save results
        if ktp_result['success'] and akta_result['success']:
            output_file = "simple_validation_results.json"
            results = {
                "ktp": ktp_result,
                "akta": akta_result
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {output_file}")
        
        print("\n" + "=" * 60)
        print("🎉 Demo completed!")
        print("\nNext steps:")
        print("1. Check simple_validation_results.json for detailed results")
        print("2. Try the API at http://localhost:8000/docs")
        print("3. Run: python example_usage.py for more examples")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure Elasticsearch is running: docker-compose up -d")
        print("2. Check .env file configuration")
        print("3. Verify OpenAI API key is valid")

if __name__ == "__main__":
    main()
