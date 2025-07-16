#!/usr/bin/env python3
"""
Oracle to PostgreSQL Trigger Converter
Optimized version with improved structure, performance, and maintainability

=== CODE FLOW OVERVIEW ===
1. Configuration & Setup
   - Load mappings from Excel or use fallback
   - Initialize core processing classes
   
2. File Processing Pipeline
   - Parse Oracle trigger sections (INSERT/UPDATE/DELETE)
   - Extract variable declarations
   - Apply regex transformations in single pass
   - Format as PostgreSQL DO blocks
   - Output as JSON structure

3. Class Architecture
   - MappingManager: Handles data type/function/exception mappings
   - RegexProcessor: Consolidates all regex transformations 
   - TriggerParser: Extracts trigger sections and variables
   - PostgreSQLFormatter: Formats output as DO blocks
   - OracleToPostgreSQLConverter: Main orchestrator

=== CONVERSION PROCESS ===
Oracle SQL → Clean → Parse Sections → Extract Variables → Transform → Format → JSON Output
"""

import re  # Regular expressions for pattern matching and text transformation
import json  # JSON handling for output format
import os  # Operating system interface for file operations
import sys  # System-specific parameters and functions
from typing import Dict, List, Tuple, Optional, Union, Callable  # Type hints for better code documentation
from pathlib import Path  # Object-oriented filesystem paths
from dataclasses import dataclass  # Decorator for creating data classes
from enum import Enum  # Support for enumerations
import argparse  # Command-line argument parsing

try:
    import pandas as pd
    from openpyxl import load_workbook, Workbook
    HAS_EXCEL_SUPPORT = True
except ImportError:
    HAS_EXCEL_SUPPORT = False
    print("⚠️  Excel support not available. Install pandas and openpyxl for full functionality.")

# ------------ Constants and Configuration ------------

class Config:
    """
    Central configuration for the converter
    
    Contains all default values and limits used throughout the application.
    Centralized configuration makes it easy to modify behavior without 
    hunting through code.
    """
    # Default folder names for input and output
    DEFAULT_ORACLE_FOLDER = 'orcale'      # Where Oracle SQL trigger files are stored
    DEFAULT_JSON_FOLDER = 'json'          # Where PostgreSQL JSON output files go
    DEFAULT_EXCEL_FILE = 'oracle_postgresql_mappings.xlsx'  # Mapping configuration file
    
    # Processing limits and batch sizes
    BATCH_SIZE = 100                      # Number of files to process in one batch
    MAX_FILE_SIZE = 10 * 1024 * 1024     # 10MB file size limit to prevent memory issues


class TriggerOperation(Enum):
    """
    Enum for trigger operations
    
    Defines the three types of database trigger operations that can be converted.
    Using an enum ensures type safety and prevents typos in operation names.
    """
    INSERT = "on_insert"    # Triggered when new records are inserted
    UPDATE = "on_update"    # Triggered when existing records are modified  
    DELETE = "on_delete"    # Triggered when records are removed


@dataclass
class ConversionResult:
    """
    Result of a conversion operation
    
    This data class provides a structured way to return conversion results,
    making it easy to handle both success and error cases consistently.
    
    Attributes:
        success: Whether the conversion completed successfully
        input_file: Path to the source Oracle SQL file
        output_file: Path to the generated PostgreSQL JSON file
        sections_converted: List of trigger sections that were converted
        error_message: Error details if conversion failed
        variables_count: Number of variables extracted from the trigger
    """
    success: bool                          # True if conversion succeeded, False otherwise
    input_file: str                        # Source file path that was processed
    output_file: str                       # Destination file path for output
    sections_converted: List[str]          # Which trigger sections were found and converted
    error_message: Optional[str] = None    # Error message if something went wrong
    variables_count: int = 0               # Count of variables extracted from DECLARE section


@dataclass
class RegexPattern:
    """
    Container for regex patterns with their replacements
    
    Attributes:
        pattern: The regex pattern to match in Oracle SQL
        replacement: Either a string replacement or a callable function for complex replacements
        flags: Regex flags (default: case insensitive)
        description: Human-readable description of what this pattern does
    """
    pattern: str  # The regex pattern to search for
    replacement: Union[str, Callable]  # Either string replacement or function for complex logic
    flags: int = re.IGNORECASE  # Regex flags - default to case insensitive matching
    description: str = ""  # Description of what this transformation does


# ------------ Core Classes ------------

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


