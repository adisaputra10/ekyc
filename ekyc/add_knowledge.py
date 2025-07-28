"""
Script untuk menambahkan knowledge ke RAG system eKYC
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from models import KnowledgeBaseEntry
from ai_document_analyzer import VectorDatabase, DocumentProcessor
from config import Settings

class KnowledgeManager:
    """Manager untuk mengelola knowledge base"""
    
    def __init__(self):
        self.config = Settings()
        self.vector_db = None
        self.doc_processor = None
        self._init_components()
    
    def _init_components(self):
        """Initialize vector database dan document processor"""
        try:
            # Initialize document processor
            self.doc_processor = DocumentProcessor(
                api_key=self.config.deepseek_api_key,
                llm_provider=self.config.llm_provider
            )
            
            # Initialize vector database
            self.vector_db = VectorDatabase(
                index_name="ekyc_knowledge_base",
                api_key=self.config.deepseek_api_key,
                llm_provider=self.config.llm_provider
            )
            
            print("✅ Knowledge manager initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing knowledge manager: {e}")
            raise
    
    def create_knowledge_entry(self, title: str, content: str, category: str, tags: List[str] = None) -> KnowledgeBaseEntry:
        """Create a new knowledge base entry"""
        return KnowledgeBaseEntry(
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def add_single_knowledge(self, entry: KnowledgeBaseEntry) -> bool:
        """Add single knowledge entry to vector database"""
        try:
            # Prepare metadata
            metadata = {
                "title": entry.title,
                "category": entry.category,
                "tags": ",".join(entry.tags),
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
                "document_type": "knowledge_base",
                "source": "manual_entry"
            }
            
            # Add to vector database
            doc_ids = await self.vector_db.add_document_from_text_async(
                content=entry.content,
                title=entry.title,
                document_type="knowledge_base",
                category=entry.category,
                metadata=metadata,
                processor=self.doc_processor
            )
            
            print(f"✅ Added knowledge: '{entry.title}' (ID: {doc_ids[0] if doc_ids else 'unknown'})")
            return True
            
        except Exception as e:
            print(f"❌ Error adding knowledge '{entry.title}': {e}")
            return False
    
    async def add_multiple_knowledge(self, entries: List[KnowledgeBaseEntry]) -> Dict[str, bool]:
        """Add multiple knowledge entries"""
        results = {}
        
        for entry in entries:
            success = await self.add_single_knowledge(entry)
            results[entry.title] = success
        
        return results
    
    async def add_knowledge_from_dict(self, knowledge_data: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Add knowledge from dictionary data"""
        entries = []
        
        for data in knowledge_data:
            entry = self.create_knowledge_entry(
                title=data.get("title", ""),
                content=data.get("content", ""),
                category=data.get("category", "general"),
                tags=data.get("tags", [])
            )
            entries.append(entry)
        
        return await self.add_multiple_knowledge(entries)

