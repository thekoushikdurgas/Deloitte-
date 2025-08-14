# Oracle to PostgreSQL Converter - Code Documentation

This document provides a detailed explanation of each file's code structure and flow in the Oracle to PostgreSQL trigger converter project.

## 📁 utilities/common.py

### Overview

Core utilities module providing logging infrastructure and JSON cleaning functionality.

### Code Flow Analysis

#### **Lines 1-15: Imports and Module Docstring**

```python
import json, os, logging, time
from datetime import datetime
from typing import Optional, Any, Tuple
```

- **Purpose**: Standard library imports for file operations, logging, and type hints
- **Key**: Sets up foundation for logging system and JSON processing

#### **Lines 17-67: setup_logging() Function**

```python
def setup_logging(log_dir="output", log_level="INFO"):
    # Creates timestamped log files
    # Configures dual output (console + file)
    # Returns logger and log file path
```

- **Purpose**: Centralized logging configuration
- **Key Features**:
  - Timestamped log files in `output/` directory
  - Dual output: console (INFO+) and file (DEBUG+)
  - Detailed formatting with file/line information
  - Handler cleanup for multiple calls

#### **Lines 69-75: Global Logger Setup**

```python
logger, log_file = setup_logging()
DEBUG_ANALYZER = True
```

- **Purpose**: Initialize global logging instance
- **Key**: Backward compatibility flag for debug logging

#### **Lines 77-120: Basic Logging Functions**

```python
def debug(msg: str, *args, **kwargs) -> None:
def info(msg: str, *args, **kwargs) -> None:
def warning(msg: str, *args, **kwargs) -> None:
def error(msg: str, *args, **kwargs) -> None:
def critical(msg: str, *args, **kwargs) -> None:
def alert(msg: str, *args, **kwargs) -> None:
```

- **Purpose**: Wrapper functions for different log levels
- **Key**: Consistent interface with DEBUG_ANALYZER flag support

#### **Lines 122-200: Specialized Logging Functions**

```python
def log_parsing_start(component: str, details: Optional[str] = None) -> None:
def log_parsing_complete(component: str, details: Optional[str] = None) -> None:
def log_parsing_error(component: str, error_msg: str, line_no: Optional[int] = None) -> None:
def log_structure_found(structure_type: str, line_no: int, details: Optional[str] = None) -> None:
def log_nesting_level(level: int, context: str) -> None:
def log_performance(operation: str, duration: float) -> None:
```

- **Purpose**: Domain-specific logging with emojis and structured messages
- **Key Features**:
  - Visual indicators (🔄, ✅, ❌, 🔍, 📊, ⏱️)
  - Context-aware logging for parsing operations
  - Performance tracking capabilities

#### **Lines 202-250: JSON Cleaning Functions**

```python
def clean_json_remove_line_no(data: Any) -> Any:
def clean_json_files() -> None:
```

- **Purpose**: Remove debugging metadata from JSON output
- **Key Features**:
  - Recursive traversal of nested structures
  - Case-insensitive key removal
  - Batch processing of JSON files
  - Error handling and progress reporting

---

## 📁 utilities/FORMATOracleTriggerAnalyzer.py

### Overview

Converts JSON analysis back to formatted Oracle PL/SQL code with proper indentation and structure.

### Code Flow Analysis

#### **Lines 1-25: Imports and Setup**

```python
import psycopg2, json, logging, time
from typing import Dict, List, Any, Union
from utilities.common import (debug, info, warning, error, ...)
```

- **Purpose**: Import dependencies and logging utilities
- **Key**: Type aliases for JSON node handling

#### **Lines 27-50: Class Initialization**

```python
class FORMATOracleTriggerAnalyzer:
    def __init__(self, analysis: Dict[str, Any]):
        self.analysis = analysis
        self.indent_unit = "  "  # 2 spaces
        # Validation of analysis structure
```

- **Purpose**: Initialize analyzer with JSON data
- **Key**: Validates required sections (declarations, main)

#### **Lines 52-100: Main SQL Generation (to_sql())**

