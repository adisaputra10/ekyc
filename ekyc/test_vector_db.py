"""
Test Elasticsearch Vector Database functionality
"""
import requests
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import time

def test_elasticsearch_connection():
    """Test koneksi ke Elasticsearch"""
    try:
        response = requests.get("http://localhost:9200")
        if response.status_code == 200:
            print("✅ Elasticsearch connection successful")
            cluster_info = response.json()
            print(f"   Version: {cluster_info['version']['number']}")
            print(f"   Cluster: {cluster_info['cluster_name']}")
            return True
        else:
            print(f"❌ Elasticsearch connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Elasticsearch: {str(e)}")
        return False

def create_vector_index():
    """Buat index dengan mapping untuk vector search"""
    
    index_name = "test_vectors"
    mapping = {
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "vector": {
                    "type": "dense_vector",
                    "dims": 384,  # Sesuai dengan sentence transformer
                    "index": True,
                    "similarity": "cosine"
                },
                "category": {"type": "keyword"}
            }
        }
    }
    
    try:
        # Delete index if exists
        requests.delete(f"http://localhost:9200/{index_name}")
        
        # Create new index
        response = requests.put(
            f"http://localhost:9200/{index_name}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(mapping)
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Vector index '{index_name}' created successfully")
            return True
        else:
            print(f"❌ Failed to create index: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating vector index: {str(e)}")
        return False

def test_vector_operations():
    """Test vector operations: index, search"""
    
    print("\n🧪 Testing Vector Operations...")
    
    # Initialize sentence transformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Sample documents
    documents = [
        {"text": "KTP adalah dokumen identitas utama warga negara Indonesia", "category": "ktp"},
        {"text": "Verifikasi eKYC memerlukan foto selfie dan dokumen identitas", "category": "ekyc"},
        {"text": "NIK terdiri dari 16 digit angka yang unik untuk setiap penduduk", "category": "nik"},
        {"text": "Paspor Indonesia berlaku untuk perjalanan internasional", "category": "passport"},
        {"text": "Face recognition digunakan untuk mencocokan foto selfie dengan KTP", "category": "biometric"}
    ]
    
    index_name = "test_vectors"
    
    # Index documents dengan vectors
    print("📝 Indexing documents with vectors...")
    for i, doc in enumerate(documents):
        # Generate vector
        vector = model.encode(doc["text"]).tolist()
        
        # Index document
        doc_with_vector = {
            "text": doc["text"],
            "vector": vector,
            "category": doc["category"]
        }
        
        response = requests.post(
            f"http://localhost:9200/{index_name}/_doc/{i}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(doc_with_vector)
        )
        
        if response.status_code in [200, 201]:
            print(f"   ✅ Document {i+1} indexed")
        else:
            print(f"   ❌ Failed to index document {i+1}: {response.text}")
    
    # Wait for indexing
    time.sleep(2)
    
    # Test vector search
    print("\n🔍 Testing vector similarity search...")
    query = "cara verifikasi identitas dengan foto"
    query_vector = model.encode(query).tolist()
    
    search_query = {
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        },
        "size": 3
    }
    
    response = requests.post(
        f"http://localhost:9200/{index_name}/_search",
        headers={"Content-Type": "application/json"},
        data=json.dumps(search_query)
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"📊 Search results for: '{query}'")
        
        for hit in results['hits']['hits']:
            score = hit['_score']
            text = hit['_source']['text']
            category = hit['_source']['category']
            print(f"   Score: {score:.3f} | Category: {category}")
            print(f"   Text: {text}")
            print()
        
        return True
    else:
        print(f"❌ Vector search failed: {response.text}")
        return False

def test_knn_search():
    """Test KNN search functionality"""
    
    print("🎯 Testing KNN Search...")
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query = "dokumen identitas Indonesia"
    query_vector = model.encode(query).tolist()
    
    knn_query = {
        "knn": {
            "field": "vector",
            "query_vector": query_vector,
            "k": 2,
            "num_candidates": 10
        },
        "_source": ["text", "category"]
    }
    
    response = requests.post(
        "http://localhost:9200/test_vectors/_search",
        headers={"Content-Type": "application/json"},
        data=json.dumps(knn_query)
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"🎯 KNN search results for: '{query}'")
        
        for hit in results['hits']['hits']:
            score = hit['_score']
            text = hit['_source']['text']
            category = hit['_source']['category']
            print(f"   Score: {score:.3f} | Category: {category}")
            print(f"   Text: {text}")
            print()
        
        return True
    else:
        print(f"❌ KNN search failed: {response.text}")
        return False

def main():
    """Main testing function"""
    
    print("🧪 Testing Elasticsearch Vector Database")
    print("=" * 50)
    
    # Test connection
    if not test_elasticsearch_connection():
        print("🚫 Cannot proceed without Elasticsearch connection")
        return
    
    # Create vector index
    if not create_vector_index():
        print("🚫 Cannot proceed without vector index")
        return
    
    # Test vector operations
    if not test_vector_operations():
        print("🚫 Vector operations failed")
        return
    
    # Test KNN search
    if not test_knn_search():
        print("🚫 KNN search failed")
        return
    
    print("🎉 All tests passed! Elasticsearch Vector Database is working correctly.")
    print("\n📚 Next steps:")
    print("   1. Initialize eKYC knowledge base: python -c 'from rag_system import *; kb = EKYCKnowledgeBase(); initialize_ekyc_knowledge_base(kb)'")
    print("   2. Start FastAPI server: python -m uvicorn main:app --reload")
    print("   3. Or start Streamlit: streamlit run streamlit_app.py")

if __name__ == "__main__":
    main()
