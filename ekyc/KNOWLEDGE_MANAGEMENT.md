# Knowledge Base Management untuk eKYC RAG System

Script-script ini digunakan untuk mengelola knowledge base dalam sistem RAG (Retrieval-Augmented Generation) eKYC.

## File Scripts

### 1. `add_knowledge.py` - Interactive Knowledge Manager
Script utama untuk mengelola knowledge base secara interaktif.

**Fitur:**
- Tambah knowledge base default eKYC (8 kategori lengkap)
- Tambah knowledge manual dengan input interaktif
- Validasi dan error handling

**Cara menggunakan:**
```bash
python add_knowledge.py
```

### 2. `setup_knowledge_base.py` - Batch Setup
Script otomatis untuk menambahkan semua knowledge default eKYC sekaligus.

**Cara menggunakan:**
```bash
python setup_knowledge_base.py
```

### 3. `test_knowledge.py` - System Test
Script untuk menguji apakah sistem knowledge base berfungsi dengan baik.

**Cara menggunakan:**
```bash
python test_knowledge.py
```

## Knowledge Base Default

Script menyediakan 8 kategori knowledge eKYC yang komprehensif:

1. **Dokumen Identitas** - Persyaratan KTP lengkap
2. **Validasi** - Validasi NIK dan format dokumen
3. **Dokumen** - Jenis-jenis dokumen yang diterima
4. **Proses** - Tahapan verifikasi eKYC
5. **Keamanan** - Privacy dan data protection
6. **Troubleshooting** - Panduan mengatasi masalah upload
7. **Integrasi** - API dan dokumentasi teknis
8. **Regulasi** - Compliance dan peraturan

## Cara Setup Lengkap

### Langkah 1: Test System
```bash
python test_knowledge.py
```

### Langkah 2: Setup Default Knowledge
```bash
python setup_knowledge_base.py
```

### Langkah 3: Tambah Knowledge Custom (Opsional)
```bash
python add_knowledge.py
# Pilih option 2 untuk tambah manual
```

## Prerequisites

Pastikan hal berikut sudah dikonfigurasi:

1. **Elasticsearch** - Harus running di localhost:9200
2. **Environment Variables** - `.env` file dengan:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key
   LLM_PROVIDER=deepseek
   ELASTICSEARCH_URL=http://localhost:9200
   ```
3. **Python Dependencies** - Install dengan:
   ```bash
   pip install -r requirements.txt
   ```

## Struktur Knowledge Entry

Setiap knowledge entry memiliki struktur:

```python
{
    "title": "Judul Knowledge",
    "content": "Konten lengkap dengan detail...",
    "category": "kategori_knowledge",
    "tags": ["tag1", "tag2", "tag3"]
}
```

## Vector Database

Knowledge disimpan dalam Elasticsearch dengan index `ekyc_knowledge_base`:
- **Embeddings**: Menggunakan sentence-transformers (all-MiniLM-L6-v2)
- **Search**: Vector similarity search untuk RAG
- **Metadata**: Category, tags, timestamp untuk filtering

## Testing RAG System

Setelah menambahkan knowledge, test via web interface dengan pertanyaan seperti:

- "Apa saja persyaratan untuk membuat KTP?"
- "Bagaimana cara validasi NIK?"
- "Dokumen apa saja yang diterima sistem eKYC?"
- "Bagaimana proses verifikasi eKYC?"
- "Apa yang harus dilakukan jika upload dokumen gagal?"

## Troubleshooting

### Error: "Cannot connect to Elasticsearch"
**Solusi:**
```bash
# Start Elasticsearch
.\start_elasticsearch.ps1
# Atau manual:
docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0
```

### Error: "DeepSeek API key not found"
**Solusi:**
1. Buat file `.env` di root directory
2. Tambahkan: `DEEPSEEK_API_KEY=your_api_key`
3. Restart script

### Error: "Module not found"
**Solusi:**
```bash
pip install -r requirements.txt
```

## Advanced Usage

### Custom Knowledge Categories
Untuk menambah kategori baru, edit `EKYC_KNOWLEDGE_BASE` di `add_knowledge.py`:

```python
{
    "title": "Custom Knowledge",
    "content": "Your content here...",
    "category": "custom_category",
    "tags": ["custom", "tags"]
}
```

### Batch Import dari File
Untuk import knowledge dari file JSON:

```python
import json
from add_knowledge import KnowledgeManager

async def import_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    km = KnowledgeManager()
    results = await km.add_knowledge_from_dict(data)
    return results
```

## Monitoring dan Maintenance

- **Log Files**: Check logs untuk debugging
- **Index Health**: Monitor Elasticsearch index health
- **Performance**: Vector search performance monitoring
- **Updates**: Regular knowledge base updates

## Support

Untuk pertanyaan atau masalah, check:
1. Log output dari script
2. Elasticsearch cluster health
3. API key validity
4. Network connectivity
