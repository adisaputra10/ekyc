"""
OCR Processor untuk eKYC System
Real OCR implementation using Tesseract and EasyOCR
"""
import os
import re
import cv2
import pytesseract
import easyocr
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Real OCR processor using multiple OCR engines"""
    
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6'  # Use LSTM OCR Engine with uniform text block
        self.easyocr_reader = None
        self._init_easyocr()
        
    def _init_easyocr(self):
        """Initialize EasyOCR reader"""
        try:
            # Initialize with Indonesian and English
            self.easyocr_reader = easyocr.Reader(['id', 'en'], gpu=False)
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.easyocr_reader = None
    
    def preprocess_image(self, image_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess image for better OCR results"""
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return image, processed
            
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            raise
    
    def extract_text_tesseract(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        try:
            original, processed = self.preprocess_image(image_path)
            
            # Extract text with confidence data
            data = pytesseract.image_to_data(
                processed, 
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT,
                lang='ind+eng'  # Indonesian and English
            )
            
            # Extract full text
            text = pytesseract.image_to_string(
                processed, 
                config=self.tesseract_config,
                lang='ind+eng'
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract word-level data
            words = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 30:  # Filter low confidence words
                    words.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
            
            return {
                'engine': 'tesseract',
                'text': text.strip(),
                'confidence': avg_confidence / 100.0,  # Normalize to 0-1
                'words': words,
                'word_count': len([w for w in words if w['text'].strip()])
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed for {image_path}: {e}")
            return {
                'engine': 'tesseract',
                'text': '',
                'confidence': 0.0,
                'words': [],
                'word_count': 0,
                'error': str(e)
            }
    
    def extract_text_easyocr(self, image_path: str) -> Dict[str, Any]:
        """Extract text using EasyOCR"""
        try:
            if self.easyocr_reader is None:
                raise ValueError("EasyOCR not initialized")
            
            # Read and process results
            results = self.easyocr_reader.readtext(image_path)
            
            # Extract text and calculate confidence
            all_text = []
            words = []
            total_confidence = 0
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Filter low confidence
                    all_text.append(text)
                    words.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': {
                            'points': bbox
                        }
                    })
                    total_confidence += confidence
            
            extracted_text = ' '.join(all_text)
            avg_confidence = total_confidence / len(results) if results else 0
            
            return {
                'engine': 'easyocr',
                'text': extracted_text.strip(),
                'confidence': avg_confidence,
                'words': words,
                'word_count': len(words)
            }
            
        except Exception as e:
            logger.error(f"EasyOCR failed for {image_path}: {e}")
            return {
                'engine': 'easyocr',
                'text': '',
                'confidence': 0.0,
                'words': [],
                'word_count': 0,
                'error': str(e)
            }
    
    def extract_text(self, image_path: str, use_both_engines: bool = True) -> Dict[str, Any]:
        """Extract text using one or both OCR engines"""
        try:
            results = {}
            
            # Try Tesseract
            tesseract_result = self.extract_text_tesseract(image_path)
            results['tesseract'] = tesseract_result
            
            # Try EasyOCR if available and requested
            if use_both_engines and self.easyocr_reader:
                easyocr_result = self.extract_text_easyocr(image_path)
                results['easyocr'] = easyocr_result
                
                # Choose best result based on confidence and text length
                if (easyocr_result['confidence'] > tesseract_result['confidence'] and 
                    len(easyocr_result['text']) > len(tesseract_result['text']) * 0.8):
                    best_result = easyocr_result
                else:
                    best_result = tesseract_result
            else:
                best_result = tesseract_result
            
            # Return combined results
            return {
                'best_result': best_result,
                'all_results': results,
                'processing_time': datetime.now().isoformat(),
                'engines_used': list(results.keys())
            }
            
        except Exception as e:
            logger.error(f"OCR processing failed for {image_path}: {e}")
            return {
                'best_result': {
                    'engine': 'error',
                    'text': '',
                    'confidence': 0.0,
                    'words': [],
                    'word_count': 0,
                    'error': str(e)
                },
                'all_results': {},
                'processing_time': datetime.now().isoformat(),
                'engines_used': []
            }

