"""
Pydantic Models untuk eKYC System
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class DocumentType(str, Enum):
    """Jenis dokumen identitas"""
    KTP = "ktp"
    SIM = "sim"
    PASSPORT = "passport"
    NPWP = "npwp"
    KARTU_KELUARGA = "kartu_keluarga"
    BPJS = "bpjs"
    SURAT_NIKAH = "surat_nikah"
    AKTA_LAHIR = "akta_lahir"
    AKTA_PERUSAHAAN = "akta_perusahaan"
    OTHER = "other"

class Gender(str, Enum):
    """Jenis kelamin"""
    MALE = "laki-laki"
    FEMALE = "perempuan"

class PersonalInfo(BaseModel):
    """Informasi Personal"""
    full_name: str = Field(..., description="Nama lengkap")
    nik: Optional[str] = Field(None, description="NIK (Nomor Induk Kependudukan)")
    birth_date: Optional[str] = Field(None, description="Tanggal lahir")
    birth_place: Optional[str] = Field(None, description="Tempat lahir")
    gender: Optional[Gender] = Field(None, description="Jenis kelamin")
    religion: Optional[str] = Field(None, description="Agama")
    marital_status: Optional[str] = Field(None, description="Status pernikahan")
    occupation: Optional[str] = Field(None, description="Pekerjaan")
    nationality: Optional[str] = Field(None, description="Kewarganegaraan")

class Address(BaseModel):
    """Informasi Alamat"""
    street: Optional[str] = Field(None, description="Jalan")
    rt_rw: Optional[str] = Field(None, description="RT/RW")
    village: Optional[str] = Field(None, description="Desa/Kelurahan")
    district: Optional[str] = Field(None, description="Kecamatan")
    city: Optional[str] = Field(None, description="Kota/Kabupaten")
    province: Optional[str] = Field(None, description="Provinsi")
    postal_code: Optional[str] = Field(None, description="Kode pos")
    full_address: Optional[str] = Field(None, description="Alamat lengkap")

class ContactInfo(BaseModel):
    """Informasi Kontak"""
    phone: Optional[str] = Field(None, description="Nomor telepon")
    email: Optional[str] = Field(None, description="Email")
    emergency_contact: Optional[str] = Field(None, description="Kontak darurat")

class CompanyInfo(BaseModel):
    """Informasi Perusahaan dari Akta"""
    company_name: Optional[str] = Field(None, description="Nama perusahaan")
    company_type: Optional[str] = Field(None, description="Jenis perusahaan (PT, CV, UD, dll)")
    registration_number: Optional[str] = Field(None, description="Nomor registrasi/akta")
    notary_name: Optional[str] = Field(None, description="Nama notaris")
    notary_number: Optional[str] = Field(None, description="Nomor notaris")
    establishment_date: Optional[str] = Field(None, description="Tanggal pendirian")
    capital_amount: Optional[str] = Field(None, description="Modal dasar")
    business_field: Optional[str] = Field(None, description="Bidang usaha")
    company_address: Optional[str] = Field(None, description="Alamat perusahaan")
    directors: Optional[List[str]] = Field(None, description="Daftar direktur/pengurus")
    shareholders: Optional[List[str]] = Field(None, description="Daftar pemegang saham")

class DocumentSubmission(BaseModel):
    """Data dokumen yang disubmit"""
    document_type: DocumentType
    file_name: str
    file_size: Optional[int] = None
    upload_date: Optional[datetime] = None
    file_path: Optional[str] = None

class AnalysisResult(BaseModel):
    """Hasil analisis dokumen"""
    document_type: str = Field(..., description="Jenis dokumen yang terdeteksi")
    confidence_score: float = Field(..., description="Skor kepercayaan deteksi")
    verification_status: str = Field(..., description="Status verifikasi")
    extracted_text: Optional[str] = Field(None, description="Teks yang diekstrak")
    detected_fields: Optional[Dict[str, Any]] = Field(None, description="Field yang terdeteksi")
    quality_score: Optional[float] = Field(None, description="Skor kualitas dokumen")
    anomalies: Optional[List[str]] = Field(None, description="Anomali yang terdeteksi")
    processing_time: Optional[float] = Field(None, description="Waktu pemrosesan")
    ocr_confidence: Optional[float] = Field(None, description="Confidence OCR")
    document_authenticity: Optional[str] = Field(None, description="Keaslian dokumen")
    
class EKYCFormData(BaseModel):
    """Data form eKYC lengkap"""
    # Informasi personal
    personal_info: PersonalInfo
    
    # Informasi alamat
    address: Address
    
    # Informasi kontak
    contact_info: ContactInfo
    
    # Dokumen yang disubmit
    documents: List[DocumentSubmission] = Field(default_factory=list)
    
    # Metadata
    submission_id: Optional[str] = Field(None, description="ID submission")
    submission_date: Optional[datetime] = Field(None, description="Tanggal submission")
    status: Optional[str] = Field("pending", description="Status aplikasi")
    notes: Optional[str] = Field(None, description="Catatan tambahan")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RAGQuery(BaseModel):
    """Query untuk RAG system"""
    query: str = Field(..., description="Pertanyaan atau query")
    document_type: Optional[str] = Field(None, description="Filter berdasarkan jenis dokumen")
    max_results: Optional[int] = Field(5, description="Maksimum hasil yang dikembalikan")
    include_context: Optional[bool] = Field(True, description="Sertakan konteks dalam respons")

class RAGResponse(BaseModel):
    """Respons dari RAG system"""
    answer: str = Field(..., description="Jawaban dari AI")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Sumber referensi")
    confidence: Optional[float] = Field(None, description="Tingkat kepercayaan jawaban")
    query_type: Optional[str] = Field(None, description="Jenis query")
    processing_time: Optional[float] = Field(None, description="Waktu pemrosesan")

class ChatMessage(BaseModel):
    """Pesan chat"""
    role: str = Field(..., description="Role: user atau assistant")
    content: str = Field(..., description="Isi pesan")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    
class ChatRequest(BaseModel):
    """Request untuk chat"""
    message: str = Field(..., description="Pesan dari user")
    conversation_id: Optional[str] = Field(None, description="ID percakapan")
    context: Optional[str] = Field(None, description="Konteks tambahan")

class ChatResponse(BaseModel):
    """Response dari chat"""
    message: str = Field(..., description="Pesan dari AI")
    conversation_id: str = Field(..., description="ID percakapan")
    timestamp: datetime = Field(default_factory=datetime.now)
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Sumber referensi")

class KnowledgeBaseEntry(BaseModel):
    """Entry dalam knowledge base"""
    title: str = Field(..., description="Judul entry")
    content: str = Field(..., description="Konten")
    category: Optional[str] = Field(None, description="Kategori")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
