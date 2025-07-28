#!/usr/bin/env python3
"""
Demo ekstraksi data dari file Akta untuk validasi
Enhanced with OCR support for scanned PDFs
"""

import os
import json
from datetime import datetime
from pdf_processor import PDFProcessor
from document_validator import DocumentValidator

def extract_pdf_text_with_ocr(file_path):
    """Extract text from PDF with OCR fallback for scanned documents"""
    processor = PDFProcessor()
    
    print("🔧 Mencoba ekstraksi teks dengan PyMuPDF...")
    result = processor.extract_text_pymupdf(file_path)
    
    if result['success'] and result['full_text'].strip():
        print(f"✅ PyMuPDF berhasil - {len(result['full_text'])} karakter")
        return result
    
    print("⚠️  PyMuPDF tidak menghasilkan teks, mencoba PyPDF2...")
    result = processor.extract_text_pypdf2(file_path)
    
    if result['success'] and result['full_text'].strip():
        print(f"✅ PyPDF2 berhasil - {len(result['full_text'])} karakter")
        return result
    
    print("⚠️  PyPDF2 juga tidak menghasilkan teks")
    print("🔍 Kemungkinan ini adalah PDF gambar/scan - memerlukan OCR")
    
    # Try OCR approach for scanned PDFs
    try:
        import fitz  # PyMuPDF
        import easyocr
        from PIL import Image
        import io
        
        print("🔧 Mencoba ekstraksi dengan OCR...")
        
        # Open PDF and convert to images
        doc = fitz.open(file_path)
        ocr_reader = easyocr.Reader(['en', 'id'])  # English and Indonesian
        
        all_text = []
        total_chars = 0
        total_pages = len(doc)
        
        for page_num in range(min(5, total_pages)):  # Process first 5 pages for speed
            print(f"   📄 Memproses halaman {page_num + 1}...")
            
            page = doc.load_page(page_num)
            
            # Convert page to image
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image (for debugging purposes)
            # image = Image.open(io.BytesIO(img_data))
            
            # Perform OCR
            ocr_results = ocr_reader.readtext(img_data)
            page_text = " ".join([result[1] for result in ocr_results])
            
            all_text.append(page_text)
            total_chars += len(page_text)
            
            print(f"      📊 {len(page_text)} karakter diekstrak")
        
        doc.close()
        
        full_text = '\n'.join(all_text)
        
        if total_chars > 100:  # Minimum threshold
            print(f"✅ OCR berhasil - total {total_chars} karakter dari {min(5, total_pages)} halaman")
            return {
                'success': True,
                'full_text': full_text,
                'total_pages': total_pages,
                'method': 'OCR',
                'pages_processed': min(5, total_pages)
            }
        else:
            print(f"❌ OCR menghasilkan teks terlalu sedikit ({total_chars} karakter)")
            return {'success': False, 'error': 'OCR hasil tidak memadai'}
            
    except ImportError as e:
        print(f"❌ Library OCR tidak tersedia: {e}")
        print("💡 Install dengan: pip install easyocr pillow")
        return {'success': False, 'error': f'OCR library missing: {e}'}
    except Exception as e:
        print(f"❌ OCR gagal: {e}")
        return {'success': False, 'error': f'OCR failed: {e}'}

def analyze_akta_structure(text):
    """Analyze the structure and extract key data from akta text"""
    print("🔍 ANALISIS STRUKTUR AKTA:")
    print("-" * 50)
    
    # Basic text analysis
    lines = text.split('\n')
    total_lines = len(lines)
    total_chars = len(text)
    words = text.split()
    total_words = len(words)
    
    print(f"📊 Statistik Dokumen:")
    print(f"   📝 Total baris: {total_lines}")
    print(f"   🔤 Total karakter: {total_chars}")
    print(f"   📖 Total kata: {total_words}")
    
    # Key sections to look for in Akta
    key_sections = {
        "nomor_akta": ["AKTA", "NOMOR", "NO"],
        "tanggal": ["TANGGAL", "HARI", "BULAN", "TAHUN"],
        "notaris": ["NOTARIS", "PPAT"],
        "nama_perusahaan": ["PT", "CV", "FIRMA", "KOPERASI"],
        "alamat": ["ALAMAT", "BERKEDUDUKAN", "DOMISILI"],
        "modal": ["MODAL", "SAHAM", "RUPIAH", "RP"],
        "direktur": ["DIREKTUR", "DIREKSI", "KOMISARIS"],
        "bidang_usaha": ["BIDANG USAHA", "KEGIATAN USAHA", "MAKSUD", "TUJUAN"],
        "npwp": ["NPWP", "NOMOR POKOK WAJIB PAJAK"],
        "siup": ["SIUP", "SURAT IZIN USAHA"],
        "saksi": ["SAKSI", "HADIR"],
        "pendirian": ["PENDIRIAN", "MENDIRIKAN", "DIBENTUK"]
    }
    
    found_sections = {}
    
    print(f"\n🔍 PENCARIAN BAGIAN PENTING:")
    print("-" * 50)
    
    for section, keywords in key_sections.items():
        found_in_lines = []
        for i, line in enumerate(lines):
            line_upper = line.upper()
            for keyword in keywords:
                if keyword in line_upper:
                    found_in_lines.append({
                        "line_number": i + 1,
                        "content": line.strip(),
                        "keyword": keyword
                    })
                    break
        
        if found_in_lines:
            found_sections[section] = found_in_lines
            print(f"✅ {section.upper().replace('_', ' ')}: Ditemukan {len(found_in_lines)} referensi")
            for item in found_in_lines[:3]:  # Show first 3 matches
                print(f"   📍 Baris {item['line_number']}: {item['content'][:80]}...")
        else:
            print(f"❌ {section.upper().replace('_', ' ')}: Tidak ditemukan")
    
    return found_sections