class RegexProcessor:
    """
    Handles all regex-based transformations efficiently
    
    This class consolidates all regex transformations into a single, optimized processor.
    Instead of making multiple passes through the SQL text, it builds a comprehensive
    list of patterns and applies them efficiently.
    
    Key benefits:
    - Reduced processing time (single pass vs multiple passes)
    - Centralized pattern management
    - Consistent error handling
    - Easy to add new transformation patterns
    """
    
    def __init__(self, mapping_manager: MappingManager):
        """
        Initialize the regex processor with mapping data
        
        Args:
            mapping_manager: The MappingManager instance containing all 
                           Oracle->PostgreSQL mappings
        """
        # Store reference to mapping manager for accessing conversion data
        self.mapping_manager = mapping_manager
        
        # Build all transformation patterns once during initialization
        # This is more efficient than rebuilding patterns for each conversion
        self.transformation_patterns = self._build_transformation_patterns()
    
    def _build_transformation_patterns(self) -> List[RegexPattern]:
        """
        Build all transformation patterns in optimal order
        
        This method creates a comprehensive list of all regex transformations
        that need to be applied. The order matters - some transformations
        should happen before others to avoid conflicts.
        
        Returns:
            List of RegexPattern objects containing all transformations
        """
        patterns = []
        
        # PHASE 1: Data type conversions
        # Convert Oracle data types to PostgreSQL equivalents
        # Example: VARCHAR2(100) -> VARCHAR(100), NUMBER -> NUMERIC
        for oracle_type, pg_type in self.mapping_manager.data_type_mappings.items():
            patterns.append(RegexPattern(
                pattern=oracle_type,
                replacement=pg_type,
                description=f"Convert Oracle data type {oracle_type} to PostgreSQL {pg_type}"
            ))
        
        # PHASE 2: Function conversions  
        # Convert Oracle built-in functions to PostgreSQL equivalents
        # Example: SUBSTR -> SUBSTRING, NVL -> COALESCE
        for oracle_func, pg_func in self.mapping_manager.function_mappings.items():
            patterns.append(RegexPattern(
                pattern=oracle_func,
                replacement=pg_func,
                description=f"Convert Oracle function {oracle_func} to PostgreSQL {pg_func}"
            ))
        
        # PHASE 3: Specific Oracle syntax transformations
        # These are specialized transformations for Oracle-specific constructs
        patterns.extend([
            # Variable references in triggers
            # Oracle uses :new.field_name and :old.field_name syntax
            # PostgreSQL needs :new_field_name and :old_field_name
            RegexPattern(
                pattern=r':new\.(\w+)',
                replacement=r':new_\1',
                description="Convert Oracle trigger :new.field to PostgreSQL :new_field format"
            ),
            RegexPattern(
                pattern=r':old\.(\w+)',
                replacement=r':old_\1', 
                description="Convert Oracle trigger :old.field to PostgreSQL :old_field format"
            ),
            
            # Package function calls
            # Oracle: package.function() -> PostgreSQL: schema$function()
            # But preserve table references like gmd.themes
            RegexPattern(
                pattern=r'(\w+)\.(\w+)\s*\(',
                replacement=lambda m: f'{m.group(1)}${m.group(2)}(' 
                    if m.group(1).lower() not in ['gmd', 'mdm', 'mdmappl', 'predmd']
                    else m.group(0),
                description="Convert Oracle package.function calls to PostgreSQL schema$function format (preserve table references)"
            ),
            
            # Null handling functions
            # Oracle NVL function -> PostgreSQL COALESCE function
            RegexPattern(
                pattern=r'\bNVL\s*\(\s*([^,]+),\s*([^)]+)\)',
                replacement=r'COALESCE(\1, \2)',
                description="Convert Oracle NVL(value, default) to PostgreSQL COALESCE(value, default)"
            ),
            
            # String function syntax differences
            # SUBSTRING with positional parameters -> SUBSTRING with FROM...FOR
            RegexPattern(
                pattern=r'SUBSTRING\s*\(\s*([^,]+),\s*(\d+),\s*([^)]+)\s*\)',
                replacement=r'SUBSTRING(\1 FROM \2 FOR \3)',
                description="Convert SUBSTRING(string, start, length) to SUBSTRING(string FROM start FOR length)"
            ),
            
            # Exception handling
            # Oracle raise_application_error -> PostgreSQL RAISE EXCEPTION
            RegexPattern(
                pattern=r'raise_application_error\s*\(\s*-?\d+\s*,\s*[\'"]([^\'"]*)[\'"][^)]*\)',
                replacement=r"RAISE EXCEPTION 'MDM_V_THEMES_IOF: \1'",
                description="Convert Oracle raise_application_error to PostgreSQL RAISE EXCEPTION"
            )
        ])
        
        return patterns
    
    def apply_transformations(self, sql: str) -> str:
        """
        Apply all transformations efficiently in a single pass where possible
        
        This method applies all the regex transformations built during initialization.
        It handles both string replacements and callable functions for complex logic.
        
        Args:
            sql: The Oracle SQL code to transform
            
        Returns:
            The transformed PostgreSQL-compatible SQL code
        """
        # STEP 1: Clean the SQL first (remove comments, normalize whitespace)
        sql = self._clean_sql(sql)
        
        # STEP 2: Apply all transformation patterns in sequence
        for pattern in self.transformation_patterns:
            try:
                if callable(pattern.replacement):
                    # Complex replacement using a function (e.g., conditional logic)
                    sql = re.sub(pattern.pattern, pattern.replacement, sql, flags=pattern.flags)
                else:
                    # Simple string replacement
                    sql = re.sub(pattern.pattern, pattern.replacement, sql, flags=pattern.flags)
            except Exception as e:
                # Log warning but continue with other patterns - don't fail the entire conversion
                print(f"⚠️  Warning: Error applying pattern '{pattern.description}': {e}")
        
        return sql
    
    def _clean_sql(self, content: str) -> str:
        """
        Clean SQL content efficiently by removing comments and normalizing whitespace
        
        This preprocessing step makes the subsequent regex transformations more reliable
        by removing distracting elements and standardizing the format.
        
        Args:
            content: Raw SQL content from Oracle trigger file
            
        Returns:
            Cleaned SQL content ready for transformation
        """
        # Define all cleaning transformations to apply
        # These are applied in sequence for maximum effectiveness
        transformations = [
            (r'--.*$', ''),         # Remove single line comments (-- comment)
            (r'/\*.*?\*/', ''),     # Remove multi-line comments (/* comment */)
            (r'[ \t]+', ' '),       # Replace multiple spaces/tabs with single space
            (r'\n\s*\n', '\n')      # Remove empty lines (multiple newlines -> single newline)
        ]
        
        # Apply each cleaning transformation
        for pattern, replacement in transformations:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
        
        # Return cleaned content with leading/trailing whitespace removed
        return content.strip()


