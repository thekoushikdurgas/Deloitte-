@echo off
echo Oracle to PostgreSQL Converter - Streamlit Web Interface
echo ========================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Python found. Starting application...
echo.

REM Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo Installing/updating dependencies...
    pip install -r requirements.txt
    echo.
)

REM Start the Streamlit application
echo Starting Oracle to PostgreSQL Converter web interface...
echo Open your browser to: http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

python start_app.py

pause