class DocumentFieldExtractor:
    """Extract specific fields from Indonesian identity documents"""
    
    def __init__(self):
        # Indonesian ID patterns
        self.patterns = {
            'nik': [
                r'\b(\d{16})\b',  # 16-digit NIK
                r'NIK\s*:?\s*(\d{16})',
                r'No\.\s*KTP\s*:?\s*(\d{16})'
            ],
            'nama': [
                r'Nama\s*:?\s*([A-Z\s]+)',
                r'NAMA\s*:?\s*([A-Z\s]+)',
                r'Name\s*:?\s*([A-Z\s]+)'
            ],
            'tempat_lahir': [
                r'Tempat[/\s]*Tgl\s*Lahir\s*:?\s*([A-Z\s]+),',
                r'TTL\s*:?\s*([A-Z\s]+),',
                r'Tempat\s*Lahir\s*:?\s*([A-Z\s]+)'
            ],
            'tanggal_lahir': [
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'(\d{1,2}\s+\w+\s+\d{4})',
                r',\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
            ],
            'jenis_kelamin': [
                r'Jenis\s*Kelamin\s*:?\s*(LAKI-LAKI|PEREMPUAN)',
                r'Sex\s*:?\s*(MALE|FEMALE)',
                r'Gender\s*:?\s*(L|P|M|F)'
            ],
            'alamat': [
                r'Alamat\s*:?\s*([^\n]+)',
                r'Address\s*:?\s*([^\n]+)'
            ],
            'agama': [
                r'Agama\s*:?\s*([A-Z\s]+)',
                r'Religion\s*:?\s*([A-Z\s]+)'
            ],
            'pekerjaan': [
                r'Pekerjaan\s*:?\s*([A-Z\s]+)',
                r'Occupation\s*:?\s*([A-Z\s]+)'
            ],
            'kewarganegaraan': [
                r'Kewarganegaraan\s*:?\s*([A-Z\s]+)',
                r'Nationality\s*:?\s*([A-Z\s]+)'
            ],
            'berlaku_hingga': [
                r'Berlaku\s*Hingga\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'Valid\s*Until\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'Berlaku\s*Hingga\s*:?\s*(SEUMUR\s*HIDUP)'
            ],
            # Company Deed (Akta Perusahaan) patterns
            'company_name': [
                r'NAMA\s+PERUSAHAAN\s*:?\s*([A-Z\s,.\-&]+)',
                r'COMPANY\s+NAME\s*:?\s*([A-Z\s,.\-&]+)',
                r'PT\.?\s+([A-Z\s,.\-&]+)',
                r'CV\.?\s+([A-Z\s,.\-&]+)',
                r'FIRMA\s+([A-Z\s,.\-&]+)'
            ],
            'company_type': [
                r'BENTUK\s+BADAN\s+HUKUM\s*:?\s*([A-Z\s]+)',
                r'JENIS\s+PERUSAHAAN\s*:?\s*([A-Z\s]+)',
                r'(PT|CV|FIRMA|PERSEKUTUAN)',
                r'PERSEROAN\s+TERBATAS',
                r'COMMANDITAIRE\s+VENNOOTSCHAP'
            ],
            'company_address': [
                r'ALAMAT\s+PERUSAHAAN\s*:?\s*([^\n]+)',
                r'DOMISILI\s*:?\s*([^\n]+)',
                r'BERKEDUDUKAN\s+DI\s*([^\n,]+)'
            ],
            'notary_name': [
                r'NOTARIS\s*:?\s*([A-Z\s,.\-]+)',
                r'NOTARY\s*:?\s*([A-Z\s,.\-]+)',
                r'DIHADAPAN\s+([A-Z\s,.\-]+),?\s+S\.?H\.?'
            ],
            'deed_number': [
                r'NOMOR\s+AKTA\s*:?\s*(\d+)',
                r'NO\.?\s*AKTA\s*:?\s*(\d+)',
                r'DEED\s+NUMBER\s*:?\s*(\d+)',
                r'AKTA\s+NOMOR\s*:?\s*(\d+)'
            ],
            'deed_date': [
                r'TANGGAL\s+AKTA\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'TERTANGGAL\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'DATED\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                r'(\d{1,2}\s+\w+\s+\d{4})'
            ],
            'authorized_capital': [
                r'MODAL\s+DASAR\s*:?\s*([A-Z\s\d,.\-]+)',
                r'AUTHORIZED\s+CAPITAL\s*:?\s*([A-Z\s\d,.\-]+)',
                r'RP\.?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)'
            ],
            'business_purpose': [
                r'MAKSUD\s+DAN\s+TUJUAN\s*:?\s*([^\n]+)',
                r'KEGIATAN\s+USAHA\s*:?\s*([^\n]+)',
                r'BIDANG\s+USAHA\s*:?\s*([^\n]+)',
                r'BUSINESS\s+PURPOSE\s*:?\s*([^\n]+)'
            ]
        }
    
    def extract_fields(self, text: str, document_type: str = 'ktp') -> Dict[str, Any]:
        """Extract structured fields from OCR text"""
        extracted_fields = {}
        
        # Clean text
        text = text.upper().strip()
        
        # Determine which patterns to use based on document type
        relevant_patterns = self._get_relevant_patterns(document_type)
        
        # Extract fields based on patterns
        for field in relevant_patterns:
            patterns = self.patterns.get(field, [])
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    extracted_fields[field] = match.group(1).strip()
                    break
        
        # Post-process fields
        extracted_fields = self._post_process_fields(extracted_fields, document_type)
        
        return extracted_fields
    
    def _get_relevant_patterns(self, document_type: str) -> list:
        """Get relevant field patterns based on document type"""
        if document_type.lower() == 'akta_perusahaan':
            return [
                'company_name', 'company_type', 'company_address', 
                'notary_name', 'deed_number', 'deed_date', 
                'authorized_capital', 'business_purpose'
            ]
        else:  # Default to KTP fields
            return [
                'nik', 'nama', 'tempat_lahir', 'tanggal_lahir',
                'jenis_kelamin', 'alamat', 'agama', 'pekerjaan',
                'kewarganegaraan', 'berlaku_hingga'
            ]
    
    def _post_process_fields(self, fields: Dict[str, str], document_type: str) -> Dict[str, Any]:
        """Post-process extracted fields"""
        processed = {}
        
        for field, value in fields.items():
            processed[field] = self._process_single_field(field, value)
        
        return processed
    
    def _process_single_field(self, field: str, value: str) -> Dict[str, Any]:
        """Process a single field based on its type"""
        if field == 'nik':
            return {
                'value': value,
                'is_valid': self._validate_nik(value),
                'province_code': value[:2] if len(value) >= 2 else '',
                'district_code': value[2:4] if len(value) >= 4 else '',
                'subdistrict_code': value[4:6] if len(value) >= 6 else ''
            }
        elif field in ['tanggal_lahir', 'deed_date']:
            return {
                'value': value,
                'normalized': self._normalize_date(value)
            }
        elif field == 'jenis_kelamin':
            return {
                'value': value,
                'normalized': self._normalize_gender(value)
            }
        elif field == 'company_type':
            return {
                'value': value,
                'normalized': self._normalize_company_type(value)
            }
        elif field == 'authorized_capital':
            return {
                'value': value,
                'cleaned': self._clean_text_field(value),
                'numeric': self._extract_numeric_value(value)
            }
        else:
            return {
                'value': value,
                'cleaned': self._clean_text_field(value)
            }
    
    def _validate_nik(self, nik: str) -> bool:
        """Validate NIK format"""
        if not nik or len(nik) != 16:
            return False
        
        # Check if all digits
        if not nik.isdigit():
            return False
        
        # Basic province code check (01-99)
        province_code = int(nik[:2])
        if province_code < 1 or province_code > 99:
            return False
        
        return True
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date format"""
        # Simple date normalization
        date_str = date_str.replace('/', '-')
        return date_str
    
    def _normalize_gender(self, gender: str) -> str:
        """Normalize gender field"""
        gender = gender.upper()
        if gender in ['LAKI-LAKI', 'MALE', 'L', 'M']:
            return 'LAKI-LAKI'
        elif gender in ['PEREMPUAN', 'FEMALE', 'P', 'F']:
            return 'PEREMPUAN'
        return gender
    
    def _normalize_company_type(self, company_type: str) -> str:
        """Normalize company type field"""
        company_type = company_type.upper()
        if 'PT' in company_type or 'PERSEROAN' in company_type:
            return 'PT'
        elif 'CV' in company_type or 'COMMANDITAIRE' in company_type:
            return 'CV'
        elif 'FIRMA' in company_type:
            return 'FIRMA'
        return company_type
    
    def _extract_numeric_value(self, text: str) -> str:
        """Extract numeric value from text (for capital amounts)"""
        # Remove currency symbols and extract numbers
        import re
        numbers = re.findall(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?', text)
        return numbers[0] if numbers else '0'
    
    def _clean_text_field(self, text: str) -> str:
        """Clean text field"""
        # Remove extra spaces and clean up
        return ' '.join(text.split())

# Create global instances
ocr_processor = OCRProcessor()
field_extractor = DocumentFieldExtractor()
