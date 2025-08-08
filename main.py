#!/usr/bin/env python3

import os
import json
import re

from utilities import OracleTriggerAnalyzer
from utilities import FORMATOracleTriggerAnalyzer




def read_oracle_triggers_to_json():
    # Define directories
    oracle_dir = "files/oracle"
    json_dir = "files/format_json"

    # Create output directory if it doesn't exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    # Get all SQL files from the oracle directory
    sql_files = [f for f in os.listdir(oracle_dir) if f.endswith(".sql")]

    # Process each SQL file
    for sql_file in sql_files:
        # Extract trigger number from filename using regex
        match = re.search(r"trigger(\d+)", sql_file)
        if match:
            trigger_num = match.group(1)

            # Read the SQL file content
            with open(os.path.join(oracle_dir, sql_file), "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Analyze the SQL content
            analyzer = OracleTriggerAnalyzer(sql_content)
            json_content = analyzer.to_json()

            # Define output filename
            output_filename = f"trigger{trigger_num}_analysis.json"

            # Write to JSON file
            with open(
                os.path.join(json_dir, output_filename), "w", encoding="utf-8"
            ) as f:
                json.dump(json_content, f, indent=2)

            print(f"Created {output_filename}")


def read_json_to_oracle_triggers() -> None:
    # Define directories
    json_dir = "files/format_json"
    sql_out_dir = "files/format_sql"

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

        analyzer = FORMATOracleTriggerAnalyzer(analysis)
        sql_content = analyzer.to_sql()

        out_filename = f"trigger{trigger_num}.sql"
        out_path = os.path.join(sql_out_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sql_content)
        print(f"Created {out_filename}")
        
if __name__ == "__main__":
    read_oracle_triggers_to_json()
    print("JSON conversion complete!")
    read_json_to_oracle_triggers()
    print("SQL formatting complete!")

# if __name__ == "__main__":
#     """
#     Entry point when script is run directly (not imported as module)
    
#     This standard Python idiom ensures that main() only runs when the script
#     is executed directly, not when it's imported by another script.
#     """
#     main() 