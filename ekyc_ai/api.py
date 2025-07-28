from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import tempfile
import shutil
import statistics
from typing import Optional
import logging

from document_validator import DocumentValidator
from config import Config
from ekyc_metrics import eKYCMetricsCollector, ProcessType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document Validation API",
    description="API untuk validasi dokumen KTP dan Akta menggunakan OpenAI dan RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize validator
try:
    validator = DocumentValidator()
    logger.info("Document validator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize document validator: {str(e)}")
    validator = None

@app.get("/")
async def serve_frontend():
    """Serve the frontend application"""
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    else:
        return {"message": "Document Validation API", "status": "running", "note": "Frontend not found"}

@app.get("/metrics.html")
async def serve_metrics():
    """Serve the metrics dashboard"""
    if os.path.exists("frontend/metrics.html"):
        return FileResponse("frontend/metrics.html")
    else:
        return {"message": "Metrics dashboard not found", "status": "error"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if validator else "unhealthy",
        "validator_ready": validator is not None
    }

@app.post("/validate/ktp")
async def validate_ktp(file: UploadFile = File(...)):
    """Validate KTP image file using enhanced processor"""
    if not validator:
        raise HTTPException(status_code=500, detail="Validator not initialized")
    
    # Check file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Import enhanced processor
        from enhanced_ktp_processor import EnhancedImageProcessor
        from datetime import datetime
        start_time = datetime.now()
        processor = EnhancedImageProcessor()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # Extract text with enhanced processor
        extraction_result = processor.extract_text_multiple_methods(temp_path)
        
        if not extraction_result['success']:
            raise HTTPException(status_code=400, detail=f"Text extraction failed: {extraction_result.get('error', 'Unknown error')}")
        
        best_result = extraction_result['best_result']
        ktp_fields = processor.extract_ktp_fields(best_result)
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Format response for frontend
        result = {
            "status": "VALID" if best_result['avg_confidence'] >= 0.7 and len(ktp_fields) >= 5 else "PARTIAL" if len(ktp_fields) >= 3 else "INVALID",
            "confidence": best_result['avg_confidence'],
            "accuracy_rate": round(best_result['avg_confidence'] * 100, 1),  # Convert to percentage
            "avg_processing_time": round(processing_time, 2),
            "validation_details": {
                "extracted_fields": ktp_fields,
                "method_used": f"{best_result['method']} + {best_result['ocr_engine']}",
                "quality_score": best_result['quality_score'],
                "text_length": best_result['text_length'],
                "completeness_status": "COMPLETE" if len(ktp_fields) >= 7 else "PARTIAL" if len(ktp_fields) >= 4 else "INCOMPLETE",
                "extraction_quality": "Excellent" if best_result['avg_confidence'] >= 0.9 else "Good" if best_result['avg_confidence'] >= 0.7 else "Fair",
                "ai_analysis": f"Enhanced OCR processing successfully extracted {len(ktp_fields)} fields from ID card with accuracy rate {round(best_result['avg_confidence'] * 100, 1)}%. Best method: {best_result['method']} with {best_result['ocr_engine']}.",
                "processing_details": {
                    "total_methods_tried": len(extraction_result['extraction_results']),
                    "successful_extractions": len([r for r in extraction_result['extraction_results'] if r['success']]),
                    "confidence_range": [min(extraction_result['confidence_scores']), max(extraction_result['confidence_scores'])] if extraction_result['confidence_scores'] else [0, 0]
                }
            },
            "processed_at": datetime.now().isoformat()
        }
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error validating KTP: {str(e)}")
        # Clean up temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate/akta")
