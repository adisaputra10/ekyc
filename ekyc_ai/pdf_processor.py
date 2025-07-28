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
        """Extract text using PyMuPDF"""
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
            
            full_text = '\n'.join(all_text)
            
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
    
    def extract_akta_fields(self, text: str) -> Dict[str, any]:
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
            r'PT\.?\s+([A-Z\s&]+?)(?:\s+Tbk|,|\n)',
            r'CV\.?\s+([A-Z\s&]+?)(?:,|\n)',
            r'PERSEROAN\s+TERBATAS\s+([A-Z\s&]+?)(?:,|\n)',
            r'PT\s*[\"\']*([A-Z\s\.\-_]+?)[\"\']*\s*(?:INDONESIA|INA|IDN|\n)',
            r'bernama\s+PT\.?\s*([A-Z\s&\.\-_]+?)(?:\s*\(|\s*berkedudukan|\n)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                if len(company_name) > 3:  # Minimal length check
                    akta_fields['nama_perusahaan'] = company_name
                    break
        
        # Notary name extraction - improved patterns for OCR text
        notary_patterns = [
            # Most specific patterns first to avoid false matches
            r'saya[,\s]+([A-Z\s\.]+?)[,\s]+(?:Sarjana\s+Hukum|SH)',  # "Berhadapan dengan saya DANIEL PARGANDA MARPAUNG Sarjana Hukum"
            r'Motaris\s+([A-Z\s\.]+?)(?:\s*,\s*SH|\s*berkedudukan)',  # "Motaris Daniel Parganda Marpaung, SH"
            r'dari\s+Motaris\s+([A-Z\s\.]+?)(?:\s*,\s*SH|\n)',       # "dari Motaris Daniel Parganda Marpaung, SH"
            r'dihadapan\s+dengan\s+saya\s+([A-Z\s\.]+?)\s+Sarjana',  # "dihadapan dengan saya DANIEL PARGANDA MARPAUNG Sarjana"
            r'NOTARIS\s+([A-Z\s\.]{5,30})(?:\s+berkedudukan|\s+di\s+[A-Z])',  # More restrictive NOTARIS pattern
        ]
        
        for pattern in notary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                notary_name = match.group(1).strip()
                # Better validation for notary names
                if (len(notary_name) >= 5 and 
                    len(notary_name) <= 50 and  # Reasonable name length
                    not any(x in notary_name.lower() for x in ['departemen', 'keputusan', 'nomor', 'penghadap', 'bertindak', 'tersebut', 'dengan', 'menerangkan']) and
                    ' ' in notary_name):  # Should contain at least one space (first + last name)
                    akta_fields['nama_notaris'] = notary_name
                    break
        
        # Address extraction - improved for OCR text
        address_patterns = [
            r'berkedudukan\s+di\s+([A-Za-z\s,]+?)(?:\n|,|\s+sesuai)',
            r'alamat\s*:\s*([A-Za-z\s,\d\.]+?)(?:\n|,)',
            r'domisili\s+di\s+([A-Za-z\s,]+?)(?:\n|,)',
            r'bertempat\s+tinggal\s+di\s+([A-Za-z\s,\d\.]+?)(?:\s+jalan|\s+Rukun|\n)',
            r'Jakarta[,\s]*([A-Za-z\s]+?)(?:\s*\d|\s*Kelurahan|\n)'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                if len(address) > 3:
                    akta_fields['alamat_perusahaan'] = address
                    break
        
        # Capital/Modal extraction - improved patterns for OCR text
        modal_patterns = [
            r'MODAL\s+DASAR.*?Rp\.?\s*([\d,\.]+)',
            r'modal\s+dasar.*?sebesar\s+Rp\.?\s*([\d,\.]+)',
            r'Rp\.?\s*([\d,\.]+).*?modal\s+dasar',
            r'Modal\s+dasar\s+Perseroan\s+berjumlah\s+Rp\.?\s*([\d,\.]+)',
            r'berjumlah\s+Rp\.?\s*([\d,\.]+).*?(?:rupiah|juta)',
            r'Rp\.\s*([\d,\.]+)\s*\([^)]*juta[^)]*rupiah\)'
        ]
        
        for pattern in modal_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                modal_value = match.group(1)
                if len(modal_value) >= 3:  # Minimal check for reasonable amount
                    akta_fields['modal_dasar'] = modal_value
                    break
        
        # Directors extraction
        director_patterns = [
            r'DIREKTUR\s+UTAMA[:\s]*([A-Z\s\.]+?)(?:\n|,|\s+berkedudukan)',
            r'DIREKTUR[:\s]*([A-Z\s\.]+?)(?:\n|,|\s+yang)',
            r'DIREKSI.*?terdiri.*?([A-Z\s\.]+?)(?:\s+sebagai|\n)',
            r'Direktur\s+Utama\s*:\s*([A-Z\s\.]+?)(?:\n|,)',
            r'menjadi\s+Direktur\s+([A-Z\s\.]+?)(?:\n|,|\s+dengan)'
        ]
        
        directors = []
        for pattern in director_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                director_name = match.group(1).strip()
                if (len(director_name) >= 5 and 
                    len(director_name) <= 50 and
                    ' ' in director_name and
                    director_name not in directors):
                    directors.append(director_name)
        
        if directors:
            akta_fields['direktur'] = directors
        
        # Commissioners extraction
        commissioner_patterns = [
            r'KOMISARIS\s+UTAMA[:\s]*([A-Z\s\.]+?)(?:\n|,|\s+berkedudukan)',
            r'KOMISARIS[:\s]*([A-Z\s\.]+?)(?:\n|,|\s+yang)',
            r'DEWAN\s+KOMISARIS.*?([A-Z\s\.]+?)(?:\s+sebagai|\n)',
            r'Komisaris\s+Utama\s*:\s*([A-Z\s\.]+?)(?:\n|,)',
            r'menjadi\s+Komisaris\s+([A-Z\s\.]+?)(?:\n|,|\s+dengan)'
        ]
        
        commissioners = []
        for pattern in commissioner_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                commissioner_name = match.group(1).strip()
                if (len(commissioner_name) >= 5 and 
                    len(commissioner_name) <= 50 and
                    ' ' in commissioner_name and
                    commissioner_name not in commissioners):
                    commissioners.append(commissioner_name)
        
        if commissioners:
            akta_fields['komisaris'] = commissioners
        
        # Business field extraction
        business_patterns = [
            r'MAKSUD\s+DAN\s+TUJUAN.*?(?:adalah|ialah)\s*([^\.]{20,200})',
            r'BIDANG\s+USAHA.*?(?:adalah|ialah|meliputi)\s*([^\.]{20,200})',
            r'KEGIATAN\s+USAHA.*?(?:adalah|ialah|meliputi)\s*([^\.]{20,200})',
            r'usaha\s+(?:dalam\s+)?bidang\s+([^\.]{10,150})',
            r'bergerak\s+(?:dalam\s+)?bidang\s+([^\.]{10,150})',
            r'menjalankan\s+usaha.*?bidang\s+([^\.]{10,150})'
        ]
        
        for pattern in business_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                business_field = match.group(1).strip()
                if len(business_field) >= 10:
                    akta_fields['bidang_usaha'] = business_field
                    break
        
        # NPWP extraction
        npwp_pattern = r'NPWP\s*[:\.]?\s*(\d{2}\.\d{3}\.\d{3}\.\d{1}-\d{3}\.\d{3})'
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
        
        validation_results['confidence_score'] = found_indicators / len(akta_indicators)
        
        # Specific validations
        validation_results['has_akta_number'] = bool(re.search(r'AKTA.*NOMOR|NOMOR.*AKTA', text, re.IGNORECASE))
        validation_results['has_notary_name'] = bool(re.search(r'NOTARIS', text, re.IGNORECASE))
        validation_results['has_company_info'] = bool(re.search(r'PT\.|CV\.|PERSEROAN', text, re.IGNORECASE))
        validation_results['has_legal_structure'] = bool(re.search(r'ANGGARAN\s+DASAR|MODAL\s+DASAR', text, re.IGNORECASE))
        
        return validation_results
