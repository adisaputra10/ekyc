# Elasticsearch v8 Vector Database Commands

## 🚀 Quick Start (Single Command)

### Windows PowerShell:
```powershell
docker run -d --name ekyc-elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "xpack.security.enrollment.enabled=false" -e "xpack.security.http.ssl.enabled=false" -e "xpack.security.transport.ssl.enabled=false" -e "bootstrap.memory_lock=true" -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" --ulimit memlock=-1:-1 -v elasticsearch_data:/usr/share/elasticsearch/data elasticsearch:8.11.0
```

### Linux/Mac:
```bash
docker run -d \
  --name ekyc-elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "xpack.security.enrollment.enabled=false" \
  -e "xpack.security.http.ssl.enabled=false" \
  -e "xpack.security.transport.ssl.enabled=false" \
  -e "bootstrap.memory_lock=true" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  --ulimit memlock=-1:-1 \
  -v elasticsearch_data:/usr/share/elasticsearch/data \
  elasticsearch:8.11.0
```

## 🛠️ Complete Setup dengan Docker Compose

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs elasticsearch

# Stop services
docker-compose down
```

## 📊 Management Commands

### Check Elasticsearch Status:
```bash
curl http://localhost:9200/_cluster/health
```

### Test Vector Database:
```bash
# Test connection
curl http://localhost:9200

# Check indices
curl http://localhost:9200/_cat/indices?v

# Test vector search capabilities
python test_vector_db.py
```

### Create Vector Index Example:
```bash
curl -X PUT "http://localhost:9200/test_vectors" -H "Content-Type: application/json" -d '{
  "mappings": {
    "properties": {
      "text": {"type": "text"},
      "vector": {
        "type": "dense_vector",
        "dims": 384,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}'
```

## 🎯 Vector Database Features

✅ **Dense Vector Support** - Store high-dimensional vectors
✅ **Cosine Similarity** - Built-in similarity scoring  
✅ **KNN Search** - K-nearest neighbors search
✅ **Script Score Queries** - Custom scoring with vectors
✅ **Hybrid Search** - Combine keyword + semantic search
✅ **Vector Indexing** - Fast vector retrieval

## 🔧 Configuration Options

### Memory Settings:
- `-e "ES_JAVA_OPTS=-Xms1g -Xmx1g"` - Heap size (adjust based on your RAM)
- `--ulimit memlock=-1:-1` - Unlimited memory lock

### Security Settings:
- `xpack.security.enabled=false` - Disable security for development
- `xpack.security.http.ssl.enabled=false` - Disable SSL

### Vector Settings:
- `"similarity": "cosine"` - Use cosine similarity for vectors
- `"index": true` - Enable vector indexing for faster search
- `"dims": 384` - Vector dimensions (adjust based on your embedding model)

## 📱 Access URLs

- **Elasticsearch**: http://localhost:9200
- **Kibana** (if started): http://localhost:5601
- **Health Check**: http://localhost:9200/_cluster/health

## 🧪 Test Vector Database

```bash
# Run vector database tests
python test_vector_db.py

# Initialize eKYC knowledge base
python -c "from rag_system import *; kb = EKYCKnowledgeBase(); initialize_ekyc_knowledge_base(kb)"
```

## 🎮 Usage Examples

### Index Document with Vector:
```python
from rag_system import EKYCKnowledgeBase

kb = EKYCKnowledgeBase()
kb.add_document(
    content="KTP adalah dokumen identitas utama Indonesia",
    title="Info KTP",
    document_type="ktp",
    category="identitas"
)
```

### Search with Vectors:
```python
results = kb.search_similar("cara verifikasi KTP", top_k=5)
```

### RAG Query:
```python
from rag_system import EKYCRAGSystem

rag = EKYCRAGSystem(kb, llm_provider="openai", api_key="your-key")
response = rag.query("Bagaimana cara memvalidasi NIK?")
```

## 🚨 Troubleshooting

### Container won't start:
```bash
# Check logs
docker logs ekyc-elasticsearch

# Common issues:
# - Insufficient memory: Increase Docker memory limit
# - Port conflict: Change port mapping -p 9201:9200
# - Permission issues: Check Docker daemon
```

### Vector operations fail:
```bash
# Check if vector mapping exists
curl http://localhost:9200/your_index/_mapping

# Verify vector dimensions match your model
# Default sentence-transformers model uses 384 dimensions
```

### Performance tuning:
```bash
# Increase heap size for large datasets
-e "ES_JAVA_OPTS=-Xms2g -Xmx2g"

# Use SSD volume for better performance
-v /fast/ssd/path:/usr/share/elasticsearch/data
```

## 🔄 Scripts Tersedia

- `start_elasticsearch.sh` - Linux/Mac startup script
- `start_elasticsearch.ps1` - Windows PowerShell script  
- `docker-compose.yml` - Docker Compose configuration
- `test_vector_db.py` - Vector database testing

## 📚 Next Steps

1. Start Elasticsearch: `.\start_elasticsearch.ps1`
2. Test vector DB: `python test_vector_db.py`
3. Initialize knowledge base: Import eKYC documents
4. Start FastAPI: `uvicorn main:app --reload`
5. Test RAG queries: Use `/rag-query` endpoint
