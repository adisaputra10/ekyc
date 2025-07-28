#!/usr/bin/env python3
"""
Enhanced Image Processor untuk KTP dengan preprocessing kualitas rendah
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import easyocr
import pytesseract
from typing import Dict, List
import logging
import os

class EnhancedImageProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.easyocr_reader = easyocr.Reader(['id', 'en'])
    
    def enhance_image_quality(self, image_path: str) -> List[np.ndarray]:
        """Apply multiple enhancement techniques to improve OCR accuracy"""
        try:
            # Read original image
            original = cv2.imread(image_path)
            if original is None:
                raise ValueError("Cannot read image")
            
            enhanced_images = []
            
            # 1. Original grayscale
            gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            enhanced_images.append(("original_gray", gray))
            
            # 2. Noise reduction + sharpening
            denoised = cv2.fastNlMeansDenoising(gray)
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            enhanced_images.append(("denoised_sharpened", sharpened))
            
            # 3. Contrast enhancement (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            clahe_enhanced = clahe.apply(gray)
            enhanced_images.append(("clahe_enhanced", clahe_enhanced))
            
            # 4. Gaussian blur + threshold
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            enhanced_images.append(("otsu_threshold", thresh_otsu))
            
            # 5. Adaptive threshold
            adaptive_thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            enhanced_images.append(("adaptive_threshold", adaptive_thresh))
            
            # 6. Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            morph = cv2.morphologyEx(thresh_otsu, cv2.MORPH_CLOSE, kernel)
            enhanced_images.append(("morphological", morph))
            
            # 7. Edge enhancement
            edges = cv2.Canny(gray, 50, 150)
            enhanced_edges = cv2.addWeighted(gray, 0.8, edges, 0.2, 0)
            enhanced_images.append(("edge_enhanced", enhanced_edges))
            
            # 8. Histogram equalization
            hist_eq = cv2.equalizeHist(gray)
            enhanced_images.append(("histogram_equalized", hist_eq))
            
            # 9. Bilateral filter (preserves edges while reducing noise)
            bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
            enhanced_images.append(("bilateral_filtered", bilateral))
            
            # 10. Unsharp masking
            gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
            unsharp = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
            enhanced_images.append(("unsharp_masked", unsharp))
            
            self.logger.info(f"Generated {len(enhanced_images)} enhanced versions")
            return enhanced_images
            
        except Exception as e:
            self.logger.error(f"Error enhancing image: {str(e)}")
            return []
    
    def extract_text_multiple_methods(self, image_path: str) -> Dict[str, any]:
        """Extract text using multiple preprocessing methods and OCR engines"""
        try:
            results = {
                'success': False,
                'extraction_results': [],
                'best_result': None,
                'confidence_scores': [],
                'error': None
            }
            
            # Get enhanced images
            enhanced_images = self.enhance_image_quality(image_path)
            
            if not enhanced_images:
                results['error'] = "Failed to enhance image"
                return results
            
            print(f"🔧 Testing OCR on {len(enhanced_images)} enhanced versions...")
            
            all_results = []
            
            for method_name, enhanced_img in enhanced_images:
                print(f"   📸 Processing: {method_name}")
                
                # Try EasyOCR
                try:
                    easyocr_result = self._extract_with_easyocr(enhanced_img, method_name)
                    if easyocr_result['text_length'] > 0:
                        all_results.append(easyocr_result)
                        print(f"      ✅ EasyOCR: {easyocr_result['text_length']} chars, conf: {easyocr_result['avg_confidence']:.2f}")
                    else:
                        print(f"      ❌ EasyOCR: No text found")
                except Exception as e:
                    print(f"      ❌ EasyOCR failed: {str(e)[:50]}")
                
                # Try Tesseract
                try:
                    tesseract_result = self._extract_with_tesseract(enhanced_img, method_name)
                    if tesseract_result['text_length'] > 0:
                        all_results.append(tesseract_result)
                        print(f"      ✅ Tesseract: {tesseract_result['text_length']} chars, conf: {tesseract_result['avg_confidence']:.2f}")
                    else:
                        print(f"      ❌ Tesseract: No text found")
                except Exception as e:
                    print(f"      ❌ Tesseract failed: {str(e)[:50]}")
            
            # Sort results by quality score
            if all_results:
                # Calculate quality score: text_length * confidence * keyword_bonus
                for result in all_results:
                    keyword_bonus = self._calculate_keyword_bonus(result['full_text'])
                    result['quality_score'] = (
                        result['text_length'] * 
                        result['avg_confidence'] * 
                        keyword_bonus
                    )
                
                # Sort by quality score
                all_results.sort(key=lambda x: x['quality_score'], reverse=True)
                
                results['success'] = True
                results['extraction_results'] = all_results
                results['best_result'] = all_results[0]
                results['confidence_scores'] = [r['avg_confidence'] for r in all_results]
                
                print(f"\n🎯 BEST RESULT:")
                best = results['best_result']
                print(f"   Method: {best['method']} + {best['ocr_engine']}")
                print(f"   Text: '{best['full_text'][:100]}{'...' if len(best['full_text']) > 100 else ''}'")
                print(f"   Length: {best['text_length']} chars")
                print(f"   Confidence: {best['avg_confidence']:.2f}")
                print(f"   Quality Score: {best['quality_score']:.2f}")
                
            else:
                results['error'] = "No text extracted from any method"
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in multi-method extraction: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extraction_results': [],
                'best_result': None
            }
    
    def _extract_with_easyocr(self, image: np.ndarray, method_name: str) -> Dict[str, any]:
        """Extract text using EasyOCR"""
        try:
            # Save temp image for EasyOCR
            temp_path = f"temp_{method_name}.jpg"
            cv2.imwrite(temp_path, image)
            
            # Extract with EasyOCR
            ocr_results = self.easyocr_reader.readtext(temp_path, detail=1)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Process results
            full_text = ""
            confidences = []
            text_data = []
            
            for bbox, text, confidence in ocr_results:
                if confidence > 0.3:  # Lower threshold for low quality images
                    full_text += text + " "
                    confidences.append(confidence)
                    text_data.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
            
            avg_confidence = np.mean(confidences) if confidences else 0
            
            return {
                'method': method_name,
                'ocr_engine': 'EasyOCR',
                'full_text': full_text.strip(),
                'text_length': len(full_text.strip()),
                'avg_confidence': avg_confidence,
                'text_data': text_data,
                'success': len(full_text.strip()) > 0
            }
            
        except Exception as e:
            return {
                'method': method_name,
                'ocr_engine': 'EasyOCR',
                'full_text': "",
                'text_length': 0,
                'avg_confidence': 0,
                'text_data': [],
                'success': False,
                'error': str(e)
            }
    
    def _extract_with_tesseract(self, image: np.ndarray, method_name: str) -> Dict[str, any]:
        """Extract text using Tesseract"""
        try:
            # Configure Tesseract for Indonesian
            custom_config = r'--oem 3 --psm 6 -l ind+eng'
            
            # Extract text
            text = pytesseract.image_to_string(image, config=custom_config)
            
            # Get detailed data with confidence
            try:
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=custom_config)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 30]  # Lower threshold
                avg_confidence = np.mean(confidences) / 100.0 if confidences else 0
            except:
                avg_confidence = 0.5  # Default confidence
            
            return {
                'method': method_name,
                'ocr_engine': 'Tesseract',
                'full_text': text.strip(),
                'text_length': len(text.strip()),
                'avg_confidence': avg_confidence,
                'text_data': [],
                'success': len(text.strip()) > 0
            }
            
        except Exception as e:
            return {
                'method': method_name,
                'ocr_engine': 'Tesseract',
                'full_text': "",
                'text_length': 0,
                'avg_confidence': 0,
                'text_data': [],
                'success': False,
                'error': str(e)
            }
    
    def _calculate_keyword_bonus(self, text: str) -> float:
        """Calculate bonus score based on KTP-related keywords"""
        ktp_keywords = [
            'NIK', 'NAMA', 'TEMPAT', 'LAHIR', 'TANGGAL', 'JENIS', 'KELAMIN',
            'GOLONGAN', 'DARAH', 'ALAMAT', 'AGAMA', 'STATUS', 'PEKERJAAN',
            'KEWARGANEGARAAN', 'BERLAKU', 'HINGGA', 'REPUBLIK', 'INDONESIA',
            'PROVINSI', 'KABUPATEN', 'KOTA', 'DESA', 'KELURAHAN', 'RT', 'RW'
        ]
        
        text_upper = text.upper()
        found_keywords = sum(1 for keyword in ktp_keywords if keyword in text_upper)
        
        # Bonus: 1.0 (no keywords) to 3.0 (many keywords)
        bonus = 1.0 + (found_keywords / len(ktp_keywords)) * 2.0
        return min(bonus, 3.0)
    
    def extract_ktp_fields(self, best_result: Dict) -> Dict[str, str]:
        """Extract specific KTP fields from the best OCR result"""
        if not best_result or not best_result.get('success'):
            return {}
        
        text = best_result.get('full_text', '')
        lines = text.split('\n')
        
        fields = {}
        
        # Simple field extraction patterns
        patterns = {
            'nik': r'(?:NIK|NOMOR INDUK KEPENDUDUKAN)[:\s]*([0-9]{16})',
            'nama': r'(?:NAMA)[:\s]*([A-Z\s]+)',
            'tempat_lahir': r'(?:TEMPAT.*LAHIR)[:\s]*([A-Z\s,]+)',
            'tanggal_lahir': r'(?:TANGGAL.*LAHIR)[:\s]*([0-9\-\/\s]+)',
            'jenis_kelamin': r'(?:JENIS.*KELAMIN)[:\s]*(LAKI-LAKI|PEREMPUAN)',
            'alamat': r'(?:ALAMAT)[:\s]*([A-Z0-9\s,\.\/]+)',
            'agama': r'(?:AGAMA)[:\s]*([A-Z\s]+)',
            'status_kawin': r'(?:STATUS.*PERKAWINAN)[:\s]*([A-Z\s]+)',
            'pekerjaan': r'(?:PEKERJAAN)[:\s]*([A-Z\s]+)',
            'kewarganegaraan': r'(?:KEWARGANEGARAAN)[:\s]*([A-Z\s]+)'
        }
        
        import re
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text.upper())
            if match:
                fields[field] = match.group(1).strip()
        
        return fields

def main():
    print("🔧 DEMO ENHANCED KTP PROCESSOR - KUALITAS RENDAH")
    print("=" * 70)
    
    # Setup paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ktp_folder = os.path.join(current_dir, "ktp")
    
    # Get KTP files
    ktp_files = []
    for file in os.listdir(ktp_folder):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            ktp_files.append(os.path.join(ktp_folder, file))
    
    if not ktp_files:
        print("❌ Tidak ditemukan file KTP di folder ktp/")
        return
    
    print(f"📁 Folder: {ktp_folder}")
    print(f"📄 Files: {[os.path.basename(f) for f in ktp_files]}")
    
    processor = EnhancedImageProcessor()
    
    for ktp_file in ktp_files:
        print(f"\n" + "="*70)
        print(f"📄 PROCESSING: {os.path.basename(ktp_file)}")
        print("="*70)
        
        # Extract with multiple methods
        result = processor.extract_text_multiple_methods(ktp_file)
        
        if result['success']:
            best_result = result['best_result']
            
            print(f"\n✅ EXTRACTION SUCCESSFUL!")
            print(f"📊 Total methods tried: {len(result['extraction_results'])}")
            print(f"🎯 Best method: {best_result['method']} + {best_result['ocr_engine']}")
            print(f"📝 Text length: {best_result['text_length']} characters")
            print(f"🎯 Confidence: {best_result['avg_confidence']:.2f}")
            print(f"⭐ Quality score: {best_result['quality_score']:.2f}")
            
            # Extract KTP fields
            fields = processor.extract_ktp_fields(best_result)
            
            if fields:
                print(f"\n📋 EXTRACTED KTP FIELDS:")
                for field, value in fields.items():
                    print(f"   {field.upper()}: {value}")
            else:
                print(f"\n⚠️  No structured KTP fields extracted")
            
            print(f"\n📄 EXTRACTED TEXT:")
            print(f"'{best_result['full_text'][:200]}{'...' if len(best_result['full_text']) > 200 else ''}'")
            
            # Show alternative results
            if len(result['extraction_results']) > 1:
                print(f"\n📊 OTHER METHODS RESULTS:")
                for i, alt_result in enumerate(result['extraction_results'][1:6], 2):  # Show top 5 alternatives
                    print(f"   {i}. {alt_result['method']} + {alt_result['ocr_engine']}: "
                          f"{alt_result['text_length']} chars, conf: {alt_result['avg_confidence']:.2f}")
        
        else:
            print(f"\n❌ EXTRACTION FAILED: {result.get('error', 'Unknown error')}")
    
    print(f"\n" + "="*70)
    print("🎯 ENHANCED KTP PROCESSOR SUMMARY")
    print("="*70)
    print("✅ Menggunakan 10 metode preprocessing gambar:")
    print("   1. Original grayscale")
    print("   2. Noise reduction + sharpening")
    print("   3. CLAHE contrast enhancement")
    print("   4. Otsu thresholding")
    print("   5. Adaptive thresholding")
    print("   6. Morphological operations")
    print("   7. Edge enhancement")
    print("   8. Histogram equalization")
    print("   9. Bilateral filtering")
    print("   10. Unsharp masking")
    
    print(f"\n✅ Menggunakan 2 OCR engine:")
    print("   - EasyOCR (lebih baik untuk bahasa Indonesia)")
    print("   - Tesseract (lebih cepat, konfigurasi khusus)")
    
    print(f"\n✅ Sistem scoring cerdas:")
    print("   - Text length × confidence × keyword bonus")
    print("   - Bonus untuk kata kunci KTP")
    print("   - Otomatis pilih hasil terbaik")
    
    print(f"\n🚀 TOTAL: 20 KOMBINASI METODE UNTUK SETIAP GAMBAR!")

if __name__ == "__main__":
    main()
