@echo off
echo Document Validation System - Quick Setup for Windows
echo =====================================================

echo.
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found!
echo.

echo Installing Python packages...
python install.py

echo.
echo Setup completed! 
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Start Elasticsearch (see docker-compose.yml)
echo 3. Run: python setup_check.py
echo 4. Test with: python test_validation.py
echo.

pause
