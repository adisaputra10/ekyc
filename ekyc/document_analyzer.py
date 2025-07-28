"""
Document Analyzer untuk eKYC System
Updated to use real OCR processing
"""
import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from models import AnalysisResult, DocumentType
from ocr_processor import ocr_processor, field_extractor
import logging

logger = logging.getLogger(__name__)

class EKYCDocumentAnalyzer:
    """Analyzer untuk dokumen eKYC"""
    
    def __init__(self):
        self.supported_types = [doc_type.value for doc_type in DocumentType]
        
    def analyze_document(self, file_path: str, document_type: Optional[str] = None) -> AnalysisResult:
        """Analyze dokumen dengan real OCR dan ekstraksi"""
        try:
            start_time = datetime.now()
            
            # Basic file validation
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Validate file type
            if file_ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Detect document type
            detected_type = self._detect_document_type(file_path, document_type)
            
            # Perform real OCR extraction
            logger.info(f"Starting OCR processing for {file_path}")
            ocr_result = ocr_processor.extract_text(file_path, use_both_engines=True)
            
            # Extract text from best OCR result
            best_result = ocr_result['best_result']
            extracted_text = best_result['text']
            ocr_confidence = best_result['confidence']
            
            logger.info(f"OCR completed. Confidence: {ocr_confidence:.2f}, Text length: {len(extracted_text)}")
            
            # Extract structured fields
            detected_fields = field_extractor.extract_fields(extracted_text, detected_type)
            
            # Calculate overall confidence based on OCR and field extraction
            field_confidence = self._calculate_field_confidence(detected_fields, detected_type)
            overall_confidence = (ocr_confidence * 0.7) + (field_confidence * 0.3)
            
            # Determine verification status
            verification_status = self._determine_verification_status(overall_confidence, detected_fields)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(file_size, file_ext, ocr_confidence)
            
            # Check for anomalies
            anomalies = self._detect_anomalies(file_path, detected_fields, extracted_text)
            
            # Determine document authenticity
            authenticity = self._assess_authenticity(overall_confidence, detected_fields, anomalies)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = AnalysisResult(
                document_type=detected_type,
                confidence_score=overall_confidence,
                verification_status=verification_status,
                extracted_text=extracted_text,
                detected_fields=detected_fields,
                quality_score=quality_score,
                anomalies=anomalies,
                processing_time=processing_time,
                ocr_confidence=ocr_confidence,
                document_authenticity=authenticity,
                metadata={
                    'file_size': file_size,
                    'file_extension': file_ext,
                    'ocr_engines_used': ocr_result['engines_used'],
                    'word_count': best_result.get('word_count', 0),
                    'field_confidence': field_confidence
                }
            )
            
            logger.info(f"Document analysis completed for {file_path} - Status: {verification_status}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {e}")
            # Return error result
            return AnalysisResult(
                document_type="unknown",
                confidence_score=0.0,
                verification_status="ERROR",
                extracted_text="",
                anomalies=[f"Analysis error: {str(e)}"],
                metadata={'error_details': str(e)}
            )
    
    def _detect_document_type(self, file_path: str, suggested_type: Optional[str] = None) -> str:
        """Detect document type from file"""
        if suggested_type and suggested_type in self.supported_types:
            return suggested_type
        
        filename = os.path.basename(file_path).lower()
        
        # Simple filename-based detection
        if any(term in filename for term in ['ktp', 'identitas']):
            return DocumentType.KTP.value
        elif any(term in filename for term in ['sim', 'driving']):
            return DocumentType.SIM.value
        elif any(term in filename for term in ['passport', 'paspor']):
            return DocumentType.PASSPORT.value
        elif any(term in filename for term in ['npwp', 'pajak']):
            return DocumentType.NPWP.value
        elif any(term in filename for term in ['kk', 'keluarga']):
            return DocumentType.KARTU_KELUARGA.value
        elif any(term in filename for term in ['akta', 'perusahaan', 'company', 'deed']):
            return DocumentType.AKTA_PERUSAHAAN.value
        else:
            return DocumentType.OTHER.value
    
    def _calculate_confidence(self, file_path: str, document_type: str) -> float:
        """Calculate confidence score"""
        # This method is now replaced by OCR-based confidence calculation
        # Keeping for backward compatibility
        base_confidence = 0.7
        
        filename = os.path.basename(file_path).lower()
        if document_type.lower() in filename:
            base_confidence += 0.1
            
        file_size = os.path.getsize(file_path)
        if file_size > 100000:  # > 100KB
            base_confidence += 0.1
            
        return min(base_confidence, 1.0)
    
    def _calculate_field_confidence(self, detected_fields: Dict[str, Any], document_type: str) -> float:
        """Calculate confidence based on extracted fields"""
        if not detected_fields:
            return 0.0
        
        # Define required fields per document type
        required_fields = {
            'ktp': ['nik', 'nama', 'tempat_lahir', 'tanggal_lahir'],
            'sim': ['nama', 'tanggal_lahir', 'alamat'],
            'passport': ['nama', 'tanggal_lahir'],
            'npwp': ['nama', 'nik'],
            'kartu_keluarga': ['alamat', 'nama']
        }
        
        required = required_fields.get(document_type.lower(), ['nama'])
        found_count = 0
        total_confidence = 0
        
        for field in required:
            if field in detected_fields:
                found_count += 1
                # Add field-specific validation confidence
                if field == 'nik' and 'is_valid' in detected_fields[field]:
                    total_confidence += 0.9 if detected_fields[field]['is_valid'] else 0.3
                else:
                    total_confidence += 0.8
        
        if len(required) == 0:
            return 0.5
        
        return total_confidence / len(required)
        try:
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            confidence = 0.5  # Base confidence
            
            # Boost confidence based on file size (reasonable size)
            if 50000 < file_size < 5000000:  # 50KB to 5MB
                confidence += 0.2
            
            # Boost confidence based on file extension
            if file_ext in ['.jpg', '.jpeg', '.png', '.pdf']:
                confidence += 0.2
            
            # Boost confidence based on document type detection
            if document_type != DocumentType.OTHER.value:
                confidence += 0.2
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.3
    
    def _determine_verification_status(self, confidence: float, detected_fields: Optional[Dict] = None) -> str:
        """Determine verification status based on confidence and fields"""
        if confidence >= 0.8:
            return "VERIFIED"
        elif confidence >= 0.6:
            return "PENDING_REVIEW"
        else:
            return "REJECTED"
    
    def _extract_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract fields from text based on document type"""
        fields = {}
        
        if document_type == DocumentType.KTP.value:
            fields = {
                "nik": self._extract_nik(text),
                "nama": self._extract_nama(text),
                "tempat_lahir": self._extract_tempat_lahir(text),
                "tanggal_lahir": self._extract_tanggal_lahir(text),
                "alamat": self._extract_alamat(text)
            }
        elif document_type == DocumentType.SIM.value:
            fields = {
                "nomor_sim": self._extract_nomor_sim(text),
                "nama": self._extract_nama(text),
                "alamat": self._extract_alamat(text),
                "tanggal_berlaku": self._extract_tanggal_berlaku(text)
            }
        elif document_type == DocumentType.PASSPORT.value:
            fields = {
                "passport_number": self._extract_passport_number(text),
                "nama": self._extract_nama(text),
                "nationality": self._extract_nationality(text),
                "expiry_date": self._extract_expiry_date(text)
            }
        
        return {k: v for k, v in fields.items() if v}  # Remove None values
    
    def _extract_nik(self, text: str) -> Optional[str]:
        """Extract NIK from text"""
        nik_pattern = r'\\b\\d{16}\\b'
        match = re.search(nik_pattern, text)
        return match.group() if match else None
    
    def _extract_nama(self, text: str) -> Optional[str]:
        """Extract name from text - mock implementation"""
        return "Mock Name Extracted"
    
    def _extract_tempat_lahir(self, text: str) -> Optional[str]:
        """Extract birth place from text - mock implementation"""
        return "Mock Birth Place"
    
    def _extract_tanggal_lahir(self, text: str) -> Optional[str]:
        """Extract birth date from text - mock implementation"""
        date_pattern = r'\\d{2}-\\d{2}-\\d{4}'
        match = re.search(date_pattern, text)
        return match.group() if match else None
    
    def _extract_alamat(self, text: str) -> Optional[str]:
        """Extract address from text - mock implementation"""
        return "Mock Address Extracted"
    
    def _extract_nomor_sim(self, text: str) -> Optional[str]:
        """Extract SIM number from text - mock implementation"""
        return "Mock SIM Number"
    
    def _extract_tanggal_berlaku(self, text: str) -> Optional[str]:
        """Extract validity date from text - mock implementation"""
        return "Mock Validity Date"
    
    def _extract_passport_number(self, text: str) -> Optional[str]:
        """Extract passport number from text - mock implementation"""
        return "Mock Passport Number"
    
    def _extract_nationality(self, text: str) -> Optional[str]:
        """Extract nationality from text - mock implementation"""
        return "Indonesian"
    
    def _extract_expiry_date(self, text: str) -> Optional[str]:
        """Extract expiry date from text - mock implementation"""
        return "Mock Expiry Date"
    
    def _calculate_quality_score(self, file_size: int, file_ext: str, ocr_confidence: Optional[float] = None) -> float:
        """Calculate document quality score"""
        score = 0.5  # Base score
        
        # File size scoring
        if 100000 < file_size < 2000000:  # 100KB to 2MB
            score += 0.3
        elif file_size >= 2000000:
            score += 0.1
        
        # File format scoring
        if file_ext in ['.jpg', '.jpeg', '.png']:
            score += 0.2
        elif file_ext == '.pdf':
            score += 0.1
        
        # OCR confidence factor
        if ocr_confidence is not None:
            score += (ocr_confidence * 0.2)
        return min(score, 1.0)
    
    def _detect_anomalies(self, file_path: str, detected_fields: Dict[str, Any], extracted_text: Optional[str] = None) -> List[str]:
        """Detect anomalies in document"""
        anomalies = []
        
        try:
            file_size = os.path.getsize(file_path)
            
            # Check file size anomalies
            if file_size < 10000:  # Less than 10KB
                anomalies.append("File size too small")
            elif file_size > 10000000:  # More than 10MB
                anomalies.append("File size too large")
            
            # Check field completeness
            if not detected_fields:
                anomalies.append("No fields extracted")
            
            # Check extracted text quality
            if extracted_text and len(extracted_text.strip()) < 10:
                anomalies.append("Very little text extracted - possible image quality issue")
            
            # Mock additional anomaly detection
            filename = os.path.basename(file_path).lower()
            if any(term in filename for term in ['copy', 'scan', 'temp']):
                anomalies.append("Potentially copied document")
                
        except Exception as e:
            anomalies.append(f"Anomaly detection error: {str(e)}")
        
        return anomalies
    
    def _assess_authenticity(self, confidence: float, detected_fields: Dict, anomalies: List[str]) -> str:
        """Assess document authenticity"""
        if len(anomalies) > 3:
            return "SUSPICIOUS"
        elif confidence < 0.4:
            return "QUESTIONABLE"
        elif confidence > 0.8 and len(anomalies) <= 1:
            return "AUTHENTIC"
        else:
            return "NEEDS_VERIFICATION"
    
    def batch_analyze(self, file_paths: List[str]) -> Dict[str, AnalysisResult]:
        """Analyze multiple documents"""
        results = {}
        
        for file_path in file_paths:
            try:
                result = self.analyze_document(file_path)
                results[file_path] = result
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                results[file_path] = AnalysisResult(
                    document_type="unknown",
                    confidence_score=0.0,
                    verification_status="ERROR",
                    extracted_text="",
                    anomalies=[f"Batch analysis error: {str(e)}"]
                )
        
        return results