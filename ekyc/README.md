# eKYC System

Electronic Know Your Customer (eKYC) system menggunakan Python dengan analisa dokumen berbasis AI/LLM.

## 🚀 Fitur Utama

- **Formulir eKYC Digital**: Input data personal, alamat, dan kontak lengkap
- **Generate Dokumen PDF**: Membuat dokumen eKYC dengan QR code untuk verifikasi
- **Analisa Dokumen AI**: Menggunakan OCR dan LLM untuk menganalisa dokumen identitas
- **Face Recognition**: Perbandingan wajah antara selfie dan foto dokumen
- **Verifikasi Otomatis**: Status verifikasi berdasarkan confidence score
- **Web Interface**: FastAPI dan Streamlit interface

## 📋 Jenis Dokumen yang Didukung

- KTP (Kartu Tanda Penduduk)
- Paspor Indonesia
- SIM (Surat Izin Mengemudi)  
- NPWP (Nomor Pokok Wajib Pajak)

## 🔧 Teknologi

- **Backend**: FastAPI, Python
- **Document Processing**: ReportLab, FPDF, QR Code
- **Computer Vision**: OpenCV, Tesseract OCR, Face Recognition
- **AI Analysis**: OpenAI GPT, LangChain
- **Frontend**: HTML/CSS, Streamlit
- **Data Models**: Pydantic

## 📦 Instalasi

1. **Clone repository dan setup virtual environment:**
```bash
cd d:/repo/ekyc
python -m venv .venv
.venv\Scripts\activate  # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup environment variables:**
```bash
copy .env.example .env
# Edit .env file dan isi OPENAI_API_KEY jika ingin menggunakan analisa AI
```

4. **Install Tesseract OCR (Windows):**
- Download dari: https://github.com/UB-Mannheim/tesseract/wiki
- Install dan tambahkan ke PATH
- Atau set path di config.py

## 🚀 Menjalankan Aplikasi

### FastAPI Web Server
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Buka browser ke: http://localhost:8000

### Streamlit App  
```bash
streamlit run streamlit_app.py
```
Buka browser ke: http://localhost:8501

### Test System
```bash
python test_ekyc.py
```

## 📖 Cara Penggunaan

### 1. Mengisi Formulir eKYC
- Buka web interface
- Isi semua data personal, alamat, dan kontak
- Upload foto selfie dan dokumen identitas
- Submit form

### 2. Generate Dokumen PDF
- Sistem akan generate PDF dengan QR code
- Download dokumen yang telah dibuat
- Simpan kode verifikasi untuk referensi

### 3. Analisa Dokumen AI
- Jika upload dokumen, sistem akan analisa menggunakan:
  - OCR untuk extract text
  - LLM untuk validasi data
  - Face recognition untuk matching
- Review hasil analisa dan confidence score

## 🔍 API Endpoints

- `GET /` - Homepage dengan form eKYC
- `POST /submit-ekyc` - Submit form dan generate dokumen
- `POST /analyze-document` - Analisa dokumen saja
- `GET /health` - Health check

## 📂 Struktur Project

```
ekyc/
├── models.py              # Data models (Pydantic)
├── document_generator.py  # PDF document generator
├── document_analyzer.py   # AI document analyzer
├── main.py               # FastAPI web server
├── streamlit_app.py      # Streamlit interface
├── config.py             # Configuration settings
├── test_ekyc.py          # Testing script
├── requirements.txt      # Dependencies
├── templates/            # HTML templates
│   ├── index.html
│   └── result.html
├── uploads/              # Uploaded files
├── outputs/              # Generated PDFs
└── static/               # Static files
```

## ⚙️ Konfigurasi

Edit `config.py` atau `.env` untuk mengatur:

- **OPENAI_API_KEY**: API key untuk analisa LLM
- **TESSERACT_CMD**: Path ke tesseract executable
- **Thresholds**: Confidence dan face match thresholds
- **File limits**: Max file size dan allowed types

## 🔒 Keamanan

- File upload dengan validasi tipe dan ukuran
- Kode verifikasi unik untuk setiap dokumen
- QR code untuk verifikasi dokumen
- Async file handling untuk performa
- Error handling yang komprehensif

## 🧪 Testing

Jalankan test untuk memastikan sistem berfungsi:

```bash
python test_ekyc.py
```

Test meliputi:
- Generate dokumen PDF
- Analisa dokumen (dengan API key)
- Validasi data models

## 📝 Contoh Output

### Generated PDF Features:
- Header dengan QR code verifikasi
- Tabel informasi personal yang terstruktur
- Data alamat dan kontak lengkap
- Daftar dokumen yang diserahkan
- Pernyataan dan area tanda tangan

### Analysis Results:
```json
{
    "document_type": "ktp",
    "confidence_score": 0.85,
    "verification_status": "verified",
    "face_match_score": 0.92,
    "issues_found": [],
    "recommendations": ["Document quality is good"]
}
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is for educational and development purposes.

## 🆘 Support

Untuk pertanyaan atau masalah:
- Check dokumentasi di README
- Review error logs
- Pastikan dependencies terinstall dengan benar
- Verify environment variables setup

## 🔄 Updates

- **v1.0**: Basic eKYC form dan PDF generation
- **v1.1**: Tambah document analysis dengan AI
- **v1.2**: Face recognition integration
- **v1.3**: Streamlit interface
- **v1.4**: Improved error handling dan validation