# Predefined knowledge base untuk eKYC
EKYC_KNOWLEDGE_BASE = [
    {
        "title": "Persyaratan Lengkap KTP",
        "content": """
        Kartu Tanda Penduduk (KTP) adalah dokumen identitas resmi yang wajib dimiliki setiap warga negara Indonesia berusia 17 tahun ke atas atau sudah menikah.
        
        Persyaratan membuat KTP:
        1. Fotocopy Akta Kelahiran atau Surat Kenal Lahir
        2. Kartu Keluarga (KK) asli dan fotocopy
        3. Surat keterangan pindah dari daerah asal (untuk pendatang)
        4. Pas foto terbaru ukuran 3x4 sebanyak 2 lembar
        5. Formulir permohonan KTP yang telah diisi lengkap
        6. Bukti pembayaran retribusi (jika diperlukan)
        
        Format NIK pada KTP terdiri dari 16 digit:
        - 6 digit pertama: kode wilayah (provinsi, kabupaten/kota, kecamatan)
        - 2 digit berikutnya: tanggal lahir
        - 2 digit berikutnya: bulan lahir
        - 2 digit berikutnya: tahun lahir (2 digit terakhir)
        - 4 digit terakhir: nomor urut kelahiran
        
        Masa berlaku KTP: seumur hidup (sejak 2013)
        """,
        "category": "dokumen_identitas",
        "tags": ["ktp", "persyaratan", "nik", "format", "identitas"]
    },
    {
        "title": "Validasi NIK Lengkap",
        "content": """
        Nomor Induk Kependudukan (NIK) adalah nomor identitas unik untuk setiap penduduk Indonesia.
        
        Struktur NIK 16 digit:
        1. Digit 1-2: Kode Provinsi (11-99)
        2. Digit 3-4: Kode Kabupaten/Kota (01-99)
        3. Digit 5-6: Kode Kecamatan (01-99)
        4. Digit 7-8: Tanggal lahir (01-31, untuk perempuan ditambah 40)
        5. Digit 9-10: Bulan lahir (01-12)
        6. Digit 11-12: Tahun lahir (2 digit terakhir)
        7. Digit 13-16: Nomor urut kelahiran (0001-9999)
        
        Validasi NIK:
        - Panjang harus tepat 16 digit
        - Semua karakter harus angka
        - Kode wilayah harus valid sesuai dengan kode Kemendagri
        - Tanggal lahir harus valid (perempuan: tanggal + 40)
        - Bulan harus antara 01-12
        - Tahun harus masuk akal (tidak masa depan)
        
        Contoh: 3171012345670001
        - 31: DKI Jakarta
        - 71: Jakarta Selatan
        - 01: Kecamatan Kebayoran Baru
        - 23: Tanggal 23 (laki-laki) atau 63 (perempuan tanggal 23)
        - 45: Tahun 1945
        - 67: Tahun 1967
        - 0001: Nomor urut kelahiran
        """,
        "category": "validasi",
        "tags": ["nik", "validasi", "format", "struktur", "kode_wilayah"]
    },
    {
        "title": "Jenis Dokumen Identitas yang Diterima",
        "content": """
        Sistem eKYC menerima berbagai jenis dokumen identitas resmi Indonesia:
        
        1. KTP (Kartu Tanda Penduduk)
           - Dokumen utama identitas WNI
           - Berlaku seumur hidup
           - Wajib untuk usia 17+ atau sudah menikah
        
        2. SIM (Surat Izin Mengemudi)
           - SIM A: Mobil penumpang
           - SIM B1: Mobil barang/bus kecil
           - SIM B2: Bus/truk besar
           - SIM C: Sepeda motor
           - Masa berlaku 5 tahun
        
        3. Paspor
           - Dokumen perjalanan internasional
           - Masa berlaku 5-10 tahun
           - Ada paspor biasa dan elektronik
        
        4. NPWP (Nomor Pokok Wajib Pajak)
           - Untuk keperluan perpajakan
           - 15 digit angka
           - Wajib untuk yang berpenghasilan
        
        5. Kartu Keluarga (KK)
           - Mencatat susunan keluarga
           - 16 digit nomor KK
           - Kepala keluarga sebagai penanggung jawab
        
        6. Dokumen Pendukung Lainnya:
           - BPJS Kesehatan/Ketenagakerjaan
           - Akta Kelahiran
           - Surat Nikah/Cerai
           - Ijazah pendidikan
        
        Setiap dokumen memiliki format dan kriteria validasi yang berbeda.
        """,
        "category": "dokumen",
        "tags": ["dokumen", "jenis", "identitas", "sim", "paspor", "npwp", "kartu_keluarga"]
    },
    {
        "title": "Proses Verifikasi eKYC",
        "content": """
        Proses verifikasi eKYC (electronic Know Your Customer) terdiri dari beberapa tahapan:
        
        Tahap 1: Upload Dokumen
        - User mengunggah foto/scan dokumen identitas
        - Format yang diterima: JPG, PNG, PDF
        - Ukuran maksimal 10MB
        - Resolusi minimal 300 DPI untuk kualitas OCR terbaik
        
        Tahap 2: Preprocessing Gambar
        - Deteksi orientasi dokumen
        - Koreksi pencahayaan dan kontras
        - Cropping area dokumen
        - Noise reduction
        
        Tahap 3: OCR (Optical Character Recognition)
        - Ekstraksi teks menggunakan Tesseract dan EasyOCR
        - Confidence scoring untuk setiap kata
        - Multiple engine validation
        
        Tahap 4: Validasi Format
        - Pengecekan format NIK, nomor dokumen
        - Validasi tanggal lahir, masa berlaku
        - Cross-validation antar field
        
        Tahap 5: Verifikasi Keaslian
        - Deteksi digital manipulation
        - Analisis font dan layout konsistensi
        - Background pattern validation
        
        Tahap 6: Database Matching
        - Pencocokan dengan database Dukcapil
        - Blacklist checking
        - Historical validation
        
        Tahap 7: Scoring dan Keputusan
        - Confidence score 0-100%
        - Risk assessment
        - Final decision: APPROVED, REJECTED, MANUAL_REVIEW
        
        Waktu proses: 30 detik - 2 menit tergantung kompleksitas dokumen.
        """,
        "category": "proses",
        "tags": ["verifikasi", "ekyc", "proses", "tahapan", "ocr", "validasi"]
    },
    {
        "title": "Keamanan Data dan Privacy",
        "content": """
        Sistem eKYC menerapkan standar keamanan tinggi untuk melindungi data personal:
        
        Enkripsi Data:
        - Data in transit: TLS 1.3 encryption
        - Data at rest: AES-256 encryption
        - Database encryption dengan key rotation
        
        Access Control:
        - Multi-factor authentication (MFA)
        - Role-based access control (RBAC)
        - Principle of least privilege
        - Session timeout dan monitoring
        
        Audit Trail:
        - Semua aktivitas dicatat dengan timestamp
        - Immutable audit logs
        - Regular security assessments
        - Compliance monitoring
        
        Data Retention:
        - Data disimpan sesuai regulasi (max 5 tahun)
        - Automatic data purging
        - Right to be forgotten (GDPR compliance)
        
        Compliance:
        - UU ITE Indonesia
        - Peraturan OJK tentang eKYC
        - ISO 27001 Information Security
        - SOC 2 Type II compliance
        
        Privacy Protection:
        - Data minimization principle
        - Purpose limitation
        - Consent management
        - Privacy by design
        
        Incident Response:
        - 24/7 security monitoring
        - Automated threat detection
        - Incident response team
        - Regular security training
        """,
        "category": "keamanan",
        "tags": ["keamanan", "privacy", "enkripsi", "compliance", "audit", "gdpr"]
    },
    {
        "title": "Troubleshooting Upload Dokumen",
        "content": """
        Panduan mengatasi masalah umum saat upload dokumen:
        
        Masalah: "File terlalu besar"
        Solusi:
        - Kompres gambar ke ukuran < 10MB
        - Gunakan format JPG dengan kualitas 80-90%
        - Crop bagian yang tidak perlu
        
        Masalah: "Gambar tidak jelas/blur"
        Solusi:
        - Gunakan pencahayaan yang cukup
        - Hindari bayangan dan silau
        - Pegang kamera dengan stabil
        - Jarak optimal 20-30cm dari dokumen
        
        Masalah: "OCR tidak bisa membaca teks"
        Solusi:
        - Pastikan dokumen dalam posisi lurus
        - Hindari dokumen yang terlipat atau rusak
        - Gunakan background kontras (dokumen di atas kertas putih)
        - Resolusi minimal 300 DPI
        
        Masalah: "Format file tidak didukung"
        Solusi:
        - Gunakan format: JPG, PNG, atau PDF
        - Konversi file ke format yang didukung
        - Hindari format eksotis atau terkompresi berlebihan
        
        Masalah: "Dokumen ditolak sistem"
        Solusi:
        - Pastikan dokumen masih berlaku
        - Cek kelengkapan data pada dokumen
        - Pastikan foto terlihat jelas dan tidak terpotong
        - Hubungi customer service jika masalah berlanjut
        
        Tips untuk hasil terbaik:
        - Foto di tempat terang dengan cahaya merata
        - Letakkan dokumen di permukaan datar
        - Pastikan semua sudut dokumen terlihat
        - Hindari penggunaan flash yang berlebihan
        - Bersihkan lensa kamera sebelum memotret
        """,
        "category": "troubleshooting",
        "tags": ["troubleshooting", "upload", "ocr", "kualitas_gambar", "panduan"]
    },
    {
        "title": "API dan Integrasi Sistem",
        "content": """
        Dokumentasi API untuk integrasi sistem eKYC:
        
        Base URL: https://api.ekyc.example.com/v1
        
        Authentication:
        - API Key dalam header: X-API-Key
        - JWT Token untuk user authentication
        - Rate limiting: 100 requests/minute
        
        Endpoints Utama:
        
        1. Upload Dokumen
        POST /documents/upload
        Headers: Content-Type: multipart/form-data
        Body: file (binary), document_type (string)
        Response: {"document_id": "uuid", "status": "uploaded"}
        
        2. Analisis Dokumen
        POST /documents/{document_id}/analyze
        Response: {
          "confidence_score": 0.95,
          "verification_status": "VERIFIED",
          "extracted_fields": {...},
          "processing_time": 1.2
        }
        
        3. Status Verifikasi
        GET /documents/{document_id}/status
        Response: {
          "status": "completed",
          "result": "approved",
          "created_at": "2024-01-01T10:00:00Z"
        }
        
        4. Batch Processing
        POST /documents/batch
        Body: {"document_ids": ["uuid1", "uuid2"]}
        Response: {"batch_id": "uuid", "status": "processing"}
        
        Webhook Events:
        - document.uploaded
        - document.processed
        - document.verified
        - document.rejected
        
        Error Codes:
        - 400: Invalid request format
        - 401: Authentication failed
        - 403: Access denied
        - 429: Rate limit exceeded
        - 500: Internal server error
        
        SDK tersedia untuk:
        - Python
        - Node.js
        - PHP
        - Java
        - .NET
        """,
        "category": "integrasi",
        "tags": ["api", "integrasi", "sdk", "webhook", "dokumentasi"]
    },
    {
        "title": "Regulasi dan Compliance eKYC",
        "content": """
        Kerangka regulasi yang mengatur implementasi eKYC di Indonesia:
        
        Peraturan Bank Indonesia (PBI):
        - PBI No. 18/40/PBI/2016 tentang Prinsip Kehati-hatian dalam Layanan Keuangan Digital
        - Ketentuan tentang identifikasi nasabah secara elektronik
        - Requirement untuk verifikasi multi-level
        
        Peraturan OJK:
        - POJK No. 12/POJK.03/2018 tentang Layanan Keuangan Digital
        - Standar eKYC untuk institusi keuangan
        - Risk-based approach dalam customer due diligence
        
        UU ITE dan Perlindungan Data:
        - UU No. 11 Tahun 2008 tentang Informasi dan Transaksi Elektronik
        - Kewajiban perlindungan data personal
        - Sanksi pelanggaran privacy
        
        Peraturan Dukcapil:
        - Ketentuan tentang penggunaan data kependudukan
        - API integration dengan sistem Dukcapil
        - Verifikasi silang dengan database resmi
        
        Standar Internasional:
        - FATF Recommendations untuk AML/CFT
        - Basel III customer identification requirements
        - ISO 27001 untuk information security management
        
        Level Verifikasi eKYC:
        
        Level 1 (Basic):
        - Verifikasi dokumen identitas basic
        - Limit transaksi rendah (< Rp 20 juta/bulan)
        - Suitable untuk e-wallet, payment gateway
        
        Level 2 (Enhanced):
        - Verifikasi dokumen + selfie/liveness detection
        - Limit transaksi menengah (< Rp 200 juta/bulan)
        - Untuk digital banking, investment platform
        
        Level 3 (Premium):
        - Multi-document verification
        - Video call verification
        - No transaction limit
        - Untuk high-value financial services
        
        Compliance Requirements:
        - Customer Due Diligence (CDD)
        - Enhanced Due Diligence (EDD) untuk high-risk customers
        - Ongoing monitoring dan transaction screening
        - Suspicious Transaction Reporting (STR)
        """,
        "category": "regulasi",
        "tags": ["regulasi", "compliance", "ojk", "bi", "uu_ite", "level_verifikasi"]
    }
]

