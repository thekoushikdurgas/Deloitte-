"""
File Manager Module for Oracle to PostgreSQL Converter

This module handles file upload, browsing, and management functionality.
"""

import streamlit as st
import os
import time
from utilities.streamlit_utils import FileManager, UIHelpers, SessionManager


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
