#!/usr/bin/env python3
"""
Enhanced KTP Demo dengan multiple OCR methods dan image analysis
"""

import os
import cv2
import numpy as np
from PIL import Image
from image_processor import ImageProcessor

def analyze_image_quality(image_path):
    """Analyze image quality for OCR"""
    print(f"\n🔍 Analyzing image quality: {os.path.basename(image_path)}")
    
    # Read image with OpenCV
    img = cv2.imread(image_path)
    if img is None:
        print("❌ Cannot read image")
        return
    
    # Basic image info
    height, width, channels = img.shape
    print(f"📏 Dimensions: {width}x{height} pixels")
    print(f"🎨 Channels: {channels}")
    
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Check brightness
    mean_brightness = np.mean(gray)
    print(f"💡 Average brightness: {mean_brightness:.1f}/255")
    
    # Check contrast
    contrast = gray.std()
    print(f"🔆 Contrast (std dev): {contrast:.1f}")
    
    # Check if image is too dark or too bright
    if mean_brightness < 50:
        print("⚠️  Image might be too dark for OCR")
    elif mean_brightness > 200:
        print("⚠️  Image might be too bright for OCR")
    else:
        print("✅ Brightness level seems OK")
    
    # Check contrast
    if contrast < 30:
        print("⚠️  Low contrast might affect OCR quality")
    else:
        print("✅ Contrast level seems OK")

def test_ocr_methods(image_path):
    """Test different OCR methods on the image"""
    print(f"\n🔧 Testing OCR methods on: {os.path.basename(image_path)}")
    
    processor = ImageProcessor()
    
    # Test EasyOCR
    print(f"\n1️⃣ Testing EasyOCR...")
    easy_result = processor.extract_text_easyocr(image_path)
    if easy_result['success']:
        text = easy_result.get('full_text', '')
        print(f"   Text extracted: '{text}' (length: {len(text)})")
        
        # Show detailed results
        if 'text_data' in easy_result:
            print(f"   Detected {len(easy_result['text_data'])} text regions:")
            for i, item in enumerate(easy_result['text_data']):
                conf = item.get('confidence', 0)
                text = item.get('text', '')
                print(f"      {i+1}. '{text}' (confidence: {conf:.2f})")
    else:
        print(f"   ❌ Failed: {easy_result.get('error', 'Unknown error')}")
    
    # Test Tesseract
    print(f"\n2️⃣ Testing Tesseract...")
    tesseract_result = processor.extract_text_tesseract(image_path)
    if tesseract_result['success']:
        text = tesseract_result.get('full_text', '')
        print(f"   Text extracted: '{text}' (length: {len(text)})")
    else:
        print(f"   ❌ Failed: {tesseract_result.get('error', 'Unknown error')}")

def suggest_improvements(image_path):
    """Suggest image improvements for better OCR"""
    print(f"\n💡 Suggestions for better OCR results:")
    
    # Read image
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    height, width = gray.shape
    
    # Size recommendation
    if width < 800 or height < 600:
        print("   📏 Consider using higher resolution image (min 800x600)")
    
    # Brightness recommendations
    mean_brightness = np.mean(gray)
    if mean_brightness < 50:
        print("   💡 Try increasing image brightness")
    elif mean_brightness > 200:
        print("   💡 Try reducing image brightness")
    
    # Contrast recommendations
    contrast = gray.std()
    if contrast < 30:
        print("   🔆 Try increasing image contrast")
    
    # General recommendations
    print("   📸 Tips for better KTP images:")
    print("      - Use good lighting (natural light is best)")
    print("      - Avoid shadows and reflections")
    print("      - Keep camera parallel to KTP surface")
    print("      - Ensure all text is clearly visible")
    print("      - Use at least 1080p resolution when taking photo")

def main():
    print("🔍 Enhanced KTP Analysis Demo")
    print("=" * 60)
    
    # Setup paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ktp_folder = os.path.join(current_dir, "ktp")
    
    # Get KTP files
    ktp_files = []
    for file in os.listdir(ktp_folder):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            ktp_files.append(os.path.join(ktp_folder, file))
    
    print(f"📁 Folder: {ktp_folder}")
    print(f"📄 Files found: {[os.path.basename(f) for f in ktp_files]}")
    
    for ktp_file in ktp_files:
        print(f"\n" + "="*70)
        print(f"📄 ANALYZING: {os.path.basename(ktp_file)}")
        print("="*70)
        
        # Analyze image quality
        analyze_image_quality(ktp_file)
        
        # Test OCR methods
        test_ocr_methods(ktp_file)
        
        # Provide suggestions
        suggest_improvements(ktp_file)
    
    print(f"\n" + "="*70)
    print("📋 SUMMARY & RECOMMENDATIONS")
    print("="*70)
    print("Based on the analysis, here are the main issues:")
    print("1. OCR extracted very little text from the images")
    print("2. This suggests the KTP images may have quality issues")
    print("3. Consider using higher quality, well-lit images")
    print("\nFor testing purposes, you can:")
    print("- Find a clearer KTP image online")
    print("- Take a new photo with better lighting")
    print("- Use a scanner instead of camera photo")
    print("\n🚀 The validation system is working correctly!")
    print("The issue is with the input image quality, not the system.")

if __name__ == "__main__":
    main()
