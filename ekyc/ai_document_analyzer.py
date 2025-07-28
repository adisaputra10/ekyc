"""
AI Document Analysis dengan RAG menggunakan Elasticsearch v8 dan LangChain
Advanced system untuk analisis dokumen dengan vector database
"""
import os
import json
import logging
import asyncio
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import hashlib
import re

# LangChain imports
from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import ElasticsearchStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# DeepSeek Configuration
import openai

# Alternative embedding untuk local
from langchain_community.embeddings import HuggingFaceEmbeddings

# DeepSeek LLM wrapper
class DeepSeekLLM:
    """DeepSeek LLM wrapper yang kompatibel dengan LangChain"""
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat", temperature: float = 0.1):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        
        # Configure DeepSeek client
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """Make DeepSeek API call"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Anda adalah expert dalam analisis dokumen identitas Indonesia dengan pengalaman lebih dari 10 tahun."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=kwargs.get("max_tokens", 1500)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            return f"Error dalam analisis DeepSeek: {str(e)}"
    
    async def acall(self, prompt: str, **kwargs) -> str:
        """Async DeepSeek API call"""
        return self.__call__(prompt, **kwargs)

# Utils
import numpy as np
from transformers import pipeline

# Optional imports (create simple models if not available)
try:
    from models import AnalysisResult, EKYCFormData
except ImportError:
    # Simple model definitions
    from pydantic import BaseModel
    from typing import List, Optional
    
    class AnalysisResult(BaseModel):
        document_type: str
        confidence_score: float
        verification_status: str
        
    class EKYCFormData(BaseModel):
        name: str
        nik: Optional[str] = None

try:
    from config import settings
except ImportError:
    # Fallback configuration
    class Settings:
        openai_api_key = None
        elasticsearch_url = "http://localhost:9200"
        elasticsearch_index = "document_vectors"
    settings = Settings()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Advanced document processor dengan LangChain dan AI capabilities"""
    
    def __init__(self, api_key: str = None, llm_provider: str = "deepseek"):
        # Initialize LangChain embeddings
        if api_key and llm_provider == "openai":
            self.embedding_model = OpenAIEmbeddings(openai_api_key=api_key)
        else:
            # Fallback ke HuggingFace embeddings (local) untuk DeepSeek
            self.embedding_model = HuggingFaceEmbeddings(
                model_name='all-MiniLM-L6-v2',
                model_kwargs={'device': 'cpu'}
            )
        
        # Initialize NLP pipeline untuk document classification
        self.classifier = pipeline(
            "text-classification",
            model="microsoft/DialoGPT-medium",
            return_all_scores=True
        )
        
        # LangChain text splitter untuk chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def split_documents(self, text: str, metadata: Dict = None) -> List[Document]:
        """Split text into LangChain Document objects"""
        chunks = self.text_splitter.split_text(text)
        documents = []
        
        for i, chunk in enumerate(chunks):
            doc_metadata = {
                "chunk_index": i,
                "total_chunks": len(chunks),
                "content_length": len(chunk),
                **(metadata or {})
            }
            
            doc = Document(
                page_content=chunk,
                metadata=doc_metadata
            )
            documents.append(doc)
        
        return documents
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities dari document text"""
        
        entities = {
            "names": [],
            "dates": [],
            "numbers": [],
            "addresses": [],
            "emails": [],
            "phones": []
        }
        
        # Extract names (simple pattern for Indonesian names)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        entities["names"] = re.findall(name_pattern, text)
        
        # Extract dates
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'\d{1,2}\s+\w+\s+\d{4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'
        ]
        for pattern in date_patterns:
            entities["dates"].extend(re.findall(pattern, text))
        
        # Extract numbers (NIK, phone, etc.)
        nik_pattern = r'\b\d{16}\b'
        phone_pattern = r'\b\d{10,15}\b'
        entities["numbers"].extend(re.findall(nik_pattern, text))
        entities["phones"].extend(re.findall(phone_pattern, text))
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities["emails"] = re.findall(email_pattern, text)
        
        return entities
    
    def classify_document_type(self, text: str) -> Dict[str, float]:
        """Classify document type menggunakan AI"""
        
        # Keywords untuk classification
        doc_keywords = {
            "ktp": ["kartu tanda penduduk", "nik", "republik indonesia", "ktp"],
            "passport": ["passport", "paspor", "republic of indonesia", "travel document"],
            "sim": ["surat izin mengemudi", "sim", "driver license", "mengemudi"],
            "npwp": ["npwp", "nomor pokok wajib pajak", "tax", "pajak"],
            "contract": ["kontrak", "perjanjian", "agreement", "contract"],
            "invoice": ["invoice", "faktur", "tagihan", "bill"],
            "receipt": ["receipt", "kwitansi", "bukti", "pembayaran"]
        }
        
        scores = {}
        text_lower = text.lower()
        
        for doc_type, keywords in doc_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            scores[doc_type] = score / len(keywords)
        
        return scores
    
    def calculate_document_quality(self, text: str, metadata: Dict = None) -> float:
        """Calculate quality score untuk document"""
        
        quality_score = 0.0
        
        # Text length check
        if len(text) > 100:
            quality_score += 0.2
        if len(text) > 500:
            quality_score += 0.1
        
        # Completeness check
        entities = self.extract_entities(text)
        if entities["names"]:
            quality_score += 0.2
        if entities["dates"]:
            quality_score += 0.1
        if entities["numbers"]:
            quality_score += 0.2
        
        # Language detection (simple)
        indonesian_words = ["dan", "atau", "yang", "di", "ke", "dari", "untuk", "dengan", "pada"]
        indonesian_count = sum(1 for word in indonesian_words if word in text.lower())
        if indonesian_count > 2:
            quality_score += 0.2
        
        # Structure check
        if "\n" in text:
            quality_score += 0.1
        
        return min(quality_score, 1.0)

class VectorDatabase:
    """Vector database menggunakan LangChain ElasticsearchStore"""
    
    def __init__(self, 
                 elasticsearch_url: str = "http://localhost:9200",
                 index_name: str = "document_vectors",
                 api_key: str = None,
                 llm_provider: str = "deepseek"):
        
        self.es_url = elasticsearch_url
        self.index_name = index_name
        self.llm_provider = llm_provider
        
        # Initialize LangChain embeddings
        if api_key and llm_provider == "openai":
            self.embedding_model = OpenAIEmbeddings(openai_api_key=api_key)
        else:
            # Use HuggingFace embeddings untuk DeepSeek atau sebagai fallback
            self.embedding_model = HuggingFaceEmbeddings(
                model_name='all-MiniLM-L6-v2',
                model_kwargs={'device': 'cpu'}
            )
        
        # Initialize LangChain Elasticsearch vector store
        self.vector_store = ElasticsearchStore(
            es_url=elasticsearch_url,
            index_name=index_name,
            embedding=self.embedding_model,
            es_params={
                "timeout": 30,
                "max_retries": 3,
                "retry_on_timeout": True
            }
        )
        
        logger.info(f"Initialized LangChain ElasticsearchStore: {index_name} with {llm_provider}")
    
    async def initialize(self):
        """Initialize method for backward compatibility"""
        # Components are already initialized in __init__
        return True
    
    async def store_documents(self, documents: List[dict]) -> List[str]:
        """Store documents in vector database using LangChain"""
        try:
            # Convert to LangChain Document format
            langchain_docs = []
            for doc in documents:
                langchain_docs.append(Document(
                    page_content=doc["content"],
                    metadata=doc.get("metadata", {})
                ))
            
            # Add to vector store
            ids = self.vector_store.add_documents(langchain_docs)
            logger.info(f"Added {len(ids)} documents to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error storing documents: {str(e)}")
            raise
    
    async def search(self, query: str, k: int = 5) -> List[dict]:
        """Search documents using vector similarity"""
        try:
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def add_documents_async(self, 
                                documents: List[Document],
                                processor: DocumentProcessor = None) -> List[str]:
        """Tambah dokumen ke vector database menggunakan LangChain (async)"""
        
        try:
            # Enrich metadata dengan analysis results
            enriched_docs = []
            
            for doc in documents:
                content = doc.page_content
                
                if processor:
                    # Add entity extraction
                    entities = processor.extract_entities(content)
                    classification_scores = processor.classify_document_type(content)
                    quality_score = processor.calculate_document_quality(content)
                    
                    # Update metadata
                    doc.metadata.update({
                        "entities": entities,
                        "classification_scores": classification_scores,
                        "quality_score": quality_score,
                        "document_hash": hashlib.md5(content.encode()).hexdigest(),
                        "created_at": datetime.now().isoformat()
                    })
                
                enriched_docs.append(doc)
            
            # Add to vector store
            doc_ids = await asyncio.to_thread(
                self.vector_store.add_documents,
                enriched_docs
            )
            
            logger.info(f"Added {len(enriched_docs)} documents to vector store")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    async def add_document_from_text_async(self, 
                                         content: str,
                                         title: str = "",
                                         document_type: str = "general",
                                         category: str = "document",
                                         metadata: Dict = None,
                                         processor: DocumentProcessor = None) -> List[str]:
        """Tambah dokumen dari text ke vector database (async)"""
        
        if metadata is None:
            metadata = {}
        
        # Add basic metadata
        base_metadata = {
            "title": title,
            "document_type": document_type,
            "category": category,
            **metadata
        }
        
        # Split into documents
        if processor is None:
            processor = DocumentProcessor()
        
        documents = processor.split_documents(content, base_metadata)
        
        # Add to vector store
        return await self.add_documents_async(documents, processor)
    
    async def search_similar_async(self, 
                                 query: str,
                                 top_k: int = 5,
                                 filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Search similar documents menggunakan LangChain vector similarity (async)"""
        
        try:
            # Perform similarity search
            if filter_dict:
                # LangChain support untuk metadata filtering
                docs_with_scores = await asyncio.to_thread(
                    self.vector_store.similarity_search_with_score,
                    query,
                    k=top_k,
                    filter=filter_dict
                )
            else:
                docs_with_scores = await asyncio.to_thread(
                    self.vector_store.similarity_search_with_score,
                    query,
                    k=top_k
                )
            
            # Format results
            results = []
            for doc, score in docs_with_scores:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "title": doc.metadata.get("title", ""),
                    "document_type": doc.metadata.get("document_type", "unknown"),
                    "category": doc.metadata.get("category", "document"),
                    "quality_score": doc.metadata.get("quality_score", 0.0)
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_retriever(self, 
                     search_type: str = "similarity",
                     search_kwargs: Dict = None):
        """Get LangChain retriever untuk RAG chains"""
        
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def _setup_index(self):
        """Setup Elasticsearch index dengan mapping untuk vectors"""
        
        mapping = {
            "mappings": {
                "properties": {
                    "content": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "title": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "document_type": {
                        "type": "keyword"
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "vector": {
                        "type": "dense_vector",
                        "dims": 384,  # Dimensi untuk all-MiniLM-L6-v2
                        "index": True,
                        "similarity": "cosine"
                    },
                    "entities": {
                        "type": "object",
                        "properties": {
                            "names": {"type": "keyword"},
                            "dates": {"type": "keyword"},
                            "numbers": {"type": "keyword"},
                            "emails": {"type": "keyword"},
                            "phones": {"type": "keyword"}
                        }
                    },
                    "quality_score": {
                        "type": "float"
                    },
                    "classification_scores": {
                        "type": "object"
                    },
                    "metadata": {
                        "type": "object"
                    },
                    "created_at": {
                        "type": "date"
                    },
                    "document_hash": {
                        "type": "keyword"
                    }
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index": {
                    "knn": {
                        "algo_param": {
                            "ef_search": 100
                        }
                    }
                }
            }
        }
        
        try:
            if not self.es_client.indices.exists(index=self.index_name):
                self.es_client.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Created Elasticsearch index: {self.index_name}")
            else:
                logger.info(f"Elasticsearch index {self.index_name} already exists")
        except Exception as e:
            logger.error(f"Error setting up Elasticsearch index: {str(e)}")
            raise
    
    async def add_document_async(self, 
                               content: str,
                               title: str = "",
                               document_type: str = "general",
                               category: str = "document",
                               metadata: Dict = None,
                               processor: DocumentProcessor = None) -> List[str]:
        """Tambah dokumen ke vector database (async)"""
        
        if metadata is None:
            metadata = {}
        
        if processor is None:
            processor = DocumentProcessor()
        
        # Generate document hash untuk deduplikasi
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Check if document already exists
        existing = await self.async_es_client.search(
            index=self.index_name,
            body={"query": {"term": {"document_hash": content_hash}}},
            size=1
        )
        
        if existing['hits']['total']['value'] > 0:
            logger.info(f"Document with hash {content_hash} already exists")
            return [existing['hits']['hits'][0]['_id']]
        
        # Process document
        entities = processor.extract_entities(content)
        classification_scores = processor.classify_document_type(content)
        quality_score = processor.calculate_document_quality(content, metadata)
        
        # Split text into chunks
        chunks = processor.text_splitter.split_text(content)
        doc_ids = []
        
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = self.embedding_model.encode(chunk).tolist()
            
            # Prepare document
            doc = {
                "content": chunk,
                "title": f"{title} (chunk {i+1})" if title else f"Chunk {i+1}",
                "document_type": document_type,
                "category": category,
                "vector": embedding,
                "entities": entities,
                "quality_score": quality_score,
                "classification_scores": classification_scores,
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "original_title": title,
                    "content_length": len(chunk)
                },
                "created_at": datetime.now().isoformat(),
                "document_hash": f"{content_hash}_{i}"
            }
            
            # Index document
            result = await self.async_es_client.index(index=self.index_name, body=doc)
            doc_ids.append(result['_id'])
        
        logger.info(f"Added document '{title}' with {len(chunks)} chunks")
        return doc_ids
    
    async def search_similar_async(self, 
                                 query: str,
                                 top_k: int = 5,
                                 document_type: Optional[str] = None,
                                 category: Optional[str] = None,
                                 min_quality: float = 0.0) -> List[Dict]:
        """Search similar documents menggunakan vector similarity (async)"""
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Build search query dengan kNN
        search_body = {
            "knn": {
                "field": "vector",
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": top_k * 2
            },
            "query": {
                "bool": {
                    "filter": []
                }
            },
            "_source": [
                "content", "title", "document_type", "category", 
                "entities", "quality_score", "classification_scores", "metadata"
            ]
        }
        
        # Add filters
        filters = []
        if document_type:
            filters.append({"term": {"document_type": document_type}})
        if category:
            filters.append({"term": {"category": category}})
        if min_quality > 0:
            filters.append({"range": {"quality_score": {"gte": min_quality}}})
        
        if filters:
            search_body["query"]["bool"]["filter"] = filters
        
        try:
            response = await self.async_es_client.search(
                index=self.index_name, 
                body=search_body
            )
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    "content": hit['_source']['content'],
                    "title": hit['_source']['title'],
                    "document_type": hit['_source']['document_type'],
                    "category": hit['_source']['category'],
                    "entities": hit['_source']['entities'],
                    "quality_score": hit['_source']['quality_score'],
                    "classification_scores": hit['_source']['classification_scores'],
                    "metadata": hit['_source']['metadata'],
                    "score": hit['_score']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def search_hybrid_async(self, 
                                query: str,
                                top_k: int = 5,
                                semantic_weight: float = 0.7,
                                keyword_weight: float = 0.3) -> List[Dict]:
        """Hybrid search: kombinasi semantic dan keyword search (async)"""
        
        # Semantic search dengan kNN
        semantic_results = await self.search_similar_async(query, top_k)
        
        # Keyword search
        keyword_search = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content^2", "title^1.5"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "size": top_k,
            "_source": [
                "content", "title", "document_type", "category", 
                "entities", "quality_score", "metadata"
            ]
        }
        
        try:
            keyword_response = await self.async_es_client.search(
                index=self.index_name, 
                body=keyword_search
            )
            
            keyword_results = []
            for hit in keyword_response['hits']['hits']:
                keyword_results.append({
                    "content": hit['_source']['content'],
                    "title": hit['_source']['title'],
                    "document_type": hit['_source']['document_type'],
                    "category": hit['_source']['category'],
                    "entities": hit['_source']['entities'],
                    "quality_score": hit['_source']['quality_score'],
                    "metadata": hit['_source']['metadata'],
                    "score": hit['_score']
                })
            
            # Combine results
            combined_results = self._combine_search_results(
                semantic_results, keyword_results,
                semantic_weight, keyword_weight
            )
            
            return combined_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return semantic_results
    
    def _combine_search_results(self, 
                               semantic_results: List[Dict],
                               keyword_results: List[Dict],
                               semantic_weight: float,
                               keyword_weight: float) -> List[Dict]:
        """Combine dan rerank search results"""
        
        # Normalize scores
        if semantic_results:
            max_semantic = max(r['score'] for r in semantic_results)
            for r in semantic_results:
                r['normalized_semantic_score'] = r['score'] / max_semantic if max_semantic > 0 else 0
        
        if keyword_results:
            max_keyword = max(r['score'] for r in keyword_results)
            for r in keyword_results:
                r['normalized_keyword_score'] = r['score'] / max_keyword if max_keyword > 0 else 0
        
        # Create lookup maps
        semantic_lookup = {
            r['content'][:100]: r['normalized_semantic_score'] 
            for r in semantic_results
        }
        keyword_lookup = {
            r['content'][:100]: r['normalized_keyword_score'] 
            for r in keyword_results
        }
        
        # Combine unique results
        all_contents = set()
        all_results = {}
        
        for result in semantic_results + keyword_results:
            content_key = result['content'][:100]
            if content_key not in all_results:
                all_results[content_key] = result
                all_contents.add(content_key)
        
        # Calculate combined scores
        final_results = []
        for content_key in all_contents:
            result = all_results[content_key].copy()
            
            semantic_score = semantic_lookup.get(content_key, 0)
            keyword_score = keyword_lookup.get(content_key, 0)
            
            combined_score = (
                semantic_weight * semantic_score + 
                keyword_weight * keyword_score
            )
            
            result['combined_score'] = combined_score
            result['semantic_score'] = semantic_score
            result['keyword_score'] = keyword_score
            
            final_results.append(result)
        
        # Sort by combined score
        final_results.sort(key=lambda x: x['combined_score'], reverse=True)
        return final_results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        try:
            # Access the underlying Elasticsearch client
            es_client = self.vector_store.client if hasattr(self.vector_store, 'client') else None
            
            if es_client:
                # Get index stats from Elasticsearch
                stats = es_client.indices.stats(index=self.index_name)
                total_docs = stats['indices'][self.index_name]['total']['docs']['count']
                
                return {
                    "total_embeddings": total_docs,
                    "index_name": self.index_name,
                    "index_size": stats['indices'][self.index_name]['total']['store']['size_in_bytes'],
                    "embedding_model": "all-MiniLM-L6-v2" if not hasattr(self.embedding_model, 'model_name') else self.embedding_model.model_name
                }
            else:
                return {
                    "total_embeddings": 0,
                    "index_name": self.index_name,
                    "index_size": 0,
                    "embedding_model": "unknown"
                }
        except Exception as e:
            logger.error(f"Error getting vector DB stats: {e}")
            return {
                "total_embeddings": 0,
                "index_name": self.index_name,
                "index_size": 0,
                "embedding_model": "error"
            }
    
    async def clear_index(self):
        """Clear all documents from the vector database index"""
        try:
            # Access the underlying Elasticsearch client
            es_client = self.vector_store.client if hasattr(self.vector_store, 'client') else None
            
            if es_client:
                # Delete all documents from the index
                es_client.delete_by_query(
                    index=self.index_name,
                    body={"query": {"match_all": {}}}
                )
                
                logger.info(f"Cleared all documents from index: {self.index_name}")
            else:
                logger.warning("No Elasticsearch client available for clearing index")
                
        except Exception as e:
            logger.error(f"Error clearing vector DB index: {e}")
            raise

class AIDocumentAnalyzer:
    """AI-powered document analyzer dengan DeepSeek dan LangChain RAG capabilities"""
    
    def __init__(self,
                 vector_db: VectorDatabase,
                 api_key: str = "",
                 llm_provider: str = "deepseek",
                 model_name: str = "deepseek-chat",
                 temperature: float = 0.1):
        
        self.vector_db = vector_db
        self.processor = DocumentProcessor(api_key, llm_provider)
        self.api_key = api_key
        self.llm_provider = llm_provider
        self.model_name = model_name
        
        # Initialize LLM berdasarkan provider
        if llm_provider == "deepseek":
            self.llm = DeepSeekLLM(
                api_key=api_key,
                model_name=model_name,
                temperature=temperature
            )
        else:  # OpenAI fallback
            self.llm = ChatOpenAI(
                openai_api_key=api_key,
                model_name=model_name,
                temperature=temperature
            )
        
        # Initialize RAG chain
        self._setup_rag_chain()
    
    def initialize(self):
        """Initialize method for AIDocumentAnalyzer"""
        # Components are already initialized in __init__
        return True
    
    async def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """Analyze document from file path"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic analysis
            entities = self.processor.extract_entities(content)
            classification_scores = self.processor.classify_document_type(content)
            quality_score = self.processor.calculate_document_quality(content)
            
            # Store in vector database
            documents = [{"content": content, "metadata": {"file_path": file_path}}]
            await self.vector_db.store_documents(documents)
            
            return {
                "status": "success",
                "analysis": {
                    "document_type": max(classification_scores, key=classification_scores.get) if classification_scores else "unknown",
                    "quality_score": quality_score,
                    "entities": entities,
                    "classification_scores": classification_scores
                },
                "content": content
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "analysis": {
                    "document_type": "unknown",
                    "quality_score": 0.0,
                    "entities": [],
                    "classification_scores": {}
                }
            }
    
    async def analyze_company_deed(self, text: str) -> Dict[str, Any]:
        """Analisis khusus untuk akta perusahaan menggunakan AI"""
        try:
            if self.llm_provider == "deepseek" and hasattr(self.llm, 'acall'):
                prompt = f"""
