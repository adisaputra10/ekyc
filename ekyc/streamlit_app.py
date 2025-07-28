"""
Streamlit Web App untuk eKYC System
Alternative interface menggunakan Streamlit
"""
import streamlit as st
import os
import uuid
from datetime import datetime
from models import EKYCFormData, PersonalInfo, Address, ContactInfo, DocumentSubmission, DocumentType, Gender
from document_generator import EKYCDocumentGenerator
from document_analyzer import EKYCDocumentAnalyzer

# Setup page
st.set_page_config(
    page_title="eKYC System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    return EKYCDocumentGenerator(), EKYCDocumentAnalyzer()

def main():
    st.title("🏛️ eKYC System")
    st.subheader("Electronic Know Your Customer - Sistem Verifikasi Identitas Digital")
    
    generator, analyzer = init_components()
    
    # Sidebar for navigation
    st.sidebar.title("📋 Menu")
    page = st.sidebar.selectbox("Pilih Halaman", [
        "Formulir eKYC",
        "Analisa Dokumen",
        "Tentang Sistem"
    ])
    
    if page == "Formulir eKYC":
        show_ekyc_form(generator, analyzer)
    elif page == "Analisa Dokumen":
        show_document_analysis(analyzer)
    else:
        show_about()

def show_ekyc_form(generator, analyzer):
    st.header("📝 Formulir eKYC")
    
    with st.form("ekyc_form"):
        # Personal Information
        st.subheader("👤 Informasi Personal")
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Nama Lengkap *", key="full_name")
            id_number = st.text_input("NIK (16 digit) *", key="id_number", max_chars=16)
            birth_place = st.text_input("Tempat Lahir *", key="birth_place")
            birth_date = st.date_input("Tanggal Lahir *", key="birth_date")
        
        with col2:
            gender = st.selectbox("Jenis Kelamin *", ["laki-laki", "perempuan"], key="gender")
            religion = st.selectbox("Agama *", [
                "Islam", "Kristen", "Katolik", "Hindu", "Buddha", "Konghucu"
            ], key="religion")
            marital_status = st.selectbox("Status Perkawinan *", [
                "Belum Kawin", "Kawin", "Cerai Hidup", "Cerai Mati"
            ], key="marital_status")
            occupation = st.text_input("Pekerjaan *", key="occupation")
        
        # Address
        st.subheader("🏠 Alamat")
        col1, col2 = st.columns(2)
        
        with col1:
            street = st.text_area("Alamat Jalan *", key="street")
            rt_rw = st.text_input("RT/RW *", key="rt_rw", placeholder="001/002")
            village = st.text_input("Kelurahan/Desa *", key="village")
            district = st.text_input("Kecamatan *", key="district")
        
        with col2:
            city = st.text_input("Kota/Kabupaten *", key="city")
            province = st.text_input("Provinsi *", key="province")
            postal_code = st.text_input("Kode Pos *", key="postal_code", max_chars=5)
            st.write("")  # spacer
        
        # Contact
        st.subheader("📞 Informasi Kontak")
        col1, col2 = st.columns(2)
        
        with col1:
            phone = st.text_input("Nomor Telepon *", key="phone")
            email = st.text_input("Email *", key="email")
        
        with col2:
            emergency_contact_name = st.text_input("Nama Kontak Darurat *", key="emergency_contact_name")
            emergency_contact_phone = st.text_input("Telepon Kontak Darurat *", key="emergency_contact_phone")
        
        # Documents
        st.subheader("📄 Dokumen Identitas")
        col1, col2 = st.columns(2)
        
        with col1:
            document_type = st.selectbox("Jenis Dokumen *", [
                "ktp", "passport", "sim", "npwp"
            ], key="document_type")
            document_number = st.text_input("Nomor Dokumen *", key="document_number")
            issued_date = st.date_input("Tanggal Terbit *", key="issued_date")
        
        with col2:
            expiry_date = st.date_input("Tanggal Berakhir", key="expiry_date", value=None)
            issuing_authority = st.text_input("Instansi Penerbit *", key="issuing_authority")
            st.write("")  # spacer
        
        # File uploads
        st.subheader("📷 Upload Dokumen")
        col1, col2 = st.columns(2)
        
        with col1:
            selfie = st.file_uploader("Foto Selfie", type=['jpg', 'jpeg', 'png'], key="selfie")
        
        with col2:
            document_image = st.file_uploader("Foto Dokumen Identitas", type=['jpg', 'jpeg', 'png'], key="document_image")
        
        # Submit button
        submitted = st.form_submit_button("🚀 Submit eKYC Form", type="primary")
        
        if submitted:
            # Validate required fields
            required_fields = [
                full_name, id_number, birth_place, gender, religion, 
                marital_status, occupation, street, rt_rw, village, 
                district, city, province, postal_code, phone, email,
                emergency_contact_name, emergency_contact_phone,
                document_type, document_number, issuing_authority
            ]
            
            if not all(required_fields):
                st.error("❌ Mohon lengkapi semua field yang bertanda *")
                return
            
            # Validate NIK format
            if len(id_number) != 16 or not id_number.isdigit():
                st.error("❌ NIK harus 16 digit angka")
                return
            
            try:
                # Create form data
                personal_info = PersonalInfo(
                    full_name=full_name,
                    id_number=id_number,
                    birth_place=birth_place,
                    birth_date=birth_date.strftime("%d/%m/%Y"),
                    gender=Gender(gender),
                    religion=religion,
                    marital_status=marital_status,
                    occupation=occupation,
                    nationality="Indonesia"
                )
                
                address = Address(
                    street=street,
                    rt_rw=rt_rw,
                    village=village,
                    district=district,
                    city=city,
                    province=province,
                    postal_code=postal_code
                )
                
                contact_info = ContactInfo(
                    phone=phone,
                    email=email,
                    emergency_contact_name=emergency_contact_name,
                    emergency_contact_phone=emergency_contact_phone
                )
                
                documents = [DocumentSubmission(
                    document_type=DocumentType(document_type),
                    document_number=document_number,
                    issued_date=issued_date.strftime("%d/%m/%Y"),
                    expiry_date=expiry_date.strftime("%d/%m/%Y") if expiry_date else None,
                    issuing_authority=issuing_authority
                )]
                
                form_data = EKYCFormData(
                    personal_info=personal_info,
                    address=address,
                    contact_info=contact_info,
                    documents=documents
                )
                
                # Save uploaded files
                os.makedirs("streamlit_uploads", exist_ok=True)
                os.makedirs("streamlit_outputs", exist_ok=True)
                
                file_id = str(uuid.uuid4())
                selfie_path = None
                document_path = None
                
                if selfie:
                    selfie_path = f"streamlit_uploads/{file_id}_selfie_{selfie.name}"
                    with open(selfie_path, "wb") as f:
                        f.write(selfie.getbuffer())
                    form_data.photo_selfie_path = selfie_path
                
                if document_image:
                    document_path = f"streamlit_uploads/{file_id}_document_{document_image.name}"
                    with open(document_path, "wb") as f:
                        f.write(document_image.getbuffer())
                
                # Generate PDF
                pdf_path = f"streamlit_outputs/ekyc_{file_id}.pdf"
                verification_code = generator.generate_document(form_data, pdf_path)
                
                # Analyze document if uploaded
                analysis_result = None
                if document_path:
                    analysis_result = analyzer.analyze_document(document_path, selfie_path)
                
                # Show results
                st.success("✅ Formulir eKYC berhasil diproses!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"🔑 Kode Verifikasi: **{verification_code}**")
                
                with col2:
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_file.read(),
                                file_name=f"ekyc_{verification_code}.pdf",
                                mime="application/pdf"
                            )
                
                # Show analysis results
                if analysis_result:
                    st.subheader("🔍 Hasil Analisa Dokumen")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Jenis Dokumen", analysis_result.document_type.upper())
                    with col2:
                        st.metric("Confidence Score", f"{analysis_result.confidence_score*100:.1f}%")
                    with col3:
                        if analysis_result.face_match_score:
                            st.metric("Face Match", f"{analysis_result.face_match_score*100:.1f}%")
                    
                    if analysis_result.verification_status == "verified":
                        st.success("✅ Dokumen terverifikasi")
                    elif analysis_result.verification_status == "requires_review":
                        st.warning("⚠️ Dokumen perlu review")
                    else:
                        st.error("❌ Dokumen ditolak")
                    
                    if analysis_result.issues_found:
                        st.warning("⚠️ Issues ditemukan:")
                        for issue in analysis_result.issues_found:
                            st.write(f"• {issue}")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_document_analysis(analyzer):
    st.header("🔍 Analisa Dokumen")
    st.write("Upload dokumen identitas untuk dianalisa menggunakan AI")
    
    document = st.file_uploader("Pilih foto dokumen identitas", type=['jpg', 'jpeg', 'png'])
    selfie = st.file_uploader("Pilih foto selfie (opsional)", type=['jpg', 'jpeg', 'png'])
    expected_doc_type = st.selectbox("Jenis dokumen yang diharapkan", [
        "auto-detect", "ktp", "passport", "sim", "npwp"
    ])
    
    if st.button("🔎 Analisa Dokumen") and document:
        try:
            # Save files temporarily
            os.makedirs("temp_analysis", exist_ok=True)
            
            doc_path = f"temp_analysis/doc_{document.name}"
            with open(doc_path, "wb") as f:
                f.write(document.getbuffer())
            
            selfie_path = None
            if selfie:
                selfie_path = f"temp_analysis/selfie_{selfie.name}"
                with open(selfie_path, "wb") as f:
                    f.write(selfie.getbuffer())
            
            # Analyze
            expected_type = None if expected_doc_type == "auto-detect" else expected_doc_type
            result = analyzer.analyze_document(doc_path, selfie_path, expected_type)
            
            # Show results
            st.subheader("📊 Hasil Analisa")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Jenis Dokumen", result.document_type.upper())
            with col2:
                st.metric("Confidence Score", f"{result.confidence_score*100:.1f}%")
            with col3:
                if result.face_match_score:
                    st.metric("Face Match", f"{result.face_match_score*100:.1f}%")
            
            # Status
            if result.verification_status == "verified":
                st.success("✅ Dokumen terverifikasi")
            elif result.verification_status == "requires_review":
                st.warning("⚠️ Dokumen perlu review")
            else:
                st.error("❌ Dokumen ditolak")
            
            # Extracted text
            with st.expander("📝 Text yang diekstrak"):
                st.text(result.extracted_text)
            
            # Issues and recommendations
            if result.issues_found:
                st.warning("⚠️ Issues ditemukan:")
                for issue in result.issues_found:
                    st.write(f"• {issue}")
            
            if result.recommendations:
                st.info("💡 Rekomendasi:")
                for rec in result.recommendations:
                    st.write(f"• {rec}")
            
            # Cleanup
            os.remove(doc_path)
            if selfie_path and os.path.exists(selfie_path):
                os.remove(selfie_path)
                
        except Exception as e:
            st.error(f"❌ Error dalam analisa: {str(e)}")

def show_about():
    st.header("ℹ️ Tentang Sistem eKYC")
    
    st.write("""
    ## 🏛️ Electronic Know Your Customer (eKYC)
    
    Sistem eKYC ini adalah solusi digital untuk verifikasi identitas elektronik yang memungkinkan:
    
    ### ✨ Fitur Utama:
    - 📝 **Form eKYC Digital**: Input data personal, alamat, dan kontak
    - 📄 **Generate Dokumen PDF**: Membuat dokumen eKYC dalam format PDF dengan QR code
    - 🔍 **Analisa Dokumen AI**: Menggunakan OCR dan LLM untuk analisa dokumen identitas
    - 👤 **Face Recognition**: Perbandingan wajah antara selfie dan foto dokumen
    - ✅ **Verifikasi Otomatis**: Status verifikasi berdasarkan confidence score
    
    ### 🔧 Teknologi yang Digunakan:
    - **Backend**: FastAPI, Python
    - **Frontend**: HTML/CSS, Streamlit
    - **Document Processing**: ReportLab, FPDF
    - **Computer Vision**: OpenCV, Tesseract OCR, Face Recognition
    - **AI Analysis**: OpenAI GPT, LangChain
    - **Database**: Pydantic Models
    
    ### 📋 Jenis Dokumen yang Didukung:
    - 🆔 KTP (Kartu Tanda Penduduk)
    - 🛂 Paspor Indonesia
    - 🚗 SIM (Surat Izin Mengemudi)
    - 💼 NPWP (Nomor Pokok Wajib Pajak)
    
    ### 🔒 Keamanan:
    - File upload dengan validasi tipe
    - Kode verifikasi unik untuk setiap dokumen
    - QR code untuk verifikasi dokumen
    - Confidence scoring untuk akurasi
    
    ### 💡 Cara Penggunaan:
    1. Isi formulir eKYC dengan data lengkap
    2. Upload foto selfie dan dokumen identitas
    3. Submit form untuk generate PDF dan analisa
    4. Download dokumen PDF yang telah dibuat
    5. Review hasil analisa AI untuk verifikasi
    """)
    
    st.divider()
    
    st.subheader("👨‍💻 Developer Information")
    st.write("""
    Sistem ini dikembangkan menggunakan Python dengan berbagai library untuk 
    document processing, computer vision, dan artificial intelligence.
    
    **Status**: Development Version  
    **Last Updated**: July 2025
    """)

if __name__ == "__main__":
    main()
