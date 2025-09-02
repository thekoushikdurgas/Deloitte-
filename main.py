#!/usr/bin/env python3
"""
Entry point for converting Oracle trigger SQL files to structured JSON analysis
and rendering them back into formatted PL/SQL.


High-level flow:
- Read all `*.sql` files from `files/oracle`.
- For each file, build an `OracleTriggerAnalyzer` to parse and analyze SQL into JSON.
- Write the analysis JSON into `files/format_json/trigger{N}_analysis.json`.
- Read each `*_analysis.json` and render it back to PL/SQL with
  `FORMATOracleTriggerAnalyzer`, writing to `files/format_sql/trigger{N}.sql`.


Logging:
- All operations are logged to both console and a timestamped log file in 'output/'.
- The log file name format is 'oracle_conversion_YYYYMMDD_HHMMSS.log'.
- Log levels: DEBUG for detailed operations, INFO for main steps, ERROR for failures.
"""


import json
import os
import re
import time
from typing import Any, Dict, List, Tuple
from utilities.common import (
    clean_json_files,
    logger,
    setup_logging,
    debug,
    info,
    warning,
    error,
    critical,
    alert,
)


from utilities.OracleTriggerAnalyzer import OracleTriggerAnalyzer
from utilities.FormatSQL import FormatSQL
from utilities.JSONTOPLJSON import JSONTOPLJSON


from datetime import datetime


# Directory constants
FORMAT_JSON_DIR = "files/format_json"
FORMAT_SQL_DIR = "files/format_sql"
FORMAT_PL_SQL_DIR = "files/format_plsql"


# File suffix constants
ANALYSIS_JSON_SUFFIX = "_analysis.json"
JSON_FILE_SUFFIX = ".json"


def convert_complex_structure_to_sql(complex_structure):
    """
    Convert the complex PL/JSON structure to a proper PostgreSQL SQL string.


    Args:
        complex_structure: The complex structure from PL/JSON


    Returns:
        str: The PostgreSQL SQL string
    """
    try:
        debug("Converting complex structure to PostgreSQL SQL")
        analyzer = FormatSQL(complex_structure)
        sql_content = analyzer.to_sql("PostgreSQL")
        analyzer_sql = sql_content["sql"]
        debug("Successfully converted complex structure to PostgreSQL SQL")
        return analyzer_sql
    except Exception as e:
        error("Failed to convert complex structure to PostgreSQL SQL: %s", str(e))
        # Return a fallback SQL structure
        return f"""-- Failed to convert complex structure
-- Error: {str(e)}
CREATE OR REPLACE FUNCTION trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    -- Placeholder for failed conversion
    RAISE NOTICE 'Trigger function placeholder';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;"""
