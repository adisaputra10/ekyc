"""
Test Vector Database dan AI Document Analyzer
"""
import asyncio
import json
import time
from ai_document_analyzer import VectorDatabase, AIDocumentAnalyzer, DocumentProcessor, initialize_knowledge_base

async def test_elasticsearch_connection():
    """Test koneksi ke Elasticsearch"""
    print("🔍 Testing Elasticsearch connection...")
    
    try:
        vector_db = VectorDatabase()
        
        # Test basic connection
        health = vector_db.es_client.cluster.health()
        print(f"✅ Elasticsearch status: {health['status']}")
        print(f"📊 Cluster name: {health['cluster_name']}")
        print(f"🟢 Active nodes: {health['number_of_nodes']}")
        
        return True
    except Exception as e:
        print(f"❌ Elasticsearch connection failed: {str(e)}")
        return False

async def test_vector_indexing():
    """Test vector indexing dan searching"""
    print("\n📝 Testing vector indexing...")
    
    try:
        vector_db = VectorDatabase()
        processor = DocumentProcessor()
        
        # Sample documents
        sample_docs = [
            {
                "title": "Contoh KTP Jakarta",
                "content": """
                REPUBLIK INDONESIA
                KARTU TANDA PENDUDUK
                
                NIK: 3171234567890123
                Nama: AHMAD SUSANTO
                Tempat/Tgl Lahir: JAKARTA, 12-03-1985
                Jenis Kelamin: LAKI-LAKI
                Alamat: JL. SUDIRMAN NO. 45
                RT/RW: 003/001
                Kel/Desa: MENTENG
                Kecamatan: MENTENG
                Agama: ISLAM
                Status Perkawinan: KAWIN
                Pekerjaan: PEGAWAI SWASTA
                Kewarganegaraan: WNI
                """,
                "document_type": "ktp",
                "category": "sample"
            },
            {
                "title": "Contoh Paspor Indonesia",
                "content": """
                REPUBLIC OF INDONESIA
                PASSPORT
                
                Passport No: C1234567
                Given Names: SITI RAHAYU
                Surname: WIDODO
                Date of Birth: 25 JUN 1992
                Place of Birth: SURABAYA
                Nationality: INDONESIA
                Sex: F
                Date of Issue: 15 JAN 2023
                Date of Expiry: 15 JAN 2028
                """,
                "document_type": "passport",
                "category": "sample"
            }
        ]
        
        # Add documents
        for doc in sample_docs:
            doc_ids = await vector_db.add_document_async(
                content=doc["content"],
                title=doc["title"],
                document_type=doc["document_type"],
                category=doc["category"],
                processor=processor
            )
            print(f"✅ Added document: {doc['title']} (IDs: {doc_ids})")
        
        # Wait for indexing
        await asyncio.sleep(2)
        
        # Test search
        print("\n🔍 Testing vector search...")
        search_queries = [
            "dokumen identitas Jakarta",
            "paspor Indonesia",
            "NIK 16 digit"
        ]
        
        for query in search_queries:
            results = await vector_db.search_similar_async(query, top_k=3)
            print(f"Query: '{query}' → Found {len(results)} results")
            
            for i, result in enumerate(results[:2]):
                print(f"  {i+1}. {result['title']} (score: {result['score']:.3f})")
        
        # Test hybrid search
        print("\n🔀 Testing hybrid search...")
        hybrid_results = await vector_db.search_hybrid_async("KTP Jakarta", top_k=3)
        print(f"Hybrid search found {len(hybrid_results)} results")
        
        for i, result in enumerate(hybrid_results):
            print(f"  {i+1}. {result['title']} (combined: {result['combined_score']:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector indexing test failed: {str(e)}")
        return False

