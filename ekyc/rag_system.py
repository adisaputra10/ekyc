"""
RAG System untuk eKYC Knowledge Base
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from models import RAGQuery, RAGResponse, KnowledgeBaseEntry, ChatMessage
from ai_document_analyzer import VectorDatabase, AIDocumentAnalyzer

logger = logging.getLogger(__name__)

class EKYCKnowledgeBase:
    """Knowledge Base untuk eKYC system"""
    
    def __init__(self):
        self.entries = []
        self.vector_db = None
        self._initialize_default_knowledge()
    
    def _initialize_default_knowledge(self):
        """Initialize dengan knowledge base default"""
        default_entries = [
            KnowledgeBaseEntry(
                title="Persyaratan KTP",
                content="KTP (Kartu Tanda Penduduk) adalah dokumen identitas resmi yang wajib dimiliki oleh setiap warga negara Indonesia yang berusia 17 tahun ke atas. Persyaratan untuk membuat KTP meliputi: fotocopy akta kelahiran, surat keterangan pindah (jika pindah domisili), pas foto terbaru ukuran 3x4, dan formulir permohonan KTP.",
                category="dokumen_identitas",
                tags=["ktp", "persyaratan", "identitas"]
            ),
            KnowledgeBaseEntry(
                title="Validasi NIK",
                content="NIK (Nomor Induk Kependudukan) terdiri dari 16 digit angka dengan format: 6 digit kode wilayah, 6 digit tanggal lahir (DDMMYY), dan 4 digit nomor urut kelahiran. Validasi NIK meliputi pengecekan format, kesesuaian kode wilayah, dan validitas tanggal lahir.",
                category="validasi",
                tags=["nik", "validasi", "format"]
            ),
            KnowledgeBaseEntry(
                title="Jenis Dokumen yang Diterima",
                content="Sistem eKYC menerima berbagai jenis dokumen identitas: KTP (Kartu Tanda Penduduk), SIM (Surat Izin Mengemudi), Paspor, NPWP (Nomor Pokok Wajib Pajak), Kartu Keluarga, BPJS, Surat Nikah, dan Akta Kelahiran. Setiap dokumen memiliki kriteria validasi yang berbeda.",
                category="dokumen",
                tags=["dokumen", "jenis", "validasi"]
            ),
            KnowledgeBaseEntry(
                title="Proses Verifikasi",
                content="Proses verifikasi eKYC meliputi beberapa tahap: 1) Upload dokumen, 2) Ekstraksi teks menggunakan OCR, 3) Validasi format dan keaslian, 4) Pencocokan data dengan database referensi, 5) Analisis kualitas gambar, 6) Deteksi anomali, 7) Pemberian skor kepercayaan.",
                category="proses",
                tags=["verifikasi", "proses", "tahapan"]
            ),
            KnowledgeBaseEntry(
                title="Keamanan Data",
                content="Data yang diproses dalam sistem eKYC dilindungi dengan enkripsi end-to-end, penyimpanan yang aman, dan akses yang terbatas. Semua data personal diperlakukan sesuai dengan peraturan perlindungan data dan privasi yang berlaku.",
                category="keamanan",
                tags=["keamanan", "privasi", "enkripsi"]
            )
        ]
        
        self.entries.extend(default_entries)
        logger.info(f"Initialized knowledge base with {len(default_entries)} default entries")
    
    async def initialize_vector_db(self):
        """Initialize vector database"""
        try:
            # Get configuration from environment
            import os
            llm_provider = os.getenv("LLM_PROVIDER", "deepseek")
            api_key = os.getenv("DEEPSEEK_API_KEY") if llm_provider == "deepseek" else os.getenv("OPENAI_API_KEY")
            
            self.vector_db = VectorDatabase(
                elasticsearch_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
                index_name=os.getenv("ELASTICSEARCH_INDEX", "document_vectors"),
                api_key=api_key,
                llm_provider=llm_provider
            )
            
            # Index all knowledge base entries
            for entry in self.entries:
                await self.vector_db.add_document_from_text_async(
                    content=f"{entry.title}. {entry.content}",
                    title=entry.title,
                    document_type="knowledge_base",
                    category=entry.category,
                    metadata={
                        "title": entry.title,
                        "category": entry.category,
                        "tags": entry.tags,
                        "created_at": entry.created_at.isoformat(),
                        "type": "knowledge_base"
                    }
                )
            
            logger.info("Vector database initialized and indexed with knowledge base")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def add_entry(self, entry: KnowledgeBaseEntry):
        """Add new entry to knowledge base"""
        self.entries.append(entry)
        logger.info(f"Added new knowledge base entry: {entry.title}")
    
    def search_entries(self, query: str, category: Optional[str] = None) -> List[KnowledgeBaseEntry]:
        """Search knowledge base entries"""
        results = []
        query_lower = query.lower()
        
        for entry in self.entries:
            # Check if query matches title, content, or tags
            if (query_lower in entry.title.lower() or 
                query_lower in entry.content.lower() or 
                any(query_lower in tag.lower() for tag in entry.tags)):
                
                # Filter by category if specified
                if category is None or entry.category == category:
                    results.append(entry)
        
        return results
    
    async def add_document(self, document_data: Dict[str, Any]) -> int:
        """Add document to knowledge base"""
        try:
            # Create knowledge base entry
            entry = KnowledgeBaseEntry(
                title=document_data.get('title', 'Untitled'),
                content=document_data.get('content', ''),
                category=document_data.get('category', 'general'),
                tags=document_data.get('tags', [])
            )
            
            # Add to local storage
            self.add_entry(entry)
            
            # Add to vector database if available
            chunks_created = 1
            if self.vector_db:
                await self.vector_db.add_document_from_text_async(
                    content=f"{entry.title}. {entry.content}",
                    title=entry.title,
                    document_type=document_data.get('document_type', 'knowledge_base'),
                    category=entry.category,
                    metadata={
                        "title": entry.title,
                        "category": entry.category,
                        "tags": entry.tags,
                        "created_at": entry.created_at.isoformat(),
                        "type": "knowledge_base",
                        **document_data.get('metadata', {})
                    }
                )
                
            logger.info(f"Added document: {entry.title}")
            return chunks_created
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            stats = {
                "document_count": len(self.entries),
                "embedding_count": 0,
                "last_update": datetime.now().isoformat()
            }
            
            # Get vector DB stats if available
            if self.vector_db:
                try:
                    # This would need to be implemented in the vector DB class
                    vector_stats = await self.vector_db.get_stats()
                    stats["embedding_count"] = vector_stats.get("total_embeddings", 0)
                except Exception as e:
                    logger.warning(f"Could not get vector DB stats: {e}")
                    
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "document_count": 0,
                "embedding_count": 0,
                "last_update": "error"
            }
    
    def list_all_documents(self) -> List[Dict[str, Any]]:
        """List all documents in knowledge base"""
        try:
            documents = []
            for i, entry in enumerate(self.entries):
                documents.append({
                    "id": str(i),
                    "title": entry.title,
                    "content": entry.content,
                    "category": entry.category,
                    "tags": entry.tags,
                    "created_at": entry.created_at.isoformat()
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    async def clear_all(self):
        """Clear all knowledge base entries"""
        try:
            # Clear local entries (keep only default ones)
            self.entries = []
            self._initialize_default_knowledge()
            
            # Clear vector database if available
            if self.vector_db:
                # This would need to be implemented in the vector DB class
                try:
                    await self.vector_db.clear_index()
                    # Re-index default entries
                    await self.initialize_vector_db()
                except Exception as e:
                    logger.warning(f"Could not clear vector DB: {e}")
                    
            logger.info("Knowledge base cleared and re-initialized")
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """Delete specific document"""
        try:
            doc_index = int(document_id)
            if 0 <= doc_index < len(self.entries):
                entry = self.entries.pop(doc_index)
                logger.info(f"Deleted document: {entry.title}")
                
                # Note: Vector DB deletion would require additional implementation
                # to track document IDs in the vector store
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    @property
    def es_client(self):
        """Get Elasticsearch client from vector DB"""
        if self.vector_db and hasattr(self.vector_db, 'es_client'):
            return self.vector_db.es_client
        return None

class EKYCRAGSystem:
    """RAG System untuk eKYC"""
    
    def __init__(self):
        self.knowledge_base = EKYCKnowledgeBase()
        self.ai_analyzer = None
        self.conversation_history = {}
    
    async def initialize(self):
        """Initialize RAG system"""
        try:
            # Initialize knowledge base vector DB
            await self.knowledge_base.initialize_vector_db()
            
            # Get configuration from environment
            import os
            llm_provider = os.getenv("LLM_PROVIDER", "deepseek")
            api_key = os.getenv("DEEPSEEK_API_KEY") if llm_provider == "deepseek" else os.getenv("OPENAI_API_KEY")
            model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat") if llm_provider == "deepseek" else "gpt-4"
            
            # Initialize AI analyzer with the same vector DB
            self.ai_analyzer = AIDocumentAnalyzer(
                vector_db=self.knowledge_base.vector_db,
                api_key=api_key,
                llm_provider=llm_provider,
                model_name=model_name
            )
            
            logger.info("RAG system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    async def query(self, rag_query: RAGQuery) -> RAGResponse:
        """Process RAG query"""
        try:
            start_time = datetime.now()
            
            # Search knowledge base
            kb_results = self.knowledge_base.search_entries(
                rag_query.query, 
                rag_query.document_type
            )
            
            # Vector search if available
            vector_results = []
            if self.knowledge_base.vector_db:
                vector_results = await self.knowledge_base.vector_db.search(
                    query=rag_query.query,
                    k=rag_query.max_results
                )
            
            # Combine results
            all_sources = []
            
            # Add knowledge base results
            for entry in kb_results[:rag_query.max_results]:
                all_sources.append({
                    "title": entry.title,
                    "content": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                    "category": entry.category,
                    "tags": entry.tags,
                    "source_type": "knowledge_base",
                    "relevance_score": 0.8  # Mock score
                })
            
            # Add vector search results
            for result in vector_results:
                if result.get('_source', {}).get('type') == 'knowledge_base':
                    all_sources.append({
                        "title": result['_source'].get('title', 'Unknown'),
                        "content": result['_source'].get('text', '')[:200] + "...",
                        "category": result['_source'].get('category', 'general'),
                        "source_type": "vector_search",
                        "relevance_score": result.get('_score', 0.0)
                    })
            
            # Generate answer using AI
            context = "\\n".join([f"- {source['title']}: {source['content']}" for source in all_sources[:3]])
            
            if self.ai_analyzer and self.ai_analyzer.llm:
                try:
                    prompt = f"""
