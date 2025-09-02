"""
Quick Check Module for Oracle to PostgreSQL Converter

This module handles verification and additional conversion tools.
"""

import streamlit as st
import os
import json
from main import (
    read_oracle_triggers_to_json,
    render_oracle_sql_from_analysis,
    convert_json_analysis_to_postgresql_sql,
    convert_postgresql_format_files_to_sql
)
from utilities.streamlit_utils import FileManager, SessionManager


def quick_check_page():
    """Quick Check page for verification and additional conversions."""
    st.title("✅ Quick Check - Verification & Conversions")
    
    st.markdown("""
    This page provides verification tools and additional conversion options that were moved from the main workflow.
    You can convert Oracle SQL files to JSON, generate formatted Oracle SQL, and compare results.
    """)
    
    tabs = st.tabs(["🔍 File Verification", "🔄 SQL Conversions", "📊 Comparison Tools"])
    
    with tabs[0]:
        _file_verification_tab()
    
    with tabs[1]:
        _sql_conversions_tab()
    
    with tabs[2]:
        _comparison_tools_tab()


def _file_verification_tab():
    """File verification tab content."""
    st.subheader("📁 Oracle SQL Files Overview")
    
    # Display Oracle SQL files
    oracle_dir = FileManager.DIRECTORIES["oracle"]
    if os.path.exists(oracle_dir):
        oracle_files = FileManager.get_files_in_directory(oracle_dir)
        
        if oracle_files:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write(f"**Found {len(oracle_files)} Oracle SQL files:**")
                for file in oracle_files:
                    st.write(f"- {file}")
            
            with col2:
                # File selector for detailed view
                selected_file = st.selectbox("Select file to preview:", oracle_files)
                
                if selected_file:
                    file_path = os.path.join(oracle_dir, selected_file)
                    st.subheader(f"📄 Preview: {selected_file}")
                    
                    # Display file content with syntax highlighting
                    content = FileManager.read_file_content(file_path)
                    if content:
                        # Show first 20 lines as preview
                        lines = content.split('\n')
                        preview_lines = lines[:20]
                        preview_content = '\n'.join(preview_lines)
                        
                        st.code(preview_content, language="sql")
                        
                        if len(lines) > 20:
                            st.info(f"Showing first 20 lines of {len(lines)} total lines")
                        
                        # File statistics
                        st.write("**File Statistics:**")
                        st.write(f"- Total lines: {len(lines)}")
                        st.write(f"- File size: {len(content)} characters")
        else:
            st.info("No Oracle SQL files found. Please upload files in the File Manager.")
    else:
        st.warning("Oracle directory not found. Please create directories in Configuration.")


