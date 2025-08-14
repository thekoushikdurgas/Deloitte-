import os
import json
import re
import copy
from datetime import datetime

from typing import Any, Dict, List, Tuple, Union
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

class FORMATPostsqlTriggerAnalyzer:
    def __init__(self, json_data):
        self.json_data = json_data

    def to_sql(self) -> str:
        return self.json_data

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
    
    i = 1
    while i <= len(files):
        file_name = files[i-1]
        debug("=== Processing file %d/%d: %s ===", i, len(files), file_name)
        try:
            # Extract trigger number from filename using regex
            match = re.search(r"trigger(\d+)", file_name)
            if not match:
                debug("Filename '%s' does not match expected pattern; skipping", file_name)
                i += 1
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
        i += 1

    info("=== File processing complete ===")
    info("Successfully processed: %d files", processed_count)
    if error_count > 0:
        warning("Failed to process: %d files", error_count)


def json_to_pl_sql_processor(src_path: str, out_path: str, trigger_num: str) -> None:
    """
    Process a JSON analysis file to formatted SQL.
    
    This function:
    1. Reads the JSON analysis file
    2. Creates a FORMATPostsqlTriggerAnalyzer instance
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
    debug("Creating FORMATPostsqlTriggerAnalyzer instance...")
    try:
        analyzer = FORMATPostsqlTriggerAnalyzer(analysis)
        debug("FORMATPostsqlTriggerAnalyzer created successfully")
    except Exception as e:
        error("Failed to create FORMATPostsqlTriggerAnalyzer: %s", str(e))
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
    
    
    
def read_json_to_postsql_triggers() -> None:
    """
    Render formatted PL/SQL for each analysis JSON file.
    
    This function processes all _analysis.json files in the files/format_json directory,
    converting them to formatted SQL files in the files/format_sql directory.
    """
    info("=== Starting JSON to Postsql triggers conversion ===")
    process_files(
        source_dir="files/format_json",
        target_dir="files/format_plsql",
        file_pattern="_analysis.json",
        output_suffix=".sql",
        processor_func=json_to_pl_sql_processor
    )
    info("=== JSON to Postsql triggers conversion complete ===")
    

if __name__ == "__main__":
    # Clean JSON files by removing line_no keys
    read_json_to_postsql_triggers()
    print("JSON cleaning complete!")
    
    # Original functionality (commented out for now)
    # read_json_to_postsql_triggers()
    # print("PostSQL JSON conversion complete!")
