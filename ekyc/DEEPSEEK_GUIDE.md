# DeepSeek Integration Guide

## Panduan Lengkap Menggunakan DeepSeek untuk eKYC Document Analysis

### 🎯 Overview

Aplikasi eKYC ini telah diperbarui untuk menggunakan **DeepSeek** sebagai LLM provider utama. DeepSeek adalah model bahasa besar yang powerful dan cost-effective untuk berbagai tugas AI, termasuk analisis dokumen dan RAG (Retrieval-Augmented Generation).

### 🔧 Setup dan Konfigurasi

#### 1. Instalasi Dependencies

```bash
# Install semua package yang diperlukan
pip install -r requirements.txt
```

#### 2. Konfigurasi Environment

Buat atau update file `.env` dengan konfigurasi DeepSeek:

```env
# LLM Configuration
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-actual-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# OpenAI (fallback)
OPENAI_API_KEY=your-openai-api-key-here

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=document_vectors
```

#### 3. Mendapatkan DeepSeek API Key

1. Kunjungi [DeepSeek Platform](https://platform.deepseek.com/)
2. Buat akun atau login
3. Buat API key baru
4. Copy API key dan masukkan ke file `.env`

#### 4. Setup Otomatis

Jalankan script setup otomatis:

```bash
python setup_deepseek.py
```

Script ini akan:
- ✅ Check semua dependencies
- ✅ Setup file `.env`
- ✅ Validasi konfigurasi DeepSeek
- ✅ Check Docker dan Elasticsearch
- ✅ Memberikan instruksi lengkap

### 🚀 Menjalankan Aplikasi

#### 1. Start Elasticsearch

```bash
# Windows PowerShell
.\scripts\run_elasticsearch.ps1

# Atau menggunakan Docker Compose
docker-compose up -d
```

#### 2. Test DeepSeek Integration

```bash
python test_deepseek_integration.py
```

#### 3. Start FastAPI Server

```bash
# Development mode
python main.py

# Atau dengan uvicorn
uvicorn main:app --reload
```

#### 4. Start Streamlit UI (Opsional)

```bash
streamlit run streamlit_app.py
```

### 🔍 Testing dan Validasi

#### Test Suite DeepSeek

File `test_deepseek_integration.py` menyediakan test lengkap:

```bash
python test_deepseek_integration.py
```

Test meliputi:
- ✅ Validasi environment dan API key
- ✅ Inisialisasi AI components
- ✅ Test DeepSeek LLM response
- ✅ Document processing dan analysis
- ✅ RAG functionality
- ✅ Chat functionality
- ✅ Vector database operations

### 📊 Fitur-Fitur Utama

#### 1. Document Analysis dengan DeepSeek

```python
from ai_document_analyzer import AIDocumentAnalyzer

# Initialize
analyzer = AIDocumentAnalyzer()
await analyzer.initialize()

# Analyze document
result = await analyzer.analyze_document("path/to/document.pdf")
print(result['analysis'])
```

#### 2. RAG (Retrieval-Augmented Generation)

```python
# Query dokumen dengan context
rag_result = await analyzer.query_rag("Apa NIK yang tertera di dokumen?")
print(rag_result['answer'])
```

#### 3. AI Chat dengan Context

```python
# Chat dengan AI tentang dokumen
messages = [{"role": "user", "content": "Jelaskan jenis dokumen ini"}]
chat_result = await analyzer.chat(messages)
print(chat_result['content'])
```

### 🌐 API Endpoints

#### Document Upload dan Analysis
```
POST /upload-document
Content-Type: multipart/form-data

Response:
{
  "analysis": {
    "document_type": "KTP",
    "quality_score": 0.95,
    "entities": [...],
    "classification": {...}
  }
}
```

#### RAG Query
```
POST /rag/query
Content-Type: application/json

Body:
{
  "query": "What is the NIK number?",
  "session_id": "optional"
}

Response:
{
  "answer": "The NIK number is...",
  "sources": [...],
  "metadata": {...}
}
```

#### AI Chat
```
POST /ai/chat
Content-Type: application/json

Body:
{
  "messages": [
    {"role": "user", "content": "Analyze this document"}
  ],
  "session_id": "optional"
}

Response:
{
  "content": "Based on the document...",
  "metadata": {...}
}
```

### 🔧 Konfigurasi Advanced

#### Custom DeepSeek Model

Update di `.env`:
```env
DEEPSEEK_MODEL=deepseek-chat  # Default
# Atau model lain yang tersedia
```

#### LLM Provider Switching

Untuk beralih ke OpenAI:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
```

#### Elasticsearch Configuration

```env
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=document_vectors
ELASTICSEARCH_USERNAME=elastic  # Jika perlu auth
ELASTICSEARCH_PASSWORD=password
```

### 🐛 Troubleshooting

#### Common Issues

1. **DeepSeek API Key Error**
   ```
   Error: DEEPSEEK_API_KEY is required when using DeepSeek
   ```
   **Solution**: Set valid API key di file `.env`

2. **Elasticsearch Connection Error**
   ```
   Error: Failed to connect to Elasticsearch
   ```
   **Solution**: Start Elasticsearch dengan `.\scripts\run_elasticsearch.ps1`

3. **Import Error**
   ```
   Error: No module named 'langchain'
   ```
   **Solution**: Install dependencies dengan `pip install -r requirements.txt`

#### Debug Mode

Enable debug logging:
```env
DEBUG=true
LANGCHAIN_VERBOSE=true
```

### 📈 Performance Optimization

#### Batch Processing

Untuk multiple documents:
```python
# Process multiple files
results = []
for file_path in file_paths:
    result = await analyzer.analyze_document(file_path)
    results.append(result)
```

#### Vector Database Optimization

```env
# Tune untuk performance
CHUNK_SIZE=1000          # Size of text chunks
CHUNK_OVERLAP=200        # Overlap between chunks
SIMILARITY_THRESHOLD=0.7 # Minimum similarity score
RETRIEVAL_K=5           # Number of results to retrieve
```

### 🎯 Best Practices

1. **API Key Security**
   - Jangan commit `.env` ke repository
   - Gunakan environment variables di production
   - Rotate API keys secara berkala

2. **Error Handling**
   - Implement retry logic untuk API calls
   - Log errors untuk debugging
   - Provide fallback ke OpenAI jika perlu

3. **Performance**
   - Cache hasil analysis untuk dokumen yang sama
   - Gunakan async/await untuk concurrent processing
   - Monitor usage dan costs

4. **Data Privacy**
   - Encrypt sensitive documents
   - Implement proper access controls
   - Follow data retention policies

### 📚 Additional Resources

- [DeepSeek Documentation](https://platform.deepseek.com/docs)
- [LangChain Integration Guide](https://python.langchain.com/docs/integrations/llms/)
- [Elasticsearch Vector Search](https://www.elastic.co/guide/en/elasticsearch/reference/current/dense-vector.html)

### 🎉 Ready to Go!

Setelah setup selesai, aplikasi siap digunakan dengan DeepSeek sebagai AI engine untuk:
- 📄 Document analysis dan classification
- 🔍 RAG-powered question answering
- 💬 AI chat dengan document context
- 🏗️ Vector-based semantic search
- 📊 Quality scoring dan entity extraction

Happy analyzing! 🚀
