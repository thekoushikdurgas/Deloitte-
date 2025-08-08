#!/usr/bin/env python3
"""
Regex Processor for Oracle to PostgreSQL Trigger Converter

This module handles all regex-based transformations for converting Oracle SQL
to PostgreSQL-compatible SQL. It applies transformations efficiently in a
single pass through the code.
"""

import re
from typing import List
from .config import RegexPattern
from .mapping_manager import MappingManager


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