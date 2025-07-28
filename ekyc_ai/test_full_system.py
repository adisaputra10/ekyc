#!/usr/bin/env python3
"""
Test script to demonstrate the full eKYC system integration
Tests both KTP and Akta validation through the API
"""

import requests
import json
from pathlib import Path

def test_ktp_validation():
    """Test KTP validation through API"""
    print("🔍 Testing KTP Validation...")
    
    # Check if we have KTP images
    ktp_dir = Path("ktp")
    if ktp_dir.exists():
        ktp_files = list(ktp_dir.glob("*.png")) + list(ktp_dir.glob("*.jpg")) + list(ktp_dir.glob("*.jpeg"))
        if ktp_files:
            ktp_file = ktp_files[0]
            print(f"Using KTP file: {ktp_file}")
            
            # Test API endpoint
            url = "http://localhost:8001/validate/ktp"
            with open(ktp_file, 'rb') as f:
                files = {'file': (ktp_file.name, f, 'image/png')}
                try:
                    response = requests.post(url, files=files, timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ KTP Validation SUCCESS")
                        print(f"Status: {result.get('status', 'Unknown')}")
                        print(f"Confidence: {result.get('confidence', 0):.2f}")
                        print(f"Fields extracted: {len(result.get('validation_details', {}).get('extracted_fields', {}))}")
                        return True
                    else:
                        print(f"❌ KTP Validation FAILED: {response.status_code} - {response.text}")
                        return False
                except requests.exceptions.RequestException as e:
                    print(f"❌ KTP API Request FAILED: {e}")
                    return False
    
    print("❌ No KTP files found in ktp/ directory")
    return False

def test_akta_validation():
    """Test Akta validation through API"""
    print("\n📄 Testing Akta Validation...")
    
    # Check if we have Akta PDF
    akta_files = list(Path(".").glob("*.pdf"))
    if akta_files:
        akta_file = akta_files[0]
        print(f"Using Akta file: {akta_file}")
        
        # Test API endpoint
        url = "http://localhost:8001/validate/akta"
        with open(akta_file, 'rb') as f:
            files = {'file': (akta_file.name, f, 'application/pdf')}
            try:
                response = requests.post(url, files=files, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Akta Validation SUCCESS")
                    print(f"Status: {result.get('status', 'Unknown')}")
                    print(f"Confidence: {result.get('confidence', 0):.2f}")
                    return True
                else:
                    print(f"❌ Akta Validation FAILED: {response.status_code} - {response.text}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"❌ Akta API Request FAILED: {e}")
                return False
    
    print("❌ No Akta PDF files found")
    return False

def test_api_health():
    """Test API health endpoint"""
    print("🏥 Testing API Health...")
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            print("✅ API Health Check PASSED")
            return True
        else:
            print(f"❌ API Health Check FAILED: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API Health Check FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting eKYC System Integration Test")
    print("=" * 50)
    
    # Test API health first
    if not test_api_health():
        print("\n❌ API is not running. Please start the API server first:")
        print("   python api.py")
        return
    
    # Test KTP validation
    ktp_success = test_ktp_validation()
    
    # Test Akta validation
    akta_success = test_akta_validation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"API Health: ✅ PASS")
    print(f"KTP Validation: {'✅ PASS' if ktp_success else '❌ FAIL'}")
    print(f"Akta Validation: {'✅ PASS' if akta_success else '❌ FAIL'}")
    
    if ktp_success and akta_success:
        print("\n🎉 ALL TESTS PASSED! Your eKYC system is fully functional.")
        print("\n🌐 You can now access the frontend at: http://localhost:8001/")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()
