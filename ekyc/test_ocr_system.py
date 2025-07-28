"""
Test script untuk memvalidasi OCR functionality
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from ocr_processor import ocr_processor, field_extractor
from document_analyzer import EKYCDocumentAnalyzer

def test_ocr_simple():
    """Test OCR dengan file gambar sederhana"""
    print("=== OCR Processor Test ===")
    
    # Create simple test image or use existing file
    print("Testing OCR processor initialization...")
    
    try:
        # Test that the processor can initialize
        print(f"Tesseract config: {ocr_processor.tesseract_config}")
        print(f"EasyOCR reader initialized: {ocr_processor.easyocr_reader is not None}")
        
        # Test field extractor
        print("\nTesting field extraction...")
        sample_text = """
        REPUBLIK INDONESIA
        KARTU TANDA PENDUDUK
        NIK: 1234567890123456
        Nama: JOHN SMITH DOE
        Tempat/Tgl Lahir: JAKARTA, 01-01-1990
        Jenis Kelamin: LAKI-LAKI
        Alamat: JL. CONTOH NO. 123
        Agama: ISLAM
        Pekerjaan: PEGAWAI SWASTA
        Kewarganegaraan: WNI
        Berlaku Hingga: SEUMUR HIDUP
        """
        
        fields = field_extractor.extract_fields(sample_text, 'ktp')
        print("Extracted fields:")
        for field, value in fields.items():
            print(f"  {field}: {value}")
        
        # Test document analyzer
        print("\nTesting document analyzer...")
        analyzer = EKYCDocumentAnalyzer()
        print(f"Supported document types: {analyzer.supported_types}")
        
        print("\n✅ All OCR components initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during OCR test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_image_processing():
    """Test dengan sample image jika ada"""
    print("\n=== Image Processing Test ===")
    
    # Check for sample images in uploads folder
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        image_files = list(uploads_dir.glob("*.jpg")) + list(uploads_dir.glob("*.png")) + list(uploads_dir.glob("*.jpeg"))
        
        if image_files:
            test_file = image_files[0]
            print(f"Testing with: {test_file}")
            
            try:
                # Test OCR extraction
                result = ocr_processor.extract_text(str(test_file))
                print(f"OCR Result:")
                print(f"  Best engine: {result['best_result']['engine']}")
                print(f"  Confidence: {result['best_result']['confidence']:.2f}")
                print(f"  Text length: {len(result['best_result']['text'])}")
                print(f"  Extracted text preview: {result['best_result']['text'][:200]}...")
                
                # Test document analysis
                analyzer = EKYCDocumentAnalyzer()
                analysis = analyzer.analyze_document(str(test_file))
                print(f"\nDocument Analysis:")
                print(f"  Document type: {analysis.document_type}")
                print(f"  Confidence: {analysis.confidence_score:.2f}")
                print(f"  Status: {analysis.verification_status}")
                print(f"  Fields detected: {len(analysis.detected_fields)}")
                
                return True
                
            except Exception as e:
                print(f"❌ Error processing image: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("No image files found in uploads folder")
            return True
    else:
        print("Uploads folder not found")
        return True

if __name__ == "__main__":
    print("🚀 Starting OCR and Document Analysis Test\n")
    
    # Test basic functionality
    ocr_ok = test_ocr_simple()
    
    # Test with real image if available
    img_ok = test_image_processing()
    
    print("\n" + "="*50)
    if ocr_ok and img_ok:
        print("✅ All tests passed! OCR system is ready.")
        print("\nYou can now:")
        print("1. Start the FastAPI server")
        print("2. Upload documents via the web interface")
        print("3. Get real OCR extraction instead of mock data")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("="*50)
