#!/usr/bin/env python3
"""
Mapping Manager for Oracle to PostgreSQL Trigger Converter

This module handles all data type, function, and exception mappings between
Oracle and PostgreSQL. It supports loading mappings from Excel files or
using fallback hardcoded mappings.
"""

import os
import re
from typing import Dict, Optional
from .config import Config, HAS_EXCEL_SUPPORT

if HAS_EXCEL_SUPPORT:
    import pandas as pd


class MappingManager:
    """
    Handles all data type, function, and exception mappings
    
    This class is responsible for:
    - Loading mappings from Excel files or using fallback data
    - Managing Oracle to PostgreSQL type conversions
    - Providing function name translations
    - Handling exception message mappings
    """
    
    def __init__(self, excel_file: Optional[str] = None):
        """
        Initialize the mapping manager
        
        Args:
            excel_file: Optional path to Excel file containing mappings.
                       If None, uses default file from Config.
        """
        # Set the Excel file path, using default if none provided
        self.excel_file = excel_file or Config.DEFAULT_EXCEL_FILE
        
        # Initialize empty mapping dictionaries
        # These will be populated by _load_mappings()
        self.data_type_mappings: Dict[str, str] = {}      # Oracle types -> PostgreSQL types
        self.function_mappings: Dict[str, str] = {}       # Oracle functions -> PostgreSQL functions  
        self.exception_mappings: Dict[str, str] = {}      # Oracle exceptions -> PostgreSQL messages
        
        # Load the actual mapping data
        self._load_mappings()
    
    def _load_mappings(self) -> None:
        """
        Load mappings from Excel file or fallback to hardcoded mappings
        
        This method tries to load from Excel first, but gracefully falls back
        to hardcoded mappings if Excel support is unavailable or files are missing.
        """
        try:
            # Check if we have Excel support and the file exists
            if HAS_EXCEL_SUPPORT and os.path.exists(self.excel_file):
                self._load_from_excel()  # Load from Excel file
                print(f"✅ Loaded mappings from {self.excel_file}")
            else:
                # Fall back to hardcoded mappings
                self._load_fallback_mappings()
                print("📦 Using fallback mappings")
        except Exception as e:
            # If anything goes wrong, use fallback mappings
            print(f"⚠️  Error loading mappings: {e}")
            self._load_fallback_mappings()
    
    def _load_from_excel(self) -> None:
        """
        Load mappings from Excel file with three sheets
        
        Reads the Excel file and populates the three mapping dictionaries.
        Each sheet has a different structure but follows the same pattern:
        Oracle_Column -> PostgreSQL_Column mappings.
        """
        # Define the sheet names and their column structures
        sheets = {
            'data_type_mappings': ('Oracle_Type', 'PostgreSQL_Type'),           # VARCHAR2 -> VARCHAR etc.
            'function_mappings': ('Oracle_Function', 'PostgreSQL_Function'),     # SUBSTR -> SUBSTRING etc.
            'exception_mappings': ('Oracle_Exception', 'PostgreSQL_Message')     # no_data_found -> "No data found" etc.
        }
        
        # Process each sheet in the Excel file
        for sheet_name, (oracle_col, pg_col) in sheets.items():
            try:
                # Read the specific sheet from the Excel file
                df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
                
                # Get reference to the appropriate mapping dictionary
                mapping_dict = getattr(self, sheet_name)
                
                # Process each row in the sheet
                for _, row in df.iterrows():
                    # Extract Oracle and PostgreSQL items, converting to string and trimming whitespace
                    oracle_item = str(row[oracle_col]).strip()
                    pg_item = str(row[pg_col]).strip()
                    
                    # Skip rows with missing or invalid data
                    if oracle_item != 'nan' and pg_item != 'nan':
                        if sheet_name == 'exception_mappings':
                            # Exception mappings are stored as-is (no regex patterns needed)
                            mapping_dict[oracle_item] = pg_item
                        else:
                            # Data types and functions need regex patterns for matching
                            pattern = self._create_pattern(oracle_item)
                            mapping_dict[pattern] = pg_item
                            
            except Exception as e:
                # Log error but continue with other sheets
                print(f"⚠️  Error loading {sheet_name}: {e}")
    
    def _create_pattern(self, oracle_item: str) -> str:
        """
        Create regex pattern for Oracle item to enable flexible matching
        
        Args:
            oracle_item: The Oracle function or data type name
            
        Returns:
            A regex pattern string that will match the item with word boundaries
            
        Examples:
            'VARCHAR2' -> r'\\bVARCHAR2\\b'
            'TIMESTAMP WITH TIME ZONE' -> r'\\bTIMESTAMP\\s+WITH\\s+TIME\\s+ZONE\\b'
            'PACKAGE.FUNCTION' -> r'\\bPACKAGE\\.FUNCTION\\b'
        """
        if ' ' in oracle_item:
            # Multi-word items like "TIMESTAMP WITH TIME ZONE"
            # Replace spaces with flexible whitespace matching (\s+)
            return r'\b' + re.escape(oracle_item).replace(r'\ ', r'\s+') + r'\b'
        elif '.' in oracle_item:
            # Package.function or schema.table items - escape the dot
            return r'\b' + re.escape(oracle_item) + r'\b'
        else:
            # Simple single-word items
            return r'\b' + oracle_item + r'\b'
    
    def _load_fallback_mappings(self) -> None:
        """
        Load minimal hardcoded mappings as fallback when Excel is unavailable
        
        These are the essential mappings needed for basic Oracle to PostgreSQL conversion.
        This ensures the converter still works even without Excel file support.
        """
        # Core data type mappings - Oracle types to PostgreSQL equivalents
        self.data_type_mappings = {
            r'\bvarchar2\b': 'varchar',         # Oracle's variable character type
            r'\bnumber\b': 'numeric',           # Oracle's numeric type  
            r'\bdate\b': 'date',                # Date type is same in both
            r'\bclob\b': 'text',                # Character LOB becomes text
            r'\bblob\b': 'bytea',               # Binary LOB becomes byte array
            r'\bnvarchar2\b': 'varchar',        # National varchar becomes varchar
            r'\bfloat\b': 'real'                # Float becomes real
        }
        
        # Essential function mappings - Oracle functions to PostgreSQL equivalents  
        self.function_mappings = {
            r'\bsubstr\b': 'SUBSTRING',         # String substring function
            r'\bnvl\b': 'COALESCE',            # Null value function
            r'\bsysdate\b': 'CURRENT_TIMESTAMP', # Current date/time function
            r'\bto_date\b': 'TO_TIMESTAMP',     # String to date conversion
            r'\binstr\b': 'POSITION',           # String position function
            r'\blength\b': 'LENGTH'             # String length function
        }
        
        # Basic exception mappings - Oracle exceptions to meaningful messages
        self.exception_mappings = {
            'no_data_found': 'No data found',           # No rows returned from query
            'too_many_rows': 'Too many rows returned',  # More rows than expected
            'others': 'Unknown error occurred'          # Generic catch-all exception
        } 