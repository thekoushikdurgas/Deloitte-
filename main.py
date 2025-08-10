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

Debugging:
- A simple DEBUG flag and helper `debug()` prints detailed progress for each step.
- Try/except blocks ensure errors are reported without stopping the whole batch.
"""

import os
import json
import re
from datetime import datetime
from typing import Any, Dict

from utilities.OracleTriggerAnalyzer import OracleTriggerAnalyzer
from utilities.FORMATOracleTriggerAnalyzer import FORMATOracleTriggerAnalyzer

# Toggle verbose debug logging here
DEBUG: bool = True


def debug(message: str) -> None:
    """Emit a debug message when DEBUG is enabled."""
    if DEBUG:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fname = os.path.basename(__file__)
        print(f"[{now} {fname}] {message}")




def read_oracle_triggers_to_json() -> None:
    """Convert all Oracle trigger SQL files into analysis JSON files."""
    # Define directories
    oracle_dir: str = "files/oracle"
    json_dir: str = "files/format_json"

    debug(f"Preparing to convert SQL from '{oracle_dir}' to JSON in '{json_dir}'")

    # Create output directory if it doesn't exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
        debug(f"Created directory: {json_dir}")

    # Get all SQL files from the oracle directory
    try:
        sql_files = [f for f in os.listdir(oracle_dir) if f.endswith(".sql")]
    except FileNotFoundError:
        print(f"[ERROR main] Source directory not found: {oracle_dir}")
        return

    debug(f"Found {len(sql_files)} SQL files: {sql_files}")

    # Process each SQL file
    for sql_file in sql_files:
        debug(f"Processing file: {sql_file}")
        try:
            # Extract trigger number from filename using regex
            match = re.search(r"trigger(\d+)", sql_file)
            if not match:
                debug("Filename does not match expected 'trigger<N>.sql' pattern; skipping")
                continue
            trigger_num = match.group(1)
            debug(f"Extracted trigger number: {trigger_num}")

            # Read the SQL file content
            src_path = os.path.join(oracle_dir, sql_file)
            with open(src_path, "r", encoding="utf-8") as f:
                sql_content: str = f.read()
            debug(f"Read {len(sql_content)} characters from {src_path}")

            # Analyze the SQL content
            analyzer = OracleTriggerAnalyzer(sql_content)
            debug("Initialized OracleTriggerAnalyzer; generating JSON...")
            json_content: Dict[str, Any] = analyzer.to_json()
            debug(f"Generated JSON keys: {list(json_content.keys())}")

            # Define output filename
            output_filename = f"trigger{trigger_num}_analysis.json"
            out_path = os.path.join(json_dir, output_filename)

            # Write to JSON file
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(json_content, f, indent=2)

            print(f"Created {output_filename}")
            debug(f"Wrote analysis JSON to {out_path}")
        except Exception as exc:
            print(f"[ERROR main] Failed to process {sql_file}: {exc}")
            continue


def read_json_to_oracle_triggers() -> None:
    """Render formatted PL/SQL for each analysis JSON file."""
    # Define directories
    json_dir: str = "files/format_json"
    sql_out_dir: str = "files/format_sql"

    debug(f"Preparing to render SQL from JSON in '{json_dir}' to '{sql_out_dir}'")

    # Ensure directories exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
        debug(f"Created directory: {json_dir}")
    if not os.path.exists(sql_out_dir):
        os.makedirs(sql_out_dir)
        debug(f"Created directory: {sql_out_dir}")

    # Process each analysis JSON file
    try:
        json_files = [f for f in os.listdir(json_dir) if f.endswith("_analysis.json")]
    except FileNotFoundError:
        print(f"[ERROR main] JSON directory not found: {json_dir}")
        return

    debug(f"Found {len(json_files)} analysis JSON files: {json_files}")

    for json_file in json_files:
        debug(f"Rendering SQL for analysis: {json_file}")
        try:
            match = re.search(r"trigger(\d+)_analysis\.json$", json_file)
            if not match:
                debug("Skipping non-trigger analysis file")
                continue
            trigger_num = match.group(1)
            json_path = os.path.join(json_dir, json_file)

            with open(json_path, "r", encoding="utf-8") as f:
                analysis = json.load(f)
            debug(f"Loaded analysis JSON with keys: {list(analysis.keys())}")

            analyzer = FORMATOracleTriggerAnalyzer(analysis)
            debug("Initialized FORMATOracleTriggerAnalyzer; rendering SQL...")
            sql_content: str = analyzer.to_sql()
            debug(f"Rendered SQL length: {len(sql_content)} characters")

            out_filename = f"trigger{trigger_num}.sql"
            out_path = os.path.join(sql_out_dir, out_filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(sql_content)
            print(f"Created {out_filename}")
            debug(f"Wrote formatted SQL to {out_path}")
        except Exception as exc:
            print(f"[ERROR main] Failed to render {json_file}: {exc}")
            continue
        
if __name__ == "__main__":
    debug("Starting batch conversion: SQL -> JSON -> SQL")
    read_oracle_triggers_to_json()
    print("JSON conversion complete!")
    read_json_to_oracle_triggers()
    print("SQL formatting complete!")
    debug("Batch conversion finished")

# if __name__ == "__main__":
#     """
#     Entry point when script is run directly (not imported as module)
    
#     This standard Python idiom ensures that main() only runs when the script
#     is executed directly, not when it's imported by another script.
#     """
#     main() 