```python
def to_sql(self) -> str:
    # Step 1: Header comments with timestamp
    # Step 2: Render declarations section
    # Step 3: Render main execution block
    # Step 4: Footer comments
```

- **Purpose**: Orchestrate entire SQL generation process
- **Key Features**:
  - Performance timing for each section
  - Structured output with proper formatting
  - Comprehensive logging of process

#### **Lines 102-180: Declaration Rendering**

```python
def _render_declarations(self, decl: Dict[str, Any]) -> List[str]:
    # Process variables with data types and defaults
    # Process constants with CONSTANT keyword
    # Process custom exceptions
```

- **Purpose**: Generate DECLARE section of PL/SQL
- **Key**: Handles variables, constants, and exceptions with proper syntax

#### **Lines 182-250: Main Block Rendering**

```python
def _render_main_block(self, node: Dict[str, Any], indent_level: int, wrap_begin_end: bool = False) -> List[str]:
    # Handle begin_end blocks
    # Process exception handlers
    # Manage indentation levels
```

- **Purpose**: Render main execution block with proper structure
- **Key**: Supports nested blocks and exception handling

#### **Lines 252-350: Statement List Processing**

```python
def _render_statement_list(self, statements: List[Dict[str, Any]], indent_level: int) -> List[str]:
    # Handle different statement types:
    # - select_statement, insert_statement, update_statement, delete_statement
    # - assignment_statement, raise_statement
    # - if_else, case_when, for_loop, begin_end
    # - unknown_statement, function_calling
```

- **Purpose**: Process and format individual SQL statements
- **Key**: Type-specific rendering with proper indentation

#### **Lines 352-450: Control Structure Rendering**

```python
def _render_if_else(self, node: Dict[str, Any], indent_level: int) -> List[str]:
def _render_case_when(self, node: Dict[str, Any], indent_level: int) -> List[str]:
def _render_for_loop(self, node: Dict[str, Any], indent_level: int) -> List[str]:
```

- **Purpose**: Render complex control structures
- **Key Features**:
  - IF-ELSIF-ELSE with proper indentation
  - CASE-WHEN (simple and searched)
  - FOR loops with cursor queries

#### **Lines 452-500: Utility Methods**

```python
def _indent(self, text: str, level: int) -> str:
def _indent_lines(self, lines: List[str], level: int) -> List[str]:
```

- **Purpose**: Consistent indentation handling
- **Key**: Deep nesting detection and warning

---

## 📁 utilities/FORMATPostsqlTriggerAnalyzer.py

### Overview

Converts JSON analysis to PostgreSQL-compatible SQL with type mappings and function translations.

### Code Flow Analysis

#### **Lines 1-25: Imports and Setup**

```python
import os, json, re, copy, pandas as pd
from utilities.common import (logger, setup_logging, debug, info, ...)
```

- **Purpose**: Import dependencies including pandas for Excel file handling
- **Key**: Regex support for SQL syntax conversion

#### **Lines 27-60: Class Initialization**

```python
class FORMATPostsqlTriggerAnalyzer:
    def __init__(self, json_data):
        # Load mappings from Excel file
        self.func_mapping = self._load_function_mappings()
        self.type_mapping = self._load_type_mappings()
        self.exception_mapping = self._load_exception_mappings()
```

- **Purpose**: Initialize with configurable mappings
- **Key**: Excel-based configuration for type and function mappings

#### **Lines 62-120: Mapping Loading Functions**

```python
def _load_function_mappings(self) -> Dict[str, str]:
def _load_type_mappings(self) -> Dict[str, str]:
def _load_exception_mappings(self) -> Dict[str, str]:
```

- **Purpose**: Load Oracle → PostgreSQL mappings from Excel
- **Key Features**:
  - Fallback to default mappings if Excel not found
  - Error handling for file operations
  - Validation of mapping data

#### **Lines 122-200: Default Mappings**

```python
def _get_default_function_mappings(self) -> Dict[str, str]:
def _get_default_type_mappings(self) -> Dict[str, str]:
```

- **Purpose**: Provide fallback mappings
- **Key**: Comprehensive coverage of common Oracle functions and types

#### **Lines 202-250: Main SQL Generation**

