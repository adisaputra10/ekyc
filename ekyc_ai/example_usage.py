#!/usr/bin/env python3
"""
Contoh penggunaan Document Validation System
"""

import json
import os
from document_validator import DocumentValidator

def example_ktp_validation():
    """Contoh validasi KTP"""
    print("=" * 50)
    print("CONTOH VALIDASI KTP")
    print("=" * 50)
    
    # Path ke file KTP (sesuaikan dengan file Anda)
    ktp_file = "ktp.png"
    
    if not os.path.exists(ktp_file):
        print(f"File KTP tidak ditemukan: {ktp_file}")
        print("Pastikan file ktp.png ada di direktori yang sama")
        return
    
    try:
        # Initialize validator
        validator = DocumentValidator()
        
        # Validasi KTP
        print(f"Memproses file: {ktp_file}")
        result = validator.validate_ktp(ktp_file)
        
        if result['success']:
            validation = result['validation_result']
            print(f"\n✅ Validasi KTP berhasil!")
            print(f"📊 Status: {'VALID' if validation.get('valid') else 'INVALID'}")
            print(f"🎯 Confidence Score: {validation.get('confidence_score', 0)}/100")
            
            # Tampilkan data yang diekstrak
            fields = result['processing_steps']['field_extraction']['extracted_fields']
            print(f"\n📋 Data yang diekstrak:")
            for field, value in fields.items():
                if value:
                    print(f"   {field.replace('_', ' ').title()}: {value}")
            
            # Tampilkan hasil validasi
            validation_results = validation.get('validation_results', {})
            print(f"\n🔍 Hasil Validasi:")
            for check, passed in validation_results.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check.replace('_', ' ').title()}")
            
            # Tampilkan ringkasan
            summary = validation.get('summary', 'Tidak ada ringkasan')
            print(f"\n📝 Ringkasan: {summary}")
            
        else:
            print(f"❌ Validasi KTP gagal: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def example_akta_validation():
    """Contoh validasi Akta"""
    print("\n" + "=" * 50)
    print("CONTOH VALIDASI AKTA")
    print("=" * 50)
    
    # Path ke file Akta (sesuaikan dengan file Anda)
    akta_file = "akta.pdf"
    
    if not os.path.exists(akta_file):
        print(f"File Akta tidak ditemukan: {akta_file}")
        print("Pastikan file akta.pdf ada di direktori yang sama")
        return
    
    try:
        # Initialize validator
        validator = DocumentValidator()
        
        # Validasi Akta
        print(f"Memproses file: {akta_file}")
        result = validator.validate_akta(akta_file)
        
        if result['success']:
            validation = result['validation_result']
            print(f"\n✅ Validasi Akta berhasil!")
            print(f"📊 Status: {'VALID' if validation.get('valid') else 'INVALID'}")
            print(f"🎯 Confidence Score: {validation.get('confidence_score', 0)}/100")
            
            # Tampilkan data yang diekstrak
            fields = result['processing_steps']['field_extraction']['extracted_fields']
            print(f"\n📋 Data yang diekstrak:")
            for field, value in fields.items():
                if value and field != 'direktur' and field != 'komisaris':
                    print(f"   {field.replace('_', ' ').title()}: {value}")
            
            # Tampilkan direksi dan komisaris
            if fields.get('direktur'):
                print(f"   Direktur: {', '.join(fields['direktur'])}")
            if fields.get('komisaris'):
                print(f"   Komisaris: {', '.join(fields['komisaris'])}")
            
            # Tampilkan hasil validasi
            validation_results = validation.get('validation_results', {})
            print(f"\n🔍 Hasil Validasi:")
            for check, passed in validation_results.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check.replace('_', ' ').title()}")
            
            # Tampilkan analisis modal
            capital_analysis = validation.get('capital_analysis', {})
            if capital_analysis:
                print(f"\n💰 Analisis Modal:")
                for key, value in capital_analysis.items():
                    if key != 'compliance_notes':
                        status = "✅" if value else "❌"
                        print(f"   {status} {key.replace('_', ' ').title()}")
            
            # Tampilkan ringkasan
            summary = validation.get('summary', 'Tidak ada ringkasan')
            print(f"\n📝 Ringkasan: {summary}")
            
        else:
            print(f"❌ Validasi Akta gagal: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def example_comprehensive_validation():
    """Contoh validasi komprehensif"""
    print("\n" + "=" * 50)
    print("CONTOH VALIDASI KOMPREHENSIF")
    print("=" * 50)
    
    ktp_file = "ktp.png"
    akta_file = "akta.pdf"
    
    if not os.path.exists(ktp_file) or not os.path.exists(akta_file):
        print("File KTP atau Akta tidak ditemukan")
        print("Pastikan ktp.png dan akta.pdf ada di direktori yang sama")
        return
    
    try:
        # Initialize validator
        validator = DocumentValidator()
        
        # Validasi komprehensif
        print(f"Memproses file: {ktp_file} dan {akta_file}")
        result = validator.validate_documents(ktp_file, akta_file)
        
        if result['success']:
            report = result['comprehensive_report']
            
            print(f"\n✅ Validasi komprehensif berhasil!")
            print(f"📊 Status Keseluruhan: {report.get('overall_status', 'UNKNOWN')}")
            print(f"🎯 Confidence Score: {report.get('overall_confidence', 0)}/100")
            
            # Status per dokumen
            doc_status = report.get('document_status', {})
            print(f"\n📄 Status per Dokumen:")
            for doc_type, status in doc_status.items():
                print(f"   {doc_type.upper()}: {status.get('status', 'UNKNOWN')} ({status.get('confidence', 0)}/100)")
            
            # Analisis lintas dokumen
            cross_analysis = report.get('cross_document_analysis', {})
            if cross_analysis:
                print(f"\n🔗 Analisis Lintas Dokumen:")
                name_consistent = cross_analysis.get('name_consistency', False)
                data_aligned = cross_analysis.get('data_alignment', False)
                print(f"   {'✅' if name_consistent else '❌'} Konsistensi Nama")
                print(f"   {'✅' if data_aligned else '❌'} Kesesuaian Data")
            
            # Assessment risiko
            risk = report.get('risk_assessment', {})
            if risk:
                print(f"\n⚠️ Assessment Risiko:")
                print(f"   Level: {risk.get('level', 'UNKNOWN')}")
                factors = risk.get('factors', [])
                if factors:
                    print(f"   Faktor Risiko:")
                    for factor in factors:
                        print(f"     - {factor}")
            
            # Tindakan selanjutnya
            actions = report.get('next_actions', [])
            if actions:
                print(f"\n📋 Tindakan yang Disarankan:")
                for action in actions:
                    print(f"   - {action}")
            
            # Ringkasan eksekutif
            summary = report.get('executive_summary', 'Tidak ada ringkasan')
            print(f"\n📝 Ringkasan Eksekutif: {summary}")
            
        else:
            print(f"❌ Validasi komprehensif gagal")
            if 'ktp_validation' in result and not result['ktp_validation']['success']:
                print(f"   KTP Error: {result['ktp_validation'].get('error', 'Unknown')}")
            if 'akta_validation' in result and not result['akta_validation']['success']:
                print(f"   Akta Error: {result['akta_validation'].get('error', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def save_results_to_file():
    """Contoh menyimpan hasil ke file"""
    print("\n" + "=" * 50)
    print("MENYIMPAN HASIL KE FILE")
    print("=" * 50)
    
    ktp_file = "ktp.png"
    akta_file = "akta.pdf"
    
    if not os.path.exists(ktp_file) or not os.path.exists(akta_file):
        print("File KTP atau Akta tidak ditemukan")
        return
    
    try:
        validator = DocumentValidator()
        result = validator.validate_documents(ktp_file, akta_file)
        
        # Simpan ke file JSON
        output_file = "hasil_validasi.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Hasil validasi disimpan ke: {output_file}")
        
        # Simpan ringkasan ke file teks
        summary_file = "ringkasan_validasi.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            if result['success']:
                report = result['comprehensive_report']
                f.write("RINGKASAN VALIDASI DOKUMEN\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"Status Keseluruhan: {report.get('overall_status', 'UNKNOWN')}\n")
                f.write(f"Confidence Score: {report.get('overall_confidence', 0)}/100\n\n")
                f.write(f"Ringkasan Eksekutif:\n{report.get('executive_summary', 'Tidak ada ringkasan')}\n")
            else:
                f.write("VALIDASI GAGAL\n")
                f.write("=" * 15 + "\n\n")
                f.write("Terjadi kesalahan dalam proses validasi.\n")
        
        print(f"✅ Ringkasan disimpan ke: {summary_file}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Main function"""
    print("CONTOH PENGGUNAAN DOCUMENT VALIDATION SYSTEM")
    print("=" * 60)
    
    print("\nContoh ini akan mendemonstrasikan:")
    print("1. Validasi KTP")
    print("2. Validasi Akta")
    print("3. Validasi Komprehensif")
    print("4. Menyimpan hasil ke file")
    
    print(f"\nCatatan: Pastikan file 'ktp.png' dan 'akta.pdf' ada di direktori saat ini")
    
    # Jalankan contoh-contoh
    example_ktp_validation()
    example_akta_validation()
    example_comprehensive_validation()
    save_results_to_file()
    
    print("\n" + "=" * 60)
    print("SELESAI")
    print("=" * 60)
    print("\nPemat: Lihat file hasil_validasi.json dan ringkasan_validasi.txt")
    print("untuk hasil lengkap validasi.")

if __name__ == "__main__":
    main()
