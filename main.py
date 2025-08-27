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
from utilities.FORMATOracleTriggerAnalyzer import FORMATOracleTriggerAnalyzer
from utilities.JSONTOPLJSON import JSONTOPLJSON
from utilities.FORMATPostsqlTriggerAnalyzer import FORMATPostsqlTriggerAnalyzer


from datetime import datetime


# Directory constants
FORMAT_JSON_DIR = "files/format_json"


# File suffix constants
ANALYSIS_JSON_SUFFIX = "_analysis.json"


def convert_complex_structure_to_sql(complex_structure):
    """
    Convert the complex PL/JSON structure to a proper PostgreSQL SQL string.


    Args:
        complex_structure: The complex structure from PL/JSON


    Returns:
        str: The PostgreSQL SQL string
    """
    analyzer = FORMATPostsqlTriggerAnalyzer(complex_structure)
    sql_content = analyzer.to_sql()
    return sql_content
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
    if error_count > 0:
        warning("Failed to process: %d files", error_count)


def sql_to_json_processor(src_path: str, out_path: str, file_name: str) -> None:
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
        file_name (str): Trigger number extracted from filename
    """

    # with open(src_path, "r", encoding="utf-8") as f:
    #     sql_content: str = f.read()
    # analyzer = OracleTriggerAnalyzer(sql_content)
    # json_content: Dict[str, Any] = analyzer.to_json()
    # with open(out_path, "w", encoding="utf-8") as f:
    #     json.dump(json_content, f, indent=2)
    debug("=== SQL to JSON processing for trigger %s ===", file_name)
    # Step 1: Read the SQL file content
    # info("Reading SQL file: %s", src_path)
    print(f"Reading SQL file: {src_path}")
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
        debug(
            "Analysis statistics: %d vars, %d consts, %d excs, %d comments",
            variables,
            constants,
            exceptions,
            comments,
        )


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


    debug("=== SQL to JSON processing complete for trigger %s ===", file_name)


def read_oracle_triggers_to_json() -> None:
    """
    Convert all Oracle trigger SQL files into analysis JSON files.


    This function processes all .sql files in the files/oracle directory,
    converting them to structured JSON analysis files in the files/format_json directory.
   
    The conversion workflow:
    1. Locate all Oracle SQL trigger files in the source directory
    2. For each file, extract the trigger number from the filename
    3. Parse the SQL content using OracleTriggerAnalyzer
    4. Save the resulting structured JSON to the target directory
    """
    info("=== Starting Oracle triggers to JSON conversion ===")
    debug("Workflow Phase 1: Convert Oracle SQL files to JSON analysis structure")
    debug("Source directory: files/oracle")
    debug("Target directory: %s", FORMAT_JSON_DIR)
   
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
    debug("Phase 1 complete: Oracle SQL files converted to JSON analysis structure")


def json_to_sql_processor(src_path: str, out_path: str, file_name: str) -> None:
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
    if "error" not in analysis:
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
            debug("SQL rendering completed successfully")
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
    process_files(
        source_dir=FORMAT_JSON_DIR,
        target_dir="files/format_sql",
        file_pattern=ANALYSIS_JSON_SUFFIX,
        output_suffix=".sql",
        processor_func=json_to_sql_processor,
    )
    info("=== JSON analysis to formatted Oracle SQL conversion complete ===")


# def validate_conversion() -> None:
#     """
#     Validate the conversion by comparing original and converted files.


#     This function:
#     1. Checks that all original files have corresponding converted files
#     2. Compares file counts between source and target directories
#     3. Reports any missing or mismatched files
#     4. Provides detailed validation statistics
#     """
#     info("=== Starting conversion validation ===")


#     # Get all original SQL files
#     oracle_dir = "files/oracle"
#     format_sql_dir = "files/format_sql"


#     debug("Checking original files in: %s", oracle_dir)
#     try:
#         original_files = [f for f in os.listdir(oracle_dir) if f.endswith(".sql")]
#         debug("Found %d original SQL files", len(original_files))
#     except FileNotFoundError:
#         error("Oracle directory not found: %s", oracle_dir)
#         return
#     except PermissionError:
#         error("Permission denied accessing oracle directory: %s", oracle_dir)
#         return