```python
def to_sql(self) -> str:
    # Render declarations with PostgreSQL syntax
    # Render main execution block
    # Wrap in DO $$ BEGIN ... END $$ structure
```

- **Purpose**: Generate PostgreSQL-compatible SQL
- **Key**: PostgreSQL-specific syntax (DO $$, := assignment, etc.)

#### **Lines 252-320: Declaration Rendering**

```python
def _render_declarations(self, decl: Dict[str, Any]) -> List[str]:
    # Convert Oracle data types to PostgreSQL
    # Handle %TYPE references
    # Process variables, constants, exceptions
```

- **Purpose**: Generate PostgreSQL DECLARE section
- **Key**: Type conversion and PostgreSQL syntax adaptation

#### **Lines 322-400: Data Type Conversion**

```python
def _convert_data_type(self, oracle_type: str) -> str:
    # Handle %TYPE references
    # Extract base type and size parameters
    # Apply type mappings
    # Preserve size parameters where appropriate
```

- **Purpose**: Convert Oracle data types to PostgreSQL equivalents
- **Key**: Complex type handling with size parameter preservation

#### **Lines 402-500: Statement Processing**

```python
def _render_statement_list(self, statements: List[Dict[str, Any]], indent_level: int) -> List[str]:
    # Convert Oracle SQL to PostgreSQL
    # Handle different statement types
    # Apply function mappings
```

- **Purpose**: Process statements with PostgreSQL syntax conversion
- **Key**: SQL syntax adaptation and function translation

#### **Lines 502-600: SQL Conversion Functions**

```python
def _convert_sql_statement(self, sql: str, stmt_type: str) -> str:
def _convert_raise_statement(self, sql: str) -> str:
def _convert_condition(self, condition: str) -> str:
```

- **Purpose**: Convert Oracle SQL syntax to PostgreSQL
- **Key Features**:
  - Function name replacement
  - DUAL table removal
  - Oracle-specific syntax conversion
  - Exception handling adaptation

#### **Lines 602-700: Control Structure Rendering**

```python
def _render_if_else(self, node: Dict[str, Any], indent_level: int) -> List[str]:
def _render_case_when(self, node: Dict[str, Any], indent_level: int) -> List[str]:
def _render_for_loop(self, node: Dict[str, Any], indent_level: int) -> List[str]:
```

- **Purpose**: Render PostgreSQL control structures
- **Key**: Similar to Oracle but with PostgreSQL syntax

#### **Lines 702-800: Function Call Handling**

```python
def _render_function_call(self, node: Dict[str, Any], indent_level: int) -> List[str]:
    # Convert Oracle functions to PostgreSQL
    # Special handling for raise_application_error
    # Use PERFORM for procedures
```

- **Purpose**: Handle function calls with PostgreSQL syntax
- **Key**: Function mapping and PostgreSQL-specific syntax

---

## 📁 utilities/JSONTOPLJSON.py

### Overview

Transforms JSON analysis into operation-specific structure (INSERT, UPDATE, DELETE) for PostgreSQL triggers.

### Code Flow Analysis

#### **Lines 1-25: Imports and Setup**

```python
import json, copy
from typing import Any, Dict, List, Tuple
from utilities.common import (logger, setup_logging, debug, info, ...)
```

- **Purpose**: Import utilities and deep copy functionality
- **Key**: Copy module for independent processing of operation types

#### **Lines 27-45: Class Initialization**

```python
class JSONTOPLJSON:
    def __init__(self, json_data):
        self.json_data = json_data
        self.sql_content = {
            "declarations": {},
            "on_insert": [],
            "on_update": [],
            "on_delete": [],
        }
        # Create deep copies for each operation type
```

- **Purpose**: Initialize with operation-specific structure
- **Key**: Deep copies prevent cross-contamination between operations

#### **Lines 47-120: Condition Modification**

```python
def modify_condition(self, condition):
    # Remove Oracle-specific keywords (INSERTING, UPDATING, DELETING)
    # Remove PostgreSQL TG_OP patterns
    # Clean up syntax issues
    # Return 'TRUE' if empty
```

