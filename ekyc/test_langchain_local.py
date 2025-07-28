"""
Simple test untuk LangChain integration tanpa OpenAI API
Demo menggunakan HuggingFace embeddings local
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

from ai_document_analyzer import VectorDatabase, DocumentProcessor, initialize_knowledge_base

async def test_local_embedding():
    """Test dengan local embeddings (tanpa OpenAI API key)"""
    
    print("🚀 Testing LangChain with Local Embeddings")
    print("=" * 50)
    
    try:
        # Initialize dengan local embeddings (tanpa OpenAI API key)
        print("📊 Initializing components...")
        
        vector_db = VectorDatabase(
            elasticsearch_url="http://localhost:9200",
            index_name="test_documents",
            openai_api_key=None  # Use local embeddings
        )
        
        processor = DocumentProcessor(openai_api_key=None)
        
        print("✅ Components initialized with local embeddings")
        
        # Test document processing
        test_document = """
        CONTOH DOKUMEN KTP
        
        NIK: 1234567890123456
        Nama: JOHN DOE
        Tempat/Tgl Lahir: JAKARTA, 01-01-1990
        Jenis Kelamin: LAKI-LAKI
        Alamat: JL. CONTOH NO. 123
        """
        
        print("\n📝 Processing test document...")
        
        # Extract entities
        entities = processor.extract_entities(test_document)
        print(f"Entities: {entities}")
        
        # Classify document type
        classification = processor.classify_document_type(test_document)
        print(f"Classification: {classification}")
        
        # Calculate quality
        quality = processor.calculate_document_quality(test_document)
        print(f"Quality Score: {quality:.2f}")
        
        # Split into documents
        documents = processor.split_documents(
            test_document, 
            {"title": "Test KTP", "document_type": "ktp"}
        )
        print(f"Split into {len(documents)} chunks")
        
        # Try to add to vector database (akan error jika Elasticsearch tidak running)
        try:
            print("\n🔍 Testing vector database connection...")
            doc_ids = await vector_db.add_documents_async(documents, processor)
            print(f"✅ Added documents with IDs: {doc_ids}")
            
            # Test search
            print("\n🔎 Testing vector search...")
            results = await vector_db.search_similar_async(
                "dokumen identitas KTP Indonesia",
                top_k=3
            )
            print(f"Found {len(results)} similar documents")
            for i, result in enumerate(results):
                print(f"  {i+1}. Score: {result['score']:.2f}, Content: {result['content'][:100]}...")
                
        except Exception as es_error:
            print(f"⚠️  Elasticsearch not available: {str(es_error)}")
            print("   To test full functionality, start Elasticsearch first")
        
        print("\n✅ Local embedding test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_knowledge_base_initialization():
    """Test initialization knowledge base"""
    
    print("\n" + "=" * 50)
    print("📚 Testing Knowledge Base Initialization")
    print("=" * 50)
    
    try:
        vector_db = VectorDatabase(
            elasticsearch_url="http://localhost:9200",
            openai_api_key=None  # Use local embeddings
        )
        
        print("📖 Initializing knowledge base...")
        await initialize_knowledge_base(vector_db, openai_api_key=None)
        print("✅ Knowledge base initialized")
        
    except Exception as e:
        print(f"⚠️  Knowledge base test requires Elasticsearch: {str(e)}")

async def main():
    """Main test function"""
    
    print("🎯 LangChain eKYC Integration Test")
    print("   Testing without OpenAI API (local embeddings only)")
    print("   For full functionality, configure OPENAI_API_KEY in .env")
    
    # Test 1: Local processing
    await test_local_embedding()
    
    # Test 2: Knowledge base (if Elasticsearch available)
    await test_knowledge_base_initialization()
    
    print("\n" + "=" * 50)
    print("✅ Tests completed!")
    print("\n📝 Next steps:")
    print("   1. Start Elasticsearch: run start_elasticsearch.ps1")
    print("   2. Add OpenAI API key to .env file")
    print("   3. Run: python langchain_demo.py")

if __name__ == "__main__":
    asyncio.run(main())
