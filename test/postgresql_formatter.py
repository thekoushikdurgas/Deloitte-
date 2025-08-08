#!/usr/bin/env python3
"""
PostgreSQL Formatter for Oracle to PostgreSQL Trigger Converter

This module handles PostgreSQL-specific formatting and DO block creation.
It formats converted SQL code into proper PostgreSQL DO blocks that can be
executed directly in PostgreSQL.
"""

import re


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