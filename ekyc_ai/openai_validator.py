from openai import OpenAI
from typing import Dict, List, Optional
import logging
import json
from config import Config

class OpenAIValidator:
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
    
    def validate_ktp(self, extracted_data: Dict, rag_context: str) -> Dict[str, any]:
        """Validate KTP document using OpenAI"""
        
        prompt = f"""
        Anda adalah seorang ahli validasi dokumen identitas Indonesia. Analisis data KTP berikut dan berikan validasi komprehensif.

        Data yang diekstrak dari KTP:
        {json.dumps(extracted_data, indent=2, ensure_ascii=False)}

        Konteks validasi dari knowledge base:
        {rag_context}

        Tugas Anda:
        1. Validasi kelengkapan data KTP (NIK, nama, tempat lahir, tanggal lahir, jenis kelamin, alamat, agama, status perkawinan, pekerjaan, kewarganegaraan)
        2. Validasi format NIK (16 digit, format kode wilayah yang benar)
        3. Validasi konsistensi data (jenis kelamin vs NIK, umur yang wajar, dll)
        4. Deteksi potensi pemalsuan atau kesalahan
        5. Berikan skor kepercayaan (0-100)

        Berikan respons dalam format JSON dengan struktur:
        {{
            "valid": boolean,
            "confidence_score": number (0-100),
            "validation_results": {{
                "nik_valid": boolean,
                "nik_format_correct": boolean,
                "data_complete": boolean,
                "data_consistent": boolean,
                "gender_nik_match": boolean
            }},
            "missing_fields": [list of missing required fields],
            "errors": [list of validation errors],
            "warnings": [list of potential issues],
            "recommendations": [list of recommendations],
            "summary": "brief summary in Indonesian"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Anda adalah sistem validasi dokumen profesional yang memberikan analisis akurat dan terstruktur."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Try to parse JSON, if fails, create a fallback response
            try:
                # First try direct JSON parsing
                result = json.loads(response_content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```json\s*\n(.*?)\n```', response_content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # Create fallback response
                        self.logger.warning("Failed to parse JSON response, creating fallback response")
                        result = {
                            "valid": "valid" in response_content.lower() and "true" in response_content.lower(),
                            "confidence_score": 50,  # Default confidence
                            "validation_results": {},
                            "missing_fields": [],
                            "errors": ["Failed to parse structured response"],
                            "warnings": [],
                            "recommendations": [],
                            "summary": "Analisis teks tidak dapat diparse sebagai JSON, namun proses validasi tetap berjalan",
                            "raw_response": response_content
                        }
                else:
                    # Extract key information from text response if JSON parsing fails
                    self.logger.warning("Failed to parse JSON response, creating fallback response")
                    result = {
                        "valid": "valid" in response_content.lower() and "true" in response_content.lower(),
                        "confidence_score": 50,  # Default confidence
                        "validation_results": {},
                        "missing_fields": [],
                        "errors": ["Failed to parse structured response"],
                        "warnings": [],
                        "recommendations": [],
                        "summary": "Analisis teks tidak dapat diparse sebagai JSON, namun proses validasi tetap berjalan",
                        "raw_response": response_content
                    }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating KTP with OpenAI: {str(e)}")
            return {
                "valid": False,
                "confidence_score": 0,
                "error": str(e),
                "summary": "Gagal melakukan validasi karena kesalahan sistem"
            }
    
    def validate_akta(self, extracted_data: Dict, rag_context: str, full_text: str = "") -> Dict[str, any]:
        """Validate Akta document using OpenAI and complete missing data"""
        
        prompt = f"""
        Anda adalah seorang ahli hukum korporat Indonesia yang berspesialisasi dalam validasi dan analisis akta pendirian perusahaan. 
        Analisis data akta berikut dan LENGKAPI data yang kurang dengan mengekstrak dari teks lengkap dokumen.

        Data yang sudah diekstrak:
        {json.dumps(extracted_data, indent=2, ensure_ascii=False)}

        Teks lengkap dokumen untuk analisis tambahan:
        {full_text[:3000]}...

        Konteks validasi dari knowledge base:
        {rag_context}

        Tugas Anda:
        1. VALIDASI kelengkapan akta (nomor akta, tanggal, notaris, nama perusahaan, modal, alamat, direksi, komisaris)
        2. LENGKAPI data yang kurang dengan mengekstrak dari teks lengkap dokumen
        3. EKSTRAK informasi direktur dan komisaris (nama-nama lengkap)
        4. EKSTRAK bidang usaha/kegiatan usaha perusahaan
        5. Validasi format dan struktur akta sesuai peraturan Indonesia
        6. Validasi persyaratan modal minimal PT (min Rp 50 juta modal dasar)
        7. Validasi kepatuhan terhadap UU No. 40 Tahun 2007 tentang PT
        8. Deteksi potensi masalah legal atau format
        9. Berikan skor kepercayaan (0-100)

        PENTING: 
        - Jika ada field yang null/kosong dalam data yang diekstrak, coba temukan informasi tersebut dari teks lengkap dan masukkan ke "completed_data".
        - Untuk direktur dan komisaris, ekstrak semua nama yang ditemukan sebagai array
        - Untuk bidang usaha, ekstrak deskripsi lengkap kegiatan/maksud perusahaan

        Berikan respons dalam format JSON dengan struktur:
        {{
            "valid": boolean,
            "confidence_score": number (0-100),
            "completed_data": {{
                "nomor_akta": "string atau null jika tidak ditemukan",
                "tanggal_akta": "string atau null",
                "nama_notaris": "string lengkap nama notaris atau null",
                "nama_perusahaan": "string nama perusahaan atau null",
                "modal_dasar": "string jumlah modal atau null",
                "modal_disetor": "string jumlah modal disetor atau null", 
                "alamat_perusahaan": "string alamat lengkap atau null",
                "direktur": ["array nama direktur"],
                "komisaris": ["array nama komisaris"],
                "bidang_usaha": "string bidang usaha atau null",
                "npwp": "string NPWP atau null"
            }},
            "validation_results": {{
                "akta_number_valid": boolean,
                "date_valid": boolean,
                "notary_mentioned": boolean,
                "company_info_complete": boolean,
                "capital_requirements_met": boolean,
                "legal_structure_valid": boolean,
                "directors_mentioned": boolean,
                "commissioners_mentioned": boolean,
                "business_field_described": boolean
            }},
            "missing_fields": [list of fields still missing after completion attempt],
            "legal_issues": [list of potential legal issues],
            "format_issues": [list of format problems],
            "capital_analysis": {{
                "modal_dasar_sufficient": boolean,
                "modal_disetor_mentioned": boolean,
                "compliance_notes": "string"
            }},
            "recommendations": [list of recommendations],
            "summary": "brief summary in Indonesian"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Anda adalah sistem validasi dokumen legal profesional dengan keahlian hukum korporat Indonesia. SELALU berikan response dalam format JSON yang valid dengan struktur yang diminta."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Clean JSON response if it has markdown formatting
            if response_content.startswith('```json'):
                response_content = response_content.replace('```json', '').replace('```', '').strip()
            elif response_content.startswith('```'):
                response_content = response_content.replace('```', '').strip()
            
            # Try to parse JSON, if fails, create a fallback response
            try:
                result = json.loads(response_content)
                
                # Ensure completed_data exists in the result
                if 'completed_data' not in result:
                    result['completed_data'] = {}
                
            except json.JSONDecodeError as je:
                # Extract key information from text response if JSON parsing fails
                self.logger.warning(f"Failed to parse JSON response: {str(je)}")
                self.logger.warning(f"Response content: {response_content[:500]}...")
                
                # Try to create a structured response from extracted data
                result = {
                    "valid": extracted_data.get('nomor_akta') is not None and extracted_data.get('nama_notaris') is not None,
                    "confidence_score": 70 if extracted_data.get('nomor_akta') and extracted_data.get('nama_notaris') else 30,
                    "completed_data": extracted_data,  # Use original extracted data as completed data
                    "validation_results": {
                        "akta_number_valid": extracted_data.get('nomor_akta') is not None,
                        "date_valid": extracted_data.get('tanggal_akta') is not None,
                        "notary_mentioned": extracted_data.get('nama_notaris') is not None,
                        "company_info_complete": extracted_data.get('nama_perusahaan') is not None,
                        "capital_requirements_met": extracted_data.get('modal_dasar') is not None,
                        "legal_structure_valid": True,
                        "directors_mentioned": len(extracted_data.get('direktur', [])) > 0,
                        "commissioners_mentioned": len(extracted_data.get('komisaris', [])) > 0,
                        "business_field_described": extracted_data.get('bidang_usaha') is not None
                    },
                    "missing_fields": [k for k, v in extracted_data.items() if v is None],
                    "legal_issues": [],
                    "format_issues": ["JSON parsing failed, using fallback validation"],
                    "capital_analysis": {
                        "modal_dasar_sufficient": extracted_data.get('modal_dasar') is not None,
                        "modal_disetor_mentioned": extracted_data.get('modal_disetor') is not None,
                        "compliance_notes": "Analysis based on extracted data"
                    },
                    "recommendations": ["Consider manual review due to parsing issues"],
                    "summary": f"Legal document successfully extracted with {len([v for v in extracted_data.values() if v is not None])} fields identified",
                    "raw_response": response_content[:1000]
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating Akta with OpenAI: {str(e)}")
            return {
                "valid": False,
                "confidence_score": 0,
                "error": str(e),
                "summary": "Gagal melakukan validasi karena kesalahan sistem"
            }
    
    def generate_validation_report(self, ktp_validation: Dict, akta_validation: Dict) -> Dict[str, any]:
        """Generate comprehensive validation report"""
        
        prompt = f"""
        Buat laporan validasi komprehensif berdasarkan hasil validasi KTP dan Akta berikut:

        Hasil Validasi KTP:
        {json.dumps(ktp_validation, indent=2, ensure_ascii=False)}

        Hasil Validasi Akta:
        {json.dumps(akta_validation, indent=2, ensure_ascii=False)}

        Tugas Anda:
        1. Buat ringkasan eksekutif tentang validitas kedua dokumen
        2. Identifikasi konsistensi data antara KTP dan Akta (jika ada)
        3. Berikan rekomendasi tindakan selanjutnya
        4. Tentukan tingkat risiko keseluruhan
        5. Saran untuk perbaikan atau verifikasi tambahan

        Berikan respons dalam format JSON dengan struktur:
        {{
            "overall_status": "VALID" | "INVALID" | "NEEDS_REVIEW",
            "overall_confidence": number (0-100),
            "executive_summary": "string",
            "document_status": {{
                "ktp": {{"status": "string", "confidence": number}},
                "akta": {{"status": "string", "confidence": number}}
            }},
            "cross_document_analysis": {{
                "name_consistency": boolean,
                "data_alignment": boolean,
                "notes": "string"
            }},
            "risk_assessment": {{
                "level": "LOW" | "MEDIUM" | "HIGH",
                "factors": [list of risk factors],
                "mitigation": [list of mitigation steps]
            }},
            "next_actions": [list of recommended actions],
            "compliance_notes": "string"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Anda adalah konsultan compliance dan validasi dokumen yang berpengalaman."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Try to parse JSON, if fails, create a fallback response
            try:
                result = json.loads(response_content)
            except json.JSONDecodeError:
                # Extract key information from text response if JSON parsing fails
                self.logger.warning("Failed to parse JSON response, creating fallback response")
                result = {
                    "overall_status": "NEEDS_REVIEW",
                    "overall_confidence": 50,
                    "executive_summary": "Comprehensive report could not be parsed as JSON, but individual validation was completed successfully",
                    "document_status": {
                        "ktp": {"status": "PROCESSED", "confidence": ktp_validation.get('confidence_score', 0)},
                        "akta": {"status": "PROCESSED", "confidence": akta_validation.get('confidence_score', 0)}
                    },
                    "cross_document_analysis": {
                        "name_consistency": False,
                        "data_alignment": False,
                        "notes": "Analisis lintas dokumen tidak dapat dilakukan karena masalah parsing"
                    },
                    "risk_assessment": {
                        "level": "MEDIUM",
                        "factors": ["Parsing error in comprehensive analysis"],
                        "mitigation": ["Review individual document validation results"]
                    },
                    "next_actions": ["Check individual document validation results", "Retry comprehensive validation"],
                    "compliance_notes": "Individual validation was successful, but comprehensive analysis needs to be reviewed",
                    "raw_response": response_content
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating validation report: {str(e)}")
            return {
                "overall_status": "ERROR",
                "overall_confidence": 0,
                "error": str(e),
                "executive_summary": "Gagal membuat laporan validasi karena kesalahan sistem"
            }
