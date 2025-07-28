#!/usr/bin/env python3
"""
Simple KTP Demo dengan debugging info
"""

import os
import json
from document_validator import DocumentValidator

def main():
    print("🔍 KTP Debug Demo - Melihat detail OCR")
    print("=" * 60)
    
    # Setup paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ktp_folder = os.path.join(current_dir, "ktp")
    
    # Get KTP files
    ktp_files = []
    for file in os.listdir(ktp_folder):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            ktp_files.append(os.path.join(ktp_folder, file))
    
    print(f"📁 Folder: {ktp_folder}")
    print(f"📄 Files found: {[os.path.basename(f) for f in ktp_files]}")
    
    try:
        # Initialize validator
        print(f"\n🔧 Initializing validator...")
        validator = DocumentValidator()
        print("✅ Validator ready!")
        
        for ktp_file in ktp_files:
            filename = os.path.basename(ktp_file)
            print(f"\n" + "="*50)
            print(f"📄 Processing: {filename}")
            print("="*50)
            
            # Process with debug info
            result = validator.validate_ktp(ktp_file)
            
            if result['success']:
                # Show OCR results
                if 'processing_steps' in result and 'ocr' in result['processing_steps']:
                    ocr_info = result['processing_steps']['ocr']
                    print(f"🔍 OCR Method: {ocr_info.get('method', 'Unknown')}")
                    print(f"📝 Raw OCR Text: '{ocr_info.get('extracted_text', '')}' (length: {len(ocr_info.get('extracted_text', ''))})")
                
                # Show extracted fields
                if 'field_extraction' in result['processing_steps']:
                    fields = result['processing_steps']['field_extraction']['extracted_fields']
                    print(f"\n📋 Extracted Fields:")
                    for field, value in fields.items():
                        print(f"   {field}: {value if value else 'None'}")
                
                # Show validation result
                validation = result['validation_result']
                print(f"\n✅ Validation Status: {'VALID' if validation.get('valid') else 'INVALID'}")
                print(f"🎯 Confidence: {validation.get('confidence_score', 0)}%")
                
                # Show raw OpenAI response if available
                if 'raw_response' in validation:
                    print(f"\n🤖 OpenAI Raw Response (first 500 chars):")
                    print(f"   {validation['raw_response'][:500]}...")
                
            else:
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎉 Debug completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
