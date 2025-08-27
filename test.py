import json
import os
import time
from typing import Any, Dict
from main import read_oracle_triggers_to_json
from utilities.OracleTriggerAnalyzer import OracleTriggerAnalyzer
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


# def sql_to_json_processor(src_path: str, out_path: str, file_name: str) -> None:
#     """
#     Process a SQL file to JSON analysis.


#     This function:
#     1. Reads the SQL file content
#     2. Creates an OracleTriggerAnalyzer instance
#     3. Generates JSON analysis
#     4. Writes the analysis to the output file


#     Args:
#         src_path (str): Path to the source SQL file
#         out_path (str): Path to the output JSON file
#         file_name (str): Trigger number extracted from filename
#     """

#     with open(src_path, "r", encoding="utf-8") as f:
#         sql_content: str = f.read()
#     analyzer = OracleTriggerAnalyzer(sql_content)
#     json_content: Dict[str, Any] = analyzer.to_json()
#     with open(out_path, "w", encoding="utf-8") as f:
#         json.dump(json_content, f, indent=2)

# def read_oracle_triggers_to_json() -> None:
#     """
#     Read all Oracle trigger files in the 'files/oracle' directory and process them.
#     """
#     for file in os.listdir("files/oracle"):
#         if file.endswith(".sql"):
#             file_name = file.split(".")[0]
#             print(f"Processing file: {file_name}")
#             sql_to_json_processor(f"files/oracle/{file}", f"files/format_json/{file_name}_analysis.json", file_name)

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
    debug("Starting main conversion workflow")


    try:
        # Set up logging for the main script
        info("=== Starting Oracle Trigger Conversion Process ===")
        main_logger, log_path = setup_logging()
        info("Logging to: %s", log_path)
        debug("Logging system initialized")
        read_oracle_triggers_to_json()
    except Exception as e:
        error(f"Error: {e}")


if __name__ == "__main__":
    main()