#     debug("Checking converted files in: %s", format_sql_dir)
#     try:
#         converted_files = [f for f in os.listdir(format_sql_dir) if f.endswith(".sql")]
#         debug("Found %d converted SQL files", len(converted_files))
#     except FileNotFoundError:
#         error("Converted SQL directory not found: %s", format_sql_dir)
#         return
#     except PermissionError:
#         error("Permission denied accessing converted SQL directory: %s", format_sql_dir)
#         return


#     info(
#         "Validation summary: %d original files and %d converted files",
#         len(original_files),
#         len(converted_files),
#     )


#     # Compare file counts
#     if len(original_files) != len(converted_files):
#         warning(
#             "File count mismatch: %d original vs %d converted",
#             len(original_files),
#             len(converted_files),
#         )
#     else:
#         info("✓ File count validation passed")


#     # Check each converted file exists
#     missing_files = []
#     found_files = []


#     i = 0
#     while i < len(original_files):
#         original_file = original_files[i]
#         trigger_match = re.search(r"trigger(\d+)", original_file)
#         if trigger_match:
#             trigger_num = trigger_match.group(1)
#             expected_converted = f"trigger{trigger_num}.sql"
#             if expected_converted not in converted_files:
#                 warning(
#                     "Missing converted file for %s: expected %s",
#                     original_file,
#                     expected_converted,
#                 )
#                 missing_files.append(expected_converted)
#             else:
#                 debug("✓ Found converted file: %s", expected_converted)
#                 found_files.append(expected_converted)
#         i += 1


#     # Report validation results
#     if missing_files:
#         warning("Missing %d converted files: %s", len(missing_files), missing_files)
#     else:
#         info("✓ All expected converted files found")


#     if found_files:
#         info("Successfully validated %d converted files", len(found_files))


#     info("=== Conversion validation complete ===")


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
    Process a JSON analysis file to formatted SQL.


    This function:
    1. Reads the JSON analysis file
    2. Creates a FORMATPostsqlTriggerAnalyzer instance
    3. Renders the SQL content
    4. Writes the formatted SQL to the output file


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
        error(f"JSON decode error reading {src_path}: {str(e)}")
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
        debug("SQL rendering completed successfully")
        debug("Rendered SQL length: {len(sql_content)} characters")
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


    debug("=== JSON to SQL processing complete for trigger %s ===", file_name)