class TriggerParser:
    """
    Handles parsing of Oracle trigger sections
    
    Oracle triggers often contain conditional logic that executes different code
    based on the operation type (INSERT, UPDATE, DELETE). This class extracts
    these sections so they can be converted to separate PostgreSQL functions.
    
    Parsing Strategy:
    1. Identify section start patterns (IF INSERTING, IF UPDATING, etc.)
    2. Track nesting levels to find the correct end of each section
    3. Extract the SQL code for each operation type
    4. Handle complex cases like shared INSERT/UPDATE blocks
    """
    
    def __init__(self):
        """
        Initialize the trigger parser with section identification patterns
        
                 These regex patterns identify the start of each trigger section.
         The negative lookahead (?!\\s+OR) prevents matching shared sections
         like "IF INSERTING OR UPDATING".
        """
        # Define patterns that identify the start of each trigger operation section
        self.section_patterns = {
            # DELETE operation patterns
            TriggerOperation.DELETE: [
                r'IF\s+DELETING',                    # IF DELETING THEN
                r'IF\s*\(\s*DELETING\s*\)',         # IF (DELETING) THEN
                r'ELSIF\s+DELETING',                 # ELSIF DELETING THEN
                r'ELSIF\s*\(\s*DELETING\s*\)'       # ELSIF (DELETING) THEN
            ],
            # INSERT operation patterns (exclude shared INSERT OR UPDATE)
            TriggerOperation.INSERT: [
                r'IF\s+INSERTING(?!\s+OR)',          # IF INSERTING (but not IF INSERTING OR)
                r'IF\s*\(\s*INSERTING\s*\)(?!\s+OR)', # IF (INSERTING) (but not with OR)
                r'ELSIF\s+INSERTING(?!\s+OR)',       # ELSIF INSERTING (but not with OR)
                r'ELSIF\s*\(\s*INSERTING\s*\)(?!\s+OR)' # ELSIF (INSERTING) (but not with OR)
            ],
            # UPDATE operation patterns (exclude shared INSERT OR UPDATE)
            TriggerOperation.UPDATE: [
                r'IF\s+UPDATING(?!\s+OR)',           # IF UPDATING (but not IF UPDATING OR)
                r'IF\s*\(\s*UPDATING\s*\)(?!\s+OR)', # IF (UPDATING) (but not with OR)
                r'ELSIF\s+UPDATING(?!\s+OR)',        # ELSIF UPDATING (but not with OR)
                r'ELSIF\s*\(\s*UPDATING\s*\)(?!\s+OR)' # ELSIF (UPDATING) (but not with OR)
            ]
        }
    
    def extract_sections(self, sql_content: str) -> Dict[str, str]:
        """
        Extract INSERT, UPDATE, DELETE sections efficiently from Oracle trigger
        
        This method parses Oracle trigger code to identify and extract the SQL
        code that should execute for each operation type. It handles nested
        IF statements and complex trigger logic.
        
        Args:
            sql_content: The complete Oracle trigger code
            
        Returns:
            Dictionary with keys 'on_insert', 'on_update', 'on_delete' and
            their corresponding SQL code as values
        """
        # Initialize result dictionary with empty strings for each operation
        sections = {op.value: '' for op in TriggerOperation}
        
        # STEP 1: Normalize content for parsing
        # Replace multiple whitespace with single space for consistent parsing
        content = re.sub(r'\s+', ' ', sql_content)
        lines = content.split('\n')
        
        # Parsing state variables
        current_section = None      # Which section we're currently parsing
        current_content = []        # Lines of code for current section
        nesting_level = 0          # Track nested IF statements
        
        # STEP 2: Process each line to identify sections
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue
            
            line_upper = line.upper()
            
            # STEP 3: Check if this line starts a new section
            for operation, patterns in self.section_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line_upper):
                        # Found start of new section
                        if current_section and current_content:
                            # Save previous section before starting new one
                            sections[current_section.value] = '\n'.join(current_content)
                        
                        # Initialize new section
                        current_section = operation
                        current_content = []
                        nesting_level = 1  # We're inside one IF block
                        break
                if current_section == operation:
                    break  # Found the section, no need to check other patterns
            
            # STEP 4: If we're inside a section, collect its content
            if current_section:
                # Track nesting level to know when section ends
                if line_upper.startswith('IF '):
                    nesting_level += 1      # Entering nested IF
                elif line_upper.startswith('END IF') or line.endswith('END;'):
                    nesting_level -= 1      # Exiting IF block
                    
                    if nesting_level <= 0:
                        # End of current section
                        sections[current_section.value] = '\n'.join(current_content)
                        current_section = None
                        current_content = []
                        continue  # Don't add the END statement to content
                
                # Add this line to current section's content
                current_content.append(line)
        
        # STEP 5: Handle any remaining content (section that didn't close properly)
        if current_section and current_content:
            sections[current_section.value] = '\n'.join(current_content)
        
        return sections
    
    def extract_variables(self, sql_content: str) -> str:
        """
        Extract variable declarations efficiently from Oracle DECLARE section
        
        Oracle triggers typically have a DECLARE section with variable declarations
        that need to be converted to PostgreSQL syntax and included in DO blocks.
        
        Args:
            sql_content: Complete Oracle trigger code
            
        Returns:
            String containing PostgreSQL-compatible variable declarations
            ready for use in DO block DECLARE section
        """
        # STEP 1: Find the DECLARE section in Oracle trigger
        # Pattern matches: DECLARE ... BEGIN (capturing everything between)
        declare_match = re.search(r'declare\s+(.*?)\s+begin', sql_content, re.IGNORECASE | re.DOTALL)
        if not declare_match:
            return ''  # No DECLARE section found
        
        # Extract the content between DECLARE and BEGIN
        var_section = declare_match.group(1)
        variables = []
        
        # STEP 2: Split variable declarations on semicolons
        # Look for semicolons followed by whitespace and a word character (start of next declaration)
        var_declarations = re.split(r';(?=\s*\w)', var_section)
        
        # STEP 3: Process each variable declaration
        for var_decl in var_declarations:
            var_decl = var_decl.strip()
            
            # Skip empty declarations and exception declarations
            if not var_decl or 'exception' in var_decl.lower():
                continue
            
            # STEP 4: Convert Oracle variable types to PostgreSQL
            pg_var = self._convert_variable_type(var_decl)
            if pg_var:
                # Ensure each variable declaration ends with semicolon
                variables.append(pg_var + ';')
        
        # STEP 5: Join all variables into single string for DO block
        return ' '.join(variables)
    
    def _convert_variable_type(self, var_decl: str) -> str:
        """
        Convert Oracle variable types to PostgreSQL equivalents
        
        Oracle has different data type names and syntax compared to PostgreSQL.
        This method handles the conversion of common Oracle types.
        
        Args:
            var_decl: Single Oracle variable declaration
            
        Returns:
            PostgreSQL-compatible variable declaration
            
        Examples:
            'v_count PLS_INTEGER := 0' -> 'v_count INTEGER := 0'
            'v_name VARCHAR2(100)' -> 'v_name VARCHAR(100)'
            'v_amount NUMBER(10,2)' -> 'v_amount NUMERIC(10,2)'
        """
        # Define Oracle to PostgreSQL type conversions
        type_conversions = {
            r'PLS_INTEGER': 'INTEGER',              # Oracle PL/SQL integer type
            r'SIMPLE_INTEGER': 'INTEGER',           # Oracle simple integer type
            r'BINARY_INTEGER': 'INTEGER',           # Oracle binary integer type
            r'VARCHAR2\((\d+)\)': r'VARCHAR(\1)',   # Oracle variable character with length
            r'NUMBER\((\d+),(\d+)\)': r'NUMERIC(\1,\2)', # Oracle number with precision,scale
            r'NUMBER': 'NUMERIC'                    # Oracle number without precision
        }
        
        # Apply each type conversion
        for oracle_pattern, pg_type in type_conversions.items():
            var_decl = re.sub(oracle_pattern, pg_type, var_decl, flags=re.IGNORECASE)
        
        # Fix Oracle assignment operator syntax
        # Oracle uses := for assignment, PostgreSQL also uses := but needs proper spacing
        var_decl = re.sub(r'\s*:\s*=\s*', ' := ', var_decl)
        
        return var_decl.strip()


