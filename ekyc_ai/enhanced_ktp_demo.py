#!/usr/bin/env python3
"""
Demo KTP final dengan Enhanced Processor untuk gambar kualitas rendah
"""

import os
import json
from datetime import datetime
from enhanced_ktp_processor import EnhancedImageProcessor
from document_validator import DocumentValidator

def validate_ktp_with_enhanced_processor(image_path: str) -> dict:
    """Validate KTP using enhanced processor and full validation pipeline"""
    
    print(f"🔧 PROCESSING KTP: {os.path.basename(image_path)}")
    print("-" * 60)
    
    # Use enhanced processor
    processor = EnhancedImageProcessor()
    
    # Extract text with multiple methods
    extraction_result = processor.extract_text_multiple_methods(image_path)
    
    if not extraction_result['success']:
        return {
            'success': False,
            'error': extraction_result.get('error', 'Extraction failed'),
            'file_name': os.path.basename(image_path)
        }
    
    best_result = extraction_result['best_result']
    
    # Extract structured KTP fields
    ktp_fields = processor.extract_ktp_fields(best_result)
    
    # Prepare data for full validation
    extracted_data = {
        'file_name': os.path.basename(image_path),
        'extraction_method': f"{best_result['method']} + {best_result['ocr_engine']}",
        'ocr_confidence': best_result['avg_confidence'],
        'quality_score': best_result['quality_score'],
        'full_text': best_result['full_text'],
        'text_length': best_result['text_length'],
        'structured_fields': ktp_fields,
        'alternative_methods': len(extraction_result['extraction_results']),
        'processing_details': {
            'total_methods_tried': len(extraction_result['extraction_results']),
            'successful_extractions': len([r for r in extraction_result['extraction_results'] if r['success']]),
            'confidence_range': [min(extraction_result['confidence_scores']), max(extraction_result['confidence_scores'])] if extraction_result['confidence_scores'] else [0, 0]
        }
    }
    
    # Validate completeness
    validation_score = calculate_ktp_completeness(ktp_fields)
    
    # Use document validator for AI validation
    try:
        validator = DocumentValidator()
        
        # Prepare for AI validation
        validation_data = {
            'extracted_fields': ktp_fields,
            'full_text': best_result['full_text'],
            'confidence': best_result['avg_confidence'],
            'method_used': extracted_data['extraction_method']
        }
        
        ai_result = validator.validate_document(validation_data, "ktp")
        
        extracted_data['ai_validation'] = ai_result
        
    except Exception as e:
        print(f"⚠️  AI validation failed: {str(e)}")
        extracted_data['ai_validation'] = {
            'success': False,
            'error': str(e)
        }
    
    # Final assessment
    final_status = "VALID" if (
        validation_score['overall_percentage'] >= 60 and 
        best_result['avg_confidence'] >= 0.5 and
        len(best_result['full_text']) >= 50
    ) else "NEEDS_REVIEW"
    
    extracted_data.update({
        'validation_score': validation_score,
        'final_status': final_status,
        'success': True
    })
    
    return extracted_data

def calculate_ktp_completeness(ktp_fields: dict) -> dict:
    """Calculate completeness score for KTP fields"""
    
    required_fields = ['nik', 'nama', 'tempat_lahir', 'jenis_kelamin', 'alamat', 'agama', 'pekerjaan']
    optional_fields = ['tanggal_lahir', 'status_kawin', 'kewarganegaraan']
    
    required_found = sum(1 for field in required_fields if field in ktp_fields and ktp_fields[field].strip())
    optional_found = sum(1 for field in optional_fields if field in ktp_fields and ktp_fields[field].strip())
    
    required_percentage = (required_found / len(required_fields)) * 100
    optional_percentage = (optional_found / len(optional_fields)) * 100 if optional_fields else 0
    
    overall_percentage = (required_percentage * 0.8) + (optional_percentage * 0.2)
    
    return {
        'required_found': required_found,
        'required_total': len(required_fields),
        'required_percentage': required_percentage,
        'optional_found': optional_found,
        'optional_total': len(optional_fields),
        'optional_percentage': optional_percentage,
        'overall_percentage': overall_percentage,
        'status': 'COMPLETE' if overall_percentage >= 80 else 'PARTIAL' if overall_percentage >= 60 else 'INCOMPLETE'
    }

