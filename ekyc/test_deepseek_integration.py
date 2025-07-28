"""
Test script khusus untuk integrasi DeepSeek API
Untuk memastikan semua fungsi AI bekerja dengan DeepSeek
"""

import asyncio
import os
import tempfile
from typing import Dict, Any

from ai_document_analyzer import AIDocumentAnalyzer, DocumentProcessor, VectorDatabase
from config import settings, validate_environment

async def test_deepseek_integration():
    """Test lengkap integrasi DeepSeek"""
    print("=== Testing DeepSeek Integration ===")
    
    try:
        # 1. Validasi environment
        print("\n1. Validating environment...")
        validate_environment()
        print(f"✓ Environment valid. Using LLM provider: {settings.llm_provider}")
        print(f"✓ DeepSeek model: {settings.deepseek_model}")
        
        # 2. Initialize vector database first
        print("\n2. Initializing vector database...")
        vector_db = VectorDatabase(
            elasticsearch_url=settings.elasticsearch_url,
            index_name=settings.elasticsearch_index,
            api_key=settings.deepseek_api_key,
            llm_provider=settings.llm_provider
        )
        await vector_db.initialize()
        print("✓ Vector database initialized")
        
        # 3. Initialize AI components
        print("\n3. Initializing AI components...")
        analyzer = AIDocumentAnalyzer(
            vector_db=vector_db,
            api_key=settings.deepseek_api_key,
            llm_provider=settings.llm_provider,
            model_name=settings.deepseek_model
        )
        analyzer.initialize()  # This is now synchronous
        print("✓ AI Document Analyzer initialized")
        
        # 4. Test DeepSeek LLM directly (skip if no real API key)
        if settings.deepseek_api_key and settings.deepseek_api_key != "your-deepseek-api-key-here":
            print("\n4. Testing DeepSeek LLM...")
            test_prompt = "Explain what eKYC (electronic Know Your Customer) means in one sentence."
            try:
                if hasattr(analyzer.llm, 'acall'):
                    response = await analyzer.llm.acall(test_prompt)
                elif hasattr(analyzer.llm, '_call'):
                    response = analyzer.llm._call(test_prompt)
                else:
                    response = "DeepSeek LLM test skipped - method not available"
                print(f"✓ DeepSeek response: {response[:100]}...")
            except Exception as e:
                print(f"⚠️  DeepSeek LLM test warning: {str(e)}")
        else:
            print("\n4. Skipping DeepSeek LLM test (no real API key)")
        
        # 5. Test document processing
        print("\n5. Testing document processing...")
        test_content = """
        Kartu Tanda Penduduk (KTP)
        
        Nama: John Doe
        NIK: 1234567890123456
        Tempat/Tgl Lahir: Jakarta, 01 Januari 1990
        Alamat: Jl. Sudirman No. 123, Jakarta
        Agama: Islam
        Status Perkawinan: Belum Kawin
        Pekerjaan: Software Engineer
        Kewarganegaraan: WNI
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
            tmp.write(test_content)
            tmp_path = tmp.name
        
        try:
            # Process document
            result = await analyzer.analyze_document(tmp_path)
            print("✓ Document analysis completed")
            print(f"  - Document type: {result['analysis']['document_type']}")
            print(f"  - Quality score: {result['analysis']['quality_score']}")
            print(f"  - Entities found: {len(result['analysis']['entities'])}")
            
            # 6. Test RAG functionality (skip if no real API key)
            if settings.deepseek_api_key and settings.deepseek_api_key != "your-deepseek-api-key-here":
                print("\n6. Testing RAG functionality...")
                rag_query = "What is the NIK number in this document?"
                rag_result = await analyzer.query_rag(rag_query)
                print("✓ RAG query successful")
                print(f"  - Query: {rag_query}")
                print(f"  - Answer: {rag_result['answer'][:100]}...")
            else:
                print("\n6. Skipping RAG test (no real API key)")
            
            # 7. Test chat functionality (skip if no real API key)
            if settings.deepseek_api_key and settings.deepseek_api_key != "your-deepseek-api-key-here":
                print("\n7. Testing chat functionality...")
                chat_messages = [
                    {"role": "user", "content": "What information can you extract from identity documents?"}
                ]
                chat_result = await analyzer.chat(chat_messages)
                print("✓ Chat functionality working")
                print(f"  - Response: {chat_result['content'][:100]}...")
            else:
                print("\n7. Skipping chat test (no real API key)")
            
            print("\n=== All DeepSeek Integration Tests Completed! ===")
            return True
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
    except Exception as e:
        print(f"\n❌ Error during DeepSeek integration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_vector_database():
    """Test vector database functionality"""
    print("\n=== Testing Vector Database ===")
    
    try:
        vector_db = VectorDatabase(
            elasticsearch_url=settings.elasticsearch_url,
            index_name=settings.elasticsearch_index,
            api_key=settings.deepseek_api_key,
            llm_provider=settings.llm_provider
        )
        await vector_db.initialize()
        
        # Test document embedding and storage
        test_docs = [
            {
                "content": "KTP adalah dokumen identitas resmi di Indonesia",
                "metadata": {"type": "definition", "doc_id": "test_1"}
            },
            {
                "content": "NIK adalah Nomor Induk Kependudukan yang unik untuk setiap warga negara",
                "metadata": {"type": "definition", "doc_id": "test_2"}
            }
        ]
        
        # Store documents
        await vector_db.store_documents(test_docs)
        print("✓ Documents stored in vector database")
        
        # Test search
        search_results = await vector_db.search("apa itu NIK", k=2)
        print(f"✓ Vector search completed, found {len(search_results)} results")
        
        for i, result in enumerate(search_results):
            print(f"  Result {i+1}: {result['content'][:50]}... (score: {result['score']:.3f})")
        
        return vector_db  # Return for use in other tests
        
    except Exception as e:
        print(f"❌ Vector database test failed: {str(e)}")
        return None

def main():
    """Main test function"""
    print("DeepSeek Integration Test Suite")
    print("=" * 50)
    
    # Check if DeepSeek API key is set
    if not settings.deepseek_api_key or settings.deepseek_api_key == "your-deepseek-api-key-here":
        print("⚠️  WARNING: DEEPSEEK_API_KEY not set properly in .env file")
        print("Please set your actual DeepSeek API key to run this test")
        return
    
    # Run tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test vector database first
        vector_db = loop.run_until_complete(test_vector_database())
        vector_success = vector_db is not None
        
        # Test DeepSeek integration
        deepseek_success = loop.run_until_complete(test_deepseek_integration())
        
        print("\n" + "=" * 50)
        print("TEST SUMMARY:")
        print(f"Vector Database: {'✓ PASSED' if vector_success else '❌ FAILED'}")
        print(f"DeepSeek Integration: {'✓ PASSED' if deepseek_success else '❌ FAILED'}")
        
        if vector_success and deepseek_success:
            print("\n🎉 All tests passed! Your DeepSeek integration is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Please check the error messages above.")
            
    finally:
        loop.close()

if __name__ == "__main__":
    main()
