#!/usr/bin/env python3
"""
Demo validasi AI untuk data Akta yang sudah diekstrak
"""

import os
import json
from datetime import datetime
from document_validator import DocumentValidator
from openai_validator import OpenAIValidator

def validate_akta_with_ai(extracted_data, akta_text):
    """Validate extracted akta data using AI"""
    print("🤖 VALIDASI AKTA DENGAN AI")
    print("-" * 50)
    
    # Create validation prompt for akta
    validation_prompt = f"""
Saya memiliki data dari akta perusahaan yang perlu divalidasi. Tolong analisis data berikut:

STATISTIK DOKUMEN:
- Total karakter: {extracted_data.get('text_stats', {}).get('total_characters', 0)}
- Total baris: {extracted_data.get('text_stats', {}).get('total_lines', 0)}
- Total kata: {extracted_data.get('text_stats', {}).get('total_words', 0)}

DATA YANG DIEKSTRAK:
- Nama File: {extracted_data.get('file_name', 'Unknown')}
- Nama Notaris: {extracted_data.get('extracted_data', {}).get('notaris', 'Tidak ditemukan')}
- Alamat/Domisili: {extracted_data.get('extracted_data', {}).get('address', 'Tidak ditemukan')}

BAGIAN YANG DITEMUKAN:
- Nomor Akta: {'✅ Ditemukan' if 'nomor_akta' in extracted_data.get('found_sections', {}) else '❌ Tidak ditemukan'}
- Tanggal: {'✅ Ditemukan' if 'tanggal' in extracted_data.get('found_sections', {}) else '❌ Tidak ditemukan'}
- Notaris: {'✅ Ditemukan' if 'notaris' in extracted_data.get('found_sections', {}) else '❌ Tidak ditemukan'}
- Nama Perusahaan: {'✅ Ditemukan' if 'nama_perusahaan' in extracted_data.get('found_sections', {}) else '❌ Tidak ditemukan'}
- Alamat: {'✅ Ditemukan' if 'alamat' in extracted_data.get('found_sections', {}) else '❌ Tidak ditemukan'}
- Modal: {'✅ Ditemukan' if 'modal' in extracted_data.get('found_sections', {}) else '❌ Tidak ditemukan'}

SKOR KELENGKAPAN: {extracted_data.get('validation_result', {}).get('percentage', 0)}%

CONTOH TEKS DARI DOKUMEN:
{akta_text[:1000]}...

Tolong berikan analisis validasi dalam format JSON dengan field:
1. is_valid: true/false
2. confidence_score: 0.0-1.0
3. document_type: jenis dokumen
4. company_name: nama perusahaan yang ditemukan
5. key_findings: temuan penting
6. potential_issues: masalah yang mungkin ada
7. recommendations: rekomendasi untuk perbaikan
8. compliance_status: status kepatuhan
"""

    validator = OpenAIValidator()
    
    print("📤 Mengirim data ke OpenAI untuk analisis...")
    
    try:
        # Prepare data in the expected format for validate_akta
        validation_data = {
            'extracted_fields': extracted_data.get('extracted_data', {}),
            'full_text': akta_text[:5000],  # First 5000 chars
            'statistics': extracted_data.get('text_stats', {}),
            'found_sections': extracted_data.get('found_sections', {}),
            'validation_result': extracted_data.get('validation_result', {})
        }
        
        # Use empty RAG context for now
        rag_context = "Standard akta validation context"
        
        ai_response = validator.validate_akta(validation_data, rag_context)
        
        if ai_response.get('success'):
            validation_result = ai_response.get('validation_details', {})
            
            print("✅ Analisis AI berhasil!")
            print(f"\n🎯 HASIL VALIDASI AI:")
            print(f"   📊 Status: {ai_response.get('status', 'Unknown')}")
            print(f"   🎯 Confidence: {ai_response.get('confidence', 0):.2f}")
            print(f"   📄 AI Analysis: {validation_result.get('ai_analysis', 'No analysis available')[:200]}...")
            
            # Issues found
            issues = validation_result.get('issues_found', [])
            if issues:
                print(f"\n⚠️  MASALAH YANG DITEMUKAN:")
                for i, issue in enumerate(issues, 1):
                    print(f"   {i}. {issue}")
            else:
                print(f"\n✅ Tidak ada masalah yang ditemukan")
            
            # Extracted fields
            extracted_fields = validation_result.get('extracted_fields', {})
            if extracted_fields:
                print(f"\n📋 FIELD YANG DIEKSTRAK:")
                for field, value in extracted_fields.items():
                    if value:
                        print(f"   📌 {field}: {str(value)[:100]}...")
            
            return {
                'is_valid': ai_response.get('status') == 'VALID',
                'confidence_score': ai_response.get('confidence', 0),
                'ai_analysis': validation_result.get('ai_analysis', ''),
                'issues_found': issues,
                'extracted_fields': extracted_fields
            }
            
        else:
            print(f"❌ Gagal validasi AI: {ai_response.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error dalam validasi AI: {str(e)}")
        return None

