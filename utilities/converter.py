#!/usr/bin/env python3
"""
Main Converter for Oracle to PostgreSQL Trigger Converter

This module contains the main OracleToPostgreSQLConverter class that orchestrates
the entire conversion process from Oracle triggers to PostgreSQL format.
"""

import os
import json
from pathlib import Path
from typing import List, Optional
from .config import Config, ConversionResult
from .mapping_manager import MappingManager
from .regex_processor import RegexProcessor
from .trigger_parser import TriggerParser
from .postgresql_formatter import PostgreSQLFormatter


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