def _sql_conversions_tab():
    """SQL conversions tab content."""
    st.subheader("🔄 SQL to JSON Conversion")
    
    # Oracle SQL to JSON conversion
    oracle_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["oracle"]) if os.path.exists(FileManager.DIRECTORIES["oracle"]) else []
    
    if oracle_files:
        st.write("**Convert Oracle SQL files to JSON Analysis:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Convert All Oracle SQL → JSON", type="primary"):
                with st.spinner("Converting Oracle SQL files to JSON..."):
                    try:
                        read_oracle_triggers_to_json()
                        st.success("✅ Successfully converted Oracle SQL files to JSON!")
                        SessionManager.add_to_history("Quick Check", "Success", "Oracle SQL → JSON conversion")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error converting files: {str(e)}")
                        SessionManager.add_to_history("Quick Check", "Error", f"Oracle SQL → JSON: {str(e)}")
        
        with col2:
            # Show JSON files if they exist
            json_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_json"]) if os.path.exists(FileManager.DIRECTORIES["format_json"]) else []
            st.metric("JSON Analysis Files", len(json_files))
    
    st.markdown("---")
    
    # JSON to Formatted Oracle SQL conversion
    st.subheader("📄 JSON to Formatted Oracle SQL")
    
    json_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_json"]) if os.path.exists(FileManager.DIRECTORIES["format_json"]) else []
    
    if json_files:
        st.write("**Convert JSON Analysis to Formatted Oracle SQL:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Convert JSON → Formatted Oracle SQL", type="primary"):
                with st.spinner("Converting JSON to formatted Oracle SQL..."):
                    try:
                        render_oracle_sql_from_analysis()
                        st.success("✅ Successfully converted JSON to formatted Oracle SQL!")
                        SessionManager.add_to_history("Quick Check", "Success", "JSON → Formatted Oracle SQL conversion")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error converting files: {str(e)}")
                        SessionManager.add_to_history("Quick Check", "Error", f"JSON → Formatted SQL: {str(e)}")
        
        with col2:
            # Show formatted SQL files if they exist
            formatted_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_sql"]) if os.path.exists(FileManager.DIRECTORIES["format_sql"]) else []
            st.metric("Formatted SQL Files", len(formatted_files))
    else:
        st.info("No JSON analysis files found. Please run the Oracle SQL → JSON conversion first.")
    
    st.markdown("---")
    
    # JSON to PostgreSQL SQL conversion
    st.subheader("🐘 JSON to PostgreSQL SQL")
    
    json_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_json"]) if os.path.exists(FileManager.DIRECTORIES["format_json"]) else []
    
    if json_files:
        st.write("**Convert JSON Analysis directly to PostgreSQL SQL:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Convert JSON → PostgreSQL SQL", type="primary"):
                with st.spinner("Converting JSON to PostgreSQL SQL..."):
                    try:
                        convert_json_analysis_to_postgresql_sql()
                        st.success("✅ Successfully converted JSON to PostgreSQL SQL!")
                        SessionManager.add_to_history("Quick Check", "Success", "JSON → PostgreSQL SQL conversion")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error converting files: {str(e)}")
                        SessionManager.add_to_history("Quick Check", "Error", f"JSON → PostgreSQL SQL: {str(e)}")
        
        with col2:
            # Show PostgreSQL files if they exist
            postgresql_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_plsql"]) if os.path.exists(FileManager.DIRECTORIES["format_plsql"]) else []
            st.metric("PostgreSQL Files", len(postgresql_files))
    else:
        st.info("No JSON analysis files found. Please run the Oracle SQL → JSON conversion first.")
    
    st.markdown("---")
    
    # Generate Final PostgreSQL SQL conversion
    st.subheader("🎯 Generate Final PostgreSQL SQL")
    
    plsql_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_plsql"]) if os.path.exists(FileManager.DIRECTORIES["format_plsql"]) else []
    
    if plsql_files:
        st.write("**Generate final PostgreSQL SQL files from PL/JSON format:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Generate Final PostgreSQL SQL", type="primary"):
                with st.spinner("Generating final PostgreSQL SQL files..."):
                    try:
                        convert_postgresql_format_files_to_sql()
                        st.success("✅ Successfully generated final PostgreSQL SQL files!")
                        SessionManager.add_to_history("Quick Check", "Success", "Generate Final PostgreSQL SQL")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error generating final PostgreSQL SQL: {str(e)}")
                        SessionManager.add_to_history("Quick Check", "Error", f"Generate Final PostgreSQL: {str(e)}")
        
        with col2:
            # Show final PostgreSQL files if they exist
            final_postgresql_files = [f for f in os.listdir(FileManager.DIRECTORIES["format_plsql"]) if f.endswith('.sql')] if os.path.exists(FileManager.DIRECTORIES["format_plsql"]) else []
            st.metric("Final PostgreSQL SQL Files", len(final_postgresql_files))
    else:
        st.info("No PL/JSON format files found. Please run the JSON → PL/JSON Format conversion first.")


