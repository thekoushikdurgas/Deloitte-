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
from .config import Config, ConversionResult, AnalysisResult
from .mapping_manager import MappingManager
from .regex_processor import RegexProcessor
from .trigger_parser import TriggerParser
from .postgresql_formatter import PostgreSQLFormatter
from .sql_analyzer import SQLAnalyzer


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
        
        # STEP 5: Initialize SQL analyzer (creates intermediate structured analysis)
        self.sql_analyzer = SQLAnalyzer()
    
    def analyze_sql_file(self, input_file: str, sql_json_file: str, verbose: bool = False) -> AnalysisResult:
        """
        Analyze Oracle SQL file and create structured JSON representation
        
        This method performs the first step of the enhanced conversion process:
        analyzing the Oracle SQL code and extracting its structure into a JSON format
        that helps understand the code better before converting to PostgreSQL.
        
        Args:
            input_file: Path to Oracle SQL trigger file
            sql_json_file: Path where SQL analysis JSON should be written
            verbose: Whether to print detailed progress information
            
        Returns:
            AnalysisResult with success status and analysis details
        """
        try:
            # =============================================================================
            # PHASE 1: INPUT VALIDATION AND READING
            # =============================================================================
            
            # Validate that input file exists
            if not os.path.exists(input_file):
                return AnalysisResult(
                    success=False,
                    input_file=input_file,
                    output_file=sql_json_file,
                    error_message=f"Input file not found: {input_file}"
                )
            
            # Check file size to prevent memory issues with very large files
            if os.path.getsize(input_file) > Config.MAX_FILE_SIZE:
                return AnalysisResult(
                    success=False,
                    input_file=input_file,
                    output_file=sql_json_file,
                    error_message=f"File too large: {input_file} (max: {Config.MAX_FILE_SIZE} bytes)"
                )
            
            if verbose:
                print(f"📊 Analyzing SQL structure: {os.path.basename(input_file)}")
            
            # =============================================================================
            # PHASE 2: PERFORM SQL ANALYSIS
            # =============================================================================
            
            # Read the Oracle trigger file content
            with open(input_file, 'r', encoding='utf-8') as f:
                oracle_content = f.read()
            
            # Ensure file has actual content
            if not oracle_content.strip():
                return AnalysisResult(
                    success=False,
                    input_file=input_file,
                    output_file=sql_json_file,
                    error_message="Input file is empty"
                )
            
            # Extract trigger name from filename
            trigger_name = Path(input_file).stem
            
            # Perform the analysis
            analysis_data = self.sql_analyzer.analyze_trigger(oracle_content, trigger_name)
            
            if verbose:
                stats = analysis_data.get('statistics', {})
                print(f"   📋 Lines: {stats.get('total_lines', 0)}")
                print(f"   🔢 Variables: {len(analysis_data.get('declarations', {}).get('variables', []))}")
                print(f"   📊 Complexity: {stats.get('complexity_score', 0)}")
            
            # =============================================================================
            # PHASE 3: SAVE ANALYSIS TO JSON FILE
            # =============================================================================
            
            # Ensure output directory exists
            output_dir = os.path.dirname(sql_json_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Save the analysis
            self.sql_analyzer.save_analysis(analysis_data, sql_json_file)
            
            # =============================================================================
            # PHASE 4: RETURN SUCCESS RESULT
            # =============================================================================
            
            return AnalysisResult(
                success=True,
                input_file=input_file,
                output_file=sql_json_file,
                analysis_data=analysis_data,
                complexity_score=analysis_data.get('statistics', {}).get('complexity_score', 0)
            )
            
        except Exception as e:
            # =============================================================================
            # ERROR HANDLING - RETURN FAILURE RESULT
            # =============================================================================
            
            return AnalysisResult(
                success=False,
                input_file=input_file,
                output_file=sql_json_file,
                error_message=str(e)
            )
    
    def convert_file(self, input_file: str, output_file: str, verbose: bool = False) -> ConversionResult:
        """
        Convert a single Oracle trigger file to PostgreSQL JSON format (Enhanced 3-step process)
        
        This is the main conversion method that orchestrates the enhanced 3-step process:
        1. SQL Analysis: Analyzes Oracle SQL and creates structured JSON representation
        2. Conversion: Parses Oracle trigger sections, applies transformations
        3. PostgreSQL Formatting: Formats as PostgreSQL DO blocks and outputs JSON
        
        Enhanced Process Flow: SQL -> SQL_JSON -> PostgreSQL_JSON
        
        Args:
            input_file: Path to Oracle SQL trigger file
            output_file: Path where PostgreSQL JSON should be written
            verbose: Whether to print detailed progress information
            
        Returns:
            ConversionResult with success status, paths, and conversion details
        """
        try:
            # =============================================================================
            # PHASE 0: ENHANCED 3-STEP PROCESS SETUP
            # =============================================================================
            
            # Generate SQL JSON file path (intermediate analysis step)
            # Create path in sql_json folder instead of json folder
            output_path = Path(output_file)
            sql_json_filename = output_path.stem + '_analysis.json'
            
            # Determine sql_json directory
            if 'json' in str(output_path.parent):
                # Replace 'json' with 'sql_json' in the path
                sql_json_dir = str(output_path.parent).replace('json', 'sql_json')
            else:
                # Use default sql_json folder
                sql_json_dir = Config.DEFAULT_SQL_JSON_FOLDER
            
            sql_json_file = os.path.join(sql_json_dir, sql_json_filename)
            
            if verbose:
                print(f"🔄 Enhanced 3-step conversion process:")
                print(f"   📄 SQL → 📊 SQL_JSON → 📝 PostgreSQL_JSON")
                print(f"   📄 {os.path.basename(input_file)} → 📊 {os.path.basename(sql_json_file)} → 📝 {os.path.basename(output_file)}")
            
            # =============================================================================
            # PHASE 1: SQL ANALYSIS - CREATE STRUCTURED REPRESENTATION
            # =============================================================================
            
            if verbose:
                print(f"📊 Step 1: Analyzing SQL structure...")
            
            # Perform SQL analysis (Step 1 of 3)
            analysis_result = self.analyze_sql_file(input_file, sql_json_file, verbose)
            if not analysis_result.success:
                return ConversionResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    sections_converted=[],
                    sql_json_file=sql_json_file,
                    error_message=f"SQL analysis failed: {analysis_result.error_message}"
                )
            
            if verbose:
                print(f"✅ SQL analysis completed: {os.path.basename(sql_json_file)}")
                print(f"🔄 Step 2: Converting to PostgreSQL...")
            
            # =============================================================================
            # PHASE 2: INPUT VALIDATION AND READING (for conversion)
            # =============================================================================
            
            # Validate that input file exists (redundant but kept for safety)
            if not os.path.exists(input_file):
                return ConversionResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    sections_converted=[],
                    sql_json_file=sql_json_file,
                    error_message=f"Input file not found: {input_file}"
                )
            
            # Check file size to prevent memory issues with very large files
            if os.path.getsize(input_file) > Config.MAX_FILE_SIZE:
                return ConversionResult(
                    success=False,
                    input_file=input_file,
                    output_file=output_file,
                    sections_converted=[],
                    sql_json_file=sql_json_file,
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
                    sql_json_file=sql_json_file,
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
            # PHASE 3: POSTGRESQL CONVERSION - TRANSFORM EACH SECTION
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
            # PHASE 4: POSTGRESQL OUTPUT - WRITE JSON FILE
            # =============================================================================
            
            # Ensure output directory exists (create if necessary)
            output_dir = os.path.dirname(output_file)
            if output_dir:  # Only create if there's actually a directory path
                os.makedirs(output_dir, exist_ok=True)
            
            # Write the final JSON structure to output file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_structure, f, indent=4)
            
            # =============================================================================
            # PHASE 5: RETURN SUCCESS RESULT (Enhanced with SQL analysis info)
            # =============================================================================
            
            if verbose:
                print(f"✅ Step 3: PostgreSQL conversion completed: {os.path.basename(output_file)}")
                print(f"🎉 3-step conversion successful!")
            
            return ConversionResult(
                success=True,
                input_file=input_file,
                output_file=output_file,
                sections_converted=converted_sections,
                sql_json_file=sql_json_file,
                variables_count=len(variables.split(';')) - 1 if variables else 0
            )
            
        except Exception as e:
            # =============================================================================
            # ERROR HANDLING - RETURN FAILURE RESULT
            # =============================================================================
            
            # Try to get sql_json_file if it was defined
            try:
                sql_json_file_for_error = sql_json_file
            except NameError:
                sql_json_file_for_error = None
            
            return ConversionResult(
                success=False,
                input_file=input_file,
                output_file=output_file,
                sections_converted=[],
                sql_json_file=sql_json_file_for_error,
                error_message=str(e)
            )
    
    def process_folder(self, oracle_folder: str, json_folder: str, verbose: bool = False) -> List[ConversionResult]:
        """
        Process all SQL files in a folder (Enhanced 3-step batch conversion)
        
        This method handles batch processing of multiple Oracle trigger files using
        the enhanced 3-step process: SQL -> SQL_JSON -> PostgreSQL_JSON.
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
                sql_json_info = f"[📊 {Path(result.sql_json_file).name}]" if result.sql_json_file else ""
                print(f"✅ {sql_file.name} → {output_file.name} {sections_info} {sql_json_info}")
            else:
                print(f"❌ {sql_file.name}: {result.error_message}")
        
        # =============================================================================
        # PHASE 4: PROVIDE SUMMARY
        # =============================================================================
        
        # Calculate success statistics
        success_count = sum(1 for r in results if r.success)
        total_sections = sum(len(r.sections_converted) for r in results if r.success)
        total_variables = sum(r.variables_count for r in results if r.success)
        sql_json_count = sum(1 for r in results if r.success and r.sql_json_file)
        
        print(f"\n🎉 Enhanced 3-step batch conversion complete!")
        print(f"   📊 Files: {success_count}/{len(results)} converted successfully")
        print(f"   📋 SQL Analysis: {sql_json_count} analysis files created")
        print(f"   📋 Sections: {total_sections} trigger sections converted")
        print(f"   📝 Variables: {total_variables} variables processed")
        
        return results 