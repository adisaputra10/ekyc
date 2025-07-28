# Document Validation System

Sistem validasi dokumen KTP dan Akta menggunakan OpenAI dan RAG (Retrieval-Augmented Generation) dengan Elasticsearch.

## Fitur Utama

- **Validasi KTP**: Ekstraksi dan validasi data dari gambar KTP menggunakan OCR (EasyOCR/Tesseract)
- **Validasi Akta**: Ekstraksi dan validasi data dari dokumen PDF Akta
- **RAG dengan Elasticsearch**: Menggunakan knowledge base untuk validasi yang lebih akurat
- **OpenAI Integration**: Analisis cerdas menggunakan GPT-4o-mini
- **RESTful API**: Interface HTTP untuk integrasi dengan aplikasi lain
- **Comprehensive Reporting**: Laporan validasi yang detail dan terstruktur

## Persyaratan Sistem

- Python 3.8+
- Elasticsearch 8.x
- OpenAI API Key
- Tesseract OCR (opsional, untuk fallback)

## Instalasi

1. **Clone repository dan masuk ke direktori**:
   ```bash
   cd d:\repo\ekyc_openai
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Elasticsearch 8**:
   - Download dan install Elasticsearch 8.x
   - Jalankan Elasticsearch di localhost:9200
   - Catat username dan password untuk konfigurasi

4. **Konfigurasi environment**:
   ```bash
   copy .env.example .env
   ```
   
   Edit file `.env` dan isi dengan konfigurasi Anda:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ELASTICSEARCH_URL=http://localhost:9200
   ELASTICSEARCH_USERNAME=elastic
   ELASTICSEARCH_PASSWORD=your_password_here
   ELASTICSEARCH_INDEX=document_validation
   LOG_LEVEL=INFO
   ```

5. **Install Tesseract OCR (opsional)**:
   - Windows: Download dari https://github.com/UB-Mannheim/tesseract/wiki
   - Tambahkan Tesseract ke PATH

## Penggunaan

### 1. Command Line Interface

**Validasi dokumen tunggal**:
```bash
python document_validator.py --single ktp.png --type ktp
python document_validator.py --single akta.pdf --type akta
```

**Validasi komprehensif (KTP + Akta)**:
```bash
python document_validator.py --ktp ktp.png --akta akta.pdf --output hasil_validasi.json
```

### 2. API Server

**Jalankan server**:
```bash
python run_api.py
```

Server akan berjalan di `http://localhost:8000`

**API Documentation**: `http://localhost:8000/docs`

**Endpoints**:

- `POST /validate/ktp` - Upload dan validasi gambar KTP
- `POST /validate/akta` - Upload dan validasi PDF Akta  
- `POST /validate/comprehensive` - Upload KTP dan Akta untuk validasi komprehensif
- `POST /validate/single` - Upload dokumen tunggal dengan deteksi otomatis
- `GET /health` - Status kesehatan API

**Contoh penggunaan dengan curl**:
```bash
# Validasi KTP
curl -X POST "http://localhost:8000/validate/ktp" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@ktp.png"

# Validasi Akta
curl -X POST "http://localhost:8000/validate/akta" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@akta.pdf"

# Validasi Komprehensif
curl -X POST "http://localhost:8000/validate/comprehensive" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "ktp_file=@ktp.png" \
     -F "akta_file=@akta.pdf"
```

### 3. Test Script

**Jalankan test dengan dokumen yang ada**:
```bash
python test_validation.py
```

## Struktur Project

```
ekyc_openai/
├── config.py                 # Konfigurasi aplikasi
├── image_processor.py        # Pemrosesan gambar dan OCR
├── pdf_processor.py          # Pemrosesan PDF dan ekstraksi teks
├── elasticsearch_rag.py      # RAG menggunakan Elasticsearch
├── openai_validator.py       # Validasi menggunakan OpenAI
├── document_validator.py     # Main validator class
├── api.py                    # FastAPI server
├── run_api.py               # Script untuk menjalankan API
├── test_validation.py       # Script testing
├── requirements.txt         # Dependencies
├── .env.example            # Contoh konfigurasi environment
└── README.md               # Dokumentasi ini
```

## Format Response

