#!/usr/bin/env python3
"""
Script untuk menjalankan server API validasi dokumen
"""

import uvicorn
from api import app
from config import Config

def main():
    """Main function to run the API server"""
    config = Config()
    
    print("=== Document Validation API Server ===")
    print("Starting FastAPI server...")
    print("API Documentation akan tersedia di: http://localhost:8000/docs")
    print("API akan berjalan di: http://localhost:8000")
    print("\nEndpoints yang tersedia:")
    print("- POST /validate/ktp - Validasi dokumen KTP")
    print("- POST /validate/akta - Validasi dokumen Akta")
    print("- POST /validate/comprehensive - Validasi kedua dokumen sekaligus")
    print("- POST /validate/single - Validasi dokumen tunggal")
    print("- GET /health - Status kesehatan API")
    print("\nTekan Ctrl+C untuk menghentikan server")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer dihentikan oleh pengguna")
    except Exception as e:
        print(f"Error menjalankan server: {str(e)}")

if __name__ == "__main__":
    main()
