#!/usr/bin/env python3
"""
Oracle to PostgreSQL Converter - Streamlit Web Interface

This Streamlit application provides a web-based interface for converting
Oracle trigger SQL files to PostgreSQL format with comprehensive management
of the conversion workflow, file operations, and configuration settings.

Features:
- File upload and management for Oracle SQL files
- Step-by-step conversion workflow with progress tracking
- Configuration management for Oracle-PostgreSQL mappings
- Visualization of conversion statistics and results
- Management of unprocessed items (rest_list.csv)
- Download and export functionality for converted files
"""

import streamlit as st
import os
import sys
import pandas as pd
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go

# Add utilities to path
sys.path.append('utilities')

# Import our conversion modules
from main import (
    read_oracle_triggers_to_json,
    render_oracle_sql_from_analysis,
    read_json_to_oracle_triggers,
    read_json_to_postsql_triggers,
    convert_json_analysis_to_postgresql_sql,
    convert_postgresql_format_files_to_sql
)
from utilities.common import setup_logging, debug, info, warning, error
from utilities.streamlit_utils import (
    FileManager, WorkflowManager, ConfigManager, 
    UIHelpers, SessionManager
)

# Page configuration
st.set_page_config(
    page_title="Oracle to PostgreSQL Converter",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
SessionManager.initialize_session_state()

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
    
    # # Quick start
    # st.subheader("🚀 Quick Start")
    
    # col1, col2 = st.columns(2)
    
    # with col1:
    #     if st.button("📁 Go to File Manager", width='stretch'):
    #         st.session_state.current_page = "file_manager"
    #         st.rerun()
    
    # with col2:
    #     if st.button("🔄 Start Conversion", width='stretch'):
    #         st.session_state.current_page = "workflow"
    #         st.rerun()

def file_manager_page():
    """File management page."""
    st.title("📁 File Manager")
    
    tabs = st.tabs(["📤 Upload Files", "📂 Browse Files", "📥 Download Results"])
    
    with tabs[0]:
        st.subheader("Upload Oracle SQL Files")
        
        uploaded_files = st.file_uploader(
            "Choose Oracle SQL files",
            type=['sql'],
            accept_multiple_files=True,
            help="Upload your Oracle trigger SQL files for conversion"
        )
        
        if uploaded_files:
            FileManager.ensure_directories()
            
            for uploaded_file in uploaded_files:
                if FileManager.save_uploaded_file(uploaded_file, FileManager.DIRECTORIES["oracle"]):
                    st.success(f"Saved: {uploaded_file.name}")
                    SessionManager.add_to_history("File Upload", "Success", f"Uploaded {uploaded_file.name}")
                else:
                    st.error(f"Failed to save: {uploaded_file.name}")
            
            st.balloons()
    
    with tabs[1]:
        st.subheader("Browse Files")
        
        # Directory selector
        directory_options = {
            "Oracle SQL Files": FileManager.DIRECTORIES["oracle"],
            "JSON Analysis": FileManager.DIRECTORIES["format_json"],
            "Formatted SQL": FileManager.DIRECTORIES["format_sql"],
            "PL/JSON Files": FileManager.DIRECTORIES["format_pl_json"],
            "PostgreSQL Files": FileManager.DIRECTORIES["format_plsql"]
        }
        
        selected_dir_name = st.selectbox("Select directory:", list(directory_options.keys()))
        directory = directory_options[selected_dir_name]
        
        if os.path.exists(directory):
            files = FileManager.get_files_in_directory(directory)
            
            if files:
                selected_file = st.selectbox("Select file to view:", files)
                
                # Clear file operation states when switching files
                if 'previous_selected_file' not in st.session_state:
                    st.session_state.previous_selected_file = selected_file
                elif st.session_state.previous_selected_file != selected_file:
                    # File changed, reset operation states
                    SessionManager.reset_file_operation_states()
                    st.session_state.previous_selected_file = selected_file
                
                if selected_file:
                    file_path = os.path.join(directory, selected_file)
                    
                    # Check if file still exists (might have been deleted)
                    if not os.path.exists(file_path):
                        st.warning(f"File {selected_file} no longer exists. It may have been deleted.")
                        st.rerun()
                        return
                    
                    col1, col2,col3,col4,col5,col6 = st.columns([2, 1,1,1,1,1])
                    
                    with col1:
                        st.subheader(f"📄 {selected_file}")
                    
                    with col2:
                        UIHelpers.create_download_button(file_path, "⬇️ Download")
                    with col3:
                        UIHelpers.create_edit_button(file_path, "✏️ Edit")
                    with col4:
                        UIHelpers.create_delete_button(file_path, "🗑️ Delete")
                    with col5:
                        UIHelpers.create_rename_button(file_path, "📝 Rename")
                    with col6:
                        # Add a refresh button
                        if st.button("🔄 Refresh", key=f"refresh_{os.path.basename(file_path)}"):
                            st.rerun()
                    
                    # Handle file editing mode
                    if st.session_state.get('editing_mode', False) and st.session_state.get('editing_file') == file_path:
                        st.subheader("✏️ Edit File")
                        current_content = FileManager.read_file_content(file_path)
                        if current_content is not None:
                            edited_content = st.text_area(
                                "Edit file content:",
                                value=current_content,
                                height=400,
                                key=f"edit_content_{os.path.basename(file_path)}"
                            )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 Save Changes", key=f"save_edit_{os.path.basename(file_path)}"):
                                    try:
                                        with open(file_path, 'w', encoding='utf-8') as f:
                                            f.write(edited_content)
                                        st.success("File saved successfully!")
                                        SessionManager.add_to_history("File Edit", "Success", f"Edited {os.path.basename(file_path)}")
                                        st.session_state['editing_mode'] = False
                                        st.session_state['editing_file'] = None
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to save file: {str(e)}")
                            
                            with col_cancel:
                                if st.button("❌ Cancel", key=f"cancel_edit_{os.path.basename(file_path)}"):
                                    st.session_state['editing_mode'] = False
                                    st.session_state['editing_file'] = None
                                    st.rerun()
                    
                    # Handle file renaming mode
                    elif st.session_state.get('rename_mode', False) and st.session_state.get('renaming_file') == file_path:
                        st.subheader("📝 Rename File")
                        current_name = os.path.basename(file_path)
                        new_name = st.text_input(
                            "New file name:",
                            value=current_name,
                            key=f"rename_input_{os.path.basename(file_path)}"
                        )
                        
                        if new_name and new_name != current_name:
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 Rename", key=f"save_rename_{os.path.basename(file_path)}"):
                                    try:
                                        new_path = os.path.join(os.path.dirname(file_path), new_name)
                                        os.rename(file_path, new_path)
                                        st.success(f"File renamed to: {new_name}")
                                        SessionManager.add_to_history("File Rename", "Success", f"Renamed {current_name} to {new_name}")
                                        st.session_state['rename_mode'] = False
                                        st.session_state['renaming_file'] = None
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to rename file: {str(e)}")
                            
                            with col_cancel:
                                if st.button("❌ Cancel", key=f"cancel_rename_{os.path.basename(file_path)}"):
                                    st.session_state['rename_mode'] = False
                                    st.session_state['renaming_file'] = None
                                    st.rerun()
                    
                    # Display file content (only when not editing/renaming)
                    if not st.session_state.get('editing_mode', False) and not st.session_state.get('rename_mode', False):
                        UIHelpers.display_file_content(file_path, selected_file)
            else:
                st.info(f"No files found in {selected_dir_name}")
        else:
            st.warning(f"Directory {directory} does not exist")
    
    with tabs[2]:
        st.subheader("Download Conversion Results")
        
        # Create download package
        if st.button("📦 Create Download Package"):
            zip_buffer = FileManager.create_download_package()
            
            if zip_buffer:
                st.download_button(
                    "⬇️ Download Conversion Results",
                    data=zip_buffer.getvalue(),
                    file_name=f"conversion_results_{time.strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
                st.success("Download package created successfully!")
            else:
                st.error("Failed to create download package")

def configuration_page():
    """Configuration management page."""
    st.title("⚙️ Configuration Management")
    
    tabs = st.tabs(["🗂️ Oracle-PostgreSQL Mappings", "⚙️ System Settings"])
    
    with tabs[0]:
        st.subheader("Oracle to PostgreSQL Mappings")
        
        # Load current mappings
        mappings = ConfigManager.load_excel_mappings()
        
        if mappings:
            st.success("✅ Mapping file found")
            
            # Display current mappings with enhanced functionality
            for sheet_name, df in mappings.items():
                display_title = sheet_name.replace('_', ' ').title()
                
                with st.expander(f"📋 {display_title}", expanded=False):
                    # Search bar at the top of each expandable section
                    search_key = f"search_{sheet_name}"
                    search_term = st.text_input(
                        f"🔍 Search in {display_title}:",
                        value=st.session_state.get(search_key, ""),
                        key=search_key,
                        placeholder=f"Type to search {display_title.lower()}..."
                    )
                    
                    # Apply search filter
                    if search_term:
                        filtered_df = ConfigManager.filter_dataframe(df, search_term)
                        if len(filtered_df) == 0:
                            st.info(f"No results found for '{search_term}' in {display_title}")
                            filtered_df = df  # Show all if no results
                        else:
                            st.info(f"Found {len(filtered_df)} of {len(df)} rows matching '{search_term}'")
                    else:
                        filtered_df = df
                    
                    # Display the dataframe
                    st.dataframe(filtered_df, width='stretch')
                    
                    # Row management buttons section
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
                    
                    with col1:
                        # Add Row button
                        if st.button("➕ Add Row", key=f"add_row_{sheet_name}"):
                            if ConfigManager.add_empty_row_to_sheet(sheet_name):
                                st.success("✅ Empty row added!")
                                SessionManager.add_to_history("Configuration", "Success", f"Added row to {sheet_name}")
                                st.rerun()
                            else:
                                st.error("❌ Failed to add row")
                    
                    with col2:
                        # Edit button (existing functionality)
                        if st.button("✏️ Edit", key=f"edit_{sheet_name}"):
                            st.session_state[f'editing_{sheet_name}'] = True
                            st.rerun()
                    
                    with col3:
                        # Delete Rows button
                        if st.button("🗑️ Delete Rows", key=f"delete_rows_{sheet_name}"):
                            st.session_state[f'deleting_rows_{sheet_name}'] = True
                            st.rerun()
                    
                    with col4:
                        # Show row count info
                        st.info(f"📊 Total rows: {len(df)}")
                    
                    # Edit mode
                    if st.session_state.get(f'editing_{sheet_name}', False):
                        st.markdown("---")
                        st.subheader(f"✏️ Editing {display_title}")
                        
                        # Use data_editor for editing
                        edited_df = st.data_editor(
                            df, 
                            width='stretch',
                            num_rows="dynamic",
                            key=f"editor_{sheet_name}"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 Save Changes", key=f"save_{sheet_name}"):
                                if ConfigManager.save_excel_sheet(sheet_name, edited_df):
                                    st.session_state[f'editing_{sheet_name}'] = False
                                    st.success(f"✅ Saved {display_title}")
                                    SessionManager.add_to_history("Configuration", "Success", f"Updated {sheet_name}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to save {display_title}")
                        
                        with col2:
                            if st.button("❌ Cancel", key=f"cancel_{sheet_name}"):
                                st.session_state[f'editing_{sheet_name}'] = False
                                st.rerun()
                    
                    # Delete rows mode
                    if st.session_state.get(f'deleting_rows_{sheet_name}', False):
                        st.markdown("---")
                        st.subheader(f"🗑️ Delete Rows from {display_title}")
                        st.warning("⚠️ Select rows to delete by entering row numbers (0-based index)")
                        
                        # Display dataframe with row indices for reference
                        df_with_index = df.copy()
                        df_with_index.index.name = "Row Index"
                        st.dataframe(df_with_index, width='stretch')
                        
                        # Input for row indices to delete
                        rows_to_delete = st.text_input(
                            "Enter row indices to delete (comma-separated, e.g., 0,2,5):",
                            key=f"delete_input_{sheet_name}",
                            placeholder="0,1,2"
                        )
                        
                        if rows_to_delete:
                            try:
                                indices = [int(x.strip()) for x in rows_to_delete.split(',') if x.strip()]
                                # Validate indices
                                valid_indices = [i for i in indices if 0 <= i < len(df)]
                                
                                if valid_indices:
                                    st.info(f"Will delete {len(valid_indices)} rows: {valid_indices}")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("🗑️ Confirm Delete", key=f"confirm_delete_{sheet_name}"):
                                            if ConfigManager.delete_selected_rows(sheet_name, valid_indices):
                                                st.session_state[f'deleting_rows_{sheet_name}'] = False
                                                st.success(f"✅ Deleted {len(valid_indices)} rows from {display_title}")
                                                SessionManager.add_to_history("Configuration", "Success", f"Deleted {len(valid_indices)} rows from {sheet_name}")
                                                st.rerun()
                                            else:
                                                st.error("❌ Failed to delete rows")
                                    
                                    with col2:
                                        if st.button("❌ Cancel Delete", key=f"cancel_delete_{sheet_name}"):
                                            st.session_state[f'deleting_rows_{sheet_name}'] = False
                                            st.rerun()
                                else:
                                    st.error("❌ No valid row indices provided")
                            
                            except ValueError:
                                st.error("❌ Invalid input. Please enter comma-separated numbers.")
            
            # Download current mappings
            st.markdown("---")
            if os.path.exists(ConfigManager.EXCEL_MAPPING_PATH):
                UIHelpers.create_download_button(
                    ConfigManager.EXCEL_MAPPING_PATH,
                    "⬇️ Download Current Mappings",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        else:
            st.warning("⚠️ Mapping file not found")
            st.info("Please upload an Oracle-PostgreSQL mapping file.")
        
        # Upload new mappings
        st.subheader("Upload New Mappings")
        uploaded_excel = st.file_uploader(
            "Upload Excel mapping file",
            type=['xlsx'],
            help="Upload a new Oracle-PostgreSQL mapping file"
        )
        
        if uploaded_excel:
            # Save uploaded file
            with open(ConfigManager.EXCEL_MAPPING_PATH, "wb") as f:
                f.write(uploaded_excel.getbuffer())
            st.success("Mapping file uploaded successfully!")
            SessionManager.add_to_history("Configuration", "Success", "Uploaded new mapping file")
            st.rerun()
    
    with tabs[1]:
        st.subheader("System Settings")
        
        # Logging settings
        with st.expander("📝 Logging Configuration"):
            log_level = st.selectbox(
                "Log Level",
                ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                index=1
            )
            
            if st.button("Apply Logging Settings"):
                setup_logging(log_level=log_level)
                st.success("Logging settings applied!")
        
        # Directory settings
        with st.expander("📁 Directory Configuration"):
            st.write("Current directory structure:")
            
            for name, directory in FileManager.DIRECTORIES.items():
                exists = os.path.exists(directory)
                status = "✅" if exists else "❌"
                st.write(f"{status} {directory} ({name})")
            
            if st.button("Create Missing Directories"):
                FileManager.ensure_directories()
                st.success("All directories created!")
                st.rerun()



def workflow_page():
    """Conversion workflow page."""
    st.title("🔄 Conversion Workflow")
    
    # Function mapping for workflow steps
    workflow_functions = {
        "read_oracle_triggers_to_json": read_oracle_triggers_to_json,
        "read_json_to_oracle_triggers": read_json_to_oracle_triggers,
        "read_json_to_postsql_triggers": read_json_to_postsql_triggers
    }
    
    # Progress indicator
    progress_container = st.container()
    
    # Step controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Run Single Step"):
            run_single_step(workflow_functions)
    
    with col2:
        if st.button("⏩ Run All Steps"):
            run_all_steps(workflow_functions, progress_container)
    
    with col3:
        if st.button("🔄 Reset Workflow"):
            SessionManager.reset_workflow()
            st.rerun()
    
    # Step details
    st.subheader("Workflow Steps")
    
    UIHelpers.display_step_status(WorkflowManager.STEPS, st.session_state.current_step)
    
    # Individual step execution
    for i, step in enumerate(WorkflowManager.STEPS):
        if st.button(f"Run Step {i+1}: {step['name']}", key=f"individual_step_{i}"):
            run_individual_step(step, i, workflow_functions, progress_container)

def run_single_step(workflow_functions):
    """Run a single workflow step."""
    current_step = st.session_state.current_step
    
    if current_step < len(WorkflowManager.STEPS):
        step = WorkflowManager.STEPS[current_step]
        
        # Check prerequisites
        if not WorkflowManager.can_run_step(current_step):
            prerequisites = WorkflowManager.get_step_prerequisites(current_step)
            st.warning(f"Cannot run step. Prerequisites: {', '.join(prerequisites)}")
            return
        
        function_name = step['function_name']
        if function_name not in workflow_functions:
            st.error(f"Function {function_name} not found")
            return
            
        with st.spinner(f"Running: {step['name']}..."):
            try:
                workflow_functions[function_name]()
                SessionManager.advance_workflow_step()
                SessionManager.add_to_history(step['name'], "Success")
                st.success(f"Completed: {step['name']}")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error in {step['name']}: {str(e)}")
                SessionManager.add_to_history(step['name'], "Error", str(e))
    else:
        st.info("All steps completed!")

def run_all_steps(workflow_functions, progress_container):
    """Run all workflow steps sequentially."""
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, step in enumerate(WorkflowManager.STEPS):
            status_text.text(f"Running: {step['name']}...")
            progress_bar.progress(i / len(WorkflowManager.STEPS))
            
            function_name = step['function_name']
            if function_name not in workflow_functions:
                st.error(f"Function {function_name} not found")
                return
            
            try:
                workflow_functions[function_name]()
                SessionManager.add_to_history(step['name'], "Success")
                
            except Exception as e:
                st.error(f"Error in {step['name']}: {str(e)}")
                SessionManager.add_to_history(step['name'], "Error", str(e))
                return
        
        progress_bar.progress(1.0)
        status_text.text("All steps completed!")
        st.session_state.current_step = len(WorkflowManager.STEPS)
        
        st.balloons()

def run_individual_step(step, step_index, workflow_functions, progress_container):
    """Run a specific workflow step."""
    # Check prerequisites
    if not WorkflowManager.can_run_step(step_index):
        prerequisites = WorkflowManager.get_step_prerequisites(step_index)
        st.warning(f"Cannot run step. Prerequisites: {', '.join(prerequisites)}")
        return
    
    function_name = step['function_name']
    if function_name not in workflow_functions:
        st.error(f"Function {function_name} not found")
        return
    
    with progress_container:
        with st.spinner(f"Running: {step['name']}..."):
            try:
                workflow_functions[function_name]()
                st.session_state.current_step = max(st.session_state.current_step, step_index + 1)
                SessionManager.add_to_history(step['name'], "Success")
                st.success(f"Completed: {step['name']}")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error in {step['name']}: {str(e)}")
                SessionManager.add_to_history(step['name'], "Error", str(e))

def analytics_page():
    """Analytics and statistics page."""
    st.title("📊 Analytics & Statistics")
    
    # File statistics
    st.subheader("📈 File Statistics")
    
    stats = FileManager.get_file_stats()
    
    # Create charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart of file counts
        if any(stats.values()):
            fig_bar = px.bar(
                x=list(stats.keys()),
                y=list(stats.values()),
                title="Files by Directory",
                labels={'x': 'Directory', 'y': 'File Count'}
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, width='stretch')
        else:
            st.info("No files found in any directory")
    
    with col2:
        # Pie chart
        if any(stats.values()):
            non_zero_stats = {k: v for k, v in stats.items() if v > 0}
            if non_zero_stats:
                fig_pie = px.pie(
                    values=list(non_zero_stats.values()),
                    names=list(non_zero_stats.keys()),
                    title="File Distribution"
                )
                st.plotly_chart(fig_pie, width='stretch')
            else:
                st.info("No files to display in pie chart")
        else:
            st.info("No files found for pie chart")
    
    # Conversion history
    st.subheader("📋 Conversion History")
    
    if st.session_state.conversion_history:
        df_history = pd.DataFrame(st.session_state.conversion_history)
        
        # Summary metrics
        total_conversions = len(df_history)
        successful_conversions = len(df_history[df_history['status'] == 'Success'])
        failed_conversions = len(df_history[df_history['status'].str.contains('Error', na=False)])
        success_rate = (successful_conversions / total_conversions * 100) if total_conversions > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Operations", total_conversions)
        with col2:
            st.metric("Successful", successful_conversions)
        with col3:
            st.metric("Failed", failed_conversions)
        with col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Timeline chart
        if len(df_history) > 1:
            st.subheader("📈 Operation Timeline")
            df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
            fig_timeline = px.scatter(
                df_history, 
                x='timestamp', 
                y='step',
                color='status',
                title="Conversion Operations Timeline",
                color_discrete_map={'Success': 'green', 'Error': 'red'}
            )
            st.plotly_chart(fig_timeline, width='stretch')
        
        # History table
        st.dataframe(df_history, width='stretch')
        
        # Clear history
        if st.button("🗑️ Clear History"):
            SessionManager.clear_history()
            st.rerun()
    
    else:
        st.info("No conversion history available.")

def quick_check_page():
    """Quick Check page for verification and additional conversions."""
    st.title("✅ Quick Check - Verification & Conversions")
    
    st.markdown("""
    This page provides verification tools and additional conversion options that were moved from the main workflow.
    You can convert Oracle SQL files to JSON, generate formatted Oracle SQL, and compare results.
    """)
    
    tabs = st.tabs(["🔍 File Verification", "🔄 SQL Conversions", "📊 Comparison Tools"])
    
    with tabs[0]:
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
                            st.write(f"**File Statistics:**")
                            st.write(f"- Total lines: {len(lines)}")
                            st.write(f"- File size: {len(content)} characters")
            else:
                st.info("No Oracle SQL files found. Please upload files in the File Manager.")
        else:
            st.warning("Oracle directory not found. Please create directories in Configuration.")
    
    with tabs[1]:
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
    
    with tabs[2]:
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
                                    st.write(f"- Type: Dictionary")
                                    st.write(f"- Keys: {len(json_data.keys())}")
                                    st.write(f"- Main keys: {list(json_data.keys())[:5]}...")
                                elif isinstance(json_data, list):
                                    st.write(f"- Type: List")
                                    st.write(f"- Items: {len(json_data)}")
                            
                            with col2:
                                st.write("**File Information:**")
                                st.write(f"- File size: {len(content)} characters")
                                st.write(f"- JSON valid: ✅")
                            
                            # Show formatted JSON (first 1000 characters)
                            st.subheader("📄 JSON Preview")
                            json_str = json.dumps(json_data, indent=2)
                            # if len(json_str) > 1000:
                            #     json_str = json_str[:1000] + "..."
                            st.json(json_str)
                    
                    except json.JSONDecodeError as e:
                        st.error(f"❌ Invalid JSON format: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Error analyzing JSON: {str(e)}")

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

def main():
    """Main application function."""
    # Initialize directories
    FileManager.ensure_directories()
    
    # Display sidebar and get selected page
    current_page = display_sidebar()
    
    # Route to appropriate page
    if current_page == "dashboard":
        dashboard_page()
    elif current_page == "file_manager":
        file_manager_page()
    elif current_page == "configuration":
        configuration_page()
    elif current_page == "workflow":
        workflow_page()
    elif current_page == "quick_check":
        quick_check_page()
    elif current_page == "analytics":
        analytics_page()
    elif current_page == "rest_list":
        rest_list_page()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🔄 **Oracle to PostgreSQL Converter** | "
        "Built with Streamlit | "
        f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

if __name__ == "__main__":
    main()
