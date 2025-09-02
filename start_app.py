#!/usr/bin/env python3
"""
Startup script for the Oracle to PostgreSQL Converter Streamlit application.

This script provides a simple way to launch the Streamlit web interface
with proper error handling and environment checks.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'streamlit',
        'pandas', 
        'plotly',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n💡 To install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        print("Or install all requirements with:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        "files/oracle",
        "files/format_json",
        "files/format_sql", 
        "files/format_pl_json",
        "files/format_plsql",
        "output",
        "utilities"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory: {directory}")

def check_files():
    """Check if core files exist."""
    required_files = [
        "app.py",
        "requirements.txt",
        "utilities/common.py",
        "utilities/streamlit_utils.py",
        "utilities/OracleTriggerAnalyzer.py",
        "utilities/FormatSQL.py",
        "utilities/JSONTOPLJSON.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} is missing")
    
    if missing_files:
        print(f"\n❌ Missing required files: {missing_files}")
        return False
    
    return True

def launch_streamlit():
    """Launch the Streamlit application."""
    print("\n🚀 Starting Oracle to PostgreSQL Converter...")
    print("📱 The web interface will open in your browser")
    print("🌐 Default URL: http://localhost:8501")
    print("\n⏹️  Press Ctrl+C to stop the application\n")
    
    try:
        # Launch Streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "false",
            "--server.address", "localhost",
            "--server.port", "8501"
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    print("🔄 Oracle to PostgreSQL Converter - Startup Script")
    print("=" * 55)
    
    # Check Python version
    if not check_python_version():
        return False
    
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        return False
    
    print("\n📁 Checking directories...")
    ensure_directories()
    
    print("\n📄 Checking core files...")
    if not check_files():
        return False
    
    print("\n✅ All checks passed!")
    time.sleep(1)
    
    # Launch the application
    return launch_streamlit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