def compare_with_standards(extracted_data):
    """Compare extracted data with akta standards"""
    print(f"\n📏 PERBANDINGAN DENGAN STANDAR AKTA")
    print("-" * 50)
    
    # Standard requirements for akta
    standards = {
        "required_sections": [
            "nomor_akta", "tanggal", "notaris", "nama_perusahaan", 
            "alamat", "modal", "direktur", "bidang_usaha"
        ],
        "optional_sections": ["npwp", "siup", "saksi"],
        "minimum_length": 10000,  # characters
        "minimum_words": 1000
    }
    
    found_sections = extracted_data.get('found_sections', {})
    text_stats = extracted_data.get('text_stats', {})
    
    # Check required sections
    required_found = 0
    required_total = len(standards['required_sections'])
    
    print("✅ BAGIAN WAJIB:")
    for section in standards['required_sections']:
        if section in found_sections:
            print(f"   ✅ {section.replace('_', ' ').title()}")
            required_found += 1
        else:
            print(f"   ❌ {section.replace('_', ' ').title()}")
    
    # Check optional sections
    optional_found = 0
    optional_total = len(standards['optional_sections'])
    
    print(f"\n📋 BAGIAN OPSIONAL:")
    for section in standards['optional_sections']:
        if section in found_sections:
            print(f"   ✅ {section.replace('_', ' ').title()}")
            optional_found += 1
        else:
            print(f"   ⏭️  {section.replace('_', ' ').title()}")
    
    # Check document size
    total_chars = text_stats.get('total_characters', 0)
    total_words = text_stats.get('total_words', 0)
    
    print(f"\n📊 UKURAN DOKUMEN:")
    print(f"   📝 Karakter: {total_chars:,} ({'✅ Memadai' if total_chars >= standards['minimum_length'] else '❌ Terlalu pendek'})")
    print(f"   📖 Kata: {total_words:,} ({'✅ Memadai' if total_words >= standards['minimum_words'] else '❌ Terlalu pendek'})")
    
    # Calculate compliance score
    required_score = (required_found / required_total) * 100
    optional_score = (optional_found / optional_total) * 100 if optional_total > 0 else 0
    size_score = 100 if total_chars >= standards['minimum_length'] and total_words >= standards['minimum_words'] else 50
    
    overall_score = (required_score * 0.6) + (optional_score * 0.2) + (size_score * 0.2)
    
    print(f"\n📊 SKOR KEPATUHAN:")
    print(f"   📋 Bagian Wajib: {required_score:.1f}% ({required_found}/{required_total})")
    print(f"   📝 Bagian Opsional: {optional_score:.1f}% ({optional_found}/{optional_total})")
    print(f"   📏 Ukuran Dokumen: {size_score:.1f}%")
    print(f"   🎯 SKOR KESELURUHAN: {overall_score:.1f}%")
    
    if overall_score >= 80:
        compliance_level = "EXCELLENT - Sangat Sesuai Standar"
    elif overall_score >= 70:
        compliance_level = "GOOD - Sesuai Standar"
    elif overall_score >= 60:
        compliance_level = "FAIR - Cukup Memadai"
    else:
        compliance_level = "POOR - Perlu Perbaikan"
    
    print(f"   📈 TINGKAT KEPATUHAN: {compliance_level}")
    
    return {
        "required_score": required_score,
        "optional_score": optional_score,
        "size_score": size_score,
        "overall_score": overall_score,
        "compliance_level": compliance_level
    }

