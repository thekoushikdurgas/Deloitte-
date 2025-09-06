"""
Configuration Module for Oracle to PostgreSQL Converter

This module handles configuration management including Oracle-PostgreSQL mappings
and system settings.
"""

import streamlit as st
import os
import time
from utilities.common import setup_logging
from utilities.streamlit_utils import ConfigManager, UIHelpers, FileManager, SessionManager

# Constants
CANCEL_BUTTON_TEXT = "❌ Cancel"


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
                            st.session_state[f'adding_row_{sheet_name}'] = True
                            st.rerun()
                    
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
                    
                    # Show input fields for adding new row
                    if st.session_state.get(f'adding_row_{sheet_name}', False):
                        st.markdown("---")
                        st.markdown("### ➕ Add New Row")
                        
                        # Get column structure for each sheet type
                        columns_config = {
                            'data_type_mappings': [
                                {'name': 'Oracle_Type', 'label': 'Oracle Data Type', 'help': 'Enter Oracle data type (e.g., VARCHAR2, NUMBER)'},
                                {'name': 'PostgreSQL_Type', 'label': 'PostgreSQL Data Type', 'help': 'Enter corresponding PostgreSQL type (e.g., VARCHAR, INTEGER)'}
                            ],
                            'function_mappings': [
                                {'name': 'Oracle_Function', 'label': 'Oracle Function', 'help': 'Enter Oracle function name (e.g., SYSDATE, NVL)'},
                                {'name': 'PostgreSQL_Function', 'label': 'PostgreSQL Function', 'help': 'Enter corresponding PostgreSQL function (e.g., NOW(), COALESCE)'}
                            ],
                            'function_list': [
                                {'name': 'function_name', 'label': 'Function Name', 'help': 'Enter function name to be tracked'}
                            ],
                            'exception_mappings': [
                                {'name': 'Oracle_Exception', 'label': 'Oracle Exception', 'help': 'Enter Oracle exception name (e.g., NO_DATA_FOUND, TOO_MANY_ROWS)'},
                                {'name': 'PostgreSQL_Message', 'label': 'PostgreSQL Message', 'help': 'Enter corresponding PostgreSQL exception handling (e.g., EXCEPTION WHEN NO_DATA_FOUND THEN)'}
                            ],
                            'schema_mappings': [
                                {'name': 'Oracle_Schema', 'label': 'Oracle Schema', 'help': 'Enter Oracle schema name (e.g., HR, SCOTT, SYS) - duplicates allowed'},
                                {'name': 'PostgreSQL_Schema', 'label': 'PostgreSQL Schema', 'help': 'Enter corresponding PostgreSQL schema name (e.g., public, hr_schema) - must be unique'}
                            ],
                            'statement_mappings': [
                                {'name': 'statement', 'label': 'Statement', 'help': 'Enter statement type (e.g., SELECT, INSERT, UPDATE, DELETE, RAISE)'},
                                {'name': 'statement_type', 'label': 'Statement Type', 'help': 'Enter corresponding statement type (e.g., select_statement, insert_statement, update_statement)'}
                            ]
                        }
                        
                        # Get the columns for current sheet
                        sheet_columns = columns_config.get(sheet_name, [])
                        new_row_data = {}
                        
                        # Create input fields for each column
                        for col in sheet_columns:
                            new_row_data[col['name']] = st.text_input(
                                col['label'],
                                key=f"new_row_{sheet_name}_{col['name']}",
                                help=col['help']
                            )
                        
                        # Action buttons
                        col_save, col_cancel = st.columns(2)
                        
                        with col_save:
                            if st.button("💾 Save New Row", key=f"save_new_row_{sheet_name}"):
                                # Validate that required fields are filled
                                if all(value.strip() for value in new_row_data.values()):
                                    # Add the new row to the dataframe and save
                                    success, message = ConfigManager.add_row_to_sheet_with_data(sheet_name, new_row_data)
                                    if success:
                                        st.success(f"✅ {message}")
                                        # Clear the adding state and input fields
                                        st.session_state[f'adding_row_{sheet_name}'] = False
                                        for col in sheet_columns:
                                            if f"new_row_{sheet_name}_{col['name']}" in st.session_state:
                                                del st.session_state[f"new_row_{sheet_name}_{col['name']}"]
                                        st.rerun()
                                    else:
                                        # Check if it's a duplicate error
                                        if "Duplicate entry" in message:
                                            st.error(f"❌ {message}")
                                        else:
                                            st.error(f"❌ {message}")
                                else:
                                    st.warning("⚠️ Please fill in all fields before saving.")
                        
                        with col_cancel:
                            if st.button(CANCEL_BUTTON_TEXT, key=f"cancel_new_row_{sheet_name}"):
                                st.session_state[f'adding_row_{sheet_name}'] = False
                                # Clear input fields
                                for col in sheet_columns:
                                    if f"new_row_{sheet_name}_{col['name']}" in st.session_state:
                                        del st.session_state[f"new_row_{sheet_name}_{col['name']}"]
                                st.rerun()
                    
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
                            if st.button(CANCEL_BUTTON_TEXT, key=f"cancel_{sheet_name}"):
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
        
        # Output folder and log management
        with st.expander("📋 Output Folder & Log Management", expanded=True):
            st.subheader("📋 Log Files Management")
            
            output_dir = FileManager.DIRECTORIES.get("output", "output")
            
            if os.path.exists(output_dir):
                # Get all log files
                log_files = [f for f in os.listdir(output_dir) if f.endswith('.log')]
                log_files.sort(reverse=True)  # Sort by newest first
                
                if log_files:
                    st.success(f"✅ Found {len(log_files)} log files in output directory")
                    
                    # Search bar for log files
                    search_term = st.text_input(
                        "🔍 Search in log files:",
                        value=st.session_state.get("log_search_term", ""),
                        key="log_search_term",
                        placeholder="Search by filename, date, or content..."
                    )
                    
                    # Filter log files based on search term
                    if search_term:
                        filtered_logs = [f for f in log_files if search_term.lower() in f.lower()]
                        if len(filtered_logs) == 0:
                            st.info(f"No log files found matching '{search_term}'")
                            filtered_logs = log_files  # Show all if no results
                        else:
                            st.info(f"Found {len(filtered_logs)} of {len(log_files)} log files matching '{search_term}'")
                    else:
                        filtered_logs = log_files
                    
                    # Log file management controls
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        if st.button("🗑️ Delete All Logs", key="delete_all_logs"):
                            st.session_state['confirm_delete_all_logs'] = True
                            st.rerun()
                    
                    with col2:
                        if st.button("📥 Download All Logs", key="download_all_logs"):
                            # Create a zip file with all logs
                            import zipfile
                            import io
                            
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                for log_file in log_files:
                                    log_path = os.path.join(output_dir, log_file)
                                    zip_file.write(log_path, log_file)
                            
                            zip_buffer.seek(0)
                            st.download_button(
                                label="⬇️ Download All Logs",
                                data=zip_buffer.getvalue(),
                                file_name=f"all_logs_{time.strftime('%Y%m%d_%H%M%S')}.zip",
                                mime="application/zip"
                            )
                    
                    with col3:
                        st.info(f"📊 Total log files: {len(log_files)}")
                    
                    # Confirmation dialog for deleting all logs
                    if st.session_state.get('confirm_delete_all_logs', False):
                        st.warning("⚠️ Are you sure you want to delete ALL log files? This action cannot be undone!")
                        col_yes, col_no = st.columns(2)
                        
                        with col_yes:
                            if st.button("✅ Yes, Delete All", key="confirm_delete_all_yes"):
                                deleted_count = 0
                                for log_file in log_files:
                                    try:
                                        os.remove(os.path.join(output_dir, log_file))
                                        deleted_count += 1
                                    except Exception as e:
                                        st.error(f"Failed to delete {log_file}: {str(e)}")
                                
                                if deleted_count > 0:
                                    st.success(f"✅ Deleted {deleted_count} log files")
                                    SessionManager.add_to_history("Log Management", "Success", f"Deleted {deleted_count} log files")
                                
                                st.session_state['confirm_delete_all_logs'] = False
                                st.rerun()
                        
                        with col_no:
                            if st.button(CANCEL_BUTTON_TEXT, key="cancel_delete_all"):
                                st.session_state['confirm_delete_all_logs'] = False
                                st.rerun()
                    
                    # Display log files with management options
                    st.markdown("---")
                    st.subheader("📄 Log Files")
                    
                    for i, log_file in enumerate(filtered_logs):
                        log_path = os.path.join(output_dir, log_file)
                        
                        # Get file stats
                        try:
                            file_size = os.path.getsize(log_path)
                            file_mtime = os.path.getmtime(log_path)
                            file_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_mtime))
                            file_size_mb = round(file_size / (1024 * 1024), 2)
                        except (OSError, IOError):
                            file_size_mb = 0
                            file_date = "Unknown"
                        
                        with st.expander(f"📄 {log_file} ({file_size_mb} MB, {file_date})", expanded=False):
                            # Log file actions
                            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                            
                            with col1:
                                if st.button("👁️ View", key=f"view_{log_file}"):
                                    st.session_state[f'viewing_log_{log_file}'] = True
                                    st.rerun()
                            
                            with col2:
                                if st.button("📥 Download", key=f"download_{log_file}"):
                                    with open(log_path, "rb") as f:
                                        st.download_button(
                                            label="⬇️ Download Log",
                                            data=f.read(),
                                            file_name=log_file,
                                            mime="text/plain",
                                            key=f"download_btn_{log_file}"
                                        )
                            
                            with col3:
                                if st.button("🗑️ Delete", key=f"delete_{log_file}"):
                                    st.session_state[f'confirm_delete_{log_file}'] = True
                                    st.rerun()
                            
                            with col4:
                                if st.button("🔍 Search Content", key=f"search_content_{log_file}"):
                                    st.session_state[f'searching_content_{log_file}'] = True
                                    st.rerun()
                            
                            # View log content
                            if st.session_state.get(f'viewing_log_{log_file}', False):
                                st.markdown("---")
                                st.subheader(f"📄 Content of {log_file}")
                                
                                try:
                                    with open(log_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    
                                    # Show first 1000 characters with option to show more
                                    if len(content) > 1000:
                                        st.text_area("Log Content (first 1000 characters):", content[:1000], height=200,)
                                        if st.button("Show Full Content", key=f"show_full_{log_file}"):
                                            st.text_area("Full Log Content:", content, height=400,)
                                    else:
                                        st.text_area("Log Content:", content, height=200,)
                                    
                                    if st.button("❌ Close View", key=f"close_view_{log_file}"):
                                        st.session_state[f'viewing_log_{log_file}'] = False
                                        st.rerun()
                                        
                                except Exception as e:
                                    st.error(f"Error reading log file: {str(e)}")
                            
                            # Search content in log
                            if st.session_state.get(f'searching_content_{log_file}', False):
                                st.markdown("---")
                                st.subheader(f"🔍 Search in {log_file}")
                                
                                search_content = st.text_input(
                                    "Enter search term:",
                                    key=f"content_search_{log_file}",
                                    placeholder="Search for specific text in the log..."
                                )
                                
                                if search_content:
                                    try:
                                        with open(log_path, 'r', encoding='utf-8') as f:
                                            lines = f.readlines()
                                        
                                        matching_lines = []
                                        for line_num, line in enumerate(lines, 1):
                                            if search_content.lower() in line.lower():
                                                matching_lines.append((line_num, line.strip()))
                                        
                                        if matching_lines:
                                            st.success(f"Found {len(matching_lines)} matching lines:")
                                            for line_num, line in matching_lines[:20]:  # Show first 20 matches
                                                st.code(f"Line {line_num}: {line}")
                                            
                                            if len(matching_lines) > 20:
                                                st.info(f"... and {len(matching_lines) - 20} more matches")
                                        else:
                                            st.info("No matching lines found")
                                            
                                    except Exception as e:
                                        st.error(f"Error searching in log file: {str(e)}")
                                
                                if st.button("❌ Close Search", key=f"close_search_{log_file}"):
                                    st.session_state[f'searching_content_{log_file}'] = False
                                    st.rerun()
                            
                            # Confirmation dialog for deleting individual log
                            if st.session_state.get(f'confirm_delete_{log_file}', False):
                                st.warning(f"⚠️ Are you sure you want to delete '{log_file}'?")
                                col_yes, col_no = st.columns(2)
                                
                                with col_yes:
                                    if st.button("✅ Yes, Delete", key=f"confirm_delete_yes_{log_file}"):
                                        try:
                                            os.remove(log_path)
                                            st.success(f"✅ Deleted {log_file}")
                                            SessionManager.add_to_history("Log Management", "Success", f"Deleted log file: {log_file}")
                                            st.session_state[f'confirm_delete_{log_file}'] = False
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Failed to delete {log_file}: {str(e)}")
                                
                                with col_no:
                                    if st.button(CANCEL_BUTTON_TEXT, key=f"cancel_delete_{log_file}"):
                                        st.session_state[f'confirm_delete_{log_file}'] = False
                                        st.rerun()
                
                else:
                    st.info("📭 No log files found in output directory")
                    
                    # Show option to create sample log or open output directory
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📁 Open Output Directory"):
                            st.info(f"Output directory: {os.path.abspath(output_dir)}")
                    
                    with col2:
                        if st.button("🔄 Refresh"):
                            st.rerun()
            
            else:
                st.warning("⚠️ Output directory does not exist")
                if st.button("Create Output Directory"):
                    FileManager.ensure_directories()
                    st.success("Output directory created!")
                    st.rerun()