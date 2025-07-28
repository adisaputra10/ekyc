"""
FastAPI Web Interface untuk eKYC System
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import FileResponse, JSONResponse
import os
import aiofiles
import logging
from typing import List, Optional
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import EKYCFormData, PersonalInfo, Address, ContactInfo, DocumentSubmission, DocumentType, Gender, AnalysisResult
from document_generator import EKYCDocumentGenerator
from document_analyzer import EKYCDocumentAnalyzer
from ai_document_analyzer import VectorDatabase, AIDocumentAnalyzer, initialize_knowledge_base

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from rag_system import EKYCKnowledgeBase, EKYCRAGSystem, initialize_ekyc_knowledge_base

# Constants
RAG_UNAVAILABLE_MSG = "RAG system not available"

app = FastAPI(title="eKYC System", description="Electronic Know Your Customer System")

# Setup directories
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
STATIC_DIR = "static"
TEMPLATES_DIR = "templates"

for directory in [UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize components
document_generator = EKYCDocumentGenerator()
document_analyzer = EKYCDocumentAnalyzer()  # Legacy analyzer

# Get configuration from environment
llm_provider = os.getenv("LLM_PROVIDER", "deepseek")
api_key = os.getenv("DEEPSEEK_API_KEY") if llm_provider == "deepseek" else os.getenv("OPENAI_API_KEY")
model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat") if llm_provider == "deepseek" else "gpt-4"

vector_db = VectorDatabase(
    elasticsearch_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
    index_name=os.getenv("ELASTICSEARCH_INDEX", "document_vectors"),
    api_key=api_key,
    llm_provider=llm_provider
)  # New vector database

ai_analyzer = AIDocumentAnalyzer(  # New AI analyzer
    vector_db=vector_db,
    llm_provider=llm_provider,
    api_key=api_key,
    model_name=model_name
)

# Initialize RAG system as global variable
rag_system = None

# Initialize knowledge base on startup
@app.on_event("startup")
async def startup_event():
    """Initialize knowledge base saat aplikasi start"""
    global rag_system
    try:
        await initialize_knowledge_base(vector_db, api_key, llm_provider)
        logger.info(f"Knowledge base initialized successfully with {llm_provider}")
        
        # Initialize RAG system after knowledge base
        rag_system = await initialize_ekyc_knowledge_base()
        logger.info("✅ RAG system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize knowledge base: {str(e)}")
        rag_system = None

@app.get("/")
async def home(request: Request):
    """Homepage dengan form eKYC"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload")
async def upload_page(request: Request):
    """Upload dokumen page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/form")
async def form_page(request: Request):
    """Form eKYC page"""
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/rag")
async def rag_page(request: Request):
    """RAG AI Assistant page"""
    return templates.TemplateResponse("rag.html", {"request": request})

# API Routes for templates
@app.post("/upload-document/")
async def upload_document(file: UploadFile = File(...), document_type: str = Form(...)):
    """Upload and save document"""
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "message": "File uploaded successfully",
            "filename": unique_filename,
            "document_type": document_type,
            "file_size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/analyze-document/{filename}")
async def analyze_document_by_filename_post(filename: str, document_type: str = Form(None)):
    """Analyze uploaded document by filename (POST method)"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Use document analyzer for image/PDF files
        result = document_analyzer.analyze_document(file_path, document_type)
        return result
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/analyze-document/{filename}")
async def analyze_document_by_filename(filename: str, document_type: str = None):
    """Analyze uploaded document by filename"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        result = document_analyzer.analyze_document(file_path, document_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/analyze-document/{filename}")
async def api_analyze_document_by_filename(filename: str, document_type: str = None):
    """API endpoint to analyze uploaded document by filename"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        result = document_analyzer.analyze_document(file_path, document_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/analyze-document/{filename}")
