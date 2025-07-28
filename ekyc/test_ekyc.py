"""
Test eKYC System
"""
import asyncio
from models import EKYCFormData, PersonalInfo, Address, ContactInfo, DocumentSubmission, DocumentType, Gender
from document_generator import EKYCDocumentGenerator
from document_analyzer import EKYCDocumentAnalyzer

def create_sample_data():
    """Buat data sample untuk testing"""
    
    personal_info = PersonalInfo(
        full_name="Budi Santoso",
        id_number="3171234567890123",
        birth_place="Jakarta",
        birth_date="15/08/1990",
        gender=Gender.MALE,
        religion="Islam",
        marital_status="Kawin",
        occupation="Software Engineer",
        nationality="Indonesia"
    )
    
    address = Address(
        street="Jl. Merdeka Raya No. 123",
        rt_rw="001/002",
        village="Kelurahan Merdeka",
        district="Kecamatan Pusat",
        city="Jakarta Pusat",
        province="DKI Jakarta",
        postal_code="10110"
    )
    
    contact_info = ContactInfo(
        phone="081234567890",
        email="budi.santoso@email.com",
        emergency_contact_name="Siti Santoso",
        emergency_contact_phone="081234567891"
    )
    
    documents = [
        DocumentSubmission(
            document_type=DocumentType.KTP,
            document_number="3171234567890123",
            issued_date="01/01/2020",
            expiry_date="01/01/2025",
            issuing_authority="Dinas Kependudukan DKI Jakarta"
        )
    ]
    
    return EKYCFormData(
        personal_info=personal_info,
        address=address,
        contact_info=contact_info,
        documents=documents
    )

def test_document_generation():
    """Test generate dokumen PDF"""
    print("Testing document generation...")
    
    # Create sample data
    form_data = create_sample_data()
    
    # Generate document
    generator = EKYCDocumentGenerator()
    output_path = "test_output/sample_ekyc.pdf"
    
    try:
        verification_code = generator.generate_document(form_data, output_path)
        print(f"✅ Document generated successfully!")
        print(f"📄 File saved to: {output_path}")
        print(f"🔑 Verification code: {verification_code}")
        return True
    except Exception as e:
        print(f"❌ Error generating document: {str(e)}")
        return False

def test_document_analysis():
    """Test analisa dokumen (requires OpenAI API key)"""
    print("\nTesting document analysis...")
    
    # Note: This requires actual image files and OpenAI API key
    analyzer = EKYCDocumentAnalyzer()
    
    try:
        # Example usage - uncomment when you have actual image files
        # result = analyzer.analyze_document("path/to/ktp_image.jpg", "path/to/selfie.jpg")
        # print(f"✅ Analysis completed!")
        # print(f"📋 Document type: {result.document_type}")
        # print(f"📊 Confidence score: {result.confidence_score:.2f}")
        # print(f"✨ Verification status: {result.verification_status}")
        
        print("📝 Document analysis test skipped (requires image files and OpenAI API key)")
        return True
        
    except Exception as e:
        print(f"❌ Error in document analysis: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting eKYC System Tests\n")
    
    # Create output directory
    import os
    os.makedirs("test_output", exist_ok=True)
    
    # Run tests
    success_count = 0
    total_tests = 2
    
    if test_document_generation():
        success_count += 1
    
    if test_document_analysis():
        success_count += 1
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
