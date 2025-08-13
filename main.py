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
    logger,
    setup_logging,
    debug,
    info,
    warning,
    error,
    critical,
    alert,
    log_parsing_start,
    log_parsing_complete,
    log_parsing_error,
    log_structure_found,
    log_nesting_level,
    log_performance,
)

from utilities.OracleTriggerAnalyzer import OracleTriggerAnalyzer
from utilities.FORMATOracleTriggerAnalyzer import FORMATOracleTriggerAnalyzer
from utilities.JSONTOPLJSON import JSONTOPLJSON


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
    """
    Process files from source_dir to target_dir using the provided processor function.
    
    This function:
    1. Ensures the target directory exists
    2. Finds all files matching the pattern in the source directory
    3. Extracts trigger numbers from filenames
    4. Processes each file using the provided processor function
    5. Handles errors gracefully with detailed logging
    
    Args:
        source_dir (str): Source directory containing files to process
        target_dir (str): Target directory for processed files
        file_pattern (str): File extension pattern to match (e.g., ".sql")
        output_suffix (str): Suffix to add to output filenames
        processor_func: Function to process each file (src_path, out_path, trigger_num)
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
    
    for i, file_name in enumerate(files, 1):
        debug("=== Processing file %d/%d: %s ===", i, len(files), file_name)
        try:
            # Extract trigger number from filename using regex
            match = re.search(r"trigger(\d+)", file_name)
            if not match:
                debug("Filename '%s' does not match expected pattern; skipping", file_name)
                continue

            trigger_num = match.group(1)
            debug("Extracted trigger number: %s", trigger_num)

            # Process the file
            src_path = os.path.join(source_dir, file_name)
            output_filename = f"trigger{trigger_num}{output_suffix}"
            out_path = os.path.join(target_dir, output_filename)

            debug("Source path: %s", src_path)
            debug("Output path: %s", out_path)

            # Run the processor function
            processor_func(src_path, out_path, trigger_num)

            info("✓ Created %s", output_filename)
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

    info("=== File processing complete ===")
    info("Successfully processed: %d files", processed_count)
    if error_count > 0:
        warning("Failed to process: %d files", error_count)


def sql_to_json_processor(src_path: str, out_path: str, trigger_num: str) -> None:
    """
    Process a SQL file to JSON analysis.
    
    This function:
    1. Reads the SQL file content
    2. Creates an OracleTriggerAnalyzer instance
    3. Generates JSON analysis
    4. Writes the analysis to the output file
    
    Args:
        src_path (str): Path to the source SQL file
        out_path (str): Path to the output JSON file
        trigger_num (str): Trigger number extracted from filename
    """
    debug("=== SQL to JSON processing for trigger %s ===", trigger_num)
    
    # Step 1: Read the SQL file content
    debug("Reading SQL file: %s", src_path)
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            sql_content: str = f.read()
        debug("Successfully read %d characters from %s", len(sql_content), src_path)
    except UnicodeDecodeError as e:
        error("Unicode decode error reading %s: %s", src_path, str(e))
        raise
    except Exception as e:
        error("Error reading file %s: %s", src_path, str(e))
        raise

    # Step 2: Analyze the SQL content
    debug("Creating OracleTriggerAnalyzer instance...")
    try:
        analyzer = OracleTriggerAnalyzer(sql_content)
        debug("OracleTriggerAnalyzer created successfully")
    except Exception as e:
        error("Failed to create OracleTriggerAnalyzer: %s", str(e))
        raise

    # Step 3: Generate JSON analysis
    debug("Generating JSON analysis...")
    try:
        json_content: Dict[str, Any] = analyzer.to_json()
        debug("JSON analysis generated successfully")
        debug("Generated JSON with keys: %s", list(json_content.keys()))
        
        # Log some statistics about the analysis
        declarations = json_content.get("declarations", {})
        variables = len(declarations.get("variables", []))
        constants = len(declarations.get("constants", []))
        exceptions = len(declarations.get("exceptions", []))
        comments = len(json_content.get("sql_comments", []))
        debug("Analysis statistics: %d vars, %d consts, %d excs, %d comments", 
              variables, constants, exceptions, comments)
        
    except Exception as e:
        error("Failed to generate JSON analysis: %s", str(e))
        raise

    # Step 4: Write to JSON file
    debug("Writing analysis JSON to: %s", out_path)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(json_content, f, indent=2)
        debug("Successfully wrote analysis JSON to %s", out_path)
    except Exception as e:
        error("Failed to write JSON file %s: %s", out_path, str(e))
        raise

    debug("=== SQL to JSON processing complete for trigger %s ===", trigger_num)


def read_oracle_triggers_to_json() -> None:
    """
    Convert all Oracle trigger SQL files into analysis JSON files.
    
    This function processes all .sql files in the files/oracle directory,
    converting them to structured JSON analysis files in the files/format_json directory.
    """
    info("=== Starting Oracle triggers to JSON conversion ===")
    process_files(
        source_dir="files/oracle",
        target_dir="files/format_json",
        file_pattern=".sql",
        output_suffix="_analysis.json",
        processor_func=sql_to_json_processor,
    )
    info("=== Oracle triggers to JSON conversion complete ===")


def json_to_sql_processor(src_path: str, out_path: str, trigger_num: str) -> None:
    """
    Process a JSON analysis file to formatted SQL.
    
    This function:
    1. Reads the JSON analysis file
    2. Creates a FORMATOracleTriggerAnalyzer instance
    3. Renders the SQL content
    4. Writes the formatted SQL to the output file
    
    Args:
        src_path (str): Path to the source JSON analysis file
        out_path (str): Path to the output SQL file
        trigger_num (str): Trigger number extracted from filename
    """
    debug("=== JSON to SQL processing for trigger %s ===", trigger_num)
    
    # Step 1: Read the JSON file
    debug("Reading JSON analysis file: %s", src_path)
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)
        logger.debug(f"Successfully loaded analysis JSON with keys: {list(analysis.keys())}")
    except json.JSONDecodeError as e:
        error("JSON decode error reading %s: %s", src_path, str(e))
        raise
    except Exception as e:
        error("Error reading JSON file %s: %s", src_path, str(e))
        raise
    
    # Step 2: Render the SQL
    debug("Creating FORMATOracleTriggerAnalyzer instance...")
    try:
        analyzer = FORMATOracleTriggerAnalyzer(analysis)
        debug("FORMATOracleTriggerAnalyzer created successfully")
    except Exception as e:
        error("Failed to create FORMATOracleTriggerAnalyzer: %s", str(e))
        raise
    
    # Step 3: Generate SQL content
    debug("Rendering SQL from analysis...")
    try:
        sql_content: str = analyzer.to_sql()
        debug(f"SQL rendering completed successfully")
        debug(f"Rendered SQL length: {len(sql_content)} characters")
    except Exception as e:
        error("Failed to render SQL: %s", str(e))
        raise
    
    # Step 4: Write to SQL file
    debug("Writing formatted SQL to: %s", out_path)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sql_content)
        debug(f"Successfully wrote formatted SQL to {out_path}")
    except Exception as e:
        error("Failed to write SQL file %s: %s", out_path, str(e))
        raise

    debug("=== JSON to SQL processing complete for trigger %s ===", trigger_num)


def read_json_to_oracle_triggers() -> None:
    """
    Render formatted PL/SQL for each analysis JSON file.
    
    This function processes all _analysis.json files in the files/format_json directory,
    converting them to formatted SQL files in the files/format_sql directory.
    """
    info("=== Starting JSON to Oracle triggers conversion ===")
    process_files(
        source_dir="files/format_json",
        target_dir="files/format_sql",
        file_pattern="_analysis.json",
        output_suffix=".sql",
        processor_func=json_to_sql_processor
    )
    info("=== JSON to Oracle triggers conversion complete ===")


def validate_conversion() -> None:
    """
    Validate the conversion by comparing original and converted files.
    
    This function:
    1. Checks that all original files have corresponding converted files
    2. Compares file counts between source and target directories
    3. Reports any missing or mismatched files
    4. Provides detailed validation statistics
    """
    info("=== Starting conversion validation ===")
    
    # Get all original SQL files
    oracle_dir = "files/oracle"
    format_sql_dir = "files/format_sql"
    
    debug("Checking original files in: %s", oracle_dir)
    try:
        original_files = [f for f in os.listdir(oracle_dir) if f.endswith(".sql")]
        debug("Found %d original SQL files", len(original_files))
    except FileNotFoundError:
        error("Oracle directory not found: %s", oracle_dir)
        return
    except PermissionError:
        error("Permission denied accessing oracle directory: %s", oracle_dir)
        return
    
    debug("Checking converted files in: %s", format_sql_dir)
    try:
        converted_files = [f for f in os.listdir(format_sql_dir) if f.endswith(".sql")]
        debug("Found %d converted SQL files", len(converted_files))
    except FileNotFoundError:
        error("Converted SQL directory not found: %s", format_sql_dir)
        return
    except PermissionError:
        error("Permission denied accessing converted SQL directory: %s", format_sql_dir)
        return
    
    info("Validation summary: %d original files and %d converted files", len(original_files), len(converted_files))
    
    # Compare file counts
    if len(original_files) != len(converted_files):
        warning("File count mismatch: %d original vs %d converted", len(original_files), len(converted_files))
    else:
        info("✓ File count validation passed")
    
    # Check each converted file exists
    missing_files = []
    found_files = []
    
    for original_file in original_files:
        trigger_match = re.search(r"trigger(\d+)", original_file)
        if trigger_match:
            trigger_num = trigger_match.group(1)
            expected_converted = f"trigger{trigger_num}.sql"
            if expected_converted not in converted_files:
                warning("Missing converted file for %s: expected %s", original_file, expected_converted)
                missing_files.append(expected_converted)
            else:
                debug("✓ Found converted file: %s", expected_converted)
                found_files.append(expected_converted)
    
    # Report validation results
    if missing_files:
        warning("Missing %d converted files: %s", len(missing_files), missing_files)
    else:
        info("✓ All expected converted files found")
        
    if found_files:
        info("Successfully validated %d converted files", len(found_files))
    
    info("=== Conversion validation complete ===")

def read_json_to_oracle_triggers() -> None:
    # Define directories
    json_dir = "files/format_json"
    sql_out_dir = "files/format_pl_json"

    # Ensure directories exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    if not os.path.exists(sql_out_dir):
        os.makedirs(sql_out_dir)

    # Process each analysis JSON file
    json_files = [f for f in os.listdir(json_dir) if f.endswith("_analysis.json")]

    for json_file in json_files:
        match = re.search(r"trigger(\d+)_analysis\.json$", json_file)
        if not match:
            # Skip non-trigger analysis files
            continue
        trigger_num = match.group(1)
        json_path = os.path.join(json_dir, json_file)
        with open(json_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)

        analyzer = JSONTOPLJSON(analysis)
        sql_content = analyzer.to_sql()

        # Save as JSON with the new structure
        out_filename = f"trigger{trigger_num}.json"
        out_path = os.path.join(sql_out_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sql_content)
        print(f"Created {out_filename}")

def main() -> None:
    """
    Main execution function for the Oracle trigger conversion process.
    
    This function orchestrates the entire conversion workflow:
    1. SQL to JSON conversion
    2. JSON to SQL conversion  
    3. Validation of results
    
    The function includes comprehensive error handling and logging.
    """
    start_time = time.time()
    
    try:
        # Set up logging for the main script
        info("=== Starting Oracle Trigger Conversion Process ===")
        main_logger, log_path = setup_logging()
        info("Logging to: %s", log_path)

        # Step 1: Convert SQL to JSON
        info("Step 1: Converting Oracle SQL files to JSON analysis...")
        step1_start = time.time()
        read_oracle_triggers_to_json()
        step1_duration = time.time() - step1_start
        info("✓ JSON conversion complete! (Duration: %.2f seconds)", step1_duration)
        
        # Step 2: Convert JSON back to SQL
        info("Step 2: Converting JSON analysis back to formatted SQL...")
        step2_start = time.time()
        read_json_to_oracle_triggers()
        step2_duration = time.time() - step2_start
        info("✓ SQL formatting complete! (Duration: %.2f seconds)", step2_duration)
        
        # Step 3: Validate conversion
        info("Step 3: Validating conversion results...")
        step3_start = time.time()
        validate_conversion()
        step3_duration = time.time() - step3_start
        info("✓ Validation complete! (Duration: %.2f seconds)", step3_duration)

        # Step 4: Convert JSON to PL/JSON
        info("Step 4: Converting JSON to PL/JSON...")
        step4_start = time.time()
        read_json_to_oracle_triggers()
        step4_duration = time.time() - step4_start
        info("✓ PL/JSON conversion complete! (Duration: %.2f seconds)", step4_duration)
        
        # Final summary
        total_duration = time.time() - start_time
        info("=== Batch conversion finished successfully ===")
        info("Total execution time: %.2f seconds", total_duration)
        info("Step breakdown:")
        info("  - SQL to JSON: %.2f seconds", step1_duration)
        info("  - JSON to SQL: %.2f seconds", step2_duration)
        info("  - Validation: %.2f seconds", step3_duration)
        
    except KeyboardInterrupt:
        critical("Process interrupted by user")
        raise
    except Exception as e:
        critical("Fatal error during conversion: %s", str(e))
        critical("Process failed after %.2f seconds", time.time() - start_time)
        raise


if __name__ == "__main__":
    main()