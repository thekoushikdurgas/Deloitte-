"""
Dashboard Module for Oracle to PostgreSQL Converter

This module handles the main dashboard page functionality.
"""

import streamlit as st
import pandas as pd
from utilities.streamlit_utils import FileManager, WorkflowManager


def dashboard_page():
    """Main dashboard page."""
    st.title("🏠 Oracle to PostgreSQL Converter Dashboard")
    
    # Welcome message
    st.markdown("""
    Welcome to the Oracle to PostgreSQL Converter! This tool helps you convert 
    Oracle trigger SQL files to PostgreSQL format through a structured workflow.
    """)
    
    # Statistics overview
    stats = FileManager.get_file_stats()
    metrics = {
        "Oracle Files": (stats.get("oracle", 0), "SQL files ready for conversion"),
        "JSON Analysis": (stats.get("format_json", 0), "Completed analysis files"),
        "Formatted SQL": (stats.get("format_sql", 0), "Formatted Oracle SQL files"),
        "PostgreSQL Files": (stats.get("format_plsql", 0), "Converted PostgreSQL files")
    }
    
    col1, col2, col3, col4 = st.columns(4)
    for i, (label, (value, help_text)) in enumerate(metrics.items()):
        with [col1, col2, col3, col4][i]:
            st.metric(label, value, help=help_text)
    
    # Workflow overview
    st.subheader("🔄 Conversion Workflow Overview")
    
    for i, step in enumerate(WorkflowManager.STEPS, 1):
        status = WorkflowManager.get_step_status(i-1)
        st.markdown(f"{i}. **{step['name']}** - {status}")
        st.write(f"   _{step['description']}_")
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    
    if st.session_state.conversion_history:
        df = pd.DataFrame(st.session_state.conversion_history)
        st.dataframe(df, width='stretch')
    else:
        st.info("No recent conversion activity.")