def ensure_dir(directory: str) -> None:
    """
    Ensure that the specified directory exists, creating it if necessary.


    Args:
        directory (str): The directory path to ensure exists


    This function creates the directory and all parent directories if they don't exist.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        debug("Created directory: %s", directory)
    else:
        debug("Directory already exists: %s", directory)


def process_files(
    source_dir: str,
    target_dir: str,
    file_pattern: str,
    output_suffix: str,
    processor_func,
) -> None:
    """process_files function."""
    """
    Process files from source_dir to target_dir using the provided processor function.


    This function:
    1. Ensures the target directory exists
    2. Finds all files matching the pattern in the source directory
    3. Extracts trigger numbers from filenames
    4. Processes each file using the provided processor function
    5. Handles errors gracefully with detailed logging
    6. Tracks file processing statistics including file details


    Args:
        source_dir (str): Source directory containing files to process
        target_dir (str): Target directory for processed files
        file_pattern (str): File extension pattern to match (e.g., ".sql")
        output_suffix (str): Suffix to add to output filenames
        processor_func: Function to process each file (src_path, out_path, file_name)
    """
    info("=== Starting file processing ===")
    info("Source directory: '%s'", source_dir)
    info("Target directory: '%s'", target_dir)
    info("File pattern: '%s'", file_pattern)
    info("Output suffix: '%s'", output_suffix)


    # Ensure directories exist
    debug("Ensuring target directory exists...")
    ensure_dir(target_dir)


    # Get all matching files from the source directory
    try:
        files = [f for f in os.listdir(source_dir) if f.endswith(file_pattern)]
        debug("Found %d files in source directory", len(files))
    except FileNotFoundError:
        error("Source directory not found: %s", source_dir)
        return
    except PermissionError:
        error("Permission denied accessing source directory: %s", source_dir)
        return


    debug("Files matching pattern '%s': %s", file_pattern, files)


    # Process each file
    processed_count = 0
    error_count = 0
    total_file_size = 0


    i = 1
    while i <= len(files):
        file_name = files[i - 1]
        debug("=== Processing file %d/%d: %s ===", i, len(files), file_name)
        try:
            # Process the file
            src_path = os.path.join(source_dir, file_name)
            filename = file_name.split('.')[0]  # Remove extension for output filename
            output_filename = f"{filename}{output_suffix}"
            out_path = os.path.join(target_dir, output_filename)


            debug("Source path: %s", src_path)
            debug("Output path: %s", out_path)
            
            # # Log file details if available
            # try:
            #     file_details = OracleTriggerAnalyzer.extract_file_details(src_path)
            #     file_size = file_details.get("filesize", 0)
            #     total_file_size += file_size
            #     debug("File size: %d bytes", file_size)
            # except Exception as e:
            #     debug("Could not extract file details: %s", str(e))


            # Run the processor function
            processor_func(src_path, out_path, file_name)


            debug("✓ Created %s", output_filename)
            processed_count += 1


        except FileNotFoundError as e:
            error("File not found: %s - %s", file_name, str(e))
            error_count += 1
        except PermissionError as e:
            error("Permission denied: %s - %s", file_name, str(e))
            error_count += 1
        except Exception as exc:
            error("Failed to process %s: %s", file_name, str(exc))
            error_count += 1
            raise
        i += 1


    info("=== File processing complete ===")
    info("Successfully processed: %d files", processed_count)
    if total_file_size > 0:
        info("Total file size processed: %d bytes (%.2f KB)", total_file_size, total_file_size / 1024)
    if error_count > 0:
        warning("Failed to process: %d files", error_count)


def sql_to_json_processor(src_path: str, out_path: str, file_name: str) -> None:
    """
    Process a SQL file to JSON analysis.


    This function:
    1. Creates an OracleTriggerAnalyzer instance directly from the file
    2. Generates JSON analysis with file details in metadata
    3. Writes the analysis to the output file


    Args:
        src_path (str): Path to the source SQL file
        out_path (str): Path to the output JSON file
        file_name (str): Trigger number extracted from filename
    """
    debug("=== SQL to JSON processing for trigger %s ===", file_name)
    
    # Step 1: Create analyzer directly from file (includes file details)
    debug("Creating OracleTriggerAnalyzer instance from file...")
    print(f"Reading SQL file: {src_path}")
    try:
        analyzer = OracleTriggerAnalyzer(src_path)
        debug("OracleTriggerAnalyzer created successfully with file details")
        debug("File details: %s", analyzer.file_details.get("filename", "unknown"))
    except FileNotFoundError as e:
        error("File not found: %s", src_path)
        raise
    except UnicodeDecodeError as e:
        error("Unicode decode error reading %s: %s", src_path, str(e))
        raise
    except Exception as e:
        error("Failed to create OracleTriggerAnalyzer: %s", str(e))
        raise


    # Step 2: Generate JSON analysis
    debug("Generating JSON analysis...")
    try:
        json_content: Dict[str, Any] = analyzer.to_json()
        debug("JSON analysis generated successfully")
        debug("Generated JSON with keys: %s", list(json_content.keys()))


        # Log file details from metadata
        metadata = json_content.get("metadata", {})
        file_details = metadata.get("file_details", {})
        if file_details:
            debug("File details in metadata: %s (%d bytes)", file_details.get("filename", "unknown"), file_details.get("filesize", 0))


        # Log some statistics about the analysis
        declarations = json_content.get("declarations", {})
        variables = len(declarations.get("variables", []))
        constants = len(declarations.get("constants", []))
        exceptions = len(declarations.get("exceptions", []))
        comments = len(json_content.get("sql_comments", []))
        debug("Analysis statistics: %d vars, %d consts, %d excs, %d comments",variables,constants,exceptions,comments,)


    except Exception as e:
        error("Failed to generate JSON analysis: %s", str(e))
        raise


    # Step 3: Write to JSON file
    debug("Writing analysis JSON to: %s", out_path)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2)
        debug("Successfully wrote analysis JSON to %s", out_path)
    except Exception as e:
        error("Failed to write JSON file %s: %s", out_path, str(e))
        raise


    debug("=== SQL to JSON processing complete for trigger %s ===", file_name)


def read_oracle_triggers_to_json() -> None:
    """
    Convert all Oracle trigger SQL files into analysis JSON files.


    This function processes all .sql files in the files/oracle directory,
    converting them to structured JSON analysis files in the files/format_json directory.
   
    The conversion workflow:
    1. Locate all Oracle SQL trigger files in the source directory
    2. For each file, extract the trigger number from the filename
    3. Parse the SQL content using OracleTriggerAnalyzer with file details
    4. Save the resulting structured JSON to the target directory with metadata
    """
    info("=== Starting Oracle triggers to JSON conversion ===")
    debug("Workflow Phase 1: Convert Oracle SQL files to JSON analysis structure")
    debug("Source directory: files/oracle")
    debug("Target directory: %s", FORMAT_JSON_DIR)
    debug("File details will be included in metadata for each processed file")
   
    # Process all files using the processor function
    process_files(
        source_dir="files/oracle",
        target_dir=FORMAT_JSON_DIR,
        file_pattern=".sql",
        output_suffix=ANALYSIS_JSON_SUFFIX,
        processor_func=sql_to_json_processor,
    )
   
    # Log successful completion
    info("=== Oracle triggers to JSON conversion complete ===")
    debug("Phase 1 complete: Oracle SQL files converted to JSON analysis structure with file metadata")


def json_to_sql_processor(src_path: str, out_path: str, file_name: str) -> None:
    """
    Process a JSON analysis file to formatted SQL.


    This function:
    1. Reads the JSON analysis file
    2. Validates the JSON structure and content
    3. Creates a FORMATOracleTriggerAnalyzer instance
    4. Renders the SQL content with enhanced error handling
    5. Writes the formatted SQL to the output file


    Args:
        src_path (str): Path to the source JSON analysis file
        out_path (str): Path to the output SQL file
        file_name (str): Trigger number extracted from filename
    """
    debug("=== JSON to SQL processing for trigger %s ===", file_name)


    # Step 1: Read the JSON file
    debug("Reading JSON analysis file: %s", src_path)
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)
        logger.debug(
            f"Successfully loaded analysis JSON with keys: {list(analysis.keys())}"
        )
    except json.JSONDecodeError as e:
        error(f"JSON decode error reading {src_path}: {str(e)}" )
        raise
    except Exception as e:
        error("Error reading JSON file %s: %s", src_path, str(e))
        raise

    # Step 1.5: Enhanced JSON validation
    if "error" not in analysis:
        debug("Validating JSON structure...")
        validation_result = validate_json_structure(analysis, file_name)
        if not validation_result["is_valid"]:
            error("JSON validation failed for %s: %s", file_name, validation_result["errors"])
            raise ValueError(f"Invalid JSON structure: {validation_result['errors']}")
        
        debug("JSON validation passed")
        
        # Step 2: Render the SQL
        debug("Creating FormatSQL instance...")
        try:
            analyzer = FormatSQL(analysis)
            debug("FormatSQL created successfully")
        except Exception as e:
            error("Failed to create FormatSQL: %s", str(e))
            raise


        # Step 3: Generate SQL content with performance monitoring
        debug("Rendering SQL from analysis...")
        try:
            render_start_time = time.time()
            sql_content: str = analyzer.to_sql("Oracle")
            analyzer_sql = sql_content["sql"]
            render_duration = time.time() - render_start_time
            
            debug("SQL rendering completed successfully")
            debug(f"Rendered SQL length: {len(analyzer_sql)} characters")
            debug(f"SQL rendering took: {render_duration:.3f} seconds")
            
            # Validate generated SQL
            sql_validation = validate_generated_sql(analyzer_sql, file_name)
            if not sql_validation["is_valid"]:
                warning("Generated SQL validation warnings for %s: %s", file_name, sql_validation["warnings"])
            
        except Exception as e:
            error("Failed to render SQL: %s", str(e))
            raise


        # Step 4: Write to SQL file
        debug("Writing formatted SQL to: %s", out_path)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(analyzer_sql)
            debug(f"Successfully wrote formatted SQL to {out_path}")
        except Exception as e:
            error(f"Failed to write SQL file {out_path}: {str(e)}")
            raise


        debug("=== JSON to SQL processing complete for trigger %s ===", file_name)
    else:
        error("Analysis Sql contains error: %s", analysis["error"])


def render_oracle_sql_from_analysis() -> None:
    """
    Render formatted PL/SQL for each analysis JSON file.


    This function processes all _analysis.json files in the files/format_json directory,
    converting them to formatted SQL files in the files/format_sql directory.
    """
    info("=== Starting JSON analysis to formatted Oracle SQL conversion ===")
    
    # Track conversion statistics
    conversion_stats = {
        "total_files": 0,
        "successful_conversions": 0,
        "failed_conversions": 0,
        "validation_warnings": 0,
        "comparison_results": []
    }
    
    process_files(
        source_dir=FORMAT_JSON_DIR,
        target_dir=FORMAT_SQL_DIR,
        file_pattern=ANALYSIS_JSON_SUFFIX,
        output_suffix=".sql",
        processor_func=json_to_sql_processor,
    )
    
    # Perform comparison with original files
    info("=== Starting comparison with original files ===")
    comparison_stats = perform_comparison_analysis()
    conversion_stats.update(comparison_stats)
    
    # Log final statistics
    info("=== Conversion Statistics ===")
    info("Total files processed: %d", conversion_stats["total_files"])
    info("Successful conversions: %d", conversion_stats["successful_conversions"])
    info("Failed conversions: %d", conversion_stats["failed_conversions"])
    info("Files with validation warnings: %d", conversion_stats["validation_warnings"])
    
    if conversion_stats["comparison_results"]:
        info("=== Comparison Results ===")
        for result in conversion_stats["comparison_results"]:
            if result["warnings"]:
                warning("File %s: %s", result["file_name"], "; ".join(result["warnings"]))
            else:
                info("File %s: Conversion successful", result["file_name"])
    
    info("=== JSON analysis to formatted Oracle SQL conversion complete ===")


def validate_json_structure(analysis: Dict[str, Any], file_name: str) -> Dict[str, Any]:
    """
    Validate the JSON structure for proper SQL generation.
    
    Args:
        analysis (Dict[str, Any]): The JSON analysis data
        file_name (str): Name of the file being processed
        
    Returns:
        Dict[str, Any]: Validation result with is_valid flag and errors list
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check required top-level sections
    required_sections = ["declarations", "main"]
    for section in required_sections:
        if section not in analysis:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Missing required section: {section}")
    
    if not validation_result["is_valid"]:
        return validation_result
    
    # Validate declarations section
    declarations = analysis.get("declarations", {})
    if not isinstance(declarations, dict):
        validation_result["is_valid"] = False
        validation_result["errors"].append("Declarations section must be a dictionary")
    else:
        # Check declaration subsections
        decl_sections = ["variables", "constants", "exceptions"]
        for decl_section in decl_sections:
            if decl_section in declarations:
                if not isinstance(declarations[decl_section], list):
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"Declarations.{decl_section} must be a list")
    
    # Validate main section
    main = analysis.get("main", {})
    if not isinstance(main, dict):
        validation_result["is_valid"] = False
        validation_result["errors"].append("Main section must be a dictionary")
    else:
        # Check main section type
        main_type = main.get("type")
        if main_type != "begin_end":
            validation_result["warnings"].append(f"Main section type '{main_type}' may not be fully supported")
        
        # Check for required main subsections
        if "begin_end_statements" not in main:
            validation_result["warnings"].append("Main section missing begin_end_statements")
    
    # Check for conversion statistics
    if "conversion_stats" in analysis:
        stats = analysis["conversion_stats"]
        if isinstance(stats, dict) and "sql_convert_count" in stats:
            sql_counts = stats["sql_convert_count"]
            if isinstance(sql_counts, dict):
                total_statements = sum(sql_counts.values())
                debug(f"JSON contains {total_statements} total statements")
                
                # Check for potentially problematic statement types
                problematic_types = ["unknown_statement"]
                for prob_type in problematic_types:
                    if prob_type in sql_counts and sql_counts[prob_type] > 0:
                        validation_result["warnings"].append(
                            f"Found {sql_counts[prob_type]} {prob_type} statements that may not render correctly"
                        )
    
    return validation_result