Berdasarkan konteks berikut tentang sistem eKYC:

{context}

Pertanyaan: {rag_query.query}

Berikan jawaban yang informatif dan akurat berdasarkan konteks di atas. Jika informasi tidak cukup, sampaikan dengan jelas.
"""
                    answer_text = await self.ai_analyzer.llm.acall(prompt)
                    
                except Exception as e:
                    logger.error(f"Error generating AI answer: {e}")
                    answer_text = f"Berdasarkan informasi yang tersedia: {context[:300]}..."
            else:
                answer_text = f"Berdasarkan informasi yang tersedia: {context[:300]}..."
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate confidence based on source quality
            confidence = min(0.9, len(all_sources) * 0.2 + 0.1)
            
            response = RAGResponse(
                answer=answer_text,
                sources=all_sources[:rag_query.max_results],
                confidence=confidence,
                query_type="knowledge_base_search",
                processing_time=processing_time
            )
            
            logger.info(f"RAG query processed in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing RAG query: {e}")
            return RAGResponse(
                answer=f"Maaf, terjadi kesalahan dalam memproses pertanyaan: {str(e)}",
                sources=[],
                confidence=0.0,
                query_type="error",
                processing_time=0.0
            )
    
    async def chat(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle chat conversation"""
        try:
            if conversation_id is None:
                conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Initialize conversation if new
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            # Add user message to history
            user_message = ChatMessage(role="user", content=message)
            self.conversation_history[conversation_id].append(user_message)
            
            # Create RAG query
            rag_query = RAGQuery(query=message, max_results=3)
            rag_response = await self.query(rag_query)
            
            # Add assistant message to history
            assistant_message = ChatMessage(role="assistant", content=rag_response.answer)
            self.conversation_history[conversation_id].append(assistant_message)
            
            return {
                "message": rag_response.answer,
                "conversation_id": conversation_id,
                "timestamp": datetime.now(),
                "sources": rag_response.sources,
                "confidence": rag_response.confidence
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "message": f"Maaf, terjadi kesalahan: {str(e)}",
                "conversation_id": conversation_id or "error",
                "timestamp": datetime.now(),
                "sources": [],
                "confidence": 0.0
            }
    
    def get_conversation_history(self, conversation_id: str) -> List[ChatMessage]:
        """Get conversation history"""
        return self.conversation_history.get(conversation_id, [])

async def initialize_ekyc_knowledge_base() -> EKYCRAGSystem:
    """Initialize eKYC knowledge base and RAG system"""
    try:
        rag_system = EKYCRAGSystem()
        await rag_system.initialize()
        logger.info("eKYC RAG system initialized successfully")
        return rag_system
    except Exception as e:
        logger.error(f"Failed to initialize eKYC RAG system: {e}")
        raise