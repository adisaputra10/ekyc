import logging
import cv2
import numpy as np
import easyocr
import pytesseract
from PIL import Image
from typing import Dict, List, Optional, Tuple
import re

class ImageProcessor:
    def __init__(self):
        self.ocr_reader = easyocr.Reader(['id', 'en'])  # Indonesian and English
        self.logger = logging.getLogger(__name__)
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Read image
        image = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Noise removal
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Dilation to make text thicker
        dilation = cv2.dilate(opening, kernel, iterations=1)
        
        return dilation
    
    def extract_text_easyocr(self, image_path: str) -> Dict[str, any]:
        """Extract text using EasyOCR"""
        try:
            preprocessed = self.preprocess_image(image_path)
            results = self.ocr_reader.readtext(preprocessed)
            
            extracted_text = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Filter low confidence results
                    extracted_text.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
            
            return {
                'success': True,
                'text_data': extracted_text,
                'full_text': ' '.join([item['text'] for item in extracted_text])
            }
        except Exception as e:
            self.logger.error(f"EasyOCR extraction failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_text_tesseract(self, image_path: str) -> Dict[str, any]:
        """Extract text using Tesseract as fallback"""
        try:
            preprocessed = self.preprocess_image(image_path)
            
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(preprocessed)
            
            # Configure tesseract for Indonesian
            custom_config = r'--oem 3 --psm 6 -l ind+eng'
            text = pytesseract.image_to_string(pil_image, config=custom_config)
            
            return {
                'success': True,
                'full_text': text.strip()
            }
        except Exception as e:
            self.logger.error(f"Tesseract extraction failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_ktp_fields(self, text_data: List[Dict]) -> Dict[str, str]:
        """Extract specific KTP fields from OCR results"""
        ktp_fields = {
            'nik': None,
            'nama': None,
            'tempat_lahir': None,
            'tanggal_lahir': None,
            'jenis_kelamin': None,
            'alamat': None,
            'agama': None,
            'status_perkawinan': None,
            'pekerjaan': None,
            'kewarganegaraan': None
        }
        
        full_text = ' '.join([item['text'] for item in text_data])
        
        # NIK extraction (16 digits)
        nik_pattern = r'\b\d{16}\b'
        nik_match = re.search(nik_pattern, full_text)
        if nik_match:
            ktp_fields['nik'] = nik_match.group()
        
        # Date pattern (DD-MM-YYYY or DD/MM/YYYY)
        date_pattern = r'\b\d{2}[-/]\d{2}[-/]\d{4}\b'
        date_matches = re.findall(date_pattern, full_text)
        if date_matches:
            ktp_fields['tanggal_lahir'] = date_matches[0]
        
        # Gender detection
        if any(word in full_text.upper() for word in ['LAKI-LAKI', 'PRIA']):
            ktp_fields['jenis_kelamin'] = 'LAKI-LAKI'
        elif any(word in full_text.upper() for word in ['PEREMPUAN', 'WANITA']):
            ktp_fields['jenis_kelamin'] = 'PEREMPUAN'
        
        # Extract other fields using keyword matching
        keywords = {
            'nama': ['NAMA', 'NAME'],
            'tempat_lahir': ['TEMPAT LAHIR', 'PLACE OF BIRTH'],
            'agama': ['AGAMA', 'RELIGION'],
            'alamat': ['ALAMAT', 'ADDRESS'],
            'pekerjaan': ['PEKERJAAN', 'OCCUPATION'],
            'status_perkawinan': ['STATUS PERKAWINAN', 'MARITAL STATUS'],
            'kewarganegaraan': ['KEWARGANEGARAAN', 'NATIONALITY']
        }
        
        for field, search_terms in keywords.items():
            for item in text_data:
                text = item['text'].upper()
                for term in search_terms:
                    if term in text:
                        # Find the next text item that likely contains the value
                        idx = text_data.index(item)
                        if idx + 1 < len(text_data):
                            ktp_fields[field] = text_data[idx + 1]['text']
                        break
        
        return ktp_fields