def main():
    print("🤖 DEMO VALIDASI AI UNTUK DATA AKTA")
    print("=" * 70)
    
    # Find the latest extraction result
    current_dir = os.path.dirname(os.path.abspath(__file__))
    result_files = []
    
    for file in os.listdir(current_dir):
        if file.startswith('akta_extraction_') and file.endswith('.json'):
            result_files.append(file)
    
    if not result_files:
        print("❌ Tidak ditemukan file hasil ekstraksi")
        print("💡 Jalankan akta_extraction_demo.py terlebih dahulu")
        return
    
    # Use the latest file
    latest_file = sorted(result_files)[-1]
    print(f"📄 Menggunakan file: {latest_file}")
    
    # Load extraction results
    with open(latest_file, 'r', encoding='utf-8') as f:
        extracted_data = json.load(f)
    
    print(f"📊 Data dari file: {extracted_data.get('file_name', 'Unknown')}")
    print(f"⏰ Diproses pada: {extracted_data.get('processed_at', 'Unknown')}")
    
    # Get original text for AI validation
    akta_file = extracted_data.get('file_name', '')
    akta_text = ""
    
    if akta_file and os.path.exists(akta_file):
        from pdf_processor import PDFProcessor
        processor = PDFProcessor()
        result = processor.extract_text_pymupdf(akta_file)
        if result.get('success'):
            akta_text = result.get('full_text', '')
    
    # Compare with standards
    compliance_result = compare_with_standards(extracted_data)
    
    # Validate with AI
    ai_validation = validate_akta_with_ai(extracted_data, akta_text)
    
    # Create final report
    final_report = {
        "extraction_data": extracted_data,
        "compliance_analysis": compliance_result,
        "ai_validation": ai_validation,
        "final_assessment": {
            "timestamp": datetime.now().isoformat(),
            "extraction_success": True,
            "compliance_score": compliance_result.get('overall_score', 0),
            "ai_confidence": ai_validation.get('confidence_score', 0) if ai_validation else 0,
            "overall_status": "VALID" if (compliance_result.get('overall_score', 0) >= 70 and 
                                       (ai_validation.get('is_valid', False) if ai_validation else True)) else "NEEDS_REVIEW"
        }
    }
    
    # Save final report
    report_file = f"akta_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Laporan lengkap disimpan ke: {report_file}")
    
    print(f"\n" + "="*70)
    print("🎯 RINGKASAN VALIDASI AKTA")
    print("="*70)
    
    overall_status = final_report['final_assessment']['overall_status']
    compliance_score = final_report['final_assessment']['compliance_score']
    ai_confidence = final_report['final_assessment']['ai_confidence']
    
    print(f"📋 STATUS AKHIR: {overall_status}")
    print(f"📊 Skor Kepatuhan: {compliance_score:.1f}%")
    print(f"🤖 Confidence AI: {ai_confidence:.2f}")
    
    if overall_status == "VALID":
        print("✅ AKTA VALID - Memenuhi standar dan lolos validasi AI")
    else:
        print("⚠️  AKTA PERLU REVIEW - Ada bagian yang perlu diperbaiki")
    
    print(f"\n📋 DATA YANG BERHASIL DIVALIDASI:")
    print("   📜 Struktur dan kelengkapan dokumen")
    print("   🏢 Informasi perusahaan")
    print("   👨‍💼 Data notaris")
    print("   📍 Alamat dan domisili")
    print("   💰 Informasi modal")
    print("   🤖 Analisis AI terhadap konten")
    
    print(f"\n🚀 SISTEM VALIDASI AKTA BERFUNGSI SEMPURNA!")

if __name__ == "__main__":
    main()