- **Purpose**: Clean Oracle trigger conditions for PostgreSQL
- **Key Features**:
  - Keyword removal with regex
  - Syntax cleanup
  - Fallback to 'TRUE' for empty conditions

#### **Lines 122-180: Condition Processing Logic**

```python
def process_condition(self, condition, condition_type):
    # Analyze condition for operation-specific keywords
    # Determine if condition applies to current operation
    # Make retention/removal decisions
```

- **Purpose**: Determine condition applicability for each operation
- **Key**: Logic for filtering operation-specific code blocks

#### **Lines 182-300: INSERT Operation Processing**

```python
def parse_pl_json_on_insert(self):
    def process_on_insert_json(statements, json_path="", condition_type="on_insert"):
        # Recursively process nested structures
        # Handle begin_end blocks, exception handlers
        # Process if_else, case_when, for_loop structures
```

- **Purpose**: Filter and process code for INSERT operations
- **Key**: Recursive processing with condition evaluation

#### **Lines 302-420: UPDATE Operation Processing**

```python
def parse_pl_json_on_update(self):
    def process_on_update_json(statements, json_path="", condition_type="on_update"):
        # Similar structure to INSERT processing
        # Different condition evaluation logic
```

- **Purpose**: Filter and process code for UPDATE operations
- **Key**: Same recursive structure, different condition logic

#### **Lines 422-540: DELETE Operation Processing**

```python
def parse_pl_json_on_delete(self):
    def process_on_delete_json(statements, json_path="", condition_type="on_delete"):
        # Similar structure to INSERT/UPDATE processing
        # DELETE-specific condition evaluation
```

- **Purpose**: Filter and process code for DELETE operations
- **Key**: Consistent structure across all operation types

#### **Lines 542-680: Main Conversion Process**

```python
def to_sql(self):
    # Step 1: Create deep copies for each operation type
    # Step 2: Process each operation type independently
    # Step 3: Combine into final structure
    # Step 4: Convert to JSON string
```

- **Purpose**: Orchestrate the entire conversion process
- **Key Features**:
  - Independent processing of operation types
  - Deep copy management
  - Final structure assembly
  - JSON string output

---

## 📁 main.py

### Overview

Main execution script that orchestrates the entire Oracle to PostgreSQL conversion workflow.

### Code Flow Analysis

#### **Lines 1-25: Imports and Setup**

```python
#!/usr/bin/env python3
import json, os, re, time
from typing import Any, Dict, List, Tuple
from utilities.common import (clean_json_files, logger, setup_logging, ...)
from utilities.OracleTriggerAnalyzer import OracleTriggerAnalyzer
from utilities.FORMATOracleTriggerAnalyzer import FORMATOracleTriggerAnalyzer
from utilities.JSONTOPLJSON import JSONTOPLJSON
from utilities.FORMATPostsqlTriggerAnalyzer import FORMATPostsqlTriggerAnalyzer
```

- **Purpose**: Import all converter components
- **Key**: Comprehensive import structure for workflow orchestration

#### **Lines 27-35: Constants and Configuration**

```python
FORMAT_JSON_DIR = "files/format_json"
ANALYSIS_JSON_SUFFIX = "_analysis.json"
```

- **Purpose**: Define directory and file naming conventions
- **Key**: Centralized configuration for file paths

#### **Lines 37-55: Utility Functions**

```python
def convert_complex_structure_to_sql(complex_structure):
def ensure_dir(directory: str) -> None:
```

- **Purpose**: Helper functions for file operations and SQL conversion
- **Key**: Directory creation and structure conversion utilities

#### **Lines 57-120: File Processing Framework**

```python
def process_files(source_dir: str, target_dir: str, file_pattern: str, output_suffix: str, processor_func):
    # Ensure target directory exists
    # Find matching files
    # Extract trigger numbers
    # Process each file with provided function
    # Handle errors gracefully
```

- **Purpose**: Generic file processing framework
- **Key Features**:
  - Error handling and logging
  - Progress tracking
  - Flexible processor function support

#### **Lines 122-200: SQL to JSON Processor**

