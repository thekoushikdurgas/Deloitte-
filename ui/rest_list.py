"""
Rest List Module for Oracle to PostgreSQL Converter

This module handles rest list management functionality.
"""

import streamlit as st
import pandas as pd
import time
import plotly.express as px
from utilities.streamlit_utils import ConfigManager, SessionManager


def rest_list_page():
    """Rest list management page."""
    st.title("📋 Rest List Manager")
    
    df = ConfigManager.load_rest_list()
    
    if df is not None and not df.empty:
        st.subheader("📊 Rest List Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Items", len(df))
        with col2:
            unique_files = df['filename'].nunique() if 'filename' in df.columns else 0
            st.metric("Unique Files", unique_files)
        with col3:
            avg_indent = df['indent'].mean() if 'indent' in df.columns else 0
            st.metric("Avg Indent", f"{avg_indent:.1f}")
        
        # Visualization
        if 'filename' in df.columns and len(df) > 0:
            st.subheader("📈 Rest Items by File")
            file_counts = df['filename'].value_counts()
            fig_rest = px.bar(
                x=file_counts.index,
                y=file_counts.values,
                title="Unprocessed Items by File",
                labels={'x': 'File', 'y': 'Item Count'}
            )
            st.plotly_chart(fig_rest, width='stretch')
        
        # Display the data
        st.subheader("📋 Rest List Data")
        
        # Filters
        if 'filename' in df.columns:
            files = df['filename'].unique()
            selected_file = st.selectbox("Filter by file:", ['All'] + list(files))
            
            if selected_file != 'All':
                df = df[df['filename'] == selected_file]
        
        # Display table
        st.dataframe(df, width='stretch')
        
        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            "⬇️ Download Rest List",
            data=csv,
            file_name=f"rest_list_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Clear rest list
        if st.button("🗑️ Clear Rest List"):
            if ConfigManager.clear_rest_list():
                st.success("Rest list cleared!")
                SessionManager.add_to_history("Rest List", "Success", "Cleared rest list")
                st.rerun()
            else:
                st.error("Failed to clear rest list")
    
    elif df is not None:
        st.info("Rest list is empty.")
    
    else:
        st.warning("Rest list file not found.")
        
        # Create empty rest list
        if st.button("Create Empty Rest List"):
            if ConfigManager.clear_rest_list():
                st.success("Empty rest list created!")
                SessionManager.add_to_history("Rest List", "Success", "Created empty rest list")
                st.rerun()
            else:
                st.error("Failed to create rest list")