async def main():
    """Main function untuk menjalankan script"""
    print("🚀 Knowledge Base Management Script")
    print("=" * 50)
    
    try:
        # Initialize knowledge manager
        print("Initializing knowledge manager...")
        km = KnowledgeManager()
        
        # Menu pilihan
        print("\nPilih aksi:")
        print("1. Tambah knowledge base default eKYC")
        print("2. Tambah knowledge manual")
        print("3. Exit")
        
        choice = input("\nMasukkan pilihan (1-3): ").strip()
        
        if choice == "1":
            print(f"\nMenambahkan {len(EKYC_KNOWLEDGE_BASE)} knowledge entries...")
            results = await km.add_knowledge_from_dict(EKYC_KNOWLEDGE_BASE)
            
            # Summary results
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            print(f"\n📊 Summary:")
            print(f"✅ Berhasil: {success_count}/{total_count}")
            print(f"❌ Gagal: {total_count - success_count}/{total_count}")
            
            if success_count > 0:
                print("\n✅ Knowledge base berhasil ditambahkan ke RAG system!")
                print("Sekarang sistem dapat menjawab pertanyaan tentang:")
                for entry in EKYC_KNOWLEDGE_BASE:
                    print(f"  - {entry['title']}")
            
        elif choice == "2":
            print("\nMasukkan knowledge baru:")
            title = input("Title: ").strip()
            category = input("Category: ").strip()
            tags_input = input("Tags (pisah dengan koma): ").strip()
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
            
            print("\nMasukkan content (ketik 'END' pada baris terpisah untuk selesai):")
            content_lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                content_lines.append(line)
            
            content = "\n".join(content_lines)
            
            if title and content:
                entry = km.create_knowledge_entry(title, content, category, tags)
                success = await km.add_single_knowledge(entry)
                
                if success:
                    print(f"✅ Knowledge '{title}' berhasil ditambahkan!")
                else:
                    print(f"❌ Gagal menambahkan knowledge '{title}'")
            else:
                print("❌ Title dan content tidak boleh kosong!")
        
        elif choice == "3":
            print("👋 Goodbye!")
            return
        
        else:
            print("❌ Pilihan tidak valid!")
    
    except KeyboardInterrupt:
        print("\n\n👋 Script dihentikan oleh user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
