import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from config import Config
from image_processor import ImageProcessor
from pdf_processor import PDFProcessor
from elasticsearch_rag import ElasticsearchRAG
from openai_validator import OpenAIValidator
from ekyc_metrics import eKYCMetricsCollector, ProcessType

class DocumentValidator:
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        # Initialize processors
        self.image_processor = ImageProcessor()
        self.pdf_processor = PDFProcessor()
        self.rag = ElasticsearchRAG()
        self.openai_validator = OpenAIValidator()
        self.metrics_collector = eKYCMetricsCollector()
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize RAG templates
        try:
            self.rag.initialize_templates()
            self.logger.info("RAG templates initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG templates: {str(e)}")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('document_validation.log'),
                logging.StreamHandler()
            ]
        )
    
    def validate_ktp(self, image_path: str) -> Dict[str, any]:
        """Validate KTP document"""
        self.logger.info(f"Starting KTP validation for: {image_path}")
        
        result = {
            "document_type": "KTP",
            "file_path": image_path,
            "timestamp": datetime.now().isoformat(),
            "processing_steps": {},
            "validation_result": {},
            "success": False
        }
        
        try:
            # Step 1: Extract text from image
            self.logger.info("Extracting text from KTP image...")
            ocr_result = self.image_processor.extract_text_easyocr(image_path)
            
            if not ocr_result['success']:
                # Fallback to Tesseract
                self.logger.warning("EasyOCR failed, trying Tesseract...")
                ocr_result = self.image_processor.extract_text_tesseract(image_path)
            
            if not ocr_result['success']:
                raise RuntimeError(f"OCR extraction failed: {ocr_result.get('error', 'Unknown error')}")
            
            result["processing_steps"]["ocr"] = {
                "success": True,
                "method": "EasyOCR" if 'text_data' in ocr_result else "Tesseract",
                "extracted_text": ocr_result.get('full_text', '')
            }
            
            # Step 2: Extract KTP fields
            self.logger.info("Extracting KTP fields...")
            if 'text_data' in ocr_result:
                ktp_fields = self.image_processor.extract_ktp_fields(ocr_result['text_data'])
            else:
                # For Tesseract, create simple text_data structure
                text_data = [{'text': line.strip()} for line in ocr_result['full_text'].split('\n') if line.strip()]
                ktp_fields = self.image_processor.extract_ktp_fields(text_data)
            
            result["processing_steps"]["field_extraction"] = {
                "success": True,
                "extracted_fields": ktp_fields
            }
            
            # Step 3: Get validation context from RAG
            self.logger.info("Getting validation context from RAG...")
            rag_context = self.rag.get_validation_context("ktp", ktp_fields)
            
            result["processing_steps"]["rag_context"] = {
                "success": True,
                "context_length": len(rag_context)
            }
            
            # Step 4: Validate with OpenAI
            self.logger.info("Validating with OpenAI...")
            validation_result = self.openai_validator.validate_ktp(ktp_fields, rag_context)
            
            result["validation_result"] = validation_result
            result["success"] = True
            
            # Step 5: Index document for future reference
            try:
                self.rag.index_document(
                    text=ocr_result.get('full_text', ''),
                    metadata={
                        "file_path": image_path,
                        "document_type": "ktp",
                        "validation_score": validation_result.get('confidence_score', 0),
                        "is_valid": validation_result.get('valid', False)
                    },
                    document_type="processed_ktp",
                    document_id=f"ktp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            except Exception as e:
                self.logger.warning(f"Failed to index document: {str(e)}")
            
            self.logger.info(f"KTP validation completed. Valid: {validation_result.get('valid', False)}")
            
        except Exception as e:
            self.logger.error(f"KTP validation failed: {str(e)}")
            result["error"] = str(e)
            result["success"] = False
        
        return result
    
    def validate_akta(self, pdf_path: str) -> Dict[str, any]:
        """Validate Akta document"""
        self.logger.info(f"Starting Akta validation for: {pdf_path}")
        
        result = {
            "document_type": "AKTA",
            "file_path": pdf_path,
            "timestamp": datetime.now().isoformat(),
            "processing_steps": {"start_time": datetime.now()},
            "validation_result": {},
            "success": False
        }
        
        try:
            # Step 1: Extract text from PDF with OCR fallback
            self.logger.info("Extracting text from Akta PDF with OCR fallback...")
            pdf_result = self.pdf_processor.extract_text_with_ocr_fallback(pdf_path)
            
            if not pdf_result['success']:
                raise RuntimeError(f"PDF extraction failed: {pdf_result.get('error', 'Unknown error')}")
            
            # Log extraction method used
            extraction_method = pdf_result.get('method', 'Unknown')
            self.logger.info(f"Text extracted using: {extraction_method}")
            
            result["processing_steps"]["pdf_extraction"] = {
                "success": True,
                "total_pages": pdf_result.get('total_pages', 0),
                "extracted_text": pdf_result.get('full_text', ''),
                "extraction_method": pdf_result.get('method', 'Unknown'),
                "character_count": pdf_result.get('character_count', len(pdf_result.get('full_text', ''))),
                "pages_processed": pdf_result.get('pages_processed', pdf_result.get('total_pages', 0))
            }
            
            # Step 2: Extract Akta fields
            self.logger.info("Extracting Akta fields...")
            akta_fields = self.pdf_processor.extract_akta_fields(pdf_result['full_text'])
            
            # Step 3: Validate Akta structure
            structure_validation = self.pdf_processor.validate_akta_structure(pdf_result['full_text'])
            
            result["processing_steps"]["field_extraction"] = {
                "success": True,
                "extracted_fields": akta_fields,
                "structure_validation": structure_validation
            }
            
            # Step 4: Get validation context from RAG
            self.logger.info("Getting validation context from RAG...")
            rag_context = self.rag.get_validation_context("akta", akta_fields)
            
            result["processing_steps"]["rag_context"] = {
                "success": True,
                "context_length": len(rag_context)
            }
            
            # Step 5: Validate with OpenAI and complete missing data
            self.logger.info("Validating with OpenAI and completing missing data...")
            validation_result = self.openai_validator.validate_akta(
                akta_fields, 
                rag_context, 
                pdf_result.get('full_text', '')
            )
            
            # Merge completed data from OpenAI back into extracted fields
            if validation_result.get('completed_data'):
                completed_data = validation_result['completed_data']
                for key, value in completed_data.items():
                    if value is not None and (akta_fields.get(key) is None or akta_fields.get(key) == ''):
                        akta_fields[key] = value
                        self.logger.info(f"Completed missing field '{key}' with value: {value}")
            
            result["validation_result"] = validation_result
            result["processing_steps"]["field_extraction"]["final_extracted_fields"] = akta_fields
            result["success"] = True
            
            # Record metrics for AI validation
            self.metrics_collector.record_validation(
                document_type="akta",
                process_type=ProcessType.AI_AUTOMATED,
                processing_time=(datetime.now() - result["processing_steps"].get("start_time", datetime.now())).total_seconds(),
                validation_result={
                    "status": "VALID" if validation_result.get("valid", False) else "INVALID",
                    "confidence": validation_result.get("confidence_score", 0),
                    "validation_details": {
                        "extracted_fields": akta_fields,
                        "errors": validation_result.get("format_issues", []),
                        "warnings": validation_result.get("legal_issues", [])
                    }
                }
            )
            
            # Step 6: Index document for future reference
            try:
                self.rag.index_document(
                    text=pdf_result.get('full_text', ''),
                    metadata={
                        "file_path": pdf_path,
                        "document_type": "akta",
                        "validation_score": validation_result.get('confidence_score', 0),
                        "is_valid": validation_result.get('valid', False),
                        "structure_score": structure_validation.get('confidence_score', 0)
                    },
                    document_type="processed_akta",
                    document_id=f"akta_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            except Exception as e:
                self.logger.warning(f"Failed to index document: {str(e)}")
            
            self.logger.info(f"Akta validation completed. Valid: {validation_result.get('valid', False)}")
            
        except Exception as e:
            self.logger.error(f"Akta validation failed: {str(e)}")
            result["error"] = str(e)
            result["success"] = False
        
        return result
    
    def validate_documents(self, ktp_path: str, akta_path: str) -> Dict[str, any]:
        """Validate both KTP and Akta documents and generate comprehensive report"""
        self.logger.info("Starting comprehensive document validation...")
        
        # Validate individual documents
        ktp_result = self.validate_ktp(ktp_path)
        akta_result = self.validate_akta(akta_path)
        
        # Generate comprehensive report
        if ktp_result['success'] and akta_result['success']:
            try:
                comprehensive_report = self.openai_validator.generate_validation_report(
                    ktp_result['validation_result'],
                    akta_result['validation_result']
                )
            except Exception as e:
                self.logger.error(f"Failed to generate comprehensive report: {str(e)}")
                comprehensive_report = {
                    "overall_status": "ERROR",
                    "error": str(e)
                }
        else:
            comprehensive_report = {
                "overall_status": "INCOMPLETE",
                "error": "One or both document validations failed"
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "ktp_validation": ktp_result,
            "akta_validation": akta_result,
            "comprehensive_report": comprehensive_report,
            "success": ktp_result['success'] and akta_result['success']
        }
    
    def validate_single_document(self, file_path: str, document_type: Optional[str] = None) -> Dict[str, any]:
        """Validate a single document (auto-detect type if not specified)"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        # Auto-detect document type if not specified
        if document_type is None:
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                document_type = 'ktp'
            elif file_ext == '.pdf':
                document_type = 'akta'
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Validate based on document type
        if document_type.lower() == 'ktp':
            return self.validate_ktp(file_path)
        elif document_type.lower() == 'akta':
            return self.validate_akta(file_path)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")


def main():
    """Main function for command-line usage"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Document Validation System')
    parser.add_argument('--ktp', type=str, help='Path to KTP image file')
    parser.add_argument('--akta', type=str, help='Path to Akta PDF file')
    parser.add_argument('--single', type=str, help='Path to single document file')
    parser.add_argument('--type', type=str, choices=['ktp', 'akta'], help='Document type for single document')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    
    args = parser.parse_args()
    
    validator = DocumentValidator()
    
    try:
        if args.ktp and args.akta:
            # Validate both documents
            result = validator.validate_documents(args.ktp, args.akta)
        elif args.single:
            # Validate single document
            result = validator.validate_single_document(args.single, args.type)
        else:
            print("Please provide either --ktp and --akta for comprehensive validation, or --single for single document validation")
            return
        
        # Output result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {args.output}")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
