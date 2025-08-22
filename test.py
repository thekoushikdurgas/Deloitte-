import time
from main import read_oracle_triggers_to_json
from utilities.OracleTriggerAnalyzer import setup_logging
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


        # Step 1: Convert SQL to JSON
        # --------------------------
        info("Step 1: Converting Oracle SQL files to JSON analysis...")
        debug("Starting Step 1: Oracle SQL → JSON conversion")
        # step1_start = time.time()
       
        # Parse Oracle trigger files into structured JSON representation
        read_oracle_triggers_to_json()
    except Exception as e:
        error(f"Error: {e}")


if __name__ == "__main__":
    main()