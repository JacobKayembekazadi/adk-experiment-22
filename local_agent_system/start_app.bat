@echo off
title Local Multi-Agent Collaboration System
echo 🤖 Local Multi-Agent Collaborative Intelligence
echo ============================================================

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

:: Change to script directory
cd /d "%~dp0"

:: Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo ✅ Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found - using system Python
)

:: Install dependencies if missing
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing required dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Check if Ollama is running
echo 🔍 Checking Ollama connection...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Ollama server not detected
    echo 💡 Start Ollama with: ollama serve
    echo.
    set /p continue="Continue anyway? (y/N): "
    if /i not "%continue%"=="y" (
        echo 👋 Exiting...
        pause
        exit /b 1
    )
) else (
    echo ✅ Ollama server is running
)

echo.
echo 🚀 Starting Streamlit application...
echo    URL: http://localhost:8501
echo    Press Ctrl+C to stop
echo ============================================================

:: Start the application
python run_streamlit.py

echo.
echo 👋 Application stopped
pause