def validate_generated_sql(sql_content: str, file_name: str) -> Dict[str, Any]:
    """
    Validate the generated SQL content for basic syntax and structure.
    
    Args:
        sql_content (str): The generated SQL content
        file_name (str): Name of the file being processed
        
    Returns:
        Dict[str, Any]: Validation result with is_valid flag and warnings list
    """
    validation_result = {
        "is_valid": True,
        "warnings": []
    }
    
    if not sql_content or not sql_content.strip():
        validation_result["is_valid"] = False
        validation_result["warnings"].append("Generated SQL content is empty")
        return validation_result
    
    # Check for basic SQL structure (works for both Oracle and PostgreSQL)
    lines = sql_content.split('\n')
    
    # Check for CREATE FUNCTION or CREATE OR REPLACE FUNCTION
    has_create_function = any('CREATE' in line.upper() and 'FUNCTION' in line.upper() for line in lines)
    if not has_create_function:
        validation_result["warnings"].append("Missing CREATE FUNCTION statement")
    
    # Check for BEGIN section
    has_begin = any('BEGIN' in line.upper() for line in lines)
    if not has_begin:
        validation_result["warnings"].append("Missing BEGIN section")
    
    # Check for END section
    has_end = any('END;' in line.upper() for line in lines)
    if not has_end:
        validation_result["warnings"].append("Missing END; section")
    
    # Check for balanced BEGIN/END pairs
    begin_count = sum(1 for line in lines if 'BEGIN' in line.upper())
    end_count = sum(1 for line in lines if 'END;' in line.upper())
    if begin_count != end_count:
        validation_result["warnings"].append(f"Unbalanced BEGIN/END pairs: {begin_count} BEGIN, {end_count} END")
    
    # Check for proper semicolon usage
    semicolon_count = sql_content.count(';')
    if semicolon_count < 5:  # Lower threshold for PostgreSQL
        validation_result["warnings"].append(f"Low semicolon count ({semicolon_count}) may indicate incomplete statements")
    
    # Check for common SQL keywords
    sql_keywords = ['IF', 'THEN', 'ELSE', 'CASE', 'WHEN', 'LOOP', 'EXCEPTION', 'RETURN', 'SELECT', 'INSERT', 'UPDATE', 'DELETE']
    missing_keywords = []
    for keyword in sql_keywords:
        if keyword not in sql_content.upper():
            missing_keywords.append(keyword)
    
    if len(missing_keywords) > 8:  # If more than 8 keywords are missing
        validation_result["warnings"].append(f"Many SQL keywords missing: {missing_keywords[:5]}...")
    
    # Check for PostgreSQL-specific elements
    if 'LANGUAGE plpgsql' in sql_content.upper():
        validation_result["warnings"].append("PostgreSQL-specific syntax detected")
    
    # Check for Oracle-specific elements
    if 'DECLARE' in sql_content.upper() and 'LANGUAGE plpgsql' not in sql_content.upper():
        validation_result["warnings"].append("Oracle-specific syntax detected")
    
    return validation_result


