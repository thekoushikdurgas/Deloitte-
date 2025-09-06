"""
Streamlit utility functions for the Oracle to PostgreSQL converter.

This module provides utility functions specifically designed for the Streamlit
web interface, including file operations, workflow management, and UI helpers.
"""

import os
import json
import pandas as pd
import time
import zipfile
import io
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st

from utilities.common import debug, info, warning, error


class FileManager:
    """Utility class for managing files in the conversion workflow."""
    
    DIRECTORIES = {
        "oracle": "files/oracle",
        "format_json": "files/format_json",
        "format_sql": "files/format_sql",
        "format_pl_json": "files/format_pl_json",
        "format_plsql": "files/format_plsql",
        "output": "output",
        "utilities": "utilities"
    }
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        for directory in cls.DIRECTORIES.values():
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_file_stats(cls) -> Dict[str, int]:
        """Get statistics about files in each directory."""
        stats = {}
        
        for name, path in cls.DIRECTORIES.items():
            if name == "utilities" or name == "output":
                continue  # Skip utility directories for stats
                
            if os.path.exists(path):
                files = [f for f in os.listdir(path) 
                        if os.path.isfile(os.path.join(path, f))]
                stats[name] = len(files)
            else:
                stats[name] = 0
        
        return stats
    
    @classmethod
    def get_files_in_directory(cls, directory: str) -> List[str]:
        """Get list of files in a directory."""
        if os.path.exists(directory):
            return [f for f in os.listdir(directory) 
                   if os.path.isfile(os.path.join(directory, f))]
        return []
    
    @classmethod
    def read_file_content(cls, file_path: str) -> Optional[str]:
        """Read and return file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            error(f"Error reading file {file_path}: {str(e)}")
            return None
    
    @classmethod
    def save_uploaded_file(cls, uploaded_file, target_directory: str) -> bool:
        """Save an uploaded file to the target directory."""
        try:
            cls.ensure_directories()
            file_path = os.path.join(target_directory, uploaded_file.name)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            debug(f"Saved uploaded file: {uploaded_file.name}")
            return True
            
        except Exception as e:
            error(f"Error saving uploaded file: {str(e)}")
            return False
    
    @classmethod
    def create_download_package(cls, include_directories: List[str] = None) -> io.BytesIO:
        """Create a ZIP package of specified directories."""
        if include_directories is None:
            include_directories = ["format_json", "format_sql", "format_pl_json", "format_plsql"]
        
        zip_buffer = io.BytesIO()
        
        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for dir_name in include_directories:
                    directory = cls.DIRECTORIES.get(dir_name)
                    
                    if directory and os.path.exists(directory):
                        for root, dirs, files in os.walk(directory):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, "files")
                                zip_file.write(file_path, arcname)
            
            zip_buffer.seek(0)
            return zip_buffer
            
        except Exception as e:
            error(f"Error creating download package: {str(e)}")
            return None


class WorkflowManager:
    """Utility class for managing the conversion workflow."""
    
    STEPS = [
        {
            "name": "Oracle SQL → JSON Analysis",
            "description": "Convert Oracle SQL files to structured JSON analysis",
            "input_dir": "oracle",
            "output_dir": "format_json",
            "function_name": "read_oracle_triggers_to_json"
        },
        {
            "name": "JSON → PL/JSON Format",
            "description": "Convert JSON analysis to PL/JSON format",
            "input_dir": "format_json",
            "output_dir": "format_pl_json", 
            "function_name": "read_json_to_oracle_triggers"
        },
        {
            "name": "PL/JSON → PostgreSQL Format",
            "description": "Convert PL/JSON to PostgreSQL trigger format (Final)",
            "input_dir": "format_pl_json",
            "output_dir": "format_plsql",
            "function_name": "read_json_to_postsql_triggers"
        }
    ]
    
    @classmethod
    def get_step_status(cls, step_index: int) -> str:
        """Get the status of a workflow step."""
        current_step = st.session_state.get('current_step', 0)
        
        if step_index < current_step:
            return "✅ Completed"
        elif step_index == current_step:
            return "⏳ Current"
        else:
            return "⏸️ Pending"
    
    @classmethod
    def can_run_step(cls, step_index: int) -> bool:
        """Check if a step can be run based on input availability."""
        if step_index >= len(cls.STEPS):
            return False
            
        step = cls.STEPS[step_index]
        input_directory = FileManager.DIRECTORIES.get(step["input_dir"])
        
        if not input_directory or not os.path.exists(input_directory):
            return False
        
        # Check if there are input files
        files = FileManager.get_files_in_directory(input_directory)
        return len(files) > 0
    
    @classmethod
    def get_step_prerequisites(cls, step_index: int) -> List[str]:
        """Get list of prerequisites for a step."""
        if step_index >= len(cls.STEPS):
            return []
        
        step = cls.STEPS[step_index]
        input_dir = step["input_dir"]
        
        prerequisites = []
        
        if input_dir == "oracle":
            prerequisites.append("Upload Oracle SQL files")
        elif input_dir == "format_json":
            prerequisites.append("Complete Step 1: Oracle SQL → JSON Analysis")
        elif input_dir == "format_pl_json":
            prerequisites.append("Complete Step 3: JSON → PL/JSON Format")
        elif input_dir == "format_plsql":
            prerequisites.append("Complete previous PostgreSQL conversion steps")
        
        return prerequisites


class ConfigManager:
    """Utility class for managing configuration files."""
    
    EXCEL_MAPPING_PATH = "utilities/oracle_postgresql_mappings.xlsx"
    REST_LIST_PATH = "utilities/rest_list.csv"
    
    @classmethod
    def load_excel_mappings(cls) -> Dict[str, pd.DataFrame]:
        """Load Oracle-PostgreSQL mappings from Excel file."""
        mappings = {}
        
        if not os.path.exists(cls.EXCEL_MAPPING_PATH):
            return mappings
        
        try:
            sheets = ['data_type_mappings', 'function_mappings', 'function_list', 'exception_mappings', 'schema_mappings', 'statement_mappings']
            
            for sheet_name in sheets:
                try:
                    df = pd.read_excel(cls.EXCEL_MAPPING_PATH, sheet_name=sheet_name)
                    mappings[sheet_name] = df
                except Exception as e:
                    warning(f"Could not load sheet {sheet_name}: {str(e)}")
            
        except Exception as e:
            error(f"Error loading Excel mappings: {str(e)}")
        
        return mappings
    
    @classmethod
    def save_excel_sheet(cls, sheet_name: str, dataframe: pd.DataFrame) -> bool:
        """Save a dataframe to a specific sheet in the Excel file."""
        try:
            # Read existing sheets
            sheet_dict = {}
            
            if os.path.exists(cls.EXCEL_MAPPING_PATH):
                with pd.ExcelFile(cls.EXCEL_MAPPING_PATH) as xls:
                    for name in xls.sheet_names:
                        if name != sheet_name:
                            sheet_dict[name] = pd.read_excel(xls, sheet_name=name)
            
            # Add the updated sheet
            sheet_dict[sheet_name] = dataframe
            
            # Write back to Excel
            with pd.ExcelWriter(cls.EXCEL_MAPPING_PATH, engine='openpyxl') as writer:
                for name, df in sheet_dict.items():
                    df.to_excel(writer, sheet_name=name, index=False)
            
            debug(f"Saved Excel sheet: {sheet_name}")
            return True
            
        except Exception as e:
            error(f"Error saving Excel sheet {sheet_name}: {str(e)}")
            return False
    
    @classmethod
    def add_empty_row_to_sheet(cls, sheet_name: str) -> bool:
        """Add an empty row to a specific sheet."""
        try:
            mappings = cls.load_excel_mappings()
            if sheet_name not in mappings:
                return False
            
            df = mappings[sheet_name]
            # Create empty row with same columns
            empty_row = pd.DataFrame([dict.fromkeys(df.columns, '')])
            updated_df = pd.concat([df, empty_row], ignore_index=True)
            
            return cls.save_excel_sheet(sheet_name, updated_df)
            
        except Exception as e:
            error(f"Error adding row to sheet {sheet_name}: {str(e)}")
            return False
    
    @classmethod
    def check_for_duplicates(cls, sheet_name: str, row_data: Dict[str, str]) -> Tuple[bool, str]:
        """
        Check if the provided row data already exists in the sheet.
        
        Args:
            sheet_name (str): Name of the sheet to check
            row_data (Dict[str, str]): Data to check for duplicates
            
        Returns:
            Tuple[bool, str]: (is_duplicate, duplicate_info)
                - is_duplicate: True if duplicate found, False otherwise
                - duplicate_info: Description of what was duplicated
        """
        try:
            mappings = cls.load_excel_mappings()
            if sheet_name not in mappings:
                return False, "Sheet not found"
            
            df = mappings[sheet_name]
            
            # Check for duplicates based on the sheet type
            if sheet_name == 'data_type_mappings':
                # For data type mappings, check Oracle_Type column
                oracle_type = row_data.get('Oracle_Type', '').strip()
                if oracle_type:
                    existing_oracle_types = df['Oracle_Type'].astype(str).str.strip()
                    if oracle_type in existing_oracle_types.values:
                        return True, f"Oracle data type '{oracle_type}' already exists"
            
            elif sheet_name == 'function_mappings':
                # For function mappings, check Oracle_Function column
                oracle_function = row_data.get('Oracle_Function', '').strip()
                if oracle_function:
                    existing_oracle_functions = df['Oracle_Function'].astype(str).str.strip()
                    if oracle_function in existing_oracle_functions.values:
                        return True, f"Oracle function '{oracle_function}' already exists"
            
            elif sheet_name == 'function_list':
                # For function list, check function_name column
                function_name = row_data.get('function_name', '').strip()
                if function_name:
                    existing_function_names = df['function_name'].astype(str).str.strip()
                    if function_name in existing_function_names.values:
                        return True, f"Function name '{function_name}' already exists"
            
            elif sheet_name == 'exception_mappings':
                # For exception mappings, check Oracle_Exception column
                oracle_exception = row_data.get('Oracle_Exception', '').strip()
                if oracle_exception:
                    existing_oracle_exceptions = df['Oracle_Exception'].astype(str).str.strip()
                    if oracle_exception in existing_oracle_exceptions.values:
                        return True, f"Oracle exception '{oracle_exception}' already exists"
            
            elif sheet_name == 'schema_mappings':
                # For schema mappings, check PostgreSQL_Schema column for uniqueness
                # Oracle_Schema can have duplicates, but PostgreSQL_Schema must be unique
                postgresql_schema = row_data.get('PostgreSQL_Schema', '').strip()
                if postgresql_schema:
                    existing_postgresql_schemas = df['PostgreSQL_Schema'].astype(str).str.strip()
                    if postgresql_schema in existing_postgresql_schemas.values:
                        return True, f"PostgreSQL schema '{postgresql_schema}' already exists (must be unique)"
            
            elif sheet_name == 'statement_mappings':
                # For statement mappings, check statement column for uniqueness
                statement = row_data.get('statement', '').strip()
                if statement:
                    existing_statements = df['statement'].astype(str).str.strip()
                    if statement in existing_statements.values:
                        return True, f"Statement '{statement}' already exists"
            
            return False, "No duplicates found"
            
        except Exception as e:
            error(f"Error checking for duplicates in sheet {sheet_name}: {str(e)}")
            return True, f"Error checking duplicates: {str(e)}"
    
    @classmethod
    def add_row_to_sheet_with_data(cls, sheet_name: str, row_data: Dict[str, str]) -> Tuple[bool, str]:
        """
        Add a row with specific data to a sheet.
        
        Args:
            sheet_name (str): Name of the sheet to add to
            row_data (Dict[str, str]): Data for the new row
            
        Returns:
            Tuple[bool, str]: (success, message)
                - success: True if row was added successfully, False otherwise
                - message: Success or error message
        """
        try:
            mappings = cls.load_excel_mappings()
            if sheet_name not in mappings:
                return False, f"Sheet '{sheet_name}' not found"
            
            df = mappings[sheet_name]
            
            # Validate that all required columns are present in row_data
            missing_columns = set(df.columns) - set(row_data.keys())
            if missing_columns:
                error_msg = f"Missing required columns for {sheet_name}: {missing_columns}"
                error(error_msg)
                return False, error_msg
            
            # Check for duplicates before adding
            is_duplicate, duplicate_info = cls.check_for_duplicates(sheet_name, row_data)
            if is_duplicate:
                return False, f"Duplicate entry: {duplicate_info}"
            
            # Create new row with provided data
            new_row = pd.DataFrame([row_data])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            if cls.save_excel_sheet(sheet_name, updated_df):
                return True, f"Successfully added new row to {sheet_name.replace('_', ' ').title()}"
            else:
                return False, "Failed to save the updated sheet"
            
        except Exception as e:
            error_msg = f"Error adding row with data to sheet {sheet_name}: {str(e)}"
            error(error_msg)
            return False, error_msg
    
    @classmethod
    def delete_selected_rows(cls, sheet_name: str, indices_to_delete: list) -> bool:
        """Delete selected rows from a specific sheet."""
        try:
            mappings = cls.load_excel_mappings()
            if sheet_name not in mappings:
                return False
            
            df = mappings[sheet_name]
            # Drop selected indices
            updated_df = df.drop(indices_to_delete).reset_index(drop=True)
            
            return cls.save_excel_sheet(sheet_name, updated_df)
            
        except Exception as e:
            error(f"Error deleting rows from sheet {sheet_name}: {str(e)}")
            return False
    
    @classmethod
    def filter_dataframe(cls, df: pd.DataFrame, search_term: str) -> pd.DataFrame:
        """Filter dataframe based on search term across all columns."""
        if not search_term:
            return df
        
        # Convert search term to lowercase for case-insensitive search
        search_term = search_term.lower()
        
        # Create a mask that checks if search term is in any column
        mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(search_term, na=False)).any(axis=1)
        
        return df[mask]
    
    @classmethod
    def load_rest_list(cls) -> Optional[pd.DataFrame]:
        """Load the rest list CSV file."""
        if not os.path.exists(cls.REST_LIST_PATH):
            return None
        
        try:
            df = pd.read_csv(cls.REST_LIST_PATH)
            return df
        except Exception as e:
            error(f"Error loading rest list: {str(e)}")
            return None
    
    @classmethod
    def save_rest_list(cls, dataframe: pd.DataFrame) -> bool:
        """Save the rest list CSV file."""
        try:
            dataframe.to_csv(cls.REST_LIST_PATH, index=False)
            debug("Saved rest list CSV")
            return True
        except Exception as e:
            error(f"Error saving rest list: {str(e)}")
            return False
    
    @classmethod
    def clear_rest_list(cls) -> bool:
        """Clear the rest list by creating an empty CSV."""
        empty_df = pd.DataFrame(columns=["filename", "line", "line_no", "indent"])
        return cls.save_rest_list(empty_df)


class UIHelpers:
    """Utility class for UI helper functions."""
    
    @staticmethod
    def display_file_content(file_path: str, file_name: str) -> None:
        """Display file content in Streamlit with appropriate formatting."""
        content = FileManager.read_file_content(file_path)
        
        if content is None:
            st.error(f"Could not read file: {file_name}")
            return
        
        # Display based on file type
        if file_name.endswith('.json'):
            try:
                json_data = json.loads(content)
                st.json(json_data)
            except json.JSONDecodeError:
                st.code(content, language="json")
        elif file_name.endswith('.sql'):
            st.code(content, language="sql")
        else:
            st.text(content)
    
    @staticmethod
    def create_download_button(file_path: str, label: str = "Download", 
                             mime_type: str = "text/plain") -> None:
        """Create a download button for a file."""
        try:
            with open(file_path, "rb") as f:
                st.download_button(
                    label=label,
                    data=f.read(),
                    file_name=os.path.basename(file_path),
                    mime=mime_type
                )
        except Exception as e:
            st.error(f"Error creating download button: {str(e)}")
    
    @staticmethod
    def display_metrics_grid(metrics: Dict[str, Any], columns: int = 4) -> None:
        """Display metrics in a grid layout."""
        cols = st.columns(columns)
        
        for i, (label, value) in enumerate(metrics.items()):
            with cols[i % columns]:
                if isinstance(value, (int, float)):
                    st.metric(label, value)
                else:
                    st.metric(label, str(value))
    
    @staticmethod
    def display_step_status(steps: List[Dict], current_step: int) -> None:
        """Display workflow step status."""
        for i, step in enumerate(steps):
            status_icon = "✅" if i < current_step else "⏳" if i == current_step else "⏸️"
            status_text = "Completed" if i < current_step else "Current" if i == current_step else "Pending"
            
            with st.expander(f"{status_icon} Step {i+1}: {step['name']}", 
                           expanded=(i == current_step)):
                st.write(f"**Status:** {status_text}")
                st.write(f"**Description:** {step.get('description', 'No description')}")
                
                if i == current_step:
                    prerequisites = WorkflowManager.get_step_prerequisites(i)
                    if prerequisites:
                        st.write("**Prerequisites:**")
                        for prereq in prerequisites:
                            st.write(f"- {prereq}")
    
    @staticmethod
    def create_edit_button(file_path: str, label: str = "✏️ Edit") -> None:
        """Create an edit button for a file."""
        try:
            if st.button(label, key=f"edit_{os.path.basename(file_path)}"):
                # Store file path in session state for editing
                st.session_state['editing_file'] = file_path
                st.session_state['editing_mode'] = True
                st.rerun()
        except Exception as e:
            st.error(f"Error creating edit button: {str(e)}")
    
    @staticmethod
    def create_delete_button(file_path: str, label: str = "🗑️ Delete") -> None:
        """Create a delete button for a file."""
        try:
            if st.button(label, key=f"delete_{os.path.basename(file_path)}"):
                # Confirm deletion
                if st.session_state.get('confirm_delete', False):
                    # Delete the file
                    try:
                        os.remove(file_path)
                        st.success(f"Deleted: {os.path.basename(file_path)}")
                        SessionManager.add_to_history("File Delete", "Success", f"Deleted {os.path.basename(file_path)}")
                        st.session_state['confirm_delete'] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete file: {str(e)}")
                else:
                    # Show confirmation
                    st.session_state['confirm_delete'] = True
                    st.warning(f"Click delete again to confirm deletion of {os.path.basename(file_path)}")
        except Exception as e:
            st.error(f"Error creating delete button: {str(e)}")
    
    @staticmethod
    def create_rename_button(file_path: str, label: str = "📝 Rename") -> None:
        """Create a rename button for a file."""
        try:
            if st.button(label, key=f"rename_{os.path.basename(file_path)}"):
                # Store file path in session state for renaming
                st.session_state['renaming_file'] = file_path
                st.session_state['rename_mode'] = True
                st.rerun()
        except Exception as e:
            st.error(f"Error creating rename button: {str(e)}")


class SessionManager:
    """Utility class for managing Streamlit session state."""
    
    @staticmethod
    def initialize_session_state() -> None:
        """Initialize session state variables."""
        if 'conversion_history' not in st.session_state:
            st.session_state.conversion_history = []
        
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 0
        
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
        
        # File operation states
        if 'editing_mode' not in st.session_state:
            st.session_state.editing_mode = False
        
        if 'editing_file' not in st.session_state:
            st.session_state.editing_file = None
        
        if 'rename_mode' not in st.session_state:
            st.session_state.rename_mode = False
        
        if 'renaming_file' not in st.session_state:
            st.session_state.renaming_file = None
        
        if 'confirm_delete' not in st.session_state:
            st.session_state.confirm_delete = False
        
        # Mapping search states
        if 'search_data_type_mappings' not in st.session_state:
            st.session_state.search_data_type_mappings = ""
        
        if 'search_function_mappings' not in st.session_state:
            st.session_state.search_function_mappings = ""
        
        if 'search_function_list' not in st.session_state:
            st.session_state.search_function_list = ""
        
        if 'search_exception_mappings' not in st.session_state:
            st.session_state.search_exception_mappings = ""
        
        if 'search_schema_mappings' not in st.session_state:
            st.session_state.search_schema_mappings = ""
        
        # Row selection states for deletion
        if 'selected_rows_data_type_mappings' not in st.session_state:
            st.session_state.selected_rows_data_type_mappings = []
        
        if 'selected_rows_function_mappings' not in st.session_state:
            st.session_state.selected_rows_function_mappings = []
        
        if 'selected_rows_function_list' not in st.session_state:
            st.session_state.selected_rows_function_list = []
        
        if 'selected_rows_exception_mappings' not in st.session_state:
            st.session_state.selected_rows_exception_mappings = []
        
        if 'selected_rows_schema_mappings' not in st.session_state:
            st.session_state.selected_rows_schema_mappings = []
        
        # Adding row states for each mapping type
        if 'adding_row_data_type_mappings' not in st.session_state:
            st.session_state.adding_row_data_type_mappings = False
        
        if 'adding_row_function_mappings' not in st.session_state:
            st.session_state.adding_row_function_mappings = False
        
        if 'adding_row_function_list' not in st.session_state:
            st.session_state.adding_row_function_list = False
        
        if 'adding_row_exception_mappings' not in st.session_state:
            st.session_state.adding_row_exception_mappings = False
        
        if 'adding_row_schema_mappings' not in st.session_state:
            st.session_state.adding_row_schema_mappings = False
    
    @staticmethod
    def add_to_history(step_name: str, status: str, details: str = "") -> None:
        """Add an entry to the conversion history."""
        history_entry = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'step': step_name,
            'status': status,
            'details': details
        }
        
        st.session_state.conversion_history.append(history_entry)
        
        # Keep only last 100 entries
        if len(st.session_state.conversion_history) > 100:
            st.session_state.conversion_history = st.session_state.conversion_history[-100:]
    
    @staticmethod
    def clear_history() -> None:
        """Clear the conversion history."""
        st.session_state.conversion_history = []
    
    @staticmethod
    def reset_workflow() -> None:
        """Reset the workflow to the beginning."""
        st.session_state.current_step = 0
    
    @staticmethod
    def advance_workflow_step() -> None:
        """Advance to the next workflow step."""
        max_steps = len(WorkflowManager.STEPS)
        if st.session_state.current_step < max_steps:
            st.session_state.current_step += 1
    
    @staticmethod
    def reset_file_operation_states() -> None:
        """Reset all file operation states."""
        st.session_state.editing_mode = False
        st.session_state.editing_file = None
        st.session_state.rename_mode = False
        st.session_state.renaming_file = None
        st.session_state.confirm_delete = False