def _comparison_tools_tab():
    """File comparison and analysis tab content."""
    st.subheader("📊 File Comparison & Analysis")
    
    # File comparison section
    oracle_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["oracle"]) if os.path.exists(FileManager.DIRECTORIES["oracle"]) else []
    formatted_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_sql"]) if os.path.exists(FileManager.DIRECTORIES["format_sql"]) else []
    json_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_json"]) if os.path.exists(FileManager.DIRECTORIES["format_json"]) else []
    
    if oracle_files and formatted_files:
        st.write("**Compare Original vs Formatted Oracle SQL:**")
        
        # File selection for comparison
        col1, col2 = st.columns(2)
        
        with col1:
            selected_original = st.selectbox("Select Original Oracle SQL:", oracle_files, key="original_comparison")
        
        with col2:
            # Try to find matching formatted file
            if selected_original:
                base_name = os.path.splitext(selected_original)[0]
                matching_formatted = [f for f in formatted_files if f.startswith(base_name)]
                
                if matching_formatted:
                    selected_formatted = st.selectbox("Select Formatted SQL:", matching_formatted, key="formatted_comparison")
                else:
                    st.warning("No matching formatted file found")
                    selected_formatted = st.selectbox("Select any Formatted SQL:", formatted_files, key="formatted_comparison_fallback")
        
        # Display comparison if both files are selected
        if selected_original and 'selected_formatted' in locals() and selected_formatted:
            if st.button("📊 Compare Files"):
                original_path = os.path.join(FileManager.DIRECTORIES["oracle"], selected_original)
                formatted_path = os.path.join(FileManager.DIRECTORIES["format_sql"], selected_formatted)
                
                original_content = FileManager.read_file_content(original_path)
                formatted_content = FileManager.read_file_content(formatted_path)
                
                if original_content and formatted_content:
                    st.subheader("📊 Side-by-Side Comparison")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Original: {selected_original}**")
                        st.code(original_content, language="sql", line_numbers=True)
                    
                    with col2:
                        st.write(f"**Formatted: {selected_formatted}**")
                        st.code(formatted_content, language="sql", line_numbers=True)
                    
                    # Basic statistics comparison
                    st.subheader("📈 Comparison Statistics")
                    col1, col2, col3 = st.columns(3)
                    
                    original_lines = len(original_content.split('\n'))
                    formatted_lines = len(formatted_content.split('\n'))
                    original_chars = len(original_content)
                    formatted_chars = len(formatted_content)
                    
                    with col1:
                        st.metric("Lines", f"{original_lines} → {formatted_lines}", delta=formatted_lines - original_lines)
                    
                    with col2:
                        st.metric("Characters", f"{original_chars} → {formatted_chars}", delta=formatted_chars - original_chars)
                    
                    with col3:
                        change_percent = ((formatted_chars - original_chars) / original_chars * 100) if original_chars > 0 else 0
                        st.metric("Change %", f"{change_percent:.1f}%")
    
    elif oracle_files and not formatted_files:
        st.info("No formatted SQL files found. Please run the JSON → Formatted Oracle SQL conversion in the SQL Conversions tab.")
    elif not oracle_files:
        st.info("No Oracle SQL files found. Please upload files in the File Manager.")
    
    # JSON Analysis Verification
    if json_files:
        st.markdown("---")
        st.subheader("🔍 JSON Analysis Verification")
        
        selected_json = st.selectbox("Select JSON file to verify:", json_files)
        
        if selected_json:
            json_path = os.path.join(FileManager.DIRECTORIES["format_json"], selected_json)
            
            if st.button("🔍 Analyze JSON Structure"):
                try:
                    content = FileManager.read_file_content(json_path)
                    if content:
                        json_data = json.loads(content)
                        
                        st.subheader(f"📋 Analysis of {selected_json}")
                        
                        # Display JSON structure information
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**JSON Structure:**")
                            if isinstance(json_data, dict):
                                st.write("- Type: Dictionary")
                                st.write(f"- Keys: {len(json_data.keys())}")
                                st.write(f"- Main keys: {list(json_data.keys())[:5]}...")
                            elif isinstance(json_data, list):
                                st.write("- Type: List")
                                st.write(f"- Items: {len(json_data)}")
                        
                        with col2:
                            st.write("**File Information:**")
                            st.write(f"- File size: {len(content)} characters")
                            st.write("- JSON valid: ✅")
                        
                        # Show formatted JSON
                        st.subheader("📄 JSON Preview")
                        json_str = json.dumps(json_data, indent=2)
                        st.json(json_str)
                
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON format: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error analyzing JSON: {str(e)}")