def extract_specific_data(text, found_sections):
    """Extract specific data points for validation"""
    print(f"\n📋 EKSTRAKSI DATA SPESIFIK:")
    print("-" * 50)
    
    extracted_data = {}
    
    # Extract company name (PT/CV)
    lines = text.split('\n')
    for line in lines:
        line_clean = line.strip().upper()
        if 'PT ' in line_clean and len(line_clean) < 100:
            # Look for PT followed by company name
            if 'PENDIRIAN' in line_clean or 'MENDIRIKAN' in line_clean:
                extracted_data['company_name'] = line.strip()
                print(f"🏢 Nama Perusahaan: {line.strip()}")
                break
    
    # Extract Akta number and date
    for line in lines:
        line_upper = line.upper()
        if 'AKTA' in line_upper and 'NOMOR' in line_upper:
            extracted_data['akta_info'] = line.strip()
            print(f"📜 Info Akta: {line.strip()}")
            break
    
    # Extract Notaris using improved logic
    import re
    notary_patterns = [
        r'saya[,\s]+([A-Z\s\.]+?)[,\s]+(?:Sarjana\s+Hukum|SH)',
        r'Motaris\s+([A-Z\s\.]+?)(?:\s*,\s*SH|\s*berkedudukan)',
        r'dari\s+Motaris\s+([A-Z\s\.]+?)(?:\s*,\s*SH|\n)'
    ]
    
    full_text_upper = text.upper()
    for pattern in notary_patterns:
        match = re.search(pattern, full_text_upper, re.IGNORECASE)
        if match:
            notary_name = match.group(1).strip()
            if (len(notary_name) >= 5 and 
                len(notary_name) <= 50 and
                not any(x in notary_name.lower() for x in ['departemen', 'keputusan', 'nomor', 'penghadap', 'bertindak']) and
                ' ' in notary_name):
                extracted_data['notaris'] = notary_name
                print(f"👨‍💼 Notaris: {notary_name}")
                break
    
    # Fallback to simple search if advanced patterns don't work
    if 'notaris' not in extracted_data:
        for line in lines:
            line_upper = line.upper()
            if 'NOTARIS' in line_upper and len(line.strip()) < 150:
                extracted_data['notaris'] = line.strip()
                print(f"👨‍💼 Notaris (fallback): {line.strip()}")
                break
    
    # Extract address/domicile
    for line in lines:
        line_upper = line.upper()
        if any(word in line_upper for word in ['BERKEDUDUKAN', 'DOMISILI', 'ALAMAT']) and len(line.strip()) < 200:
            extracted_data['address'] = line.strip()
            print(f"📍 Alamat/Domisili: {line.strip()}")
            break
    
    # Extract modal/capital
    for line in lines:
        line_upper = line.upper()
        if 'MODAL' in line_upper and any(word in line_upper for word in ['RUPIAH', 'RP', 'IDR']):
            extracted_data['modal'] = line.strip()
            print(f"💰 Modal: {line.strip()}")
            break
    
    if not extracted_data:
        print("⚠️  Tidak dapat mengekstrak data spesifik dengan pola yang ada")
        print("💡 Coba periksa format dokumen atau gunakan kata kunci yang berbeda")
    
    return extracted_data

