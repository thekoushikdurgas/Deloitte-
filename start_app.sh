#!/bin/bash

# Oracle to PostgreSQL Converter - Streamlit Web Interface Launcher
# For Unix/Linux/macOS systems

echo "🔄 Oracle to PostgreSQL Converter - Streamlit Web Interface"
echo "============================================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    if ! command_exists python; then
        echo "❌ Error: Python is not installed or not in PATH"
        echo "Please install Python 3.8 or higher"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "✅ Python found: $($PYTHON_CMD --version)"
echo

# Check if pip is available
if ! command_exists pip3 && ! command_exists pip; then
    echo "❌ Error: pip is not installed"
    echo "Please install pip for Python package management"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing/updating dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
    echo
fi

# Make sure the startup script is executable
chmod +x start_app.py 2>/dev/null || true

# Start the Streamlit application
echo "🚀 Starting Oracle to PostgreSQL Converter web interface..."
echo "🌐 Open your browser to: http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop the application"
echo

$PYTHON_CMD start_app.py
