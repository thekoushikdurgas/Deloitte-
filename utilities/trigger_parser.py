#!/usr/bin/env python3
"""
Trigger Parser for Oracle to PostgreSQL Trigger Converter

This module handles parsing of Oracle trigger sections and variable extraction.
It identifies and extracts INSERT, UPDATE, DELETE sections from Oracle triggers
and processes variable declarations from DECLARE sections.
"""

import re
from typing import Dict
from .config import TriggerOperation


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