Analisis dokumen akta perusahaan berikut dan ekstrak informasi penting:

DOKUMEN:
{text}

Ekstrak informasi berikut:
1. Nama perusahaan
2. Jenis perusahaan (PT, CV, UD, dll)
3. Nomor akta/registrasi
4. Nama notaris
5. Nomor notaris
6. Tanggal pendirian
7. Modal dasar
8. Bidang usaha
9. Alamat perusahaan
10. Daftar direktur/pengurus
11. Daftar pemegang saham

Berikan respons dalam format JSON dengan struktur:
{{
    "company_name": "...",
    "company_type": "...",
    "registration_number": "...",
    "notary_name": "...",
    "notary_number": "...",
    "establishment_date": "...",
    "capital_amount": "...",
    "business_field": "...",
    "company_address": "...",
    "directors": ["..."],
    "shareholders": ["..."],
    "validity_assessment": "...",
    "completeness_score": 0.0,
    "anomalies": ["..."]
}}

Jika informasi tidak ditemukan, gunakan null atau array kosong.
"""
                
                try:
                    response = await self.llm.acall(prompt)
                    # Try to parse JSON response
                    import json
                    try:
                        analysis_result = json.loads(response)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, create a structured response
                        analysis_result = {
                            "company_name": "Tidak dapat diekstrak",
                            "company_type": "Tidak dapat diekstrak",
                            "registration_number": None,
                            "notary_name": None,
                            "notary_number": None,
                            "establishment_date": None,
                            "capital_amount": None,
                            "business_field": None,
                            "company_address": None,
                            "directors": [],
                            "shareholders": [],
                            "validity_assessment": "Analisis tidak dapat diselesaikan",
                            "completeness_score": 0.5,
                            "anomalies": ["Format respons AI tidak valid"],
                            "raw_response": response
                        }
                    
                    return analysis_result
                    
                except Exception as e:
                    return {
                        "company_name": "Error dalam analisis",
                        "error": str(e),
                        "validity_assessment": "Gagal dianalisis",
                        "completeness_score": 0.0,
                        "anomalies": [f"Error AI: {str(e)}"]
                    }
            else:
                return {
                    "company_name": "AI tidak tersedia",
                    "validity_assessment": "Analisis manual diperlukan",
                    "completeness_score": 0.0,
                    "anomalies": ["AI engine tidak tersedia"]
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "validity_assessment": "Error dalam analisis",
                "completeness_score": 0.0,
                "anomalies": [f"System error: {str(e)}"]
            }

    async def query_rag(self, query: str) -> Dict[str, Any]:
        """Query RAG system"""
        try:
            # Search for relevant documents
            search_results = await self.vector_db.search(query, k=3)
            
            # Format context
            context_parts = []
            for i, result in enumerate(search_results):
                context_parts.append(f"Document {i+1}: {result['content'][:200]}...")
            
            context = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
            
            if self.llm_provider == "deepseek" and hasattr(self.llm, 'acall'):
                prompt = f"""Based on the following context documents, answer the question:

CONTEXT:
{context}

QUESTION: {query}

Provide a detailed and accurate answer based on the context."""
                
                try:
                    answer = await self.llm.acall(prompt)
                except Exception as e:
                    answer = f"Error calling DeepSeek: {str(e)}"
            else:
                answer = "DeepSeek API not available or no API key provided"
            
            return {
                "answer": answer,
                "sources": search_results,
                "context": context
            }
            
        except Exception as e:
            return {
                "answer": f"Error in RAG query: {str(e)}",
                "sources": [],
                "context": ""
            }
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Chat with AI"""
        try:
            if not messages:
                return {"content": "No messages provided"}
            
            # Get last user message
            user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                return {"content": "No user message found"}
            
            if self.llm_provider == "deepseek" and hasattr(self.llm, 'acall'):
                try:
                    response = await self.llm.acall(user_message)
                except Exception as e:
                    response = f"Error calling DeepSeek: {str(e)}"
            else:
                response = "DeepSeek API not available or no API key provided"
            
            return {"content": response}
            
        except Exception as e:
            return {"content": f"Error in chat: {str(e)}"}
    
    def _setup_rag_chain(self):
        """Setup LangChain RAG chain untuk document analysis dengan DeepSeek"""
        
        # Custom prompt untuk document analysis
        analysis_prompt = PromptTemplate(
            input_variables=["context", "question", "document_type", "entities"],
            template="""
Anda adalah expert dalam analisis dokumen identitas Indonesia dengan pengalaman lebih dari 10 tahun.

KONTEKS DOKUMEN REFERENSI:
{context}

JENIS DOKUMEN: {document_type}
ENTITAS DIEKSTRAK: {entities}

PERTANYAAN ANALISIS:
{question}

Berikan analisis yang mencakup:
1. Validasi kelengkapan data
2. Konsistensi informasi  
3. Deteksi potensi fraud atau anomali
4. Kualitas dan kejelasan dokumen
5. Rekomendasi specific untuk jenis dokumen ini
6. Skor kepercayaan (1-10)

Format jawaban dalam bahasa Indonesia yang professional dan detail.
"""
        )
        
        # Get retriever dari vector database
        retriever = self.vector_db.get_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        # Setup RAG chain dengan DeepSeek atau OpenAI
        if self.llm_provider == "deepseek":
            # Manual RAG chain untuk DeepSeek
            self.rag_chain = None
            self.retriever = retriever
            self.analysis_prompt = analysis_prompt
        else:
            # LangChain RetrievalQA untuk OpenAI
            self.rag_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={
                    "prompt": analysis_prompt
                },
                return_source_documents=True
            )
        
        # Setup conversational chain dengan memory (hanya untuk OpenAI)
        if self.llm_provider != "deepseek":
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            self.conversational_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=self.memory,
                return_source_documents=True
            )
    
    async def analyze_document_with_rag(self, 
                                      content: str,
                                      document_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Comprehensive document analysis dengan DeepSeek/OpenAI RAG"""
        
        try:
            # 1. Basic document processing
            entities = self.processor.extract_entities(content)
            classification_scores = self.processor.classify_document_type(content)
            quality_score = self.processor.calculate_document_quality(content)
            
            # 2. Determine document type
            predicted_type = max(classification_scores, key=classification_scores.get)
            confidence = classification_scores[predicted_type]
            
            # 3. Prepare analysis question
            analysis_question = f"""
            Analisa dokumen berikut dengan detail:
            
            KONTEN DOKUMEN:
            {content[:2000]}
            
            Fokus pada validasi, konsistensi, dan deteksi fraud untuk dokumen jenis {predicted_type}.
            """
            
            # 4. Run RAG analysis berdasarkan provider
            if self.llm_provider == "deepseek":
                # Manual RAG untuk DeepSeek
                llm_analysis, source_documents = await self._deepseek_rag_analysis(
                    analysis_question, predicted_type, entities
                )
            else:
                # LangChain RAG untuk OpenAI
                rag_result = await asyncio.to_thread(
                    self.rag_chain,
                    {
                        "query": analysis_question,
                        "document_type": predicted_type,
                        "entities": json.dumps(entities, ensure_ascii=False)
                    }
                )
                llm_analysis = rag_result["result"]
                source_documents = rag_result["source_documents"]
            
            # 5. Format source documents
            similar_docs = []
            for doc in source_documents:
                if hasattr(doc, 'page_content'):
                    # LangChain Document object
                    similar_docs.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "title": doc.metadata.get("title", ""),
                        "document_type": doc.metadata.get("document_type", "unknown"),
                        "quality_score": doc.metadata.get("quality_score", 0.0)
                    })
                else:
                    # Dict object dari manual search
                    similar_docs.append(doc)
            
            # 6. Calculate final scores
            final_confidence = min(confidence + (quality_score * 0.3), 1.0)
            
            # 7. Determine verification status
            if final_confidence >= 0.8 and quality_score >= 0.7:
                verification_status = "verified"
            elif final_confidence >= 0.6 and quality_score >= 0.5:
                verification_status = "requires_review"
            else:
                verification_status = "rejected"
            
            return {
                "document_type": predicted_type,
                "confidence_score": final_confidence,
                "quality_score": quality_score,
                "verification_status": verification_status,
                "entities": entities,
                "classification_scores": classification_scores,
                "llm_analysis": llm_analysis,
                "similar_documents": similar_docs,
                "extracted_content": content[:1000] + "..." if len(content) > 1000 else content,
                "recommendations": self._generate_recommendations(
                    verification_status, quality_score, llm_analysis
                ),
                "metadata": {
                    "content_length": len(content),
                    "processing_timestamp": datetime.now().isoformat(),
                    "model_version": f"v2.0_{self.llm_provider}",
                    "rag_sources": len(source_documents),
                    "llm_provider": self.llm_provider
                }
            }
            
        except Exception as e:
            logger.error(f"Error in document analysis: {str(e)}")
            return {
                "document_type": "unknown",
                "confidence_score": 0.0,
                "quality_score": 0.0,
                "verification_status": "error",
                "error": str(e),
                "entities": {},
                "recommendations": ["Terjadi error dalam analisis. Silakan coba lagi."]
            }
    
    async def _deepseek_rag_analysis(self, question: str, document_type: str, entities: Dict) -> tuple:
        """Manual RAG analysis untuk DeepSeek"""
        
        try:
            # 1. Search untuk relevant documents
            search_query = f"analisis dokumen {document_type} {' '.join(entities.get('names', [])[:2])}"
            similar_docs = await self.vector_db.search_similar_async(search_query, top_k=3)
            
            # 2. Build context
            context_parts = []
            for i, doc in enumerate(similar_docs):
                context_parts.append(f"Dokumen referensi {i+1}:\n{doc['content'][:500]}...")
            
            context = "\n\n".join(context_parts) if context_parts else "Tidak ada dokumen referensi."
            
            # 3. Format prompt dengan context
            prompt = self.analysis_prompt.format(
                context=context,
                question=question,
                document_type=document_type,
                entities=json.dumps(entities, ensure_ascii=False)
            )
            
            # 4. Call DeepSeek
            llm_analysis = await self.llm.acall(prompt)
            
            return llm_analysis, similar_docs
            
        except Exception as e:
            logger.error(f"Error in DeepSeek RAG analysis: {str(e)}")
            return f"Error dalam analisis DeepSeek: {str(e)}", []
    
    async def chat_with_documents(self, 
                                question: str,
                                context_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """Chat interface untuk berinteraksi dengan knowledge base"""
        
        try:
            if self.llm_provider == "deepseek":
                # Manual chat untuk DeepSeek
                # 1. Search untuk relevant documents
                similar_docs = await self.vector_db.search_similar_async(question, top_k=5)
                
                # 2. Build context
                context_parts = []
                for i, doc in enumerate(similar_docs):
                    context_parts.append(f"Dokumen {i+1}:\n{doc['content'][:300]}...")
                
                context = "\n\n".join(context_parts) if context_parts else "Tidak ada dokumen referensi."
                
                # 3. Format prompt
                chat_prompt = f"""
                Berdasarkan konteks dokumen berikut, jawab pertanyaan dengan detail dan akurat:
                
                KONTEKS:
                {context}
                
                PERTANYAAN: {question}
                
                Berikan jawaban yang informatif dan professional dalam bahasa Indonesia.
                """
                
                # 4. Call DeepSeek
                answer = await self.llm.acall(chat_prompt)
                
                return {
                    "answer": answer,
                    "source_documents": [
                        {
                            "content": doc["content"],
                            "metadata": doc.get("metadata", {})
                        }
                        for doc in similar_docs
                    ],
                    "chat_history": [],
                    "llm_provider": "deepseek"
                }
                
            else:
                # LangChain conversational chain untuk OpenAI
                result = await asyncio.to_thread(
                    self.conversational_chain,
                    {"question": question}
                )
                
                return {
                    "answer": result["answer"],
                    "source_documents": [
                        {
                            "content": doc.page_content,
                            "metadata": doc.metadata
                        }
                        for doc in result["source_documents"]
                    ],
                    "chat_history": self.memory.chat_memory.messages,
                    "llm_provider": "openai"
                }
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return {
                "answer": f"Maaf, terjadi error: {str(e)}",
                "source_documents": [],
                "chat_history": [],
                "llm_provider": self.llm_provider
            }
    
    async def analyze_document_with_rag(self, 
                                      content: str,
                                      document_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Comprehensive document analysis dengan RAG"""
        
        try:
            # 1. Basic document processing
            entities = self.processor.extract_entities(content)
            classification_scores = self.processor.classify_document_type(content)
            quality_score = self.processor.calculate_document_quality(content)
            
            # 2. Determine document type
            predicted_type = max(classification_scores, key=classification_scores.get)
            confidence = classification_scores[predicted_type]
            
            # 3. Search for similar documents dalam knowledge base
            search_query = f"analisis dokumen {predicted_type} {' '.join(entities.get('names', [])[:2])}"
            similar_docs = await self.vector_db.search_hybrid_async(search_query, top_k=3)
            
            # 4. Build context untuk LLM
            context_parts = []
            for i, doc in enumerate(similar_docs):
                context_parts.append(f"Dokumen referensi {i+1}:\n{doc['content'][:500]}...")
            
            context = "\n\n".join(context_parts) if context_parts else "Tidak ada dokumen referensi."
            
            # 5. Generate LLM analysis
            llm_analysis = await self._get_llm_analysis(
                content, predicted_type, entities, context, document_context
            )
            
            # 6. Calculate final scores
            final_confidence = min(confidence + (quality_score * 0.3), 1.0)
            
            # 7. Determine verification status
            if final_confidence >= 0.8 and quality_score >= 0.7:
                verification_status = "verified"
            elif final_confidence >= 0.6 and quality_score >= 0.5:
                verification_status = "requires_review"
            else:
                verification_status = "rejected"
            
            return {
                "document_type": predicted_type,
                "confidence_score": final_confidence,
                "quality_score": quality_score,
                "verification_status": verification_status,
                "entities": entities,
                "classification_scores": classification_scores,
                "llm_analysis": llm_analysis,
                "similar_documents": similar_docs,
                "extracted_content": content[:1000] + "..." if len(content) > 1000 else content,
                "recommendations": self._generate_recommendations(
                    verification_status, quality_score, llm_analysis
                ),
                "metadata": {
                    "content_length": len(content),
                    "processing_timestamp": datetime.now().isoformat(),
                    "model_version": "v2.0"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in document analysis: {str(e)}")
            return {
                "document_type": "unknown",
                "confidence_score": 0.0,
                "quality_score": 0.0,
                "verification_status": "error",
                "error": str(e),
                "entities": {},
                "recommendations": ["Terjadi error dalam analisis. Silakan coba lagi."]
            }
    
    def _generate_recommendations(self, 
                                verification_status: str,
                                quality_score: float,
                                llm_analysis: str) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        if verification_status == "rejected":
            recommendations.append("Dokumen ditolak. Mohon upload ulang dengan kualitas yang lebih baik.")
            recommendations.append("Pastikan semua informasi terlihat jelas dan tidak buram.")
        
        if quality_score < 0.5:
            recommendations.append("Kualitas dokumen perlu diperbaiki.")
            recommendations.append("Gunakan pencahayaan yang baik saat mengambil foto.")
            recommendations.append("Pastikan dokumen tidak terlipat atau rusak.")
        
        if verification_status == "requires_review":
            recommendations.append("Dokumen memerlukan review manual.")
            recommendations.append("Tim akan melakukan verifikasi tambahan dalam 1-2 hari kerja.")
        
        # Extract recommendations dari LLM analysis
        if "rekomendasi" in llm_analysis.lower():
            lines = llm_analysis.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['rekomen', 'saran', 'sebaiknya']):
                    if len(line.strip()) > 20:
                        recommendations.append(line.strip())
        
        return recommendations[:5]  # Limit to 5 recommendations

# Utility functions
async def initialize_knowledge_base(vector_db: VectorDatabase, api_key: str = None, llm_provider: str = "deepseek"):
    """Initialize knowledge base dengan sample data menggunakan LangChain"""
    
    knowledge_data = [
        {
            "title": "Standar Dokumen KTP Indonesia",
            "content": """
            Kartu Tanda Penduduk (KTP) Indonesia memiliki standar sebagai berikut:
            
            Format NIK: 16 digit yang terdiri dari:
            - 6 digit kode wilayah (provinsi, kabupaten/kota, kecamatan)
            - 6 digit tanggal lahir (DDMMYY dengan kode gender)
            - 4 digit nomor urut
            
            Elemen wajib:
            - Foto wajah ukuran 2x3 cm
            - Nama lengkap sesuai akta kelahiran
            - Tempat dan tanggal lahir
            - Jenis kelamin
            - Alamat lengkap
            - RT/RW, Kelurahan/Desa, Kecamatan
            - Agama
            - Status perkawinan
            - Pekerjaan
            - Kewarganegaraan Indonesia
            - Tanda tangan
            
            Fitur keamanan:
            - Hologram dengan logo Garuda
            - Microtext
            - Invisible ink
            - Special paper material
            """,
            "document_type": "ktp",
            "category": "standard"
        },
        {
            "title": "Deteksi Fraud Dokumen Identitas",
            "content": """
            Indikator fraud pada dokumen identitas:
            
            1. Fisik dokumen:
               - Kualitas kertas berbeda dari asli
               - Warna tidak konsisten
               - Font yang salah
               - Hologram rusak atau hilang
               - Laminasi yang buruk
            
            2. Data tidak konsisten:
               - NIK format salah
               - Tanggal lahir tidak masuk akal
               - Alamat tidak valid
               - Foto tidak sesuai
               - Tanda tangan berbeda
            
            3. Red flags:
               - Dokumen terlalu baru untuk usia yang diklaim
               - Informasi yang bertentangan
               - Kualitas foto yang sangat berbeda
               - Kesalahan ejaan pada nama tempat
               - Format tanggal yang salah
            
            4. Teknik verifikasi:
               - Cross-check dengan database resmi
               - Biometric verification
               - Document authentication
               - Background check
            """,
            "document_type": "general",
            "category": "fraud_detection"
        },
        {
            "title": "Standar Passport Indonesia",
            "content": """
            Passport Republik Indonesia memiliki standar internasional:
            
            Format dan Elemen:
            - Nomor passport: 8 karakter (1 huruf + 7 angka)
            - Halaman data personal dengan microprint
            - Machine Readable Zone (MRZ)
            - Foto digital dengan ghost image
            - Chip elektronik (e-passport)
            
            Fitur keamanan:
            - RFID chip dengan biometric data
            - Security laminate dengan hologram
            - Invisible UV ink
            - Watermark Garuda
            - Security thread
            - Rainbow printing
            
            Validasi penting:
            - Tanggal penerbitan dan expiry
            - Konsistensi data dengan KTP
            - Kualitas foto dan tanda tangan
            - Machine readable zone accuracy
            """,
            "document_type": "passport",
            "category": "standard"
        }
    ]
    
    processor = DocumentProcessor(api_key, llm_provider)
    
    for data in knowledge_data:
        await vector_db.add_document_from_text_async(
            content=data["content"],
            title=data["title"],
            document_type=data["document_type"],
            category=data["category"],
            processor=processor
        )
    
    logger.info(f"Knowledge base initialized with {llm_provider} sample data")

# Example usage dengan DeepSeek
async def main():
    # Configuration
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key")
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # deepseek atau openai
    
    # Initialize components dengan DeepSeek
    vector_db = VectorDatabase(
        elasticsearch_url=ELASTICSEARCH_URL,
        api_key=DEEPSEEK_API_KEY,
        llm_provider=LLM_PROVIDER
    )
    
    analyzer = AIDocumentAnalyzer(
        vector_db=vector_db,
        api_key=DEEPSEEK_API_KEY,
        llm_provider=LLM_PROVIDER,
        model_name="deepseek-chat"
    )
    
    # Initialize knowledge base
    await initialize_knowledge_base(vector_db, DEEPSEEK_API_KEY, LLM_PROVIDER)
    
    # Sample document analysis
    sample_document = """
    REPUBLIK INDONESIA
    KARTU TANDA PENDUDUK
    
    NIK: 3171234567890123
    Nama: BUDI SANTOSO
    Tempat/Tgl Lahir: JAKARTA, 15-08-1990
    Jenis Kelamin: LAKI-LAKI
    Alamat: JL. MERDEKA NO. 123
    RT/RW: 001/002
    Kel/Desa: MERDEKA
    Kecamatan: PUSAT
    Agama: ISLAM
    Status Perkawinan: KAWIN
    Pekerjaan: KARYAWAN SWASTA
    Kewarganegaraan: WNI
    """
    
    print(f"🔍 Analyzing document with {LLM_PROVIDER.upper()} RAG...")
    result = await analyzer.analyze_document_with_rag(sample_document)
    
    print("\n📊 Analysis Result:")
    print(f"Document Type: {result['document_type']}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"Quality: {result['quality_score']:.2f}")
    print(f"Status: {result['verification_status']}")
    print(f"Entities: {result['entities']}")
    print(f"RAG Sources: {result['metadata']['rag_sources']}")
    print(f"LLM Provider: {result['metadata']['llm_provider']}")
    print(f"LLM Analysis: {result['llm_analysis'][:300]}...")
    
    # Test chat interface
    print("\n💬 Testing chat interface...")
    chat_result = await analyzer.chat_with_documents(
        "Apa saja indikator fraud pada dokumen KTP?"
    )
    print(f"Chat Answer: {chat_result['answer'][:200]}...")
    print(f"Chat Provider: {chat_result['llm_provider']}")
    
    print(f"\n✅ {LLM_PROVIDER.upper()} integration completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