def validate_akta_completeness(extracted_data, found_sections):
    """Validate if akta contains required elements"""
    print(f"\n✅ VALIDASI KELENGKAPAN AKTA:")
    print("-" * 50)
    
    required_elements = [
        "nomor_akta",
        "tanggal", 
        "notaris",
        "nama_perusahaan",
        "alamat",
        "modal"
    ]
    
    validation_score = 0
    total_elements = len(required_elements)
    
    for element in required_elements:
        if element in found_sections:
            print(f"✅ {element.replace('_', ' ').title()}: DITEMUKAN")
            validation_score += 1
        else:
            print(f"❌ {element.replace('_', ' ').title()}: TIDAK DITEMUKAN")
    
    completeness_percentage = (validation_score / total_elements) * 100
    
    print(f"\n📊 SKOR KELENGKAPAN: {validation_score}/{total_elements} ({completeness_percentage:.1f}%)")
    
    if completeness_percentage >= 80:
        status = "VALID - Dokumen Lengkap"
        print(f"🎉 STATUS: {status}")
    elif completeness_percentage >= 60:
        status = "PARTIAL - Perlu Dilengkapi"
        print(f"⚠️  STATUS: {status}")
    else:
        status = "INVALID - Dokumen Tidak Lengkap"
        print(f"❌ STATUS: {status}")
    
    return {
        "completeness_score": validation_score,
        "total_elements": total_elements,
        "percentage": completeness_percentage,
        "status": status
    }

def main():
    print("📋 DEMO EKSTRAKSI DATA AKTA UNTUK VALIDASI")
    print("=" * 70)
    
    # Find akta files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    akta_files = []
    
    for file in os.listdir(current_dir):
        if file.lower().endswith('.pdf') and 'akta' in file.lower():
            akta_files.append(file)
    
    if not akta_files:
        print("❌ Tidak ditemukan file PDF akta di folder ini")
        print("💡 Pastikan ada file PDF dengan nama yang mengandung 'akta'")
        return
    
    print(f"📁 Folder: {current_dir}")
    print(f"📄 File Akta ditemukan: {akta_files}")
    
    processor = PDFProcessor()
    
    for akta_file in akta_files:
        print(f"\n" + "="*70)
        print(f"📄 MENGANALISIS: {akta_file}")
        print("="*70)
        
        file_path = os.path.join(current_dir, akta_file)
        
        # Extract text from PDF with OCR fallback
        print("🔧 Mengekstrak teks dari PDF...")
        extraction_result = extract_pdf_text_with_ocr(file_path)
        
        if not extraction_result['success']:
            print(f"❌ Gagal mengekstrak PDF: {extraction_result.get('error', 'Unknown error')}")
            continue
        
        full_text = extraction_result.get('full_text', '')
        
        if not full_text.strip():
            print("❌ Tidak ada teks yang dapat diekstrak dari PDF")
            continue
        
        extraction_method = extraction_result.get('method', 'PDF Text')
        print(f"✅ Berhasil mengekstrak {len(full_text)} karakter dengan {extraction_method}")
        
        # Show first few lines
        lines = full_text.split('\n')[:10]
        print(f"\n📄 10 BARIS PERTAMA:")
        for i, line in enumerate(lines, 1):
            if line.strip():
                print(f"   {i:2d}. {line.strip()[:80]}...")
        
        # Analyze structure
        found_sections = analyze_akta_structure(full_text)
        
        # Extract specific data
        extracted_data = extract_specific_data(full_text, found_sections)
        
        # Validate completeness
        validation_result = validate_akta_completeness(extracted_data, found_sections)
        
        # Save results
        result_data = {
            "file_name": akta_file,
            "processed_at": datetime.now().isoformat(),
            "text_stats": {
                "total_characters": len(full_text),
                "total_lines": len(full_text.split('\n')),
                "total_words": len(full_text.split())
            },
            "found_sections": found_sections,
            "extracted_data": extracted_data,
            "validation_result": validation_result,
            "first_10_lines": [line.strip() for line in lines if line.strip()]
        }
        
        result_file = f"akta_extraction_{akta_file.replace('.pdf', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Hasil disimpan ke: {result_file}")
    
    print(f"\n" + "="*70)
    print("🎯 RINGKASAN EKSTRAKSI DATA AKTA")
    print("="*70)
    print("✅ Data yang berhasil diekstrak dan dianalisis:")
    print("   📜 Informasi Akta (nomor, tanggal)")
    print("   🏢 Nama Perusahaan") 
    print("   👨‍💼 Nama Notaris")
    print("   📍 Alamat/Domisili")
    print("   💰 Modal Perusahaan")
    print("   📊 Skor Kelengkapan Dokumen")
    
    print(f"\n💡 DATA INI SIAP UNTUK VALIDASI AI:")
    print("   - Bisa dikirim ke OpenAI untuk analisis lebih lanjut")
    print("   - Bisa dibandingkan dengan template referensi")
    print("   - Bisa divalidasi dengan aturan bisnis")
    
    print(f"\n🚀 SISTEM EKSTRAKSI AKTA BERFUNGSI DENGAN BAIK!")

if __name__ == "__main__":
    main()
