"""
Configuration Module for Oracle to PostgreSQL Converter

This module handles configuration management including Oracle-PostgreSQL mappings
and system settings.
"""

import streamlit as st
import os
from utilities.common import setup_logging
from utilities.streamlit_utils import ConfigManager, UIHelpers, FileManager, SessionManager


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
                            if st.button("❌ Cancel", key=f"cancel_new_row_{sheet_name}"):
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
