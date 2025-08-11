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

import os
import json
import re
import logging
from typing import Any, Dict, Callable

from utilities.OracleTriggerAnalyzer import OracleTriggerAnalyzer
from utilities.FORMATOracleTriggerAnalyzer import FORMATOracleTriggerAnalyzer
from utilities.common import debug, logger, setup_logging

def ensure_dir(directory: str) -> None:
    """Ensure that the specified directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.debug(f"Created directory: {directory}")


def process_files(source_dir: str, target_dir: str, file_pattern: str, 
                  output_suffix: str, processor_func) -> None:
    """Process files from source_dir to target_dir using the provided processor function."""
    logger.info(f"Processing files from '{source_dir}' to '{target_dir}'")
    
    # Ensure directories exist
    ensure_dir(target_dir)
    
    # Get all matching files from the source directory
    try:
        files = [f for f in os.listdir(source_dir) if f.endswith(file_pattern)]
    except FileNotFoundError:
        logger.error(f"Source directory not found: {source_dir}")
        return
    
    logger.debug(f"Found {len(files)} files matching pattern: {files}")
    
    # Process each file
    for file_name in files:
        logger.debug(f"Processing file: {file_name}")
        try:
            # Extract trigger number from filename using regex
            match = re.search(r"trigger(\d+)", file_name)
            if not match:
                logger.warning(f"Filename '{file_name}' does not match expected pattern; skipping")
                continue
            
            trigger_num = match.group(1)
            logger.debug(f"Extracted trigger number: {trigger_num}")
            
            # Process the file
            src_path = os.path.join(source_dir, file_name)
            output_filename = f"trigger{trigger_num}{output_suffix}"
            out_path = os.path.join(target_dir, output_filename)
            
            # Run the processor function
            processor_func(src_path, out_path, trigger_num)
            
            logger.info(f"Created {output_filename}")
        except Exception as exc:
            logger.error(f"Failed to process {file_name}: {exc}", exc_info=True)


def sql_to_json_processor(src_path: str, out_path: str, _trigger_num: str) -> None:
    """Process a SQL file to JSON analysis."""
    # Read the SQL file content
    with open(src_path, "r", encoding="utf-8") as f:
        sql_content: str = f.read()
    logger.debug(f"Read {len(sql_content)} characters from {src_path}")
    
    # Analyze the SQL content
    analyzer = OracleTriggerAnalyzer(sql_content)
    logger.debug("Generating JSON analysis...")
    json_content: Dict[str, Any] = analyzer.to_json()
    logger.debug(f"Generated JSON with keys: {list(json_content.keys())}")
    
    # Write to JSON file
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2)
    logger.debug(f"Wrote analysis JSON to {out_path}")


def json_to_sql_processor(src_path: str, out_path: str, _trigger_num: str) -> None:
    """Process a JSON analysis file to formatted SQL."""
    # Read the JSON file
    with open(src_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)
    logger.debug(f"Loaded analysis JSON with keys: {list(analysis.keys())}")
    
    # Render the SQL
    analyzer = FORMATOracleTriggerAnalyzer(analysis)
    logger.debug("Rendering SQL...")
    sql_content: str = analyzer.to_sql()
    logger.debug(f"Rendered SQL length: {len(sql_content)} characters")
    
    # Write to SQL file
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(sql_content)
    logger.debug(f"Wrote formatted SQL to {out_path}")


def read_oracle_triggers_to_json() -> None:
    """Convert all Oracle trigger SQL files into analysis JSON files."""
    process_files(
        source_dir="files/oracle",
        target_dir="files/format_json",
        file_pattern=".sql",
        output_suffix="_analysis.json",
        processor_func=sql_to_json_processor
    )


def read_json_to_oracle_triggers() -> None:
    """Render formatted PL/SQL for each analysis JSON file."""
    process_files(
        source_dir="files/format_json",
        target_dir="files/format_sql",
        file_pattern="_analysis.json",
        output_suffix=".sql",
        processor_func=json_to_sql_processor
    )
        
if __name__ == "__main__":
    # Set up logging for the main script
    main_logger, log_path = setup_logging()
    logger.info(f"Starting batch conversion: SQL -> JSON -> SQL (Logging to {log_path})")
    
    read_oracle_triggers_to_json()
    logger.info("JSON conversion complete!")
    
    read_json_to_oracle_triggers()
    logger.info("SQL formatting complete!")
    
    logger.info("Batch conversion finished")