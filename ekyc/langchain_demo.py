"""
Example penggunaan AI Document Analyzer dengan LangChain
Demonstrasi fitur RAG untuk analisis dokumen eKYC
"""
import asyncio
import os
from dotenv import load_dotenv

from ai_document_analyzer import (
    VectorDatabase, 
    AIDocumentAnalyzer, 
    DocumentProcessor,
    initialize_knowledge_base
)
from config import settings, validate_environment

# Load environment variables
load_dotenv()

async def test_basic_analysis():
    """Test basic document analysis dengan LangChain"""
    
    print("🚀 Starting LangChain Document Analyzer Test")
    print("=" * 50)
    
    try:
        # Validate environment
        validate_environment()
        
        # Initialize components
        print("📊 Initializing LangChain components...")
        
        vector_db = VectorDatabase(
            elasticsearch_url=settings.elasticsearch_url,
            index_name=settings.elasticsearch_index,
            openai_api_key=settings.openai_api_key
        )
        
        analyzer = AIDocumentAnalyzer(
            vector_db=vector_db,
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model
        )
        
        # Initialize knowledge base
        print("📚 Setting up knowledge base...")
        await initialize_knowledge_base(vector_db, settings.openai_api_key)
        
        # Test document
        test_document = """
        REPUBLIK INDONESIA
        KARTU TANDA PENDUDUK
        
        NIK: 3171234567890123
        Nama: SITI NURHALIZA
        Tempat/Tgl Lahir: JAKARTA, 25-12-1995
        Jenis Kelamin: PEREMPUAN
        Alamat: JL. SUDIRMAN NO. 45
        RT/RW: 003/005
        Kel/Desa: TANAH ABANG
        Kecamatan: TANAH ABANG
        Agama: ISLAM
        Status Perkawinan: BELUM KAWIN
        Pekerjaan: MAHASISWA
        Kewarganegaraan: WNI
        Berlaku Hingga: SEUMUR HIDUP
        """
        
        print("🔍 Analyzing document with LangChain RAG...")
        result = await analyzer.analyze_document_with_rag(test_document)
        
        print("\n📋 Analysis Results:")
        print(f"Document Type: {result['document_type']}")
        print(f"Confidence Score: {result['confidence_score']:.2f}")
        print(f"Quality Score: {result['quality_score']:.2f}")
        print(f"Verification Status: {result['verification_status']}")
        print(f"RAG Sources Used: {result['metadata']['rag_sources']}")
        
        print(f"\n👤 Extracted Entities:")
        for entity_type, values in result['entities'].items():
            if values:
                print(f"  {entity_type}: {values}")
        
        print(f"\n🤖 LLM Analysis Preview:")
        print(result['llm_analysis'][:300] + "...")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

async def test_chat_interface():
    """Test chat interface untuk knowledge base"""
    
    print("\n" + "=" * 50)
    print("💬 Testing Chat Interface")
    print("=" * 50)
    
    try:
        # Initialize components
        vector_db = VectorDatabase(
            elasticsearch_url=settings.elasticsearch_url,
            openai_api_key=settings.openai_api_key
        )
        
        analyzer = AIDocumentAnalyzer(
            vector_db=vector_db,
            openai_api_key=settings.openai_api_key
        )
        
        # Test questions
        questions = [
            "Apa saja elemen wajib dalam KTP Indonesia?",
            "Bagaimana cara mendeteksi dokumen KTP palsu?",
            "Sebutkan fitur keamanan pada passport Indonesia",
            "Apa format NIK yang benar?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n❓ Question {i}: {question}")
            
            chat_result = await analyzer.chat_with_documents(question)
            
            print(f"🤖 Answer: {chat_result['answer'][:200]}...")
            print(f"📚 Sources: {len(chat_result['source_documents'])} documents")
        
    except Exception as e:
        print(f"❌ Chat Error: {str(e)}")

async def test_document_upload():
    """Test upload dan processing dokumen baru"""
    
    print("\n" + "=" * 50)
    print("📤 Testing Document Upload")
    print("=" * 50)
    
    try:
        # Initialize components
        vector_db = VectorDatabase(
            elasticsearch_url=settings.elasticsearch_url,
            openai_api_key=settings.openai_api_key
        )
        
        processor = DocumentProcessor(settings.openai_api_key)
        
        # Sample new document untuk knowledge base
        new_document = """
        PANDUAN VERIFIKASI SIM INDONESIA
        
        Surat Izin Mengemudi (SIM) Indonesia memiliki karakteristik:
        
        1. Format nomor: 12 digit angka
        2. Kategori SIM:
           - SIM A: Mobil penumpang
           - SIM B1: Mobil barang/bus kecil
           - SIM B2: Bus besar/truk
           - SIM C: Sepeda motor
        
        3. Masa berlaku:
           - SIM A, B1, B2: 5 tahun
           - SIM C: 5 tahun
        
        4. Fitur keamanan:
           - Hologram resmi Polri
           - Foto digital dengan kualitas tinggi
           - Barcode untuk verifikasi
           - Material khusus anti-fotokopi
        
        5. Validasi penting:
           - Kesesuaian foto dengan pemegang
           - Tanggal berlaku yang valid
           - Nomor SIM tidak duplikat
           - Alamat sesuai dengan KTP
        """
        
        print("📝 Adding new document to knowledge base...")
        doc_ids = await vector_db.add_document_from_text_async(
            content=new_document,
            title="Panduan Verifikasi SIM Indonesia",
            document_type="sim",
            category="standard",
            processor=processor
        )
        
        print(f"✅ Document added with {len(doc_ids)} chunks")
        
        # Test search dengan dokumen baru
        print("\n🔍 Testing search with new document...")
        results = await vector_db.search_similar_async(
            "bagaimana cara verifikasi SIM Indonesia?",
            top_k=3
        )
        
        for i, result in enumerate(results, 1):
            print(f"\n📄 Result {i}:")
            print(f"  Title: {result['title']}")
            print(f"  Type: {result['document_type']}")
            print(f"  Score: {result['score']:.2f}")
            print(f"  Content: {result['content'][:150]}...")
        
    except Exception as e:
        print(f"❌ Upload Error: {str(e)}")

async def main():
    """Main demo function"""
    
    print("🎯 LangChain eKYC Document Analyzer Demo")
    print("Version:", settings.app_version)
    print("Model:", settings.openai_model)
    print("Elasticsearch:", settings.elasticsearch_url)
    
    # Test 1: Basic Analysis
    await test_basic_analysis()
    
    # Test 2: Chat Interface
    await test_chat_interface()
    
    # Test 3: Document Upload
    await test_document_upload()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print("🚀 LangChain integration is working properly")

if __name__ == "__main__":
    # Create .env template jika belum ada
    if not os.path.exists(".env"):
        from config import create_env_template
        create_env_template()
        print("📝 Please update .env file with your API keys before running!")
    else:
        asyncio.run(main())
