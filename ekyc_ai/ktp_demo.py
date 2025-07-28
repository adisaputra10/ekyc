#!/usr/bin/env python3
"""
Simple Demo untuk Validasi KTP di Folder ktp/
"""

import os
import json
from datetime import datetime
from document_validator import DocumentValidator

def get_ktp_files(ktp_folder):
    """Get all KTP image files from folder"""
    supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    ktp_files = []
    
    if not os.path.exists(ktp_folder):
        print(f"❌ Folder {ktp_folder} tidak ditemukan")
        return []
    
    for file in os.listdir(ktp_folder):
        file_path = os.path.join(ktp_folder, file)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(file.lower())
            if ext in supported_extensions:
                ktp_files.append(file_path)
    
    return ktp_files

def validate_single_ktp(validator, ktp_file):
    """Validate single KTP file"""
    filename = os.path.basename(ktp_file)
    print(f"\n📄 Processing: {filename}")
    print("-" * 50)
    
    try:
        # Validate KTP
        result = validator.validate_ktp(ktp_file)
        
        if result['success']:
            validation = result['validation_result']
            
            # Display basic info
            print(f"✅ Status: {'VALID' if validation.get('valid') else 'INVALID'}")
            print(f"🎯 Confidence: {validation.get('confidence_score', 0)}%")
            
            # Display extracted fields
            if 'processing_steps' in result and 'field_extraction' in result['processing_steps']:
                fields = result['processing_steps']['field_extraction']['extracted_fields']
                print(f"\n📋 Data yang berhasil diekstrak:")
                
                field_labels = {
                    'nik': 'NIK',
                    'nama': 'Nama Lengkap',
                    'tempat_lahir': 'Tempat Lahir',
                    'tanggal_lahir': 'Tanggal Lahir',
                    'jenis_kelamin': 'Jenis Kelamin',
                    'alamat': 'Alamat',
                    'agama': 'Agama',
                    'status_perkawinan': 'Status Perkawinan',
                    'pekerjaan': 'Pekerjaan',
                    'kewarganegaraan': 'Kewarganegaraan'
                }
                
                for field, value in fields.items():
                    if value and value.strip():
                        label = field_labels.get(field, field.replace('_', ' ').title())
                        print(f"   {label}: {value}")
            
            # Display validation details if available
            if 'validation_results' in validation:
                val_results = validation['validation_results']
                print(f"\n🔍 Detail Validasi:")
                
                validation_labels = {
                    'nik_valid': 'NIK Valid',
                    'nik_format_correct': 'Format NIK Benar',
                    'data_complete': 'Data Lengkap',
                    'data_consistent': 'Data Konsisten',
                    'gender_nik_match': 'Jenis Kelamin Sesuai NIK'
                }
                
                for check, passed in val_results.items():
                    if isinstance(passed, bool):
                        status = "✅" if passed else "❌"
                        label = validation_labels.get(check, check.replace('_', ' ').title())
                        print(f"   {status} {label}")
            
            # Display summary
            if validation.get('summary'):
                print(f"\n📝 Ringkasan: {validation['summary']}")
            
            # Display errors or warnings
            if validation.get('errors'):
                print(f"\n⚠️ Errors:")
                for error in validation['errors']:
                    print(f"   - {error}")
            
            if validation.get('warnings'):
                print(f"\n⚠️ Warnings:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")
            
        else:
            print(f"❌ Validasi gagal: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error processing {filename}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'file': ktp_file
        }

def main():
    print("🚀 KTP Validation Demo - Folder ktp/")
    print("=" * 60)
    
    # Setup paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ktp_folder = os.path.join(current_dir, "ktp")
    
    # Get all KTP files
    ktp_files = get_ktp_files(ktp_folder)
    
    if not ktp_files:
        print(f"❌ Tidak ada file KTP yang ditemukan di folder: {ktp_folder}")
        print("Pastikan folder 'ktp' berisi file gambar KTP (.png, .jpg, .jpeg, dll)")
        return
    
    print(f"📁 Folder KTP: {ktp_folder}")
    print(f"📄 File KTP ditemukan: {len(ktp_files)}")
    for i, file in enumerate(ktp_files, 1):
        print(f"   {i}. {os.path.basename(file)}")
    
    try:
        # Initialize validator
        print(f"\n🔧 Initializing validator...")
        validator = DocumentValidator()
        print("✅ Validator ready!")
        
        # Validate all KTP files
        all_results = []
        successful_validations = 0
        
        for ktp_file in ktp_files:
            result = validate_single_ktp(validator, ktp_file)
            all_results.append(result)
            
            if result.get('success') and result.get('validation_result', {}).get('valid'):
                successful_validations += 1
        
        # Summary
        print(f"\n" + "=" * 60)
        print("📊 RINGKASAN VALIDASI")
        print("=" * 60)
        print(f"Total file diproses: {len(ktp_files)}")
        print(f"Validasi berhasil: {len([r for r in all_results if r.get('success')])}")
        print(f"KTP Valid: {successful_validations}")
        print(f"KTP Invalid: {len(ktp_files) - successful_validations}")
        
        # Save detailed results
        output_file = f"ktp_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "folder": ktp_folder,
            "total_files": len(ktp_files),
            "successful_validations": successful_validations,
            "results": all_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Individual file status
        print(f"\n📋 Status per file:")
        for i, result in enumerate(all_results):
            filename = os.path.basename(ktp_files[i])
            if result.get('success'):
                validation = result.get('validation_result', {})
                status = "VALID" if validation.get('valid') else "INVALID"
                confidence = validation.get('confidence_score', 0)
                print(f"   {filename}: {status} ({confidence}%)")
            else:
                print(f"   {filename}: ERROR - {result.get('error', 'Unknown')}")
        
        print(f"\n🎉 Validasi selesai!")
        print(f"\nNext steps:")
        print(f"1. Check {output_file} untuk hasil detail")
        print(f"2. Review file KTP yang invalid untuk perbaikan")
        print(f"3. Gunakan API di http://localhost:8000/docs untuk validasi real-time")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print(f"\nTroubleshooting:")
        print(f"1. Pastikan Elasticsearch running: docker-compose up -d")
        print(f"2. Check .env file configuration")
        print(f"3. Verify OpenAI API key")

if __name__ == "__main__":
    main()
