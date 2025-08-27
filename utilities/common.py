import json
import os
import logging
import time
from datetime import datetime
from typing import Optional, Any, Tuple, Dict, List, Union
from pathlib import Path
from contextlib import contextmanager


# Custom exceptions for better error handling
class OracleAnalysisError(Exception):
    """Base exception for Oracle trigger analysis errors."""
    pass


class ParseError(OracleAnalysisError):
    """Exception raised when parsing SQL content fails."""
    pass


class ValidationError(OracleAnalysisError):
    """Exception raised when data validation fails."""
    pass


class ConversionError(OracleAnalysisError):
    """Exception raised when conversion between formats fails."""
    pass


class FileOperationError(OracleAnalysisError):
    """Exception raised when file operations fail."""
    pass


"""
Common utilities module for the Oracle to PostgreSQL converter.


This module provides:
1. Logging infrastructure with various log levels and specialized logging functions
2. JSON cleaning utilities to remove unnecessary metadata
3. Shared utility functions used across the application


The logging system is designed to output both to console (for immediate visibility)
and to timestamped log files (for later analysis and debugging).
"""


# Configure logging system
def setup_logging(log_dir="output", log_level="INFO"):
    """
    Set up logging configuration to output to both console and file.
   
    Args:
        log_dir (str): Directory to store log files
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   
    Returns:
        tuple: (logger, log_file_path)
    """
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
   
    # Create a timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"oracle_conversion_{timestamp}.log")
   
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture all levels
   
    # Clear any existing handlers (in case setup_logging is called multiple times)
    if logger.hasHandlers():
        logger.handlers.clear()
    # logger.handlers.clear()
    # Create formatters with more detailed information
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
   
    # Create file handler for all log messages
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
   
    # Create console handler with configurable log level
    console_handler = logging.StreamHandler()
    console_level = getattr(logging, log_level.upper(), logging.INFO)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
   
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
   
    return logger, log_file


# Global logger instance
logger, log_file = setup_logging()


# For backward compatibility with existing code
DEBUG_ANALYZER = True


def debug(msg: str, *args, **kwargs) -> None:
    """
    Write a debug-level log message through the configured logging system.
   
    This function is a wrapper around logger.debug() that respects the DEBUG_ANALYZER
    flag for backward compatibility. Debug messages provide detailed information
    useful during development and troubleshooting but not needed for normal operation.
   
    Args:
        msg (str): The message format string
        *args: Variable arguments to be formatted into the message string
        **kwargs: Keyword arguments passed to the underlying logger
       
    Example:
        >>> debug("Processing item %d: %s", item_id, item_name)
        >>> debug("Found %d matches in file %s", len(matches), filename)
    """
    if DEBUG_ANALYZER:
        logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """Info level logging."""
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """Warning level logging."""
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """Error level logging."""
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """Critical level logging."""
    logger.critical(msg, *args, **kwargs)


def alert(msg: str, *args, **kwargs) -> None:
    """Alert level logging (same as critical)."""
    logger.critical(f"🚨 ALERT: {msg}", *args, **kwargs)


# # Custom specialized logging functions for better categorization and readability
# def log_parsing_start(component: str, details: Optional[str] = None) -> None:
#     """
#     Log the start of a parsing operation with standardized formatting.
   
#     This function creates an INFO-level log entry specifically for the beginning
#     of a parsing phase, with consistent formatting and a spinner emoji.
   
#     Args:
#         component (str): The name of the component or phase being parsed
#         details (Optional[str]): Additional details about the parsing operation
   
#     Example:
#         >>> log_parsing_start("SQL declaration", "processing variables and constants")
#         [INFO] 🔄 Starting SQL declaration parsing: processing variables and constants
#     """
#     msg = f"Starting {component} parsing"
#     if details:
#         msg += f": {details}"
#     logger.info(f"🔄 {msg}")


# def log_parsing_complete(component: str, details: Optional[str] = None) -> None:
#     """
#     Log the successful completion of a parsing operation.
   
#     This function creates an INFO-level log entry for the successful completion
#     of a parsing phase, with consistent formatting and a checkmark emoji.
   
#     Args:
#         component (str): The name of the component or phase that was parsed
#         details (Optional[str]): Additional details or statistics about the parsing results
   
#     Example:
#         >>> log_parsing_complete("SQL declaration", "processed 15 variables and 3 constants")
#         [INFO] ✅ Completed SQL declaration parsing: processed 15 variables and 3 constants
#     """
#     msg = f"Completed {component} parsing"
#     if details:
#         msg += f": {details}"
#     logger.info(f"✅ {msg}")


# def log_parsing_error(component: str, error_msg: str, line_no: Optional[int] = None) -> None:
#     """
#     Log an error that occurred during parsing with context information.
   
#     This function creates an ERROR-level log entry for parsing failures,
#     with an X emoji and optional line number reference for easier debugging.
   
#     Args:
#         component (str): The component or phase where the error occurred
#         error_msg (str): The error message or description
#         line_no (Optional[int]): The line number where the error occurred, if applicable
   
#     Example:
#         >>> log_parsing_error("variable declaration", "invalid data type", 45)
#         [ERROR] ❌ Error in variable declaration: invalid data type (line 45)
#     """
#     msg = f"Error in {component}: {error_msg}"
#     if line_no:
#         msg += f" (line {line_no})"
#     logger.error(f"❌ {msg}")


# def log_structure_found(structure_type: str, line_no: int, details: Optional[str] = None) -> None:
#     """
#     Log the discovery of a code structure during parsing.
   
