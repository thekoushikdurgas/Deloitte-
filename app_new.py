#!/usr/bin/env python3
"""
Oracle to PostgreSQL Converter - Streamlit Web Interface

This is the main entry point for the Streamlit application. The application has been
refactored into modular components organized in the ui/ directory for better maintainability.

Features:
- File upload and management for Oracle SQL files
- Step-by-step conversion workflow with progress tracking
- Configuration management for Oracle-PostgreSQL mappings
- Visualization of conversion statistics and results
- Management of unprocessed items (rest_list.csv)
- Download and export functionality for converted files
"""

import streamlit as st
import sys
import time

# Add utilities to path
sys.path.append('utilities')

# Page configuration
st.set_page_config(
    page_title="Oracle to PostgreSQL Converter",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import UI modules
from ui.sidebar import display_sidebar
from ui.dashboard import dashboard_page
from ui.file_manager import file_manager_page
from ui.configuration import configuration_page
from ui.workflow import workflow_page
from ui.analytics import analytics_page
from ui.quick_check import quick_check_page
from ui.rest_list import rest_list_page

# Import utilities
from utilities.streamlit_utils import FileManager, SessionManager


def main():
    """Main application function."""
    # Initialize session state
    SessionManager.initialize_session_state()
    
    # Initialize directories
    FileManager.ensure_directories()
    
    # Display sidebar and get selected page
    current_page = display_sidebar()
    
    # Route to appropriate page
    page_functions = {
        "dashboard": dashboard_page,
        "file_manager": file_manager_page,
        "configuration": configuration_page,
        "workflow": workflow_page,
        "quick_check": quick_check_page,
        "analytics": analytics_page,
        "rest_list": rest_list_page
    }
    
    # Execute the selected page function
    if current_page in page_functions:
        page_functions[current_page]()
    else:
        st.error(f"Unknown page: {current_page}")
        dashboard_page()  # Fallback to dashboard
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🔄 **Oracle to PostgreSQL Converter** | "
        "Built with Streamlit | "
        f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )


if __name__ == "__main__":
    main()