def read_json_to_postsql_triggers() -> None:
    """
    Convert PL/JSON files to PostgreSQL format.


    This function processes all .json files in the files/format_pl_json directory,
    converting them to PostgreSQL format files in the files/format_plsql directory.
    """
    info("=== Starting PL/JSON to PostgreSQL format conversion ===")
    process_files(
        source_dir="files/format_pl_json",
        target_dir="files/format_plsql",
        file_pattern=".json",
        output_suffix="_postgresql.json",
        processor_func=convert_pl_json_to_postgresql_format,
    )
    info("=== PL/JSON to PostgreSQL format conversion complete ===")


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
                postgresql_format["on_insert"].append({"type": "sql", "sql": sql_content})


            # Handle on_update
            if "on_update" in pl_json_data and pl_json_data["on_update"]:
                sql_content = convert_complex_structure_to_sql(pl_json_data["on_update"])
                postgresql_format["on_update"].append({"type": "sql", "sql": sql_content})


            # Handle on_delete
            if "on_delete" in pl_json_data and pl_json_data["on_delete"]:
                sql_content = convert_complex_structure_to_sql(pl_json_data["on_delete"])
                postgresql_format["on_delete"].append({"type": "sql", "sql": sql_content})


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
        source_dir="files/format_plsql",
        target_dir="files/format_plsql",
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
        main_logger, log_path = setup_logging()
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


        # if check_errors_in_json():
        #     error("Errors found in JSON files, skipping conversion")
        #     return

        # Step 2: Convert JSON back to SQL
        # -------------------------------
        info("Step 2: Converting JSON analysis back to formatted SQL...")
        debug("Starting Step 2: JSON analysis → formatted Oracle SQL")
        step2_start = time.time()
       
        # Generate formatted SQL from the JSON analysis
        render_oracle_sql_from_analysis()
       
        step2_duration = time.time() - step2_start
        info("✓ SQL formatting complete! (Duration: %.2f seconds)", step2_duration)
        debug(f"Step 2 completed in {step2_duration:.2f} seconds")


        # Step 3: Clean JSON files
        # -----------------------
        info("Step 3: Cleaning JSON files...")
        debug("Starting Step 3: Cleaning and optimizing JSON files")
        step3_start = time.time()
       
        # Remove line numbers and other metadata from JSON files
        clean_json_files()
       
        step3_duration = time.time() - step3_start
        info("✓ JSON cleaning complete! (Duration: %.2f seconds)", step3_duration)
        debug(f"Step 3 completed in {step3_duration:.2f} seconds")


        # # Step 4: Validate conversion results
        # # ---------------------------------
        # info("Step 4: Validating conversion results...")
        # debug("Starting Step 4: Validating conversion completeness")
        # step4_start = time.time()
       
        # # Check that all files were converted successfully
        # # validate_conversion()
       
        # step4_duration = time.time() - step4_start
        # info("✓ Validation complete! (Duration: %.2f seconds)", step4_duration)
        # debug(f"Step 4 completed in {step4_duration:.2f} seconds")


        # Step 5: Convert JSON to PL/JSON
        # ------------------------------
        info("Step 5: Converting JSON to PL/JSON...")
        debug("Starting Step 5: JSON → PostgreSQL-compatible PL/JSON")
        step5_start = time.time()
       
        # Transform JSON to operation-specific structure for PostgreSQL
        read_json_to_oracle_triggers()
       
        step5_duration = time.time() - step5_start
        info("✓ PL/JSON conversion complete! (Duration: %.2f seconds)", step5_duration)
        debug(f"Step 5 completed in {step5_duration:.2f} seconds")


        # Step 6: Convert PL/JSON to PostgreSQL format
        # ------------------------------------------
        info("Step 6: Converting PL/JSON to PostgreSQL format...")
        debug("Starting Step 6: PL/JSON → PostgreSQL format JSON")
        step6_start = time.time()
       
        # Convert PL/JSON to PostgreSQL trigger structure
        read_json_to_postsql_triggers()
       
        step6_duration = time.time() - step6_start
        info("✓ PostgreSQL format conversion complete! (Duration: %.2f seconds)", step6_duration)
        debug(f"Step 6 completed in {step6_duration:.2f} seconds")


        # Step 7: Generate final PostgreSQL SQL files
        # -----------------------------------------
        info("Step 7: Converting PostgreSQL format JSON to final SQL...")
        debug("Starting Step 7: PostgreSQL JSON → SQL output files")
        step7_start = time.time()
       
        # Generate the final PostgreSQL SQL files
        convert_postgresql_format_files_to_sql()
       
        step7_duration = time.time() - step7_start
        info("✓ Final SQL generation complete! (Duration: %.2f seconds)", step7_duration)
        debug(f"Step 7 completed in {step7_duration:.2f} seconds")


        # Final summary
        # ------------
        total_duration = time.time() - start_time
        info("=== Batch conversion finished successfully ===")
        info("Total execution time: %.2f seconds", total_duration)
       
        # Detailed performance breakdown
        info("Performance breakdown by step:")
        info("  - Step 1 (SQL → JSON):              %.2f seconds (%.1f%%)", step1_duration, step1_duration/total_duration*100)
        info("  - Step 2 (JSON → Oracle SQL):       %.2f seconds (%.1f%%)", step2_duration, step2_duration/total_duration*100)
        info("  - Step 3 (JSON cleaning):           %.2f seconds (%.1f%%)", step3_duration, step3_duration/total_duration*100)
        # info("  - Step 4 (Validation):              %.2f seconds (%.1f%%)", step4_duration, step4_duration/total_duration*100)
        info("  - Step 5 (JSON → PL/JSON):          %.2f seconds (%.1f%%)", step5_duration, step5_duration/total_duration*100)
        info("  - Step 6 (PL/JSON → PostgreSQL):    %.2f seconds (%.1f%%)", step6_duration, step6_duration/total_duration*100)
        info("  - Step 7 (PostgreSQL JSON → SQL):   %.2f seconds (%.1f%%)", step7_duration, step7_duration/total_duration*100)
       
        debug("Main conversion workflow completed successfully")


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