async def test_ai_analysis():
    """Test AI document analysis dengan RAG"""
    print("\n🤖 Testing AI document analysis...")
    
    try:
        # Initialize components
        vector_db = VectorDatabase()
        
        # Initialize dengan knowledge base
        await initialize_knowledge_base(vector_db)
        
        # Note: Untuk testing tanpa OpenAI API key
        analyzer = AIDocumentAnalyzer(
            vector_db=vector_db,
            llm_provider="openai",  # Ganti dengan "mock" untuk testing
            api_key="test-key",     # Ganti dengan API key asli
            model_name="gpt-4"
        )
        
        # Sample document untuk analisis
        sample_document = """
        REPUBLIK INDONESIA
        KARTU TANDA PENDUDUK
        
        NIK: 3173456789012345
        Nama: BUDI SETIAWAN
        Tempat/Tgl Lahir: JAKARTA, 20-05-1988
        Jenis Kelamin: LAKI-LAKI
        Alamat: JL. THAMRIN NO. 67
        RT/RW: 002/003
        Kel/Desa: MENTENG
        Kecamatan: MENTENG
        Agama: KRISTEN
        Status Perkawinan: BELUM KAWIN
        Pekerjaan: PROGRAMMER
        Kewarganegaraan: WNI
        Berlaku Hingga: SEUMUR HIDUP
        """
        
        print("📄 Analyzing sample document...")
        
        # Basic analysis tanpa LLM
        processor = DocumentProcessor()
        entities = processor.extract_entities(sample_document)
        classification = processor.classify_document_type(sample_document)
        quality = processor.calculate_document_quality(sample_document)
        
        print(f"✅ Document classification: {classification}")
        print(f"✅ Quality score: {quality:.2f}")
        print(f"✅ Extracted entities: {entities}")
        
        # Test vector search untuk dokumen ini
        search_results = await vector_db.search_similar_async(
            "analisis dokumen KTP validasi", top_k=3
        )
        print(f"✅ Found {len(search_results)} similar documents in knowledge base")
        
        return True
        
    except Exception as e:
        print(f"❌ AI analysis test failed: {str(e)}")
        return False

async def test_performance():
    """Test performance vector database"""
    print("\n⚡ Testing performance...")
    
    try:
        vector_db = VectorDatabase()
        processor = DocumentProcessor()
        
        # Generate multiple test documents
        test_docs = []
        for i in range(10):
            doc_content = f"""
            Test Document {i}
            NIK: 317{i:012d}
            Nama: TEST USER {i}
            Alamat: Jl. Test No. {i}
            """
            test_docs.append({
                "title": f"Test Doc {i}",
                "content": doc_content,
                "document_type": "test",
                "category": "performance"
            })
        
        # Measure indexing time
        start_time = time.time()
        
        for doc in test_docs:
            await vector_db.add_document_async(
                content=doc["content"],
                title=doc["title"],
                document_type=doc["document_type"],
                category=doc["category"],
                processor=processor
            )
        
        indexing_time = time.time() - start_time
        print(f"✅ Indexed {len(test_docs)} documents in {indexing_time:.2f} seconds")
        print(f"📊 Average: {indexing_time/len(test_docs):.3f} seconds per document")
        
        # Wait for indexing
        await asyncio.sleep(2)
        
        # Measure search time
        search_queries = ["test document", "NIK 317", "user alamat"]
        
        start_time = time.time()
        for query in search_queries:
            results = await vector_db.search_similar_async(query, top_k=5)
        search_time = time.time() - start_time
        
        print(f"✅ Completed {len(search_queries)} searches in {search_time:.3f} seconds")
        print(f"📊 Average: {search_time/len(search_queries):.3f} seconds per search")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run semua tests"""
    print("🚀 Starting comprehensive tests for AI Document Analyzer with RAG\n")
    
    tests = [
        ("Elasticsearch Connection", test_elasticsearch_connection),
        ("Vector Indexing & Search", test_vector_indexing),
        ("AI Document Analysis", test_ai_analysis),
        ("Performance Testing", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        print("="*60)
        
        try:
            success = await test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for production.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        print("\n💡 Troubleshooting tips:")
        print("- Make sure Elasticsearch is running on localhost:9200")
        print("- Check if all Python dependencies are installed")
        print("- Verify OpenAI API key if testing LLM features")

if __name__ == "__main__":
    print("🔧 AI Document Analyzer Test Suite")
    print("📋 This will test Elasticsearch v8 + Vector Database + RAG system")
    print("\n⚠️  Prerequisites:")
    print("- Elasticsearch v8 running on localhost:9200")
    print("- All Python packages installed")
    print("- Optional: OpenAI API key for LLM testing")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    asyncio.run(run_all_tests())
