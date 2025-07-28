#!/usr/bin/env python3
"""
Script instalasi untuk Document Validation System
"""

import subprocess
import sys
import os
import shutil

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def install_packages():
    """Install required packages"""
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing Python packages")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def create_env_file():
    """Create .env file from template"""
    print("\n🔄 Setting up environment configuration...")
    
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists('.env.example'):
        try:
            shutil.copy('.env.example', '.env')
            print("✅ Created .env from template")
            print("⚠️  Please edit .env file and add your API keys!")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ .env.example not found")
        return False

def create_upload_directory():
    """Create uploads directory"""
    print("\n🔄 Creating upload directory...")
    
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        try:
            os.makedirs(upload_dir)
            print(f"✅ Created {upload_dir} directory")
        except Exception as e:
            print(f"❌ Failed to create {upload_dir} directory: {e}")
            return False
    else:
        print(f"✅ {upload_dir} directory already exists")
    
    return True

def print_next_steps():
    """Print instructions for next steps"""
    print("\n" + "="*60)
    print("🎉 INSTALLATION COMPLETED!")
    print("="*60)
    
    print("\n📋 NEXT STEPS:")
    print("\n1. Configure Environment Variables:")
    print("   - Edit .env file")
    print("   - Add your OPENAI_API_KEY")
    print("   - Add your ELASTICSEARCH_PASSWORD")
    
    print("\n2. Setup Elasticsearch:")
    print("   - Install Elasticsearch 8.x")
    print("   - Start Elasticsearch service")
    print("   - Note down the password for elastic user")
    
    print("\n3. Test Installation:")
    print("   python setup_check.py")
    
    print("\n4. Run Validation Tests:")
    print("   python test_validation.py")
    
    print("\n5. Start API Server:")
    print("   python run_api.py")
    
    print("\n6. Access API Documentation:")
    print("   http://localhost:8000/docs")
    
    print("\n📚 For detailed instructions, see README.md")

def main():
    """Main installation function"""
    print("Document Validation System - Installation Script")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Installation failed: Incompatible Python version")
        sys.exit(1)
    
    # Install packages
    if not install_packages():
        print("\n❌ Installation failed: Package installation error")
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        print("\n⚠️  Warning: Environment file setup incomplete")
    
    # Create upload directory
    if not create_upload_directory():
        print("\n⚠️  Warning: Upload directory creation failed")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
