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
    st.markdown("This section provides two essential comparison tools for validating your conversion workflow.")
    
    # === CHECK 1: Oracle SQL vs Formatted Oracle SQL ===
    st.markdown("### 1️⃣ Oracle SQL Files vs Formatted Oracle SQL Files")
    
    oracle_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["oracle"]) if os.path.exists(FileManager.DIRECTORIES["oracle"]) else []
    formatted_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_sql"]) if os.path.exists(FileManager.DIRECTORIES["format_sql"]) else []
    
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
            if st.button("📊 Compare Oracle SQL Files", key="compare_oracle_sql"):
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
        st.info("ℹ️ No formatted SQL files found. Please run the JSON → Formatted Oracle SQL conversion in the SQL Conversions tab.")
    elif not oracle_files:
        st.info("ℹ️ No Oracle SQL files found. Please upload files in the File Manager.")
    
    # === CHECK 2: PostgreSQL Format JSON vs Uploaded JSON ===
    st.markdown("---")
    st.markdown("### 2️⃣ PostgreSQL Format JSON vs Uploaded JSON")
    
    # Get PostgreSQL format JSON files
    postgresql_files = FileManager.get_files_in_directory(FileManager.DIRECTORIES["format_plsql"]) if os.path.exists(FileManager.DIRECTORIES["format_plsql"]) else []
    postgresql_json_files = [f for f in postgresql_files if f.endswith('.json')]
    
    if postgresql_json_files:
        st.write("**Compare PostgreSQL Format JSON with User Uploaded JSON:**")
        
        # File selection for PostgreSQL JSON
        col1, col2 = st.columns(2)
        
        with col1:
            selected_postgresql_json = st.selectbox("Select PostgreSQL Format JSON:", postgresql_json_files, key="postgresql_json_comparison")
        
        with col2:
            # File uploader for user JSON
            uploaded_json_file = st.file_uploader(
                "Upload JSON file to compare",
                type=['json'],
                key="uploaded_json_comparison",
                help="Upload a JSON file to compare against the PostgreSQL format"
            )
        
        # Display comparison if both files are available
        if selected_postgresql_json and uploaded_json_file:
            if st.button("📊 Compare JSON Files", key="compare_json_files"):
                postgresql_json_path = os.path.join(FileManager.DIRECTORIES["format_plsql"], selected_postgresql_json)
                postgresql_content = FileManager.read_file_content(postgresql_json_path)
                
                # Read uploaded file content
                try:
                    uploaded_content = uploaded_json_file.read().decode('utf-8')
                    uploaded_json_file.seek(0)  # Reset file pointer
                    
                    if postgresql_content and uploaded_content:
                        st.subheader("📊 JSON Comparison")
                        
                        # Parse both JSON files for structural comparison
                        try:
                            postgresql_json = json.loads(postgresql_content)
                            uploaded_json = json.loads(uploaded_content)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**PostgreSQL Format: {selected_postgresql_json}**")
                                st.json(postgresql_json)
                            
                            with col2:
                                st.write(f"**Uploaded: {uploaded_json_file.name}**")
                                st.json(uploaded_json)
                            
                            # JSON structure comparison
                            st.subheader("📈 JSON Structure Comparison")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                postgresql_keys = len(postgresql_json.keys()) if isinstance(postgresql_json, dict) else 0
                                uploaded_keys = len(uploaded_json.keys()) if isinstance(uploaded_json, dict) else 0
                                st.metric("Keys Count", f"{postgresql_keys} vs {uploaded_keys}")
                            
                            with col2:
                                postgresql_size = len(postgresql_content)
                                uploaded_size = len(uploaded_content)
                                st.metric("File Size", f"{postgresql_size} vs {uploaded_size}")
                            
                            with col3:
                                # Check if both have same structure
                                same_keys = (isinstance(postgresql_json, dict) and isinstance(uploaded_json, dict) and 
                                           set(postgresql_json.keys()) == set(uploaded_json.keys()))
                                st.metric("Same Structure", "✅ Yes" if same_keys else "❌ No")
                            
                            with col4:
                                # Check data type compatibility
                                same_type = type(postgresql_json) == type(uploaded_json)
                                st.metric("Same Type", "✅ Yes" if same_type else "❌ No")
                            
                            # Show key differences if applicable
                            if isinstance(postgresql_json, dict) and isinstance(uploaded_json, dict):
                                postgresql_keys_set = set(postgresql_json.keys())
                                uploaded_keys_set = set(uploaded_json.keys())
                                
                                only_in_postgresql = postgresql_keys_set - uploaded_keys_set
                                only_in_uploaded = uploaded_keys_set - postgresql_keys_set
                                
                                if only_in_postgresql or only_in_uploaded:
                                    st.subheader("🔍 Key Differences")
                                    
                                    if only_in_postgresql:
                                        st.warning(f"Keys only in PostgreSQL format: {', '.join(only_in_postgresql)}")
                                    
                                    if only_in_uploaded:
                                        st.warning(f"Keys only in uploaded file: {', '.join(only_in_uploaded)}")
                                else:
                                    st.success("✅ Both JSON files have the same key structure!")
                        
                        except json.JSONDecodeError as e:
                            st.error(f"❌ JSON parsing error: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Error comparing JSON files: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ Error reading uploaded file: {str(e)}")
    else:
        st.info("ℹ️ No PostgreSQL format JSON files found. Please run the conversion workflow to generate PostgreSQL format files.")