class PostgreSQLFormatter:
    """
    Handles PostgreSQL-specific formatting and DO block creation
    
    This class is responsible for the final formatting stage of the conversion process.
    It takes the transformed SQL code and formats it into proper PostgreSQL DO blocks
    that can be executed directly in PostgreSQL.
    
    Key Responsibilities:
    1. Clean up and format converted SQL for readability
    2. Wrap SQL in PostgreSQL DO blocks with proper syntax
    3. Include variable declarations in the DECLARE section
    4. Ensure the result is valid, executable PostgreSQL code
    """
    
    def format_sql(self, sql: str) -> str:
        """
        Format SQL for better readability and fix common syntax issues
        
        This method cleans up the converted SQL to make it more readable
        and fixes common formatting problems that can occur during conversion.
        
        Args:
            sql: The converted SQL code that needs formatting
            
        Returns:
            Formatted SQL with improved readability and fixed syntax issues
        """
        # STEP 1: Remove literal newline characters and normalize whitespace
        # Sometimes conversion introduces literal \\n characters that need to be removed
        sql = re.sub(r'\\n', ' ', sql)
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        # STEP 2: Fix common formatting issues that occur during conversion
        fixes = [
            # Remove redundant THEN keywords before other statements
            (r'\bTHEN\s+(CASE|SELECT|UPDATE|INSERT|DELETE|IF)\b', r'\1'),
            # Ensure proper spacing in compound keywords
            (r'\bEND\s+IF\b', 'END IF'),
            (r'\bEND\s+CASE\b', 'END CASE'),
            # Add line breaks after semicolons for major statements
            (r';\s*(IF|SELECT|UPDATE|INSERT|CALL)', r';\n\1')
        ]
        
        # Apply each formatting fix
        for pattern, replacement in fixes:
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        
        return sql
    
    def wrap_in_do_block(self, sql: str, variables: str) -> str:
        """
        Wrap SQL in PostgreSQL DO block with proper variable declarations
        
        PostgreSQL uses DO blocks for executing procedural code. This method
        creates a complete, executable DO block with DECLARE section for variables.
        
        Args:
            sql: The formatted SQL code to wrap
            variables: Variable declarations for the DECLARE section
            
        Returns:
            Complete PostgreSQL DO block ready for execution
            
        Format:
            DO $$ 
            DECLARE 
                variable declarations...
            BEGIN 
                sql code...
            END $$;
        """
        # STEP 1: Clean up Oracle-specific keywords from SQL content
        # Remove Oracle's DECLARE/BEGIN/END structure since we're creating our own
        sql = re.sub(r'^(declare|begin)\s+', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'end;\s*$', '', sql, flags=re.IGNORECASE)
        sql = sql.strip()
        
        # STEP 2: Format variables for DECLARE section
        if variables:
            # Clean up any double semicolons and ensure proper spacing
            variables = re.sub(r';\s*;', ';', variables).strip()
            if not variables.endswith(' '):
                variables += ' '  # Add space before BEGIN keyword
            
            # Create DO block with DECLARE section
            return f"DO $$ DECLARE {variables}BEGIN {sql} END $$;"
        else:
            # Create DO block without DECLARE section (no variables)
            return f"DO $$ BEGIN {sql} END $$;"


