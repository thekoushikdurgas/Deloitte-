#!/usr/bin/env python3
"""
Configuration, Constants, and Data Classes for Oracle to PostgreSQL Trigger Converter

This module contains all the configuration settings, enumerations, and data classes
used throughout the converter application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, Callable
import re

# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

class Config:
    """
    Central configuration for the converter
    
    Contains all default values and limits used throughout the application.
    Centralized configuration makes it easy to modify behavior without 
    hunting through code.
    """
    # Default folder names for input and output
    DEFAULT_ORACLE_FOLDER = 'orcale'      # Where Oracle SQL trigger files are stored
    DEFAULT_JSON_FOLDER = 'json'          # Where PostgreSQL JSON output files go
    DEFAULT_EXCEL_FILE = 'oracle_postgresql_mappings.xlsx'  # Mapping configuration file
    
    # Processing limits and batch sizes
    BATCH_SIZE = 100                      # Number of files to process in one batch
    MAX_FILE_SIZE = 10 * 1024 * 1024     # 10MB file size limit to prevent memory issues


# =============================================================================
# ENUMERATIONS
# =============================================================================

class TriggerOperation(Enum):
    """
    Enum for trigger operations
    
    Defines the three types of database trigger operations that can be converted.
    Using an enum ensures type safety and prevents typos in operation names.
    """
    INSERT = "on_insert"    # Triggered when new records are inserted
    UPDATE = "on_update"    # Triggered when existing records are modified  
    DELETE = "on_delete"    # Triggered when records are removed


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ConversionResult:
    """
    Result of a conversion operation
    
    This data class provides a structured way to return conversion results,
    making it easy to handle both success and error cases consistently.
    
    Attributes:
        success: Whether the conversion completed successfully
        input_file: Path to the source Oracle SQL file
        output_file: Path to the generated PostgreSQL JSON file
        sections_converted: List of trigger sections that were converted
        error_message: Error details if conversion failed
        variables_count: Number of variables extracted from the trigger
    """
    success: bool                          # True if conversion succeeded, False otherwise
    input_file: str                        # Source file path that was processed
    output_file: str                       # Destination file path for output
    sections_converted: List[str]          # Which trigger sections were found and converted
    error_message: Optional[str] = None    # Error message if something went wrong
    variables_count: int = 0               # Count of variables extracted from DECLARE section


@dataclass
class RegexPattern:
    """
    Container for regex patterns with their replacements
    
    Attributes:
        pattern: The regex pattern to match in Oracle SQL
        replacement: Either a string replacement or a callable function for complex replacements
        flags: Regex flags (default: case insensitive)
        description: Human-readable description of what this pattern does
    """
    pattern: str  # The regex pattern to search for
    replacement: Union[str, Callable]  # Either string replacement or function for complex logic
    flags: int = re.IGNORECASE  # Regex flags - default to case insensitive matching
    description: str = ""  # Description of what this transformation does


# =============================================================================
# DEPENDENCY CHECK
# =============================================================================

try:
    import pandas as pd
    from openpyxl import load_workbook, Workbook
    HAS_EXCEL_SUPPORT = True
except ImportError:
    HAS_EXCEL_SUPPORT = False
    print("⚠️  Excel support not available. Install pandas and openpyxl for full functionality.") 