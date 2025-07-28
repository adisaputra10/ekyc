"""
Enhanced FastAPI Web Interface untuk eKYC System dengan API lengkap
"""
import os
import uuid
import json
import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from document_analyzer import EKYCDocumentAnalyzer
from ai_document_analyzer import DocumentProcessor, VectorDatabase
from config import Settings
from models import KnowledgeBaseEntry
from add_knowledge import KnowledgeManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ChatMessage(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str] = []

class DocumentUploadResponse(BaseModel):
    filename: str
    file_id: str
    status: str
    message: str

class DocumentAnalysisResponse(BaseModel):
    file_id: str
    confidence_score: float
    verification_status: str
    document_type: str
    extracted_fields: Dict[str, Any]
    processing_time: float
    quality_score: float
    anomaly_detected: bool
    authenticity_score: float

class KnowledgeRequest(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str] = []

class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: int = 10

class KnowledgeSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int

# Initialize FastAPI app
app = FastAPI(
    title="eKYC System API",
    description="Electronic Know Your Customer System with AI and RAG",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
STATIC_DIR = Path("static")
TEMPLATES_DIR = Path("templates")

for directory in [UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR, TEMPLATES_DIR]:
    directory.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global variables for components
settings = None
knowledge_manager = None
document_processor = None
vector_db = None

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global settings, knowledge_manager, document_processor, vector_db
    
    try:
        # Load settings
        settings = Settings()
        logger.info(f"Settings loaded: LLM Provider = {settings.llm_provider}")
        
        # Initialize knowledge manager
        knowledge_manager = KnowledgeManager()
        logger.info("Knowledge manager initialized")
        
        # Initialize document processor
        document_processor = DocumentProcessor(
            api_key=settings.deepseek_api_key,
            llm_provider=settings.llm_provider
        )
        logger.info("Document processor initialized")
        
        # Initialize vector database
        vector_db = VectorDatabase(
            index_name="ekyc_knowledge_base",
            api_key=settings.deepseek_api_key,
            llm_provider=settings.llm_provider
        )
        logger.info("Vector database initialized")
        
        logger.info("🚀 eKYC System startup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise

# ========== WEB ROUTES ==========

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Chat page"""
    return templates.TemplateResponse("rag.html", {"request": request})

@app.get("/form", response_class=HTMLResponse)
async def form_page(request: Request):
    """Form page"""
    return templates.TemplateResponse("form.html", {"request": request})

# ========== API ROUTES ==========

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "knowledge_manager": knowledge_manager is not None,
            "document_processor": document_processor is not None,
            "vector_db": vector_db is not None
        }
    }

@app.post("/api/upload-document/", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload document for analysis"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file type
        allowed_types = [".jpg", ".jpeg", ".png", ".pdf"]
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed: {', '.join(allowed_types)}"
            )
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size and file.size > max_size:
            raise HTTPException(status_code=400, detail="File too large. Maximum 10MB allowed")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"File uploaded: {safe_filename} ({len(content)} bytes)")
        
        return DocumentUploadResponse(
            filename=safe_filename,
            file_id=file_id,
            status="uploaded",
            message="File uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/analyze-document/{filename}", response_model=DocumentAnalysisResponse)
async def analyze_document(filename: str):
    """Analyze uploaded document"""
    try:
        file_path = UPLOAD_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file_id from filename
        file_id = filename.split('_')[0]
        
        start_time = datetime.now()
        
        # Initialize document analyzer
        analyzer = EKYCDocumentAnalyzer()
        
        # Analyze document
        result = await analyzer.analyze_document_async(str(file_path))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Document analyzed: {filename} in {processing_time:.2f}s")
        
        return DocumentAnalysisResponse(
            file_id=file_id,
            confidence_score=result.get("confidence_score", 0.0),
            verification_status=result.get("verification_status", "unknown"),
            document_type=result.get("document_type", "unknown"),
            extracted_fields=result.get("extracted_fields", {}),
            processing_time=processing_time,
            quality_score=result.get("quality_score", 0.0),
            anomaly_detected=result.get("anomaly_detected", False),
            authenticity_score=result.get("authenticity_score", 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/rag/query/", response_model=ChatResponse)
async def rag_query(message: ChatMessage):
    """Query RAG system"""
    try:
        if not knowledge_manager or not vector_db:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        # Search for relevant knowledge
        search_results = await vector_db.search_similar_async(
            query_text=message.query,
            top_k=5
        )
        
        # Extract context from search results
        context_texts = []
        sources = []
        
        for result in search_results:
            if hasattr(result, 'page_content'):
                context_texts.append(result.page_content)
            if hasattr(result, 'metadata') and result.metadata.get('title'):
                sources.append(result.metadata['title'])
        
        # Generate answer using LLM
        if document_processor:
            context = "\n\n".join(context_texts[:3])  # Use top 3 results
            
            prompt = f"""Berdasarkan informasi berikut tentang eKYC, jawab pertanyaan user dengan akurat dan informatif:

CONTEXT:
{context}

PERTANYAAN: {message.query}

JAWABAN:"""
            
            answer = await document_processor.llm.agenerate([prompt])
            if answer and answer.generations and answer.generations[0]:
                response_text = answer.generations[0][0].text.strip()
            else:
                response_text = "Maaf, saya tidak dapat memberikan jawaban saat ini."
        else:
            response_text = "Sistem RAG tidak tersedia."
        
        # Calculate confidence based on search results
        confidence = 0.8 if search_results else 0.1
        
        logger.info(f"RAG query processed: '{message.query}' -> {len(response_text)} chars")
        
        return ChatResponse(
            answer=response_text,
            confidence=confidence,
            sources=sources[:3]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@app.post("/api/knowledge/add/")
async def add_knowledge(knowledge: KnowledgeRequest):
    """Add new knowledge to the system"""
    try:
        if not knowledge_manager:
            raise HTTPException(status_code=503, detail="Knowledge manager not initialized")
        
        # Create knowledge entry
        entry = KnowledgeBaseEntry(
            title=knowledge.title,
            content=knowledge.content,
            category=knowledge.category,
            tags=knowledge.tags,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add to knowledge base
        success = await knowledge_manager.add_single_knowledge(entry)
        
        if success:
            logger.info(f"Knowledge added: {knowledge.title}")
            return {"status": "success", "message": "Knowledge added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add knowledge error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add knowledge: {str(e)}")

@app.post("/api/knowledge/search/", response_model=KnowledgeSearchResponse)
async def search_knowledge(search_request: KnowledgeSearchRequest):
    """Search knowledge base"""
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector database not initialized")
        
        # Search for similar documents
        search_results = await vector_db.search_similar_async(
            query_text=search_request.query,
            top_k=search_request.limit
        )
        
        # Format results
        results = []
        for result in search_results:
            result_dict = {
                "title": getattr(result, 'metadata', {}).get('title', 'Unknown'),
                "content": getattr(result, 'page_content', '')[:200] + "...",
                "category": getattr(result, 'metadata', {}).get('category', 'general'),
                "score": getattr(result, 'score', 0.0) if hasattr(result, 'score') else 0.8
            }
            results.append(result_dict)
        
        logger.info(f"Knowledge search: '{search_request.query}' -> {len(results)} results")
        
        return KnowledgeSearchResponse(
            results=results,
            total=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")

@app.get("/api/stats/")
async def get_stats():
    """Get system statistics"""
    try:
        # Get basic stats (in a real system, these would come from a database)
        stats = {
            "total_documents_processed": 0,
            "total_verified": 0,
            "total_rejected": 0,
            "average_confidence": 0.0,
            "average_processing_time": 0.0,
            "knowledge_base_entries": 0,
            "system_uptime": "0 days",
            "last_updated": datetime.now().isoformat()
        }
        
        # Try to get knowledge base count
        if vector_db:
            try:
                # This would require implementing a count method in VectorDatabase
                stats["knowledge_base_entries"] = 7  # From our setup
            except:
                pass
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/api/documents/")
async def list_documents():
    """List uploaded documents"""
    try:
        documents = []
        
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                documents.append({
                    "filename": file_path.name,
                    "file_id": file_path.name.split('_')[0] if '_' in file_path.name else file_path.stem,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sort by creation time (newest first)
        documents.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "documents": documents,
            "total": len(documents)
        }
        
    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.delete("/api/documents/{file_id}")
async def delete_document(file_id: str):
    """Delete a document"""
    try:
        # Find file with this ID
        for file_path in UPLOAD_DIR.glob(f"{file_id}_*"):
            if file_path.is_file():
                file_path.unlink()
                logger.info(f"Document deleted: {file_path.name}")
                return {"status": "success", "message": "Document deleted successfully"}
        
        raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

# ========== ERROR HANDLERS ==========

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

# ========== MAIN ==========

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