class OracleToPostgreSQLConverter:
    """
    Main converter class - now optimized and focused
    
    This is the primary orchestrator that coordinates all conversion activities:
    - Manages the conversion pipeline from Oracle to PostgreSQL
    - Coordinates mapping management, regex processing, parsing, and formatting
    - Provides both single file and batch folder processing capabilities
    - Returns structured results with detailed success/error information
    """
    
    def __init__(self, excel_file: Optional[str] = None):
        """
        Initialize the main converter with all necessary components
        
        This constructor sets up the complete conversion pipeline by initializing
        all the specialized classes that handle different aspects of the conversion.
        
        Args:
            excel_file: Optional path to Excel file containing custom mappings.
                       If None, uses the default Excel file or fallback mappings.
        """
        # STEP 1: Initialize mapping manager (loads Oracle->PostgreSQL mappings)
        self.mapping_manager = MappingManager(excel_file)
        
        # STEP 2: Initialize regex processor (handles all transformations)
        self.regex_processor = RegexProcessor(self.mapping_manager)
        
        # STEP 3: Initialize trigger parser (extracts sections and variables)
        self.trigger_parser = TriggerParser()
        
        # STEP 4: Initialize formatter (creates final PostgreSQL DO blocks)
        self.formatter = PostgreSQLFormatter()
    
    def convert_file(self, input_file: str, output_file: str, verbose: bool = False) -> ConversionResult:
        """
        Convert a single Oracle trigger file to PostgreSQL JSON format
        
        This is the main conversion method that orchestrates the entire process:
        1. Validates input file
        2. Parses Oracle trigger sections and variables  
        3. Applies all transformations
        4. Formats as PostgreSQL DO blocks
        5. Outputs structured JSON
        
        Args:
            input_file: Path to Oracle SQL trigger file
            output_file: Path where PostgreSQL JSON should be written
            verbose: Whether to print detailed progress information
            
        Returns:
            ConversionResult with success status and details
        """
        try:
            # =============================================================================
            # PHASE 1: INPUT VALIDATION AND READING
            # =============================================================================
            
            # Validate that input file exists
            if not os.path.exists(input_file):
                return ConversionResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    sections_converted=[],
                    error_message=f"Input file not found: {input_file}"
                )
            
            # Check file size to prevent memory issues with very large files
            if os.path.getsize(input_file) > Config.MAX_FILE_SIZE:
                return ConversionResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    sections_converted=[],
                    error_message=f"File too large: {input_file} (max: {Config.MAX_FILE_SIZE} bytes)"
                )
            
            # Read the Oracle trigger file content
            with open(input_file, 'r', encoding='utf-8') as f:
                oracle_content = f.read()
            
            # Ensure file has actual content
            if not oracle_content.strip():
                return ConversionResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    sections_converted=[],
                    error_message="Input file is empty"
                )
            
            # =============================================================================
            # PHASE 2: PARSING - EXTRACT VARIABLES AND SECTIONS
            # =============================================================================
            
            # Extract variable declarations from DECLARE section
            variables = self.trigger_parser.extract_variables(oracle_content)
            
            # Extract INSERT/UPDATE/DELETE sections from trigger logic
            sections = self.trigger_parser.extract_sections(oracle_content)
            
            if verbose:
                var_count = len(variables.split(';')) - 1 if variables else 0
                print(f"📊 Extracted {var_count} variables")
                print(f"📋 Found sections: {[k for k, v in sections.items() if v.strip()]}")
            
            # =============================================================================
            # PHASE 3: CONVERSION - TRANSFORM EACH SECTION
            # =============================================================================
            
            json_structure = {}      # Final JSON structure to output
            converted_sections = []  # Track which sections were successfully converted
            
            # Process each trigger section (INSERT, UPDATE, DELETE)
            for operation, sql_content in sections.items():
                if sql_content.strip():  # Only process non-empty sections
                    if verbose:
                        print(f"🔄 Converting {operation} section...")
                    
                    # STEP 1: Apply all regex transformations (data types, functions, syntax)
                    converted_sql = self.regex_processor.apply_transformations(sql_content)
                    
                    # STEP 2: Format the SQL for better readability
                    formatted_sql = self.formatter.format_sql(converted_sql)
                    
                    # STEP 3: Wrap in PostgreSQL DO block with variables
                    final_sql = self.formatter.wrap_in_do_block(formatted_sql, variables)
                    
                    # STEP 4: Add to JSON structure
                    json_structure[operation] = [{"type": "sql", "sql": final_sql}]
                    converted_sections.append(operation)
            
            # =============================================================================
            # PHASE 4: OUTPUT - WRITE JSON FILE
            # =============================================================================
            
            # Ensure output directory exists (create if necessary)
            output_dir = os.path.dirname(output_file)
            if output_dir:  # Only create if there's actually a directory path
                os.makedirs(output_dir, exist_ok=True)
            
            # Write the final JSON structure to output file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_structure, f, indent=4)
            
            # =============================================================================
            # PHASE 5: RETURN SUCCESS RESULT
            # =============================================================================
            
            return ConversionResult(
                success=True,
                input_file=input_file,
                output_file=output_file,
                sections_converted=converted_sections,
                variables_count=len(variables.split(';')) - 1 if variables else 0
            )
            
        except Exception as e:
            # =============================================================================
            # ERROR HANDLING - RETURN FAILURE RESULT
            # =============================================================================
            
            return ConversionResult(
                success=False,
                input_file=input_file,
                output_file=output_file,
                sections_converted=[],
                error_message=str(e)
            )
    
    def process_folder(self, oracle_folder: str, json_folder: str, verbose: bool = False) -> List[ConversionResult]:
        """
        Process all SQL files in a folder (batch conversion)
        
        This method handles batch processing of multiple Oracle trigger files.
        It's designed to be efficient and provide clear progress feedback.
        
        Args:
            oracle_folder: Directory containing Oracle SQL trigger files
            json_folder: Directory where PostgreSQL JSON files should be created
            verbose: Whether to show detailed progress for each file
            
        Returns:
            List of ConversionResult objects, one for each processed file
        """
        # =============================================================================
        # PHASE 1: SETUP AND VALIDATION
        # =============================================================================
        
        # Convert folder paths to Path objects for easier manipulation
        oracle_path = Path(oracle_folder)
        json_path = Path(json_folder)
        
        # Validate that source folder exists
        if not oracle_path.exists():
            print(f"❌ Oracle folder '{oracle_folder}' does not exist")
            return []  # Return empty list since no processing can be done
        
        # Create output folder if it doesn't exist
        json_path.mkdir(exist_ok=True)
        
        # =============================================================================
        # PHASE 2: DISCOVER FILES TO PROCESS
        # =============================================================================
        
        # Find all SQL files in the Oracle folder
        sql_files = list(oracle_path.glob('*.sql'))
        
        if not sql_files:
            print(f"⚠️  No .sql files found in '{oracle_folder}'")
            return []  # Nothing to process
        
        print(f"🔍 Found {len(sql_files)} SQL file(s) to convert")
        
        # =============================================================================
        # PHASE 3: PROCESS EACH FILE
        # =============================================================================
        
        results = []  # Collect results for all files
        
        for sql_file in sql_files:
            # Generate output filename (same name but .json extension)
            output_file = json_path / (sql_file.stem + '.json')
            
            if verbose:
                print(f"📄 Processing: {sql_file.name}")
            
            # Convert the individual file
            result = self.convert_file(str(sql_file), str(output_file), verbose)
            results.append(result)
            
            # Provide immediate feedback on each file
            if result.success:
                sections_info = f"({len(result.sections_converted)} sections)" if result.sections_converted else ""
                print(f"✅ {sql_file.name} → {output_file.name} {sections_info}")
            else:
                print(f"❌ {sql_file.name}: {result.error_message}")
        
        # =============================================================================
        # PHASE 4: PROVIDE SUMMARY
        # =============================================================================
        
        # Calculate success statistics
        success_count = sum(1 for r in results if r.success)
        total_sections = sum(len(r.sections_converted) for r in results if r.success)
        total_variables = sum(r.variables_count for r in results if r.success)
        
        print(f"\n🎉 Batch conversion complete!")
        print(f"   📊 Files: {success_count}/{len(results)} converted successfully")
        print(f"   📋 Sections: {total_sections} trigger sections converted")
        print(f"   📝 Variables: {total_variables} variables processed")
        
        return results