### Validasi KTP
```json
{
  "document_type": "KTP",
  "file_path": "path/to/ktp.png",
  "timestamp": "2025-07-27T10:30:00",
  "success": true,
  "processing_steps": {
    "ocr": {
      "success": true,
      "method": "EasyOCR",
      "extracted_text": "..."
    },
    "field_extraction": {
      "success": true,
      "extracted_fields": {
        "nik": "1234567890123456",
        "nama": "JOHN DOE",
        "tempat_lahir": "JAKARTA",
        "tanggal_lahir": "01-01-1990",
        "jenis_kelamin": "LAKI-LAKI",
        "alamat": "...",
        "agama": "ISLAM",
        "status_perkawinan": "BELUM KAWIN",
        "pekerjaan": "KARYAWAN SWASTA",
        "kewarganegaraan": "WNI"
      }
    }
  },
  "validation_result": {
    "valid": true,
    "confidence_score": 85,
    "validation_results": {
      "nik_valid": true,
      "nik_format_correct": true,
      "data_complete": true,
      "data_consistent": true,
      "gender_nik_match": true
    },
    "missing_fields": [],
    "errors": [],
    "warnings": [],
    "recommendations": [],
    "summary": "KTP valid dengan tingkat kepercayaan tinggi"
  }
}
```

### Validasi Akta
```json
{
  "document_type": "AKTA",
  "file_path": "path/to/akta.pdf",
  "timestamp": "2025-07-27T10:30:00",
  "success": true,
  "processing_steps": {
    "pdf_extraction": {
      "success": true,
      "total_pages": 15,
      "extracted_text": "..."
    },
    "field_extraction": {
      "success": true,
      "extracted_fields": {
        "nomor_akta": "30",
        "tanggal_akta": "08 Agustus 2000",
        "nama_notaris": "...",
        "nama_perusahaan": "PT MORA TELEMATIKA INDONESIA",
        "modal_dasar": "...",
        "modal_disetor": "...",
        "alamat_perusahaan": "...",
        "direktur": ["..."],
        "komisaris": ["..."],
        "npwp": "..."
      },
      "structure_validation": {
        "has_akta_number": true,
        "has_notary_name": true,
        "has_company_info": true,
        "has_legal_structure": true,
        "confidence_score": 0.9
      }
    }
  },
  "validation_result": {
    "valid": true,
    "confidence_score": 88,
    "validation_results": {
      "akta_number_valid": true,
      "date_valid": true,
      "notary_mentioned": true,
      "company_info_complete": true,
      "capital_requirements_met": true,
      "legal_structure_valid": true,
      "directors_mentioned": true
    },
    "missing_fields": [],
    "legal_issues": [],
    "format_issues": [],
    "capital_analysis": {
      "modal_dasar_sufficient": true,
      "modal_disetor_mentioned": true,
      "compliance_notes": "..."
    },
    "recommendations": [],
    "summary": "Akta valid dengan struktur legal yang lengkap"
  }
}
```

### Validasi Komprehensif
```json
{
  "timestamp": "2025-07-27T10:30:00",
  "success": true,
  "ktp_validation": { /* hasil validasi KTP */ },
  "akta_validation": { /* hasil validasi Akta */ },
  "comprehensive_report": {
    "overall_status": "VALID",
    "overall_confidence": 86,
    "executive_summary": "...",
    "document_status": {
      "ktp": {"status": "VALID", "confidence": 85},
      "akta": {"status": "VALID", "confidence": 88}
    },
    "cross_document_analysis": {
      "name_consistency": true,
      "data_alignment": true,
      "notes": "..."
    },
    "risk_assessment": {
      "level": "LOW",
      "factors": [],
      "mitigation": []
    },
    "next_actions": [],
    "compliance_notes": "..."
  }
}
```

## Troubleshooting

### Elasticsearch Connection Error
- Pastikan Elasticsearch berjalan di localhost:9200
- Check username dan password di file .env
- Pastikan Elasticsearch cluster dalam status healthy

### OpenAI API Error
- Pastikan API key valid dan memiliki quota
- Check koneksi internet
- Pastikan menggunakan model yang tersedia (gpt-4o-mini)

### OCR Error
- Pastikan gambar KTP berkualitas baik dan readable
- Install Tesseract OCR sebagai fallback
- Check format file yang didukung (PNG, JPG, JPEG)

### PDF Processing Error
- Pastikan file PDF tidak terenkripsi
- Check apakah PDF berisi teks (bukan scan image)
- Gunakan PDF dengan kualitas yang baik

## Kontribusi

1. Fork repository
2. Buat branch fitur baru
3. Commit perubahan Anda
4. Push ke branch
5. Buat Pull Request

## Lisensi

Project ini menggunakan lisensi MIT. Lihat file LICENSE untuk detail lebih lanjut.

## Support

Untuk dukungan teknis atau pertanyaan, silakan buat issue di repository ini.