async def api_analyze_document_by_filename_post(filename: str, document_type: str = Form(None)):
    """API endpoint to analyze uploaded document by filename (POST method)"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        result = document_analyzer.analyze_document(file_path, document_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/chat/")
async def chat_endpoint(message: dict):
    """Chat with AI assistant"""
    try:
        user_message = message.get("message", "")
        conversation_id = message.get("conversation_id")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        if rag_system:
            response = await rag_system.chat(user_message, conversation_id)
            return response
        else:
            return {
                "message": "AI system is currently unavailable. Please try again later.",
                "conversation_id": conversation_id or "unavailable",
                "timestamp": datetime.now(),
                "sources": [],
                "confidence": 0.0
            }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/api/rag/query/")
async def rag_query_endpoint(query: dict):
    """Process RAG query"""
    try:
        query_text = query.get("query", "")
        document_type = query.get("document_type")
        max_results = query.get("max_results", 5)
        include_context = query.get("include_context", True)
        
        if not query_text:
            raise HTTPException(status_code=400, detail="Query is required")
        
        if rag_system:
            from models import RAGQuery
            rag_query_obj = RAGQuery(
                query=query_text,
                document_type=document_type,
                max_results=max_results,
                include_context=include_context
            )
            response = await rag_system.query(rag_query_obj)
            return response
        else:
            return {
                "answer": "RAG system is currently unavailable. Please try again later.",
                "sources": [],
                "confidence": 0.0,
                "query_type": "unavailable",
                "processing_time": 0.0
            }
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

class EKYCSubmissionForm:
    def __init__(self, request: Request):
        self.request = request
    
    async def parse_form_data(self) -> tuple:
        form = await self.request.form()
        
        # Extract form data
        personal_data = {
            'full_name': form.get('full_name'),
            'id_number': form.get('id_number'),
            'birth_place': form.get('birth_place'),
            'birth_date': form.get('birth_date'),
            'gender': form.get('gender'),
            'religion': form.get('religion'),
            'marital_status': form.get('marital_status'),
            'occupation': form.get('occupation'),
            'nationality': form.get('nationality', 'Indonesia')
        }
        
        address_data = {
            'street': form.get('street'),
            'rt_rw': form.get('rt_rw'),
            'village': form.get('village'),
            'district': form.get('district'),
            'city': form.get('city'),
            'province': form.get('province'),
            'postal_code': form.get('postal_code')
        }
        
        contact_data = {
            'phone': form.get('phone'),
            'email': form.get('email'),
            'emergency_contact_name': form.get('emergency_contact_name'),
            'emergency_contact_phone': form.get('emergency_contact_phone')
        }
        
        document_data = {
            'document_type': form.get('document_type'),
            'document_number': form.get('document_number'),
            'issued_date': form.get('issued_date'),
            'expiry_date': form.get('expiry_date'),
            'issuing_authority': form.get('issuing_authority')
        }
        
        files = {
            'selfie': form.get('selfie'),
            'document_image': form.get('document_image')
        }
        
        return personal_data, address_data, contact_data, document_data, files

@app.post("/submit-ekyc")
async def submit_ekyc(request: Request):
    """Submit form eKYC dan generate dokumen"""
    
    try:
        # Parse form data
        form_parser = EKYCSubmissionForm(request)
        personal_data, address_data, contact_data, document_data, files = await form_parser.parse_form_data()
        
        # Create form data objects
        personal_info = PersonalInfo(
            full_name=personal_data['full_name'],
            id_number=personal_data['id_number'],
            birth_place=personal_data['birth_place'],
            birth_date=personal_data['birth_date'],
            gender=Gender(personal_data['gender']),
            religion=personal_data['religion'],
            marital_status=personal_data['marital_status'],
            occupation=personal_data['occupation'],
            nationality=personal_data['nationality']
        )
        
        address = Address(
            street=address_data['street'],
            rt_rw=address_data['rt_rw'],
            village=address_data['village'],
            district=address_data['district'],
            city=address_data['city'],
            province=address_data['province'],
            postal_code=address_data['postal_code']
        )
        
        contact_info = ContactInfo(
            phone=contact_data['phone'],
            email=contact_data['email'],
            emergency_contact_name=contact_data['emergency_contact_name'],
            emergency_contact_phone=contact_data['emergency_contact_phone']
        )
        
        documents = [DocumentSubmission(
            document_type=DocumentType(document_data['document_type']),
            document_number=document_data['document_number'],
            issued_date=document_data['issued_date'],
            expiry_date=document_data['expiry_date'],
            issuing_authority=document_data['issuing_authority']
        )]
        
        form_data = EKYCFormData(
            personal_info=personal_info,
            address=address,
            contact_info=contact_info,
            documents=documents
        )
        
        # Save uploaded files
        file_id = str(uuid.uuid4())
        selfie_path = None
        document_path = None
        
        selfie = files.get('selfie')
        document_image = files.get('document_image')
        
        if selfie and hasattr(selfie, 'filename') and selfie.filename:
            selfie_path = os.path.join(UPLOAD_DIR, f"{file_id}_selfie_{selfie.filename}")
            async with aiofiles.open(selfie_path, "wb") as buffer:
                content = await selfie.read()
                await buffer.write(content)
            form_data.photo_selfie_path = selfie_path
        
        if document_image and hasattr(document_image, 'filename') and document_image.filename:
            document_path = os.path.join(UPLOAD_DIR, f"{file_id}_document_{document_image.filename}")
            async with aiofiles.open(document_path, "wb") as buffer:
                content = await document_image.read()
                await buffer.write(content)
        
        # Generate PDF document
        pdf_path = os.path.join(OUTPUT_DIR, f"ekyc_{file_id}.pdf")
        verification_code = document_generator.generate_document(form_data, pdf_path)
        
        # Analyze document if uploaded dengan AI RAG
        analysis_result = None
        rag_insights = None
        
        if document_path:
            # Try AI analyzer first
            try:
                ai_analysis = await ai_analyzer.analyze_document_with_rag(
                    content="Document image uploaded - OCR processing needed",
                    document_context={"form_data": form_data.dict()}
                )
                
                # Convert to legacy AnalysisResult format
                analysis_result = AnalysisResult(
                    document_type=ai_analysis["document_type"],
                    extracted_text=ai_analysis.get("extracted_content", ""),
                    confidence_score=ai_analysis["confidence_score"],
                    verification_status=ai_analysis["verification_status"],
                    issues_found=ai_analysis.get("recommendations", []),
                    recommendations=ai_analysis.get("recommendations", []),
                    face_match_score=None
                )
                rag_insights = ai_analysis
                
            except Exception as e:
                logger.error(f"AI analysis failed: {str(e)}")
                # Fallback ke legacy analyzer
                analysis_result = document_analyzer.analyze_document(
                    document_path, 
                    selfie_path
                )
                rag_insights = None
        
        return templates.TemplateResponse("result.html", {
            "request": request,
            "success": True,
            "verification_code": verification_code,
            "pdf_path": f"/outputs/ekyc_{file_id}.pdf",
            "analysis_result": analysis_result,
            "rag_insights": rag_insights,
            "form_data": form_data
        })
    
    except Exception as e:
        return templates.TemplateResponse("result.html", {
            "request": request,
            "success": False,
            "error": str(e)
        })

@app.post("/analyze-document")
async def analyze_document_endpoint(
    document: UploadFile = File(...),
    selfie: Optional[UploadFile] = File(None),
    expected_doc_type: Optional[str] = Form(None)
):
    """Endpoint untuk analisa dokumen saja"""
    
    try:
        # Save uploaded files
        file_id = str(uuid.uuid4())
        
        document_path = os.path.join(UPLOAD_DIR, f"{file_id}_doc_{document.filename}")
        async with aiofiles.open(document_path, "wb") as buffer:
            content = await document.read()
            await buffer.write(content)
        
        selfie_path = None
        if selfie:
            selfie_path = os.path.join(UPLOAD_DIR, f"{file_id}_selfie_{selfie.filename}")
            async with aiofiles.open(selfie_path, "wb") as buffer:
                content = await selfie.read()
                await buffer.write(content)
        
        # Analyze document dengan AI RAG
        ai_analysis = await ai_analyzer.analyze_document_with_rag(
            content="Document image uploaded",
            document_context={"expected_doc_type": expected_doc_type}
        )
        
        return JSONResponse(content=ai_analysis)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag-query")
async def rag_query_endpoint(
    query: str = Form(...),
    document_type: Optional[str] = Form(None),
    top_k: int = Form(default=5)
):
    """Endpoint untuk RAG query"""
    
    try:
        # Search dalam knowledge base
        if document_type:
            results = await vector_db.search_similar_async(
                query, top_k, document_type=document_type
            )
        else:
            results = await vector_db.search_hybrid_async(query, top_k)
        
        return JSONResponse(content={
            "query": query,
            "results": results,
            "total_found": len(results)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-knowledge")
async def add_knowledge_endpoint(
    title: str = Form(...),
    content: str = Form(...),
    document_type: str = Form(default="general"),
    category: str = Form(default="knowledge")
):
    """Endpoint untuk menambah knowledge ke database"""
    
    try:
        doc_ids = await vector_db.add_document_async(
            content=content,
            title=title,
            document_type=document_type,
            category=category
        )
        
        return JSONResponse(content={
            "message": "Knowledge added successfully",
            "document_ids": doc_ids,
            "title": title
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search-knowledge")
async def search_knowledge_endpoint(
    q: str,
    doc_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10
):
    """Endpoint untuk search knowledge base"""
    
    try:
        results = await vector_db.search_hybrid_async(
            query=q,
            top_k=limit
        )
        
        # Filter by doc_type and category if provided
        if doc_type or category:
            filtered_results = []
            for result in results:
                if doc_type and result.get('document_type') != doc_type:
                    continue
                if category and result.get('category') != category:
                    continue
                filtered_results.append(result)
            results = filtered_results
        
        return JSONResponse(content={
            "query": q,
            "results": results[:limit],
            "total_found": len(results)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag-query")
async def rag_query_endpoint(
    query: str = Form(...),
    context_type: Optional[str] = Form("general")
):
    """Endpoint untuk query RAG system"""
    
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        response = rag_system.query(
            question=query,
            context_data={"context_type": context_type}
        )
        
        return JSONResponse(content={
            "success": True,
            "answer": response["answer"],
            "relevant_documents": response["relevant_documents"],
            "metadata": response["metadata"]
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag-search")
async def rag_search_endpoint(
    q: str,
    top_k: int = 5,
    doc_type: Optional[str] = None
):
    """Endpoint untuk search knowledge base"""
    
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        results = rag_system.knowledge_base.search_entries(
            query=q
        )
        
        # Convert KnowledgeBaseEntry objects to dictionaries
        results_dict = []
        for result in results[:top_k]:
            results_dict.append({
                "title": result.title,
                "content": result.content,
                "category": result.category,
                "tags": result.tags,
                "created_at": result.created_at.isoformat()
            })
        
        return JSONResponse(content={
            "success": True,
            "query": q,
            "results": results_dict,
            "total": len(results_dict)
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional API endpoints for frontend
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check vector database connection
        vector_status = "healthy"
        try:
            # Simple connection test
            info = await vector_db.get_index_info()
            vector_status = "healthy"
        except:
            vector_status = "unhealthy"
        
        # Check RAG system
        rag_status = "healthy" if rag_system else "unavailable"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "vector_database": vector_status,
                "rag_system": rag_status,
                "ai_analyzer": "healthy"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/statistics")
async def get_statistics():
    """Get system statistics"""
    try:
        # Count documents in uploads directory
        upload_files = os.listdir(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else []
        documents_processed = len(upload_files)
        
        # Get knowledge base count
        knowledge_entries = 0
        try:
            info = await vector_db.get_index_info()
            knowledge_entries = info.get("total_documents", 0)
        except:
            knowledge_entries = 0
        
        return {
            "documents_processed": documents_processed,
            "accuracy_rate": 95.7,  # Mock data - can be calculated from actual analysis results
            "knowledge_entries": knowledge_entries,
            "uptime": "24h",  # Mock data - can be calculated from startup time
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/api/recent-uploads")
async def get_recent_uploads():
    """Get recent uploaded documents"""
    try:
        uploads = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    uploads.append({
                        "filename": filename,
                        "document_type": "unknown",  # Can be enhanced to store document type
                        "uploaded_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "file_size": stat.st_size
                    })
        
        # Sort by upload time, most recent first
        uploads.sort(key=lambda x: x["uploaded_at"], reverse=True)
        return uploads[:10]  # Return last 10 uploads
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent uploads: {str(e)}")

@app.get("/api/knowledge-base/status")
async def get_knowledge_base_status():
    """Get knowledge base status"""
    try:
        if not vector_db:
            return {"status": "unavailable", "message": "Vector database not initialized"}
        
        info = await vector_db.get_index_info()
        return {
            "status": "active",
            "message": "Ready to answer questions",
            "total_documents": info.get("total_documents", 0),
            "index_name": info.get("index_name", "unknown"),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking knowledge base: {str(e)}",
            "last_updated": None
        }

@app.get("/documents")
async def documents_page(request: Request):
    """Documents management page"""
    return templates.TemplateResponse("documents.html", {"request": request})

@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents with analysis status"""
    try:
        documents = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    
                    # Check if analysis result exists
                    analysis_path = os.path.join(OUTPUT_DIR, f"{filename}_analysis.json")
                    has_analysis = os.path.exists(analysis_path)
                    
                    documents.append({
                        "filename": filename,
                        "upload_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "file_size": stat.st_size,
                        "has_analysis": has_analysis,
                        "file_type": os.path.splitext(filename)[1].lower()
                    })
        
        # Sort by upload date, most recent first
        documents.sort(key=lambda x: x["upload_date"], reverse=True)
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.delete("/api/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document and its analysis"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        analysis_path = os.path.join(OUTPUT_DIR, f"{filename}_analysis.json")
        
        deleted_files = []
        
        # Delete main file
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted_files.append(filename)
        
        # Delete analysis file if exists
        if os.path.exists(analysis_path):
            os.remove(analysis_path)
            deleted_files.append(f"{filename}_analysis.json")
        
        if not deleted_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "message": "Document deleted successfully",
            "deleted_files": deleted_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

# Knowledge Base Management Routes
@app.get("/knowledge")
async def knowledge_page(request: Request):
    """Knowledge base management page"""
    return templates.TemplateResponse("knowledge.html", {"request": request})

@app.get("/review")
async def review_page(request: Request):
    """Manual review page for admins"""
    return templates.TemplateResponse("review.html", {"request": request})

@app.post("/api/knowledge/embed-pdf")
async def embed_pdf_to_knowledge(file: UploadFile = File(...), document_type: str = Form("knowledge_base")):
    """Embed PDF content into knowledge base"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail=RAG_UNAVAILABLE_MSG)
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file temporarily
        file_id = str(uuid.uuid4())
        temp_file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
        
        async with aiofiles.open(temp_file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Extract text from PDF (you might need to implement PDF text extraction)
        # For now, we'll use a placeholder
        pdf_content = extract_pdf_text(temp_file_path)
        
        # Add to knowledge base
        chunks_created = await rag_system.knowledge_base.add_document({
            "title": file.filename,
            "content": pdf_content,
            "document_type": "pdf",
            "source": file.filename,
            "metadata": {
                "file_size": len(content),
                "upload_date": datetime.now().isoformat(),
                "file_id": file_id
            }
        })
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        return {
            "message": "PDF embedded successfully",
            "filename": file.filename,
            "chunks_created": chunks_created,
            "file_id": file_id
        }
        
    except Exception as e:
        logger.error(f"PDF embedding error: {e}")
        # Clean up temp file if exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Failed to embed PDF: {str(e)}")

@app.post("/api/knowledge/add-manual")
async def add_manual_knowledge(request: Request):
    """Add manual knowledge to knowledge base"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        data = await request.json()
        
        # Validate required fields
        if not data.get('title') or not data.get('content'):
            raise HTTPException(status_code=400, detail="Title and content are required")
        
        # Add to knowledge base
        chunks_created = await rag_system.knowledge_base.add_document({
            "title": data['title'],
            "content": data['content'],
            "document_type": "manual",
            "category": data.get('category', 'general'),
            "tags": data.get('tags', []),
            "metadata": {
                "created_date": datetime.now().isoformat(),
                "source": "manual_entry"
            }
        })
        
        return {
            "message": "Knowledge added successfully",
            "title": data['title'],
            "chunks_created": chunks_created
        }
        
    except Exception as e:
        logger.error(f"Manual knowledge addition error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add knowledge: {str(e)}")

@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        if not rag_system:
            return {
                "total_documents": 0,
                "total_embeddings": 0,
                "vector_db_status": "unavailable",
                "last_update": "never"
            }
        
        # Get stats from knowledge base
        stats = await rag_system.knowledge_base.get_stats()
        
        return {
            "total_documents": stats.get("document_count", 0),
            "total_embeddings": stats.get("embedding_count", 0),
            "vector_db_status": "healthy" if rag_system.knowledge_base.es_client and rag_system.knowledge_base.es_client.ping() else "unhealthy",
            "last_update": stats.get("last_update", "never")
        }
        
    except Exception as e:
        logger.error(f"Knowledge stats error: {e}")
        return {
            "total_documents": 0,
            "total_embeddings": 0,
            "vector_db_status": "error",
            "last_update": "error"
        }

@app.get("/api/knowledge/list")
async def list_knowledge():
    """List all knowledge base entries"""
    try:
        if not rag_system:
            return []
        
        # Get all documents from knowledge base
        documents = rag_system.knowledge_base.list_all_documents()
        
        return documents
        
    except Exception as e:
        logger.error(f"Knowledge list error: {e}")
        return []

@app.delete("/api/knowledge/clear")
async def clear_knowledge_base():
    """Clear entire knowledge base"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        # Clear knowledge base
        await rag_system.knowledge_base.clear_all()
        
        return {"message": "Knowledge base cleared successfully"}
        
    except Exception as e:
        logger.error(f"Knowledge clear error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear knowledge base: {str(e)}")

@app.delete("/api/knowledge/{item_id}")
async def delete_knowledge_item(item_id: str):
    """Delete specific knowledge item"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        # Delete specific document
        deleted = rag_system.knowledge_base.delete_document(item_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Knowledge item not found")
        
        return {"message": "Knowledge item deleted successfully"}
        
    except Exception as e:
        logger.error(f"Knowledge delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete knowledge item: {str(e)}")

# Review API endpoints
@app.get("/api/review/stats")
async def get_review_stats():
    """Get review statistics"""
    try:
        # Get documents that need review (status PENDING)
        # In a real app, this would query a database
        pending_count = 0
        approved_today = 0
        rejected_today = 0
        total_today = 0
        
        return {
            "pending": pending_count,
            "approved_today": approved_today, 
            "rejected_today": rejected_today,
            "total_today": total_today
        }
        
    except Exception as e:
        logger.error(f"Review stats error: {e}")
        return {
            "pending": 0,
            "approved_today": 0,
            "rejected_today": 0,
            "total_today": 0
        }

@app.get("/api/review/pending")
async def get_pending_review_documents():
    """Get documents pending manual review"""
    try:
        # Mock data - in real app, query database for PENDING status
        mock_documents = [
            {
                "id": "doc_001",
                "document_type": "KTP",
                "upload_time": "2025-07-27T08:00:00",
                "confidence": 0.65,
                "verification_status": "PENDING",
                "extracted_data": {
                    "name": "John Doe",
                    "nik": "1234567890123456"
                }
            },
            {
                "id": "doc_002", 
                "document_type": "AKTA_PERUSAHAAN",
                "upload_time": "2025-07-27T09:15:00",
                "confidence": 0.45,
                "verification_status": "PENDING",
                "extracted_data": {
                    "company_name": "PT Example Corp",
                    "registration_number": "ABC123456"
                }
            }
        ]
        
        return mock_documents
        
    except Exception as e:
        logger.error(f"Pending documents error: {e}")
        return []

@app.get("/api/review/recent")  
async def get_recent_review_decisions():
    """Get recent review decisions"""
    try:
        # Mock data - in real app, query database for recent reviews
        mock_decisions = [
            {
                "document_id": "doc_003",
                "document_type": "KTP",
                "decision": "VERIFIED",
                "reviewer": "Admin",
                "review_time": "2025-07-27T07:30:00",
                "notes": "All information verified correctly"
            },
            {
                "document_id": "doc_004",
                "document_type": "PASSPORT", 
                "decision": "REJECTED",
                "reviewer": "Admin",
                "review_time": "2025-07-27T07:15:00",
                "notes": "Document image quality too poor"
            }
        ]
        
        return mock_decisions
        
    except Exception as e:
        logger.error(f"Recent decisions error: {e}")
        return []

@app.post("/api/review/{document_id}")
async def make_review_decision(document_id: str, request: Request):
    """Make a manual review decision"""
    try:
        data = await request.json()
        decision = data.get('decision')  # VERIFIED or REJECTED
        notes = data.get('notes', '')
        reviewer = data.get('reviewer', 'Admin')
        
        if decision not in ['VERIFIED', 'REJECTED']:
            raise HTTPException(status_code=400, detail="Invalid decision")
        
        # In a real app, update the document status in database
        logger.info(f"Review decision for {document_id}: {decision} by {reviewer}")
        
        return {
            "message": f"Document {decision.lower()} successfully",
            "document_id": document_id,
            "decision": decision,
            "reviewer": reviewer,
            "review_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Review decision error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process review decision: {str(e)}")

@app.get("/api/documents/{document_id}/image")
async def get_document_image(document_id: str):
    """Get document image for review"""
    try:
        # In a real app, retrieve actual document image from storage
        # For now, return a placeholder
        raise HTTPException(status_code=404, detail="Document image not found")
        
    except Exception as e:
        logger.error(f"Document image error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document image: {str(e)}")

def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        # Try to use PyMuPDF if available, otherwise fallback
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            # Fallback: return file info if PyMuPDF not available
            file_size = os.path.getsize(file_path)
            return f"PDF Document: {os.path.basename(file_path)}\nFile Size: {file_size} bytes\nNote: Full text extraction requires PyMuPDF library"
            
    except Exception as e:
        logger.error(f"PDF text extraction error: {e}")
        return f"Error extracting text from PDF: {str(e)}"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "rag_system": "available" if rag_system else "unavailable",
        "elasticsearch": "connected" if rag_system and rag_system.knowledge_base.es_client and rag_system.knowledge_base.es_client.ping() else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