# =============================================================================
# INTERFACE FUNCTIONS - USER INTERACTION AND MENU SYSTEM  
# =============================================================================

def show_interactive_menu():
    """
    Display interactive menu and get user choice
    
    This function provides a user-friendly menu system for the converter.
    It handles input validation and provides clear options for different
    conversion scenarios.
    
    Returns:
        String representing the user's menu choice ('1', '2', '3', '4', or '5')
    """
    # Display the main menu header with clear branding
    print("\n" + "="*60)
    print("🚀 Oracle to PostgreSQL Trigger Converter (Optimized)")
    print("="*60)
    
    # Show all available options with clear descriptions
    print("\n1. 📁 Convert entire folder (default: orcale → json)")
    print("2. 📁 Convert folder with custom names")
    print("3. 📄 Convert single file")
    print("4. ❓ Show help")
    print("5. 🚪 Exit")
    
    # Input validation loop - keep asking until valid choice
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice  # Valid choice, return it
            print("❌ Invalid choice. Please enter 1-5.")
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n👋 Goodbye!")
            sys.exit(0)


def main():
    """
    Main entry point for the Oracle to PostgreSQL Trigger Converter
    
    This function determines whether to run in interactive mode (menu-driven)
    or command-line mode (with arguments) and handles the overall application flow.
    
    Modes:
    - Interactive Mode: No command line arguments - shows menu system
    - Command Line Mode: Arguments provided - direct execution
    """
    
    # =============================================================================
    # DETERMINE EXECUTION MODE
    # =============================================================================
    
    if len(sys.argv) == 1:
        # =============================================================================
        # INTERACTIVE MODE - MENU-DRIVEN INTERFACE
        # =============================================================================
        
        # Initialize the converter once for the interactive session
        converter = OracleToPostgreSQLConverter()
        
        # Main interactive loop - keep showing menu until user exits
        while True:
            choice = show_interactive_menu()
            
            # -------------------------------------------------------------------------
            # OPTION 1: Convert entire folder with default settings
            # -------------------------------------------------------------------------
            if choice == '1':
                try:
                    verbose = input("Verbose output? (y/n): ").strip().lower() == 'y'
                    print(f"\n🔄 Converting {Config.DEFAULT_ORACLE_FOLDER} → {Config.DEFAULT_JSON_FOLDER}")
                    converter.process_folder(Config.DEFAULT_ORACLE_FOLDER, Config.DEFAULT_JSON_FOLDER, verbose)
                except (EOFError, KeyboardInterrupt):
                    print("\n⚠️  Operation cancelled by user")
                    continue
                
            # -------------------------------------------------------------------------
            # OPTION 2: Convert folder with custom folder names
            # -------------------------------------------------------------------------
            elif choice == '2':
                try:
                    oracle_folder = input(f"Oracle folder ({Config.DEFAULT_ORACLE_FOLDER}): ").strip() or Config.DEFAULT_ORACLE_FOLDER
                    json_folder = input(f"JSON folder ({Config.DEFAULT_JSON_FOLDER}): ").strip() or Config.DEFAULT_JSON_FOLDER
                    verbose = input("Verbose output? (y/n): ").strip().lower() == 'y'
                    print(f"\n🔄 Converting {oracle_folder} → {json_folder}")
                    converter.process_folder(oracle_folder, json_folder, verbose)
                except (EOFError, KeyboardInterrupt):
                    print("\n⚠️  Operation cancelled by user")
                    continue
                
            # -------------------------------------------------------------------------
            # OPTION 3: Convert single file
            # -------------------------------------------------------------------------
            elif choice == '3':
                try:
                    input_file = input("Input Oracle SQL file: ").strip()
                    if not input_file:
                        print("❌ Input file path cannot be empty")
                        continue
                        
                    output_file = input("Output JSON file (optional): ").strip()
                    if not output_file:
                        # Generate output filename automatically
                        output_file = input_file.replace('.sql', '.json')
                        
                    verbose = input("Verbose output? (y/n): ").strip().lower() == 'y'
                    
                    print(f"\n🔄 Converting {input_file} → {output_file}")
                    result = converter.convert_file(input_file, output_file, verbose)
                    
                    if result.success:
                        sections_info = f" ({len(result.sections_converted)} sections)" if result.sections_converted else ""
                        print(f"✅ Successfully converted: {result.input_file} → {result.output_file}{sections_info}")
                    else:
                        print(f"❌ Conversion failed: {result.error_message}")
                        
                except (EOFError, KeyboardInterrupt):
                    print("\n⚠️  Operation cancelled by user")
                    continue
                    
            # -------------------------------------------------------------------------
            # OPTION 4: Show help information
            # -------------------------------------------------------------------------
            elif choice == '4':
                print("\n📖 Help - Oracle to PostgreSQL Trigger Converter")
                print("="*60)
                print("This optimized tool converts Oracle PL/SQL triggers to PostgreSQL format.")
                print("\n🔄 Conversion Features:")
                print("  • Data type mappings (VARCHAR2 → VARCHAR, NUMBER → NUMERIC, etc.)")
                print("  • Function mappings (SUBSTR → SUBSTRING, NVL → COALESCE, etc.)")
                print("  • Exception handling conversion")
                print("  • Variable reference conversion (:new.field → :new_field)")
                print("  • Package function calls (pkg.func → pkg$func)")
                print("  • Wraps output in PostgreSQL DO blocks")
                print("\n📁 Input/Output:")
                print("  • Input: Oracle PL/SQL trigger files (.sql)")
                print("  • Output: PostgreSQL triggers in JSON format (.json)")
                print("\n⚙️  Configuration:")
                print(f"  • Mappings loaded from {Config.DEFAULT_EXCEL_FILE}")
                print("  • Falls back to built-in mappings if Excel unavailable")
                
                try:
                    input("\nPress Enter to continue...")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue  # Return to menu
                
            # -------------------------------------------------------------------------
            # OPTION 5: Exit application
            # -------------------------------------------------------------------------
            elif choice == '5':
                print("\n👋 Goodbye!")
                break
            
            # Ask if user wants to perform another operation
            try:
                continue_choice = input("\nPerform another operation? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("\n👋 Goodbye!")
                    break
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Goodbye!")
                break
    
    else:
        # =============================================================================
        # COMMAND LINE MODE - DIRECT EXECUTION WITH ARGUMENTS
        # =============================================================================
        
        # Set up command line argument parser
        parser = argparse.ArgumentParser(
            description='Convert Oracle PL/SQL triggers to PostgreSQL format',
            epilog='Examples:\n'
                   '  python convert.py trigger1.sql                    # Convert single file\n'
                   '  python convert.py orcale --folder -o json -v      # Convert folder with verbose output\n'
                   '  python convert.py trigger1.sql -o output.json     # Convert with custom output name',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Define command line arguments
        parser.add_argument('input', help='Input Oracle SQL file or folder path')
        parser.add_argument('-o', '--output', help='Output JSON file or folder path')
        parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
        parser.add_argument('--folder', action='store_true', help='Force folder processing mode')
        
        # Parse the command line arguments
        args = parser.parse_args()
        
        # Initialize converter for command line mode
        converter = OracleToPostgreSQLConverter()
        
        # Determine processing mode: folder or single file
        if args.folder or os.path.isdir(args.input):
            # -------------------------------------------------------------------------
            # FOLDER PROCESSING MODE
            # -------------------------------------------------------------------------
            output_folder = args.output or Config.DEFAULT_JSON_FOLDER
            print(f"🔄 Processing folder: {args.input} → {output_folder}")
            
            results = converter.process_folder(args.input, output_folder, args.verbose)
            
            # Exit with error code if no files were successfully converted
            if not any(r.success for r in results):
                sys.exit(1)
                
        else:
            # -------------------------------------------------------------------------
            # SINGLE FILE PROCESSING MODE
            # -------------------------------------------------------------------------
            output_file = args.output or args.input.replace('.sql', '.json')
            print(f"🔄 Processing file: {args.input} → {output_file}")
            
            result = converter.convert_file(args.input, output_file, args.verbose)
            
            if result.success:
                print(f"✅ Conversion completed successfully")
            else:
                print(f"❌ Conversion failed: {result.error_message}")
                sys.exit(1)  # Exit with error code for failed conversion


# =============================================================================
# SCRIPT EXECUTION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    """
    Entry point when script is run directly (not imported as module)
    
    This standard Python idiom ensures that main() only runs when the script
    is executed directly, not when it's imported by another script.
    """
    main()



