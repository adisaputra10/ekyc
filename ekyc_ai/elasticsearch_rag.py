from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List, Dict, Optional
import logging
import json
from config import Config

class ElasticsearchRAG:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Elasticsearch client
        self.es_client = Elasticsearch(
            [self.config.ELASTICSEARCH_URL],
            basic_auth=(self.config.ELASTICSEARCH_USERNAME, self.config.ELASTICSEARCH_PASSWORD),
            verify_certs=False
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.config.OPENAI_API_KEY
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Initialize Elasticsearch vector store
        self.vector_store = ElasticsearchStore(
            es_connection=self.es_client,
            index_name=self.config.ELASTICSEARCH_INDEX,
            embedding=self.embeddings
        )
    
    def create_index_if_not_exists(self):
        """Create Elasticsearch index if it doesn't exist"""
        try:
            if not self.es_client.indices.exists(index=self.config.ELASTICSEARCH_INDEX):
                mapping = {
                    "mappings": {
                        "properties": {
                            "text": {"type": "text"},
                            "metadata": {"type": "object"},
                            "vector": {
                                "type": "dense_vector",
                                "dims": 1536  # OpenAI embedding dimension
                            },
                            "document_type": {"type": "keyword"},
                            "document_id": {"type": "keyword"},
                            "timestamp": {"type": "date"}
                        }
                    }
                }
                
                self.es_client.indices.create(
                    index=self.config.ELASTICSEARCH_INDEX,
                    body=mapping
                )
                self.logger.info(f"Created index: {self.config.ELASTICSEARCH_INDEX}")
            
        except Exception as e:
            self.logger.error(f"Error creating index: {str(e)}")
            raise
    
    def index_document(self, text: str, metadata: Dict, document_type: str, document_id: str):
        """Index a document into Elasticsearch"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            documents = []
            for i, chunk in enumerate(chunks):
                doc_metadata = {
                    **metadata,
                    "document_type": document_type,
                    "document_id": document_id,
                    "chunk_id": f"{document_id}_chunk_{i}"
                }
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=doc_metadata
                ))
            
            # Add documents to vector store
            self.vector_store.add_documents(documents)
            
            self.logger.info(f"Indexed {len(documents)} chunks for document {document_id}")
            
        except Exception as e:
            self.logger.error(f"Error indexing document: {str(e)}")
            raise
    
    def index_ktp_template(self):
        """Index KTP validation templates and rules"""
        ktp_templates = [
            {
                "text": "KTP valid harus memiliki NIK 16 digit, nama lengkap, tempat tanggal lahir, jenis kelamin, alamat, RT/RW, kelurahan, kecamatan, agama, status perkawinan, pekerjaan, kewarganegaraan WNI, dan masa berlaku seumur hidup.",
                "metadata": {"template_type": "ktp_validation_rules"},
                "document_type": "template",
                "document_id": "ktp_validation_template"
            },
            {
                "text": "NIK KTP Indonesia terdiri dari 16 digit dengan format: 6 digit kode wilayah + 6 digit tanggal lahir + 4 digit nomor urut. Untuk perempuan, tanggal lahir ditambah 40.",
                "metadata": {"template_type": "nik_validation"},
                "document_type": "template", 
                "document_id": "nik_validation_template"
            },
            {
                "text": "KTP Indonesia harus memiliki logo Garuda Pancasila, tulisan REPUBLIK INDONESIA, dan background security features yang sulit dipalsukan.",
                "metadata": {"template_type": "ktp_security_features"},
                "document_type": "template",
                "document_id": "ktp_security_template"
            }
        ]
        
        for template in ktp_templates:
            self.index_document(
                text=template["text"],
                metadata=template["metadata"],
                document_type=template["document_type"],
                document_id=template["document_id"]
            )
    
    def index_akta_template(self):
        """Index Akta validation templates and rules"""
        akta_templates = [
            {
                "text": "Akta pendirian perusahaan harus memiliki nomor akta, tanggal pembuatan, nama notaris, nama perusahaan, modal dasar, modal disetor, alamat perusahaan, susunan direksi dan komisaris, bidang usaha, dan NPWP.",
                "metadata": {"template_type": "akta_validation_rules"},
                "document_type": "template",
                "document_id": "akta_validation_template"
            },
            {
                "text": "Akta notaris Indonesia harus dibuat oleh notaris yang berwenang, memiliki format baku sesuai peraturan, dan ditandatangani oleh para pihak dan notaris.",
                "metadata": {"template_type": "akta_legal_requirements"},
                "document_type": "template",
                "document_id": "akta_legal_template"
            },
            {
                "text": "Modal dasar PT minimal Rp 50 juta dan modal disetor minimal 25% dari modal dasar sesuai UU No. 40 Tahun 2007 tentang Perseroan Terbatas.",
                "metadata": {"template_type": "pt_capital_requirements"},
                "document_type": "template",
                "document_id": "pt_capital_template"
            }
        ]
        
        for template in akta_templates:
            self.index_document(
                text=template["text"],
                metadata=template["metadata"],
                document_type=template["document_type"],
                document_id=template["document_id"]
            )
    
    def search_similar_documents(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Search for similar documents using vector similarity"""
        try:
            # Prepare filter for Elasticsearch
            es_filter = None
            if filter_dict:
                # Convert filter_dict to proper Elasticsearch filter format
                es_filter = []
                for key, value in filter_dict.items():
                    es_filter.append({"term": {f"metadata.{key}": value}})
            
            # Perform similarity search with proper filter
            if es_filter:
                results = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k,
                    pre_filter=es_filter
                )
            else:
                results = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k
                )
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": score
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_validation_context(self, document_type: str, extracted_data: Dict) -> str:
        """Get relevant validation context from RAG"""
        try:
            # Create search query based on document type and extracted data
            if document_type == "ktp":
                query_parts = []
                if extracted_data.get('nik'):
                    query_parts.append(f"NIK {extracted_data['nik']}")
                if extracted_data.get('nama'):
                    query_parts.append(f"nama {extracted_data['nama']}")
                query_parts.append("validasi KTP Indonesia")
                query = " ".join(query_parts)
            elif document_type == "akta":
                query_parts = []
                if extracted_data.get('nama_perusahaan'):
                    query_parts.append(f"perusahaan {extracted_data['nama_perusahaan']}")
                if extracted_data.get('modal_dasar'):
                    query_parts.append(f"modal {extracted_data['modal_dasar']}")
                query_parts.append("validasi akta pendirian")
                query = " ".join(query_parts)
            else:
                query = f"validasi dokumen {document_type}"
            
            # Search for relevant context
            results = self.search_similar_documents(
                query=query,
                k=3,
                filter_dict={"document_type": "template"} if document_type in ["ktp", "akta"] else None
            )
            
            # Combine results into context
            context_parts = []
            for result in results:
                context_parts.append(result["content"])
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Error getting validation context: {str(e)}")
            return ""
    
    def initialize_templates(self):
        """Initialize validation templates in Elasticsearch"""
        try:
            self.create_index_if_not_exists()
            self.index_ktp_template()
            self.index_akta_template()
            self.logger.info("Validation templates initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing templates: {str(e)}")
            raise
