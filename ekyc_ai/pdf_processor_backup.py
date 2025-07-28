import PyPDF2
import fitz  # PyMuPDF
from typing import Dict, List
import logging
import re
from datetime import datetime

class PDFProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_text_pypdf2(self, pdf_path: str) -> Dict[str, any]:
        """Extract text using PyPDF2"""
        try:
            text_content = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    text_content.append({
                        'page': page_num + 1,
                        'text': text
                    })
            
            full_text = '\n'.join([page['text'] for page in text_content])
            
            return {
                'success': True,
                'pages': text_content,
                'full_text': full_text,
                'total_pages': len(text_content)
            }
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_text_pymupdf(self, pdf_path: str) -> Dict[str, any]:
        """Extract text using PyMuPDF (fitz) - better for complex PDFs"""
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_content.append({
                    'page': page_num + 1,
                    'text': text
                })
            
            doc.close()
            full_text = '\n'.join([page['text'] for page in text_content])
            
            return {
                'success': True,
                'pages': text_content,
                'full_text': full_text,
                'total_pages': len(text_content)
            }
        except Exception as e:
            self.logger.error(f"PyMuPDF extraction failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_text_with_ocr_fallback(self, file_path):
        """
        Extract text from PDF with OCR fallback for scanned documents
        Returns: dict with success, full_text, method, and other metadata
        """
        # Try regular text extraction first
        result = self.extract_text_pymupdf(file_path)
        if result['success'] and result['full_text'].strip():
            result['method'] = 'PyMuPDF'
            return result
        
        # Try PyPDF2 as fallback
        result = self.extract_text_pypdf2(file_path)
        if result['success'] and result['full_text'].strip():
            result['method'] = 'PyPDF2'
            return result
        
        # If both fail, try OCR for scanned PDFs
        try:
            import fitz  # PyMuPDF
            import easyocr
            import io
            
            print("🔍 Attempting OCR extraction for scanned PDF...")
            
            # Open PDF and convert to images
            doc = fitz.open(file_path)
            ocr_reader = easyocr.Reader(['en', 'id'])  # English and Indonesian
            
            all_text = []
            total_chars = 0
            total_pages = len(doc)
            
            for page_num in range(min(5, total_pages)):  # Process first 5 pages for speed
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Perform OCR
                ocr_results = ocr_reader.readtext(img_data)
                page_text = " ".join([result[1] for result in ocr_results])
                
                all_text.append(page_text)
                total_chars += len(page_text)
            
            doc.close()
            
            full_text = '
'.join(all_text)
            
            if total_chars > 50:  # Minimum threshold
                print(f"✅ OCR successful - extracted {total_chars} characters from {min(5, total_pages)} pages")
                return {
                    'success': True,
                    'full_text': full_text,
                    'total_pages': total_pages,
                    'method': 'OCR',
                    'pages_processed': min(5, total_pages),
                    'character_count': total_chars
                }
            else:
                return {'success': False, 'error': 'OCR produced insufficient text'}
                
        except ImportError as e:
            return {'success': False, 'error': f'OCR libraries not available: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'OCR failed: {e}'}
        """Extract specific fields from Akta document"""
        akta_fields = {
            'nomor_akta': None,
            'tanggal_akta': None,
            'nama_notaris': None,
            'nama_perusahaan': None,
            'modal_dasar': None,
            'modal_disetor': None,
            'alamat_perusahaan': None,
            'direktur': [],
            'komisaris': [],
            'bidang_usaha': None,
            'npwp': None
        }
        
        # Nomor Akta pattern
        akta_patterns = [
            r'AKTA\s+(?:NO|NOMOR)\.?\s*(\d+)',
            r'NOMOR\s*:\s*(\d+)',
            r'NO\.\s*(\d+)'
        ]
        
        for pattern in akta_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                akta_fields['nomor_akta'] = match.group(1)
                break
        
        # Date patterns
        date_patterns = [
            r'(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            r'tanggal\s+(\d{1,2})\s+(\w+)\s+(\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                akta_fields['tanggal_akta'] = match.group(0)
                break
        
        # Company name extraction (usually after "PT" or "CV")
        company_patterns = [
            r'(?:PT|CV)\s+([A-Z\s]+?)(?:\s+(?:yang|berkedudukan|dengan))',
            r'PERSEROAN\s+TERBATAS\s+([A-Z\s]+)',
            r'nama\s+perseroan\s*:\s*([A-Za-z\s]+)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                akta_fields['nama_perusahaan'] = match.group(1).strip()
                break
        
        # Modal patterns
        modal_patterns = [
            r'modal\s+dasar\s*(?:sebesar|:)?\s*Rp\.?\s*([\d.,]+)',
            r'MODAL\s+DASAR\s*Rp\.?\s*([\d.,]+)'
        ]
        
        for pattern in modal_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                akta_fields['modal_dasar'] = match.group(1)
                break
        
        # Extract directors and commissioners
        director_patterns = [
            r'DIREKTUR\s*(?:UTAMA)?\s*:\s*([A-Za-z\s]+)',
            r'PRESIDEN\s+DIREKTUR\s*:\s*([A-Za-z\s]+)'
        ]
        
        for pattern in director_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            akta_fields['direktur'].extend(matches)
        
        commissioner_patterns = [
            r'KOMISARIS\s*(?:UTAMA)?\s*:\s*([A-Za-z\s]+)',
            r'PRESIDEN\s+KOMISARIS\s*:\s*([A-Za-z\s]+)'
        ]
        
        for pattern in commissioner_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            akta_fields['komisaris'].extend(matches)
        
        # NPWP pattern - simplified
        npwp_pattern = r'NPWP\s*(?:NO|NOMOR)?\s*[:.]?\s*(\d{15})'
        npwp_match = re.search(npwp_pattern, text, re.IGNORECASE)
        if npwp_match:
            akta_fields['npwp'] = npwp_match.group(1)
        
        return akta_fields
    
    def validate_akta_structure(self, text: str) -> Dict[str, any]:
        """Validate if the document has proper akta structure"""
        validation_results = {
            'has_akta_number': False,
            'has_notary_name': False,
            'has_company_info': False,
            'has_legal_structure': False,
            'confidence_score': 0.0
        }
        
        # Check for akta indicators
        akta_indicators = [
            r'AKTA\s+(?:PENDIRIAN|PERUBAHAN)',
            r'NOTARIS',
            r'PERSEROAN\s+TERBATAS',
            r'MODAL\s+DASAR',
            r'ANGGARAN\s+DASAR'
        ]
        
        found_indicators = 0
        for indicator in akta_indicators:
            if re.search(indicator, text, re.IGNORECASE):
                found_indicators += 1
        
        # Calculate confidence based on found indicators
        validation_results['confidence_score'] = found_indicators / len(akta_indicators)
        
        # Individual checks
        validation_results['has_akta_number'] = bool(re.search(r'AKTA\s+(?:NO|NOMOR)', text, re.IGNORECASE))
        validation_results['has_notary_name'] = bool(re.search(r'NOTARIS', text, re.IGNORECASE))
        validation_results['has_company_info'] = bool(re.search(r'(?:PT|PERSEROAN\s+TERBATAS)', text, re.IGNORECASE))
        validation_results['has_legal_structure'] = bool(re.search(r'ANGGARAN\s+DASAR', text, re.IGNORECASE))
        
        return validation_results