def compare_original_and_generated(original_path: str, generated_path: str, file_name: str) -> Dict[str, Any]:
    """
    Compare original SQL with generated SQL to identify differences.
    
    Args:
        original_path (str): Path to original SQL file
        generated_path (str): Path to generated SQL file
        file_name (str): Name of the file being compared
        
    Returns:
        Dict[str, Any]: Comparison result with statistics and differences
    """
    comparison_result = {
        "original_lines": 0,
        "generated_lines": 0,
        "line_differences": 0,
        "structural_differences": [],
        "warnings": []
    }
    
    try:
        # Read original SQL
        with open(original_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        # Read generated SQL
        with open(generated_path, "r", encoding="utf-8") as f:
            generated_content = f.read()
        
        # Basic line count comparison
        original_lines = original_content.split('\n')
        generated_lines = generated_content.split('\n')
        
        comparison_result["original_lines"] = len(original_lines)
        comparison_result["generated_lines"] = len(generated_lines)
        
        # Count non-empty lines
        original_non_empty = len([line for line in original_lines if line.strip()])
        generated_non_empty = len([line for line in generated_lines if line.strip()])
        
        # Calculate difference percentage
        if original_non_empty > 0:
            diff_percentage = abs(original_non_empty - generated_non_empty) / original_non_empty * 100
            if diff_percentage > 20:  # More than 20% difference
                comparison_result["warnings"].append(
                    f"Significant line count difference: {diff_percentage:.1f}%"
                )
        
        # Check for structural elements
        structural_elements = {
            "DECLARE": ("DECLARE", "Declaration section"),
            "BEGIN": ("BEGIN", "Begin section"),
            "EXCEPTION": ("EXCEPTION", "Exception handling"),
            "END;": ("END;", "End statement")
        }
        
        for element, (keyword, description) in structural_elements.items():
            original_has = keyword in original_content.upper()
            generated_has = keyword in generated_content.upper()
            
            if original_has != generated_has:
                comparison_result["structural_differences"].append(
                    f"{description}: {'Missing' if not generated_has else 'Extra'} in generated"
                )
        
        debug(f"Comparison complete for {file_name}: {comparison_result['original_lines']} original, {comparison_result['generated_lines']} generated lines")
        
    except Exception as e:
        comparison_result["warnings"].append(f"Comparison failed: {str(e)}")
    
    return comparison_result


def perform_comparison_analysis() -> Dict[str, Any]:
    """
    Perform comparison analysis between original and generated SQL files.
    
    Returns:
        Dict[str, Any]: Comparison statistics
    """
    comparison_stats = {
        "total_files": 0,
        "successful_conversions": 0,
        "failed_conversions": 0,
        "validation_warnings": 0,
        "comparison_results": []
    }
    
    try:
        # Get list of original SQL files
        oracle_dir = "files/oracle"
        format_sql_dir = FORMAT_SQL_DIR
        
        if not os.path.exists(oracle_dir) or not os.path.exists(format_sql_dir):
            warning("Cannot perform comparison: missing directories")
            return comparison_stats
        
        original_files = [f for f in os.listdir(oracle_dir) if f.endswith(".sql")]
        generated_files = [f for f in os.listdir(format_sql_dir) if f.endswith(".sql")]
        
        comparison_stats["total_files"] = len(original_files)
        
        for original_file in original_files:
            # Find corresponding generated file
            base_name = original_file.replace(".sql", "")
            generated_file = f"{base_name}_analysis.sql"  # Match the actual generated filename
            
            if generated_file in generated_files:
                original_path = os.path.join(oracle_dir, original_file)
                generated_path = os.path.join(format_sql_dir, generated_file)
                
                try:
                    comparison_result = compare_original_and_generated(
                        original_path, generated_path, original_file
                    )
                    comparison_result["file_name"] = original_file
                    comparison_stats["comparison_results"].append(comparison_result)
                    
                    if not comparison_result["warnings"]:
                        comparison_stats["successful_conversions"] += 1
                    else:
                        comparison_stats["validation_warnings"] += 1
                        
                except Exception as e:
                    error("Comparison failed for %s: %s", original_file, str(e))
                    comparison_stats["failed_conversions"] += 1
            else:
                warning("No generated file found for %s", original_file)
                comparison_stats["failed_conversions"] += 1
        
    except Exception as e:
        error("Comparison analysis failed: %s", str(e))
    
    return comparison_stats


def read_json_to_oracle_triggers() -> None:
    """read_json_to_oracle_triggers function."""
    # Define directories
    json_dir = FORMAT_JSON_DIR
    sql_out_dir = "files/format_pl_json"


    # Ensure directories exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    if not os.path.exists(sql_out_dir):
        os.makedirs(sql_out_dir)


    # Process each analysis JSON file
    json_files = [f for f in os.listdir(json_dir) if f.endswith(ANALYSIS_JSON_SUFFIX)]


    i = 0
    while i < len(json_files):
        json_file = json_files[i]
        json_path = os.path.join(json_dir, json_file)
        with open(json_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)
        if "error" not in analysis:
            debug(f"processing {json_file}")
            analyzer = JSONTOPLJSON(analysis)
            sql_content = analyzer.to_sql()


            # Save as JSON with the new structure
            json_file_name = json_file.replace(ANALYSIS_JSON_SUFFIX, "").split('.')[0]
            out_filename = f"{json_file_name}.json"
            out_path = os.path.join(sql_out_dir, out_filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(sql_content)
            debug(f"Created {out_filename}")
        else:
            debug(f"Skipping {json_file} due to error in analysis: {analysis['error']}")
        i += 1


def json_to_pl_sql_processor(src_path: str, out_path: str, file_name: str) -> None:
    """
    Process a JSON analysis file to formatted PostgreSQL SQL.


    This function:
    1. Reads the JSON analysis file
    2. Creates a FormatSQL instance
    3. Renders the PostgreSQL SQL content
    4. Writes the formatted SQL to the output file


    Args:
        src_path (str): Path to the source JSON analysis file
        out_path (str): Path to the output SQL file
        file_name (str): Trigger number extracted from filename
    """
    debug("=== JSON to PostgreSQL SQL processing for trigger %s ===", file_name)


    # Step 1: Read the JSON file
    debug("Reading JSON analysis file: %s", src_path)
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)
        logger.debug(
            f"Successfully loaded analysis JSON with keys: {list(analysis.keys())}"
        )
    except json.JSONDecodeError as e:
        error(f"JSON decode error reading {src_path}: {str(e)}")
        raise
    except Exception as e:
        error("Error reading JSON file %s: %s", src_path, str(e))
        raise


    # Step 2: Render the SQL
    debug("Creating FormatSQL instance...")
    try:
        analyzer = FormatSQL(analysis)
        debug("FormatSQL created successfully")
    except Exception as e:
        error("Failed to create FormatSQL: %s", str(e))
        raise


    # Step 3: Generate SQL content
    debug("Rendering PostgreSQL SQL from analysis...")
    try:
        sql_content: str = analyzer.to_sql("PostgreSQL")
        analyzer_sql = sql_content["sql"]
        debug("PostgreSQL SQL rendering completed successfully")
        debug("Rendered SQL length: %d characters", len(analyzer_sql))
    except Exception as e:
        error("Failed to render PostgreSQL SQL: %s", str(e))
        raise


    # Step 4: Write to SQL file
    debug("Writing formatted PostgreSQL SQL to: %s", out_path)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(analyzer_sql)
        debug("Successfully wrote formatted PostgreSQL SQL to %s", out_path)
    except Exception as e:
        error("Failed to write PostgreSQL SQL file %s: %s", out_path, str(e))
        raise


    debug("=== JSON to PostgreSQL SQL processing complete for trigger %s ===", file_name)


def read_json_to_postsql_triggers() -> None:
    """
    Convert PL/JSON files to PostgreSQL format.


    This function processes all .json files in the files/format_pl_json directory,
    converting them to PostgreSQL format files in the files/format_plsql directory.
    """
    info("=== Starting PL/JSON to PostgreSQL format conversion ===")
    process_files(
        source_dir="files/format_pl_json",
        target_dir=FORMAT_PL_SQL_DIR,
        file_pattern=JSON_FILE_SUFFIX,
        output_suffix="_postgresql.json",
        processor_func=convert_pl_json_to_postgresql_format,
    )
    info("=== PL/JSON to PostgreSQL format conversion complete ===")


def convert_json_analysis_to_postgresql_sql() -> None:
    """
    Convert JSON analysis files directly to PostgreSQL SQL.
    
    This function processes all _analysis.json files in the files/format_json directory,
    converting them directly to PostgreSQL SQL files in the files/format_plsql directory.
    """
    info("=== Starting JSON analysis to PostgreSQL SQL conversion ===")
    process_files(
        source_dir=FORMAT_JSON_DIR,
        target_dir=FORMAT_PL_SQL_DIR,
        file_pattern=ANALYSIS_JSON_SUFFIX,
        output_suffix="_postgresql.sql",
        processor_func=json_to_pl_sql_processor,
    )
    info("=== JSON analysis to PostgreSQL SQL conversion complete ===")


def convert_pl_json_to_postgresql_format(
    src_path: str, out_path: str, file_name: str
) -> None:
    """convert_pl_json_to_postgresql_format function."""
    """
    Convert PL/JSON files to PostgreSQL format with on_insert, on_update, on_delete structure.


    This function:
    1. Reads the PL/JSON file from format_pl_json directory
    2. Converts it to the expected PostgreSQL format with on_insert, on_update, on_delete sections
    3. Writes the converted format to format_plsql directory


    Args:
        src_path (str): Path to the source PL/JSON file
        out_path (str): Path to the output PostgreSQL format file
        file_name (str): Trigger number extracted from filename
    """
    debug("=== Converting PL/JSON to PostgreSQL format for trigger %s ===", file_name)


    # Step 1: Read the PL/JSON file
    debug("Reading PL/JSON file: %s", src_path)
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            pl_json_data = json.load(f)
        debug(
            "Successfully loaded PL/JSON data with keys: %s", list(pl_json_data.keys())
        )
    except json.JSONDecodeError as e:
        error("JSON decode error reading %s: %s", src_path, str(e))
        raise
    except Exception as e:
        error("Error reading PL/JSON file %s: %s", src_path, str(e))
        raise
    if "error" not in pl_json_data:
        # Step 2: Convert to PostgreSQL format
        debug("Converting to PostgreSQL format...")
        try:
            # Create the expected PostgreSQL format structure
            postgresql_format = {"on_insert": [], "on_update": [], "on_delete": []}

            # Convert the PL/JSON structure to PostgreSQL format
            # The PL/JSON files have on_insert, on_update, on_delete arrays with complex objects
            # We need to convert these to simple SQL strings

            # Handle on_insert
            if "on_insert" in pl_json_data and pl_json_data["on_insert"]:
                # Convert the complex structure to a simple SQL string
                sql_content = convert_complex_structure_to_sql(pl_json_data["on_insert"])
                # Split into individual statements for better handling
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                for stmt in statements:
                    if stmt:
                        postgresql_format["on_insert"].append({"type": "sql", "sql": stmt + ";"})

            # Handle on_update
            if "on_update" in pl_json_data and pl_json_data["on_update"]:
                sql_content = convert_complex_structure_to_sql(pl_json_data["on_update"])
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                for stmt in statements:
                    if stmt:
                        postgresql_format["on_update"].append({"type": "sql", "sql": stmt + ";"})

            # Handle on_delete
            if "on_delete" in pl_json_data and pl_json_data["on_delete"]:
                sql_content = convert_complex_structure_to_sql(pl_json_data["on_delete"])
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                for stmt in statements:
                    if stmt:
                        postgresql_format["on_delete"].append({"type": "sql", "sql": stmt + ";"})

            debug("PostgreSQL format conversion completed")


        except Exception as e:
            error("Failed to convert to PostgreSQL format: %s", str(e))
            raise


        # Step 3: Write to PostgreSQL format file
        debug("Writing PostgreSQL format to: %s", out_path)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(postgresql_format, f, indent=4)
            debug("Successfully wrote PostgreSQL format to %s", out_path)
        except Exception as e:
            error("Failed to write PostgreSQL format file %s: %s", out_path, str(e))
            raise


        debug(
            "=== PL/JSON to PostgreSQL format conversion complete for trigger %s ===",
            file_name,
        )
    else:
        error("PL/JSON file %s does not contain an error key, skipping conversion", src_path)


def convert_postgresql_format_to_sql(
    src_path: str, out_path: str, file_name: str
) -> None:
    """convert_postgresql_format_to_sql function."""
    """
    Convert PostgreSQL format JSON files to actual SQL files.


    This function:
    1. Reads the PostgreSQL format JSON file
    2. Extracts the SQL content from on_insert, on_update, on_delete sections
    3. Writes the SQL content to a .sql file


    Args:
        src_path (str): Path to the source PostgreSQL format JSON file
        out_path (str): Path to the output SQL file
        file_name (str): Trigger number extracted from filename
    """
    debug("=== Converting PostgreSQL format to SQL for trigger %s ===", file_name)


    # Step 1: Read the PostgreSQL format JSON file
    debug("Reading PostgreSQL format file: %s", src_path)
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            postgresql_data = json.load(f)
        debug(
            "Successfully loaded PostgreSQL format data with keys: %s",
            list(postgresql_data.keys()),
        )
    except json.JSONDecodeError as e:
        error("JSON decode error reading %s: %s", src_path, str(e))
        raise
    except Exception as e:
        error("Error reading PostgreSQL format file %s: %s", src_path, str(e))
        raise


    # Step 2: Extract SQL content
    debug("Extracting SQL content...")
    try:
        sql_lines = []
        sql_lines.append(f"-- PostgreSQL Trigger for {file_name}")
        sql_lines.append(
            f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        sql_lines.append("")


        # Add on_insert SQL
        if "on_insert" in postgresql_data and postgresql_data["on_insert"]:
            sql_lines.append("-- ON INSERT")
            for item in postgresql_data["on_insert"]:
                if item.get("type") == "sql":
                    sql_lines.append(item["sql"])
            sql_lines.append("")


        # Add on_update SQL
        if "on_update" in postgresql_data and postgresql_data["on_update"]:
            sql_lines.append("-- ON UPDATE")
            for item in postgresql_data["on_update"]:
                if item.get("type") == "sql":
                    sql_lines.append(item["sql"])
            sql_lines.append("")


        # Add on_delete SQL
        if "on_delete" in postgresql_data and postgresql_data["on_delete"]:
            sql_lines.append("-- ON DELETE")
            for item in postgresql_data["on_delete"]:
                if item.get("type") == "sql":
                    sql_lines.append(item["sql"])
            sql_lines.append("")


        sql_content = "\n".join(sql_lines)
        debug("SQL content extraction completed")


    except Exception as e:
        error("Failed to extract SQL content: %s", str(e))
        raise


    # Step 3: Write to SQL file
    debug("Writing SQL to: %s", out_path)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sql_content)
        debug("Successfully wrote SQL to %s", out_path)
    except Exception as e:
        error("Failed to write SQL file %s: %s", out_path, str(e))
        raise


    debug(
        "=== PostgreSQL format to SQL conversion complete for trigger %s ===",
        file_name,
    )


def convert_postgresql_format_files_to_sql() -> None:
    """
    Convert PostgreSQL format JSON files to actual SQL files.


    This function processes all _postgresql.json files in the files/format_plsql directory,
    converting them to actual SQL files in the same directory.
    """
    info("=== Starting PostgreSQL format to SQL conversion ===")
    process_files(
        source_dir=FORMAT_PL_SQL_DIR,
        target_dir=FORMAT_PL_SQL_DIR,
        file_pattern="_postgresql.json",
        output_suffix=".sql",
        processor_func=convert_postgresql_format_to_sql,
    )
    info("=== PostgreSQL format to SQL conversion complete ===")


def main() -> None:
    """
    Main execution function for the Oracle trigger conversion process.


    This function orchestrates the entire conversion workflow through these major steps:
    1. SQL to JSON conversion: Parse Oracle trigger files into structured JSON
    2. JSON to SQL conversion: Convert JSON analysis back to formatted Oracle SQL
    3. JSON cleaning: Clean up the JSON files (remove line numbers, etc.)
    4. Validation: Verify all conversions completed successfully
    5. JSON to PL/JSON: Transform JSON to PostgreSQL-compatible structure
    6. PL/JSON to PostgreSQL: Convert PL/JSON to PostgreSQL SQL
    7. Final output generation: Create the final SQL files


    Each step is timed and logged for performance monitoring and debugging.
    The function includes comprehensive error handling with detailed logging.
    """
    start_time = time.time()


    try:
        # Set up logging for the main script
        _ , log_path = setup_logging()
        debug("Starting main conversion workflow")
        info("=== Starting Oracle Trigger Conversion Process ===")
        info("Logging to: %s", log_path)
        debug("Logging system initialized")


        # Step 1: Convert SQL to JSON
        # --------------------------
        info("Step 1: Converting Oracle SQL files to JSON analysis...")
        debug("Starting Step 1: Oracle SQL → JSON conversion")
        step1_start = time.time()
       
        # Parse Oracle trigger files into structured JSON representation
        read_oracle_triggers_to_json()
       
        step1_duration = time.time() - step1_start
        info("✓ JSON conversion complete! (Duration: %.2f seconds)", step1_duration)
        debug(f"Step 1 completed in {step1_duration:.2f} seconds")

        # # Step 2: Convert JSON back to SQL
        # # -------------------------------
        # info("Step 2: Converting JSON analysis back to formatted SQL...")
        # debug("Starting Step 2: JSON analysis → formatted Oracle SQL")
        # step2_start = time.time()
       
        # # Generate formatted SQL from the JSON analysis
        # render_oracle_sql_from_analysis()
       
        # step2_duration = time.time() - step2_start
        # info("✓ SQL formatting complete! (Duration: %.2f seconds)", step2_duration)
        # debug(f"Step 2 completed in {step2_duration:.2f} seconds")


        # # Step 3: Clean JSON files
        # # -----------------------
        # info("Step 3: Cleaning JSON files...")
        # debug("Starting Step 3: Cleaning and optimizing JSON files")
        # step3_start = time.time()
       
        # # Remove line numbers and other metadata from JSON files
        # clean_json_files()
       
        # step3_duration = time.time() - step3_start
        # info("✓ JSON cleaning complete! (Duration: %.2f seconds)", step3_duration)
        # debug(f"Step 3 completed in {step3_duration:.2f} seconds")


        # # Step 5: Convert JSON to PL/JSON
        # # ------------------------------
        # info("Step 5: Converting JSON to PL/JSON...")
        # debug("Starting Step 5: JSON → PostgreSQL-compatible PL/JSON")
        # step5_start = time.time()
       
        # # Transform JSON to operation-specific structure for PostgreSQL
        # read_json_to_oracle_triggers()
       
        # step5_duration = time.time() - step5_start
        # info("✓ PL/JSON conversion complete! (Duration: %.2f seconds)", step5_duration)
        # debug(f"Step 5 completed in {step5_duration:.2f} seconds")


        # # Step 6: Convert PL/JSON to PostgreSQL format
        # # ------------------------------------------
        # info("Step 6: Converting PL/JSON to PostgreSQL format...")
        # debug("Starting Step 6: PL/JSON → PostgreSQL format JSON")
        # step6_start = time.time()
       
        # # Convert PL/JSON to PostgreSQL trigger structure
        # read_json_to_postsql_triggers()
       
        # step6_duration = time.time() - step6_start
        # info("✓ PostgreSQL format conversion complete! (Duration: %.2f seconds)", step6_duration)
        # debug(f"Step 6 completed in {step6_duration:.2f} seconds")


        # # Step 7: Convert JSON analysis directly to PostgreSQL SQL
        # # ------------------------------------------------------
        # info("Step 7: Converting JSON analysis directly to PostgreSQL SQL...")
        # debug("Starting Step 7: JSON analysis → PostgreSQL SQL")
        # step7_start = time.time()
       
        # # Convert JSON analysis directly to PostgreSQL SQL
        # convert_json_analysis_to_postgresql_sql()
       
        # step7_duration = time.time() - step7_start
        # info("✓ Direct PostgreSQL SQL conversion complete! (Duration: %.2f seconds)", step7_duration)
        # debug(f"Step 7 completed in {step7_duration:.2f} seconds")


        # # Step 8: Generate final PostgreSQL SQL files
        # # -----------------------------------------
        # info("Step 8: Converting PostgreSQL format JSON to final SQL...")
        # debug("Starting Step 8: PostgreSQL JSON → SQL output files")
        # step8_start = time.time()
       
        # # Generate the final PostgreSQL SQL files
        # convert_postgresql_format_files_to_sql()
       
        # step8_duration = time.time() - step8_start
        # info("✓ Final SQL generation complete! (Duration: %.2f seconds)", step8_duration)
        # debug(f"Step 8 completed in {step8_duration:.2f} seconds")


        # # Final summary
        # # ------------
        # total_duration = time.time() - start_time
        # info("=== Batch conversion finished successfully ===")
        # info("Total execution time: %.2f seconds", total_duration)
       
        # # Detailed performance breakdown
        # info("Performance breakdown by step:")
        # info("  - Step 1 (SQL → JSON):              %.2f seconds (%.1f%%)", step1_duration, step1_duration/total_duration*100)
        # info("  - Step 2 (JSON → Oracle SQL):       %.2f seconds (%.1f%%)", step2_duration, step2_duration/total_duration*100)
        # info("  - Step 3 (JSON cleaning):           %.2f seconds (%.1f%%)", step3_duration, step3_duration/total_duration*100)
        # # info("  - Step 4 (Validation):              %.2f seconds (%.1f%%)", step4_duration, step4_duration/total_duration*100)
        # info("  - Step 5 (JSON → PL/JSON):          %.2f seconds (%.1f%%)", step5_duration, step5_duration/total_duration*100)
        # info("  - Step 6 (PL/JSON → PostgreSQL):    %.2f seconds (%.1f%%)", step6_duration, step6_duration/total_duration*100)
        # info("  - Step 7 (JSON → PostgreSQL SQL):   %.2f seconds (%.1f%%)", step7_duration, step7_duration/total_duration*100)
        # info("  - Step 8 (PostgreSQL JSON → SQL):   %.2f seconds (%.1f%%)", step8_duration, step8_duration/total_duration*100)
       
        # debug("Main conversion workflow completed successfully")


    except KeyboardInterrupt:
        critical("Process interrupted by user")
        debug("Keyboard interrupt received - workflow aborted")
        raise
       
    except Exception as e:
        critical("Fatal error during conversion: %s", str(e))
        critical("Process failed after %.2f seconds", time.time() - start_time)
        debug(f"Fatal error details: {type(e).__name__}: {str(e)}")
        import traceback
        debug(f"Error traceback: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()