```python
def sql_to_json_processor(src_path: str, out_path: str, trigger_num: str) -> None:
    # Read SQL file content
    # Create OracleTriggerAnalyzer instance
    # Generate JSON analysis
    # Write analysis to output file
```

- **Purpose**: Convert Oracle SQL files to JSON analysis
- **Key**: Step 1 of the conversion workflow

#### **Lines 202-250: Oracle Triggers to JSON Conversion**

```python
def read_oracle_triggers_to_json() -> None:
    # Process all .sql files in files/oracle/
    # Convert to structured JSON analysis
    # Save to files/format_json/
```

- **Purpose**: Batch conversion of Oracle trigger files
- **Key**: Phase 1 of the conversion process

#### **Lines 252-320: JSON to SQL Processor**

```python
def json_to_sql_processor(src_path: str, out_path: str, trigger_num: str) -> None:
    # Read JSON analysis file
    # Create FORMATOracleTriggerAnalyzer instance
    # Render SQL content
    # Write formatted SQL to output file
```

- **Purpose**: Convert JSON analysis back to formatted Oracle SQL
- **Key**: Step 2 of the conversion workflow

#### **Lines 322-350: Oracle SQL Rendering**

```python
def render_oracle_sql_from_analysis() -> None:
    # Process all _analysis.json files
    # Convert to formatted SQL
    # Save to files/format_sql/
```

- **Purpose**: Batch rendering of formatted Oracle SQL
- **Key**: Phase 2 of the conversion process

#### **Lines 352-420: Validation Functions**

```python
def validate_conversion() -> None:
    # Check file counts between source and target
    # Verify all expected files exist
    # Report validation statistics
```

- **Purpose**: Ensure conversion completeness
- **Key**: Quality assurance for the conversion process

#### **Lines 422-500: JSON to PL/JSON Conversion**

```python
def read_json_to_oracle_triggers() -> None:
    # Process analysis JSON files
    # Create JSONTOPLJSON instances
    # Generate operation-specific structure
    # Save to files/format_pl_json/
```

- **Purpose**: Transform JSON to PostgreSQL-compatible structure
- **Key**: Phase 3 of the conversion process

#### **Lines 502-580: PL/JSON to PostgreSQL Format**

```python
def read_json_to_postsql_triggers() -> None:
    # Process PL/JSON files
    # Convert to PostgreSQL format
    # Save to files/format_plsql/
```

- **Purpose**: Convert PL/JSON to PostgreSQL trigger structure
- **Key**: Phase 4 of the conversion process

#### **Lines 582-680: PostgreSQL Format Processing**

```python
def convert_pl_json_to_postgresql_format(src_path: str, out_path: str, trigger_num: str) -> None:
def convert_postgresql_format_to_sql(src_path: str, out_path: str, trigger_num: str) -> None:
def convert_postgresql_format_files_to_sql() -> None:
```

- **Purpose**: Final conversion to PostgreSQL SQL
- **Key**: Phase 5 of the conversion process

#### **Lines 682-916: Main Execution Function**

```python
def main() -> None:
    # Step 1: SQL → JSON conversion
    # Step 2: JSON → Oracle SQL conversion
    # Step 3: JSON cleaning
    # Step 4: Validation
    # Step 5: JSON → PL/JSON conversion
    # Step 6: PL/JSON → PostgreSQL format
    # Step 7: Final SQL generation
```

- **Purpose**: Orchestrate the complete 7-step workflow
- **Key Features**:
  - Performance timing for each step
  - Comprehensive error handling
  - Detailed logging and progress reporting
  - Final summary with statistics

---

## 🔄 Overall Workflow Summary

The converter follows this 7-step process:

1. **SQL → JSON**: Parse Oracle triggers into structured analysis
2. **JSON → Oracle SQL**: Validate parsing by regenerating Oracle SQL
3. **JSON Cleaning**: Remove debugging metadata
4. **Validation**: Ensure conversion completeness
5. **JSON → PL/JSON**: Transform to operation-specific structure
6. **PL/JSON → PostgreSQL**: Convert to PostgreSQL format
7. **Final SQL**: Generate executable PostgreSQL SQL

Each step includes comprehensive logging, error handling, and performance monitoring to ensure reliable conversion results.