async def validate_akta(file: UploadFile = File(...)):
    """Validate Akta PDF file"""
    if not validator:
        raise HTTPException(status_code=500, detail="Validator not initialized")
    
    # Check file type
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        from datetime import datetime
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # Record start time
        start_time = datetime.now()
        
        # Validate document
        raw_result = validator.validate_akta(temp_path)
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Transform to frontend-compatible format
        validation_result = raw_result.get('validation_result', {})
        
        # Use final extracted fields (including OpenAI completed data)
        extracted_fields = raw_result.get('processing_steps', {}).get('field_extraction', {}).get('final_extracted_fields', {})
        
        # If final_extracted_fields is not available, fallback to original
        if not extracted_fields:
            extracted_fields = raw_result.get('processing_steps', {}).get('field_extraction', {}).get('extracted_fields', {})
        
        # Get OpenAI completed data for additional context
        completed_data = validation_result.get('completed_data', {})
        
        # Merge any additional completed data that wasn't already merged
        for key, value in completed_data.items():
            if value is not None and key not in extracted_fields:
                extracted_fields[key] = value
        
        # Determine status based on validation result
        is_valid = validation_result.get('valid', False)
        confidence = validation_result.get('confidence_score', 0)
        
        if is_valid and confidence >= 0.8:
            status = "VALID"
        elif confidence >= 0.6:
            status = "PARTIAL"
        else:
            status = "INVALID"
        
        # Format response for frontend
        result = {
            "status": status,
            "confidence": confidence,
            "accuracy_rate": round(confidence, 1),  # Already in percentage format
            "avg_processing_time": round(processing_time, 2),
            "validation_details": {
                "extracted_fields": extracted_fields,
                "document_structure": raw_result.get('processing_steps', {}).get('field_extraction', {}).get('structure_validation', {}),
                "total_pages": raw_result.get('processing_steps', {}).get('pdf_extraction', {}).get('total_pages', 0),
                "total_characters": len(raw_result.get('processing_steps', {}).get('pdf_extraction', {}).get('extracted_text', '')),
                "ai_analysis": validation_result.get('explanation', f'Legal document has been processed and validated using AI with accuracy rate {round(confidence, 1)}%.'),
                "processing_method": "PDF extraction + AI validation + RAG context",
                "extraction_quality": "Excellent" if confidence >= 0.9 else "Good" if confidence >= 0.7 else "Fair",
                "completeness_status": "COMPLETE" if len(extracted_fields) >= 5 else "PARTIAL" if len(extracted_fields) >= 3 else "INCOMPLETE"
            },
            "processing_time_seconds": round(processing_time, 2),
            "processed_at": end_time.isoformat()
        }
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error validating Akta: {str(e)}")
        # Clean up temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate/comprehensive")
async def validate_comprehensive(
    ktp_file: UploadFile = File(...),
    akta_file: UploadFile = File(...)
):
    """Validate both KTP and Akta documents and generate comprehensive report"""
    if not validator:
        raise HTTPException(status_code=500, detail="Validator not initialized")
    
    # Check file types
    if not ktp_file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="KTP file must be an image")
    
    if akta_file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Akta file must be a PDF")
    
    ktp_temp_path = None
    akta_temp_path = None
    
    try:
        # Save KTP file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(ktp_file.filename)[1]) as temp_file:
            shutil.copyfileobj(ktp_file.file, temp_file)
            ktp_temp_path = temp_file.name
        
        # Save Akta file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(akta_file.file, temp_file)
            akta_temp_path = temp_file.name
        
        # Validate both documents
        result = validator.validate_documents(ktp_temp_path, akta_temp_path)
        
        # Clean up temporary files
        os.unlink(ktp_temp_path)
        os.unlink(akta_temp_path)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error in comprehensive validation: {str(e)}")
        # Clean up temporary files if they exist
        if ktp_temp_path and os.path.exists(ktp_temp_path):
            os.unlink(ktp_temp_path)
        if akta_temp_path and os.path.exists(akta_temp_path):
            os.unlink(akta_temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate/single")
async def validate_single(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None)
):
    """Validate a single document with optional type specification"""
    if not validator:
        raise HTTPException(status_code=500, detail="Validator not initialized")
    
    temp_path = None
    
    try:
        # Determine file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # Validate document
        result = validator.validate_single_document(temp_path, document_type)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error validating single document: {str(e)}")
        # Clean up temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/summary")
