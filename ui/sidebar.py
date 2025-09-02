"""
Sidebar Module for Oracle to PostgreSQL Converter

This module handles the sidebar navigation and file statistics display.
"""

import streamlit as st
from utilities.streamlit_utils import FileManager


def display_sidebar():
    """Display the sidebar with navigation and file statistics."""
    st.sidebar.title("🔄 Oracle to PostgreSQL")
    st.sidebar.markdown("---")
    
    # Navigation
    pages = {
        "🏠 Dashboard": "dashboard",
        "📁 File Manager": "file_manager", 
        "⚙️ Configuration": "configuration",
        "🔄 Conversion Workflow": "workflow",
        "✅ Quick Check": "quick_check",
        "📊 Analytics": "analytics",
        "📋 Rest List Manager": "rest_list"
    }
    
    selected_page = st.sidebar.selectbox(
        "Navigate to:",
        list(pages.keys()),
        format_func=lambda x: x
    )
    
    st.sidebar.markdown("---")
    
    # File statistics
    st.sidebar.subheader("📊 File Statistics")
    stats = FileManager.get_file_stats()
    
    directory_names = {
        "oracle": "Oracle SQL Files",
        "format_json": "JSON Analysis", 
        "format_sql": "Formatted SQL",
        "format_pl_json": "PL/JSON Files",
        "format_plsql": "PostgreSQL Files"
    }
    
    for key, count in stats.items():
        name = directory_names.get(key, key)
        color = "🟢" if count > 0 else "🔴"
        st.sidebar.metric(
            label=f"{color} {name}",
            value=count
        )
    
    st.sidebar.markdown("---")
    
    # Quick actions
    st.sidebar.subheader("⚡ Quick Actions")
    
    if st.sidebar.button("🗂️ Create Directories"):
        FileManager.ensure_directories()
        st.sidebar.success("Directories created!")
    
    if st.sidebar.button("🔄 Refresh Stats"):
        st.rerun()
    
    return pages[selected_page]