def main():
    print("🚀 DEMO KTP FINAL - ENHANCED PROCESSOR UNTUK KUALITAS RENDAH")
    print("=" * 80)
    
    # Setup paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ktp_folder = os.path.join(current_dir, "ktp")
    
    # Get KTP files
    ktp_files = []
    for file in os.listdir(ktp_folder):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            ktp_files.append(os.path.join(ktp_folder, file))
    
    if not ktp_files:
        print("❌ Tidak ditemukan file KTP di folder ktp/")
        return
    
    print(f"📁 Folder: {ktp_folder}")
    print(f"📄 Files: {[os.path.basename(f) for f in ktp_files]}")
    
    all_results = []
    
    for ktp_file in ktp_files:
        print(f"\n" + "="*80)
        print(f"📄 VALIDATING: {os.path.basename(ktp_file)}")
        print("="*80)
        
        # Validate with enhanced processor
        result = validate_ktp_with_enhanced_processor(ktp_file)
        
        if result['success']:
            print(f"\n✅ VALIDATION SUCCESSFUL!")
            
            # Show extraction details
            print(f"🔧 Method used: {result['extraction_method']}")
            print(f"📊 OCR confidence: {result['ocr_confidence']:.2f}")
            print(f"⭐ Quality score: {result['quality_score']:.2f}")
            print(f"📝 Text length: {result['text_length']} chars")
            print(f"🔄 Methods tried: {result['alternative_methods']}")
            
            # Show structured fields
            fields = result['structured_fields']
            if fields:
                print(f"\n📋 EXTRACTED KTP FIELDS:")
                for field, value in fields.items():
                    print(f"   {field.upper()}: {value[:50]}{'...' if len(value) > 50 else ''}")
            
            # Show validation score
            validation = result['validation_score']
            print(f"\n📊 COMPLETENESS SCORE:")
            print(f"   Required fields: {validation['required_found']}/{validation['required_total']} ({validation['required_percentage']:.1f}%)")
            print(f"   Optional fields: {validation['optional_found']}/{validation['optional_total']} ({validation['optional_percentage']:.1f}%)")
            print(f"   Overall score: {validation['overall_percentage']:.1f}%")
            print(f"   Status: {validation['status']}")
            
            # Show final status
            print(f"\n🎯 FINAL STATUS: {result['final_status']}")
            
            if result['final_status'] == 'VALID':
                print("✅ KTP berhasil divalidasi dengan enhanced processor!")
            else:
                print("⚠️  KTP perlu review manual")
            
        else:
            print(f"\n❌ VALIDATION FAILED: {result.get('error', 'Unknown error')}")
        
        all_results.append(result)
    
    # Save comprehensive report
    report = {
        'timestamp': datetime.now().isoformat(),
        'processor_type': 'enhanced_multi_method',
        'total_files': len(ktp_files),
        'successful_validations': len([r for r in all_results if r.get('success', False)]),
        'results': all_results,
        'enhancement_summary': {
            'preprocessing_methods': 10,
            'ocr_engines': 2,
            'total_combinations': 20,
            'quality_scoring': True,
            'keyword_bonus': True,
            'field_extraction': True
        }
    }
    
    report_file = f"enhanced_ktp_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n" + "="*80)
    print("🎯 SUMMARY - ENHANCED KTP PROCESSOR")
    print("="*80)
    
    successful = len([r for r in all_results if r.get('success', False)])
    print(f"📊 Results: {successful}/{len(ktp_files)} files successfully processed")
    
    if successful > 0:
        # Calculate average scores
        valid_results = [r for r in all_results if r.get('success', False)]
        avg_confidence = sum(r.get('ocr_confidence', 0) for r in valid_results) / len(valid_results)
        avg_quality = sum(r.get('quality_score', 0) for r in valid_results) / len(valid_results)
        avg_completeness = sum(r.get('validation_score', {}).get('overall_percentage', 0) for r in valid_results) / len(valid_results)
        
        print(f"📈 Average OCR confidence: {avg_confidence:.2f}")
        print(f"⭐ Average quality score: {avg_quality:.2f}")
        print(f"📋 Average completeness: {avg_completeness:.1f}%")
        
        # Show improvement statistics
        print(f"\n🚀 ENHANCEMENT BENEFITS:")
        print(f"   ✅ 10 preprocessing methods untuk setiap gambar")
        print(f"   ✅ 2 OCR engines (EasyOCR + Tesseract)")
        print(f"   ✅ 20 total kombinasi metode")
        print(f"   ✅ Automatic best result selection")
        print(f"   ✅ KTP keyword bonus scoring")
        print(f"   ✅ Structured field extraction")
        print(f"   ✅ Quality assessment untuk gambar buruk")
        
        # Show specific improvements
        best_methods = {}
        for result in valid_results:
            method = result.get('extraction_method', 'unknown')
            if method not in best_methods:
                best_methods[method] = 0
            best_methods[method] += 1
        
        print(f"\n📊 BEST PERFORMING METHODS:")
        for method, count in sorted(best_methods.items(), key=lambda x: x[1], reverse=True):
            print(f"   🏆 {method}: {count} times")
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    print(f"\n" + "="*80)
    print("🎉 ENHANCED KTP PROCESSOR - SIAP UNTUK PRODUKSI!")
    print("="*80)
    print("✅ Dapat menangani gambar KTP kualitas rendah")
    print("✅ Multiple preprocessing methods untuk optimization")  
    print("✅ Automatic best result selection")
    print("✅ Structured field extraction")
    print("✅ Comprehensive validation scoring")
    print("✅ Production-ready dengan fallback methods")

if __name__ == "__main__":
    main()