async def get_metrics_summary():
    """Get summary of eKYC metrics for comparison"""
    try:
        if not validator:
            raise HTTPException(status_code=500, detail="Validator not initialized")
        
        # Extract summary data from metrics
        ai_metrics = [m for m in validator.metrics_collector.metrics_data if m.process_type == ProcessType.AI_AUTOMATED]
        manual_metrics = [m for m in validator.metrics_collector.metrics_data if m.process_type == ProcessType.MANUAL]
        
        time_saved = 0
        cost_savings = 0
        
        if ai_metrics and manual_metrics:
            ai_avg_time = statistics.mean([m.processing_time_seconds for m in ai_metrics])
            manual_avg_time = statistics.mean([m.processing_time_seconds for m in manual_metrics])
            time_saved = (manual_avg_time - ai_avg_time) * len(ai_metrics) / 3600  # Convert to hours
            
            ai_avg_cost = statistics.mean([m.cost_estimate for m in ai_metrics])
            manual_avg_cost = statistics.mean([m.cost_estimate for m in manual_metrics])
            cost_savings = (manual_avg_cost - ai_avg_cost) * len(ai_metrics)
        
        summary = {
            "ai_validations": len(ai_metrics),
            "manual_validations": len(manual_metrics),
            "time_saved_hours": max(0, time_saved),
            "cost_savings": max(0, cost_savings)
        }
        
        return JSONResponse(content=summary)
    
    except Exception as e:
        logger.error(f"Error getting metrics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/comparison")
async def get_metrics_comparison():
    """Get detailed comparison between AI and manual validation"""
    try:
        if not validator:
            raise HTTPException(status_code=500, detail="Validator not initialized")
        
        # Extract comparison data
        ai_metrics = [m for m in validator.metrics_collector.metrics_data if m.process_type == ProcessType.AI_AUTOMATED]
        manual_metrics = [m for m in validator.metrics_collector.metrics_data if m.process_type == ProcessType.MANUAL]
        
        comparison = {
            "ai_avg_time": statistics.mean([m.processing_time_seconds for m in ai_metrics]) if ai_metrics else 0,
            "manual_avg_time": statistics.mean([m.processing_time_seconds for m in manual_metrics]) if manual_metrics else 0,
            "ai_accuracy": statistics.mean([m.accuracy_score for m in ai_metrics]) * 100 if ai_metrics else 0,
            "manual_accuracy": statistics.mean([m.accuracy_score for m in manual_metrics]) * 100 if manual_metrics else 0,
            "ai_cost": statistics.mean([m.cost_estimate for m in ai_metrics]) if ai_metrics else 0,
            "manual_cost": statistics.mean([m.cost_estimate for m in manual_metrics]) if manual_metrics else 0,
            "ai_throughput": 3600 / statistics.mean([m.processing_time_seconds for m in ai_metrics]) if ai_metrics else 0,
            "manual_throughput": 3600 / statistics.mean([m.processing_time_seconds for m in manual_metrics]) if manual_metrics else 0
        }
        
        return JSONResponse(content=comparison)
    
    except Exception as e:
        logger.error(f"Error getting metrics comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/roi")
async def get_roi_analysis():
    """Get ROI analysis for AI vs manual validation"""
    try:
        if not validator:
            raise HTTPException(status_code=500, detail="Validator not initialized")
        
        report = validator.metrics_collector.generate_comparison_report()
        
        # Extract ROI data from report
        roi_analysis = {
            "monthly_ai_cost": report.get("cost_analysis", {}).get("ai_total_cost", 0),
            "monthly_manual_cost": report.get("cost_analysis", {}).get("manual_total_cost", 0),
            "monthly_savings": report.get("cost_analysis", {}).get("cost_savings", 0),
            "roi_percentage": report.get("roi_analysis", {}).get("roi_percentage", 0),
            "payback_period": report.get("roi_analysis", {}).get("payback_period", "N/A")
        }
        
        return JSONResponse(content=roi_analysis)
    
    except Exception as e:
        logger.error(f"Error getting ROI analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/metrics/export")
async def export_metrics():
    """Export all metrics to JSON file"""
    try:
        if not validator:
            raise HTTPException(status_code=500, detail="Validator not initialized")
        
        export_path = validator.metrics_collector.export_metrics()
        
        # Return file for download
        if os.path.exists(export_path):
            return FileResponse(
                path=export_path,
                filename=os.path.basename(export_path),
                media_type='application/json'
            )
        else:
            raise HTTPException(status_code=404, detail="Export file not found")
    
    except Exception as e:
        logger.error(f"Error exporting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Load configuration
    config = Config()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level=config.LOG_LEVEL.lower()
    )