#     This function creates a DEBUG-level log entry when a specific code structure
#     (like an IF statement, loop, etc.) is found during parsing, with a magnifying
#     glass emoji for visual distinction.
   
#     Args:
#         structure_type (str): The type of structure found (e.g., "if_else", "begin_end")
#         line_no (int): The line number where the structure starts
#         details (Optional[str]): Additional details about the structure
   
#     Example:
#         >>> log_structure_found("if_else", 120, "with 2 ELSIF clauses")
#         [DEBUG] 🔍 Found if_else at line 120: with 2 ELSIF clauses
#     """
#     msg = f"Found {structure_type} at line {line_no}"
#     if details:
#         msg += f": {details}"
#     logger.debug(f"🔍 {msg}")


# def log_nesting_level(level: int, context: str) -> None:
#     """
#     Log information about the current nesting level during parsing.
   
#     This function creates a DEBUG-level log entry showing the current nesting
#     level of code structures, with visual indentation and a chart emoji.
   
#     Args:
#         level (int): The current nesting level (0 = top level)
#         context (str): Description of the context or structure being nested
   
#     Example:
#         >>> log_nesting_level(2, "if_statement inside begin_end")
#         [DEBUG] 📊   Nesting level 2 in if_statement inside begin_end
#     """
#     indent = "  " * level
#     logger.debug(f"📊 {indent}Nesting level {level} in {context}")


# def log_performance(operation: str, duration: float) -> None:
#     """
#     Log performance metrics for an operation.
   
#     This function creates a DEBUG-level log entry with timing information
#     for performance analysis, with a stopwatch emoji for visual distinction.
   
#     Args:
#         operation (str): Name of the operation that was timed
#         duration (float): Duration of the operation in seconds
   
#     Example:
#         >>> log_performance("SQL parsing", 0.352)
#         [DEBUG] ⏱️ SQL parsing completed in 0.352s
#     """
#     logger.debug(f"⏱️ {operation} completed in {duration:.3f}s")


def clean_json_remove_line_no(data: Any) -> Any:
    """
    Recursively remove all keys containing 'line_no' from a JSON data structure.
   
    This function traverses a complex nested JSON structure and removes any dictionary
    keys that contain the string 'line_no' (case insensitive). It works recursively
    through dictionaries and lists, preserving the original structure but excluding
    the line number metadata.
   
    Line number information is useful during development and debugging but is not needed
    in the final output JSON, making the files cleaner and smaller.
   
    Args:
        data (Any): The JSON data structure to clean (can be a dict, list, or primitive value)
       
    Returns:
        Any: A new copy of the data structure with line_no keys removed
       
    Example:
        >>> data = {"name": "func1", "line_no": 42, "params": [{"name": "p1", "line_no": 43}]}
        >>> clean_json_remove_line_no(data)
        {"name": "func1", "params": [{"name": "p1"}]}
    """
    # Process dictionary objects
    if isinstance(data, dict):
        # Create a new dict without keys containing 'line_no'
        cleaned_dict = {}
        for key, value in data.items():
            # Skip keys containing 'line_no' (case insensitive)
            if 'line_no' not in key.lower():
                # Recursively clean the value
                cleaned_dict[key] = clean_json_remove_line_no(value)
        return cleaned_dict
       
    # Process list objects
    elif isinstance(data, list):
        # Process each item in the list recursively
        return [clean_json_remove_line_no(item) for item in data]
       
    # Return primitive values as-is (strings, numbers, booleans, None)
    else:
        return data




def clean_json_files() -> None:
    """
    Clean JSON files by removing line_no keys and save in the same folder.
   
    This function:
    1. Scans the format_json directory for JSON files
    2. Loads each JSON file and removes all keys containing 'line_no'
    3. Saves the cleaned JSON data back to the same file
    4. Logs the progress and any errors encountered
   
    Line number information is useful during analysis but not needed in the final output,
    removing it makes the JSON files smaller and cleaner.
    """
    # Define directory
    json_dir = "files/format_json"
   
    debug(f"Starting JSON cleaning process in directory: {json_dir}")
   
    # Ensure directory exists
    if not os.path.exists(json_dir):
        error(f"Directory {json_dir} does not exist!")
        return


    # Process all JSON files in the directory
    json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
    debug(f"Found {len(json_files)} JSON files to clean")


    cleaned_count = 0
    error_count = 0
   
    for json_file in json_files:
        json_path = os.path.join(json_dir, json_file)
        debug(f"Processing file: {json_file}")
       
        try:
            # Read the JSON file
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
                debug(f"Successfully loaded JSON data ({len(str(json_data))} bytes)")
            if "error" in json_data:
                debug(f"Skipping file {json_file} due to existing 'error' key")
                continue
            # Clean the JSON data by removing line_no keys
            start_time = time.time()
            cleaned_data = clean_json_remove_line_no(json_data)
            duration = time.time() - start_time
            debug(f"Cleaned JSON data in {duration:.3f} seconds")
           
            # Save the cleaned JSON back to the same file
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
           
            logger.debug(f"✅ Cleaned {json_file}")
            cleaned_count += 1
           
        except json.JSONDecodeError as e:
            error(f"❌ JSON parsing error in {json_file}: {str(e)}")
            error_count += 1
        except IOError as e:
            error(f"❌ I/O error processing {json_file}: {str(e)}")
            error_count += 1
        except Exception as e:
            error(f"❌ Unexpected error processing {json_file}: {str(e)}")
            error_count += 1
   
    # Final summary
    info(f"JSON cleaning complete: {cleaned_count} files cleaned, {error_count} errors")
           





