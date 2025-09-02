import json
from math import e
import os
import re
import time
from typing import Any, Dict, List, Tuple
import pandas as pd
from numpy import copy
from utilities.common import (
    append_to_excel_sheet,
    logger,
    main_excel_file,
    setup_logging,
    debug,
    info,
    warning,
    error,
    critical,
    alert,
)


class OracleTriggerAnalyzer:
    """
    Parser and analyzer for Oracle PL/SQL trigger bodies.


    Architecture and flow:
    - Constructor receives raw SQL text and splits it into `DECLARE` and main sections.
    - Rule validation runs immediately to catch formatting violations (e.g., IF/THEN split lines).
    - Declaration parsing extracts variables, constants, exceptions into structured lists.
    - Main body is tokenized into lines, strip comments, then grouped into structured nodes:
      begin_end, if_else, case_when_statements, for_loop, DML/select, assignment, raise.
    - Finally, `to_json()` emits a dict with `declarations`, `main`, and `sql_comments`.
    """

    def __init__(self, filepath: str, encoding: str = 'utf-8'):
        """
        Initialize the OracleTriggerAnalyzer with SQL content.


        Args:
            sql_content (str): The raw SQL trigger content to analyze
            file_details (Dict[str, Any], optional): Dictionary containing file information
                with keys like 'filename', 'filepath', 'filesize', etc.


        Process flow:
            1. Store the raw SQL content
            2. Initialize data structures for parsed components
            3. Convert raw SQL to structured line format
            4. Parse SQL into declare and main sections
            5. Validate formatting rules
        """
        start_time = time.time()
        debug(
            "Initializing OracleTriggerAnalyzer with %d characters of SQL",
            len(filepath),
        )
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Extract file details
        file_details = self.extract_file_details(filepath)
        
        # Read file content
        with open(filepath, 'r', encoding=encoding) as f:
            sql_content = f.read()

        self.sql_content: str = sql_content
        self.file_details: Dict[str, Any] = file_details or {}
        self.declare_section: List[int] = [0, 0]
        # self.main_section: List[int] = [0, 0]
        self.main_section_lines: Dict = {}
        self.variables: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []
        self.exceptions: List[Dict[str, Any]] = []
        self.sql_comments: List[str] = []
        self.structured_lines: List[Dict[str, Any]] = []
        self.rest_string_list: List = []
        self.strng_convert_json: Dict = {
            "select_statement": 0,
            "insert_statement": 0,
            "update_statement": 0,
            "delete_statement": 0,
            "raise_statement": 0,
            "assignment": 0,
            "for_loop": 0,
            "if_else": 0,
            "case_when": 0,
            "begin_end": 0,
            "exception_handler": 0,
            "function_calling": 0,
            "when_statement": 0,
            "elif_statement": 0,
            "fetch_statement": 0,
            "open_statement": 0,
            "exit_statement": 0,
            "close_statement": 0,
            "merge_statement": 0,
            "null_statement": 0,
            "return_statement": 0,
            "with_statement": 0,
        }

        logger.debug(f"structured lines conversion {len(self.structured_lines)} lines processed",)

        # Step 3: Parse SQL into declare and main sections
        logger.debug("SQL section parsing")
        self._parse_sql()
        logger.debug("SQL section parsing")

        duration = time.time() - start_time
        logger.debug(f"OracleTriggerAnalyzer initialization {duration} seconds")

    def _convert_to_structured_lines(self):
        """
        Convert raw SQL content into a structured line representation.


        Each line is represented as a dictionary with the following structure:
        {
            "indent": int,           # The indentation level (number of leading spaces)
            "line": str,             # The line content without leading whitespace
            "line_no": int,          # The line number (1-based)
            "is_end_semicolon": bool # Whether the line ends with a semicolon
        }


        This structured format makes it easier to:
        1. Process lines based on their indentation level (nesting)
        2. Track statement boundaries via semicolons
        3. Maintain line numbers for error reporting
        4. Handle comment removal while preserving structure
        """
        debug("Converting SQL content to structured lines")
        raw_lines = self.sql_content.splitlines()
        self.structured_lines = []

        # Track statistics for debugging
        semicolon_lines = 0
        empty_lines = 0

        for i, line in enumerate(raw_lines, start=1):
            # Calculate indentation level (number of leading spaces)
            indent_level = len(line) - len(line.lstrip())

            # Get content without leading whitespace
            content = line.rstrip()

            # Skip completely empty lines from structured representation
            if not content:
                empty_lines += 1
                continue

            # Check if line ends with semicolon
            is_end_semicolon = content.rstrip().endswith(";")
            if is_end_semicolon:
                semicolon_lines += 1

            self.structured_lines.append(
                {
                    "indent": indent_level,
                    "line": content,
                    "line_no": i,
                    # "is_end_semicolon": is_end_semicolon,
                }
            )

        debug(
            "Structured lines conversion complete: %d total, %d with semicolons, %d empty lines skipped",
            len(self.structured_lines),
            semicolon_lines,
            empty_lines,
        )
    def load_function_name(self):
        """
        Load function name from the excel file (utilities/oracle_postgresql_mappings.xlsx) in sheet "function_list".
        """
        function_list = pd.read_excel(main_excel_file, sheet_name="function_list")
        function_name = function_list["function_name"].tolist()
        return function_name

    def _strip_block_comments(self):
        """
        Strip block comments (/* ... */) from structured lines.


        This method processes each line to remove block comments while preserving
        the structure of the original content. It handles multi-line block comments
        that span across multiple structured lines.


        Performance optimization:
            - Fast path check for lines without any block comments
            - Preserves line numbers and indentation for proper error reporting
        """
        clean_lines = []
        extracted_comments = []
        in_block_comment = False
        current_comment = ""

        for line_info in self.structured_lines:
            line = line_info["line"]

            # Fast path: if no block comment markers, keep line as is
            if "/*" not in line and "*/" not in line and not in_block_comment:
                clean_lines.append(line_info)
                continue

            # Process line with potential block comments
            clean_line = ""
            i = 0

            while i < len(line):
                if not in_block_comment:
                    # Look for start of block comment
                    if line[i : i + 2] == "/*":
                        in_block_comment = True
                        current_comment = "/*"
                        i += 2
                    else:
                        clean_line += line[i]
                        i += 1
                else:
                    # Inside block comment, look for end
                    if line[i : i + 2] == "*/":
                        in_block_comment = False
                        current_comment += "*/"
                        extracted_comments.append(current_comment)
                        current_comment = ""
                        i += 2
                    else:
                        current_comment += line[i]
                        i += 1

            # If we're still in a block comment, add newline to current comment
            if in_block_comment:
                current_comment += "\n"

            # Only add line if it has content after comment removal
            if clean_line.strip():
                clean_lines.append(
                    {
                        "indent": line_info["indent"],
                        "line": clean_line,
                        "line_no": line_info["line_no"],
                        # "is_end_semicolon": clean_line.rstrip().endswith(";"),
                    }
                )

        # If we end with an unclosed block comment, add it to extracted comments
        if in_block_comment and current_comment:
            extracted_comments.append(current_comment)
            logger.debug("Unclosed block comment detected")

        # Update self.structured_lines and self.sql_comments
        self.structured_lines = clean_lines
        self.sql_comments.extend(extracted_comments)

        logger.debug("Block comment stripping complete: %d comments extracted, %d lines cleaned", len(extracted_comments), len(clean_lines))

    def _strip_inline_comments_from_lines(self):
        """
        Remove inline comments (-- ...) from structured lines.


        This method updates self.structured_lines and adds extracted comments to self.sql_comments.
        """
        clean_lines = []
        extracted_comments = []

        for line_info in self.structured_lines:
            line = line_info["line"]

            # Find the position of the first inline comment
            comment_pos = line.find("--")

            if comment_pos == -1:
                # No inline comment found, keep line as is
                clean_lines.append(line_info)
            else:
                # Extract the comment
                comment = line[comment_pos:].strip()
                extracted_comments.append(comment)

                # Keep the part before the comment
                clean_part = line[:comment_pos].rstrip()

                if clean_part:
                    # Only add line if there's content after comment removal
                    clean_lines.append(
                        {
                            "indent": line_info["indent"],
                            "line": clean_part,
                            "line_no": line_info["line_no"],
                            # "is_end_semicolon": clean_part.rstrip().endswith(";"),
                        }
                    )

        # Update self.structured_lines and self.sql_comments
        self.structured_lines = clean_lines
        self.sql_comments.extend(extracted_comments)

        logger.debug("Inline comment stripping complete: %d comments extracted, %d lines cleaned", len(extracted_comments), len(clean_lines))

    def _parse_sql(self) -> None:
        """
        Split SQL content into DECLARE and main (BEGIN...END) sections.


        This method:
        1. Builds the full SQL from structured lines
        2. Identifies the DECLARE section (if present)
        3. Sets the main section with the BEGIN block
        4. Processes declarations into categories (variables, constants, exceptions)


        Pattern: DECLARE ... BEGIN ... END
        """
        # Step 1: Convert to structured lines
        logger.debug("structured lines conversion")
        self._convert_to_structured_lines()
        logger.debug("structured lines conversion")

        # Step 2: Remove block comments (/* ... */)
        self._strip_block_comments()
        logger.debug("Removed block comments from main section")

        # Step 3: Remove inline comments (-- ...)
        self._strip_inline_comments_from_lines()
        logger.debug("Removed inline comments from main section")

        # Find DECLARE and BEGIN sections
        declare_start = -1
        begin_start = -1

        for i, line_info in enumerate(self.structured_lines):
            line_content = line_info["line"].strip().upper()

            # Find DECLARE section
            if line_content.startswith("DECLARE"):
                declare_start = line_info["line_no"]
                logger.debug("Found DECLARE at line %d", declare_start)
                # Find BEGIN section
            elif line_content.startswith("BEGIN") and begin_start == -1:
                begin_start = line_info["line_no"]
                logger.debug("Found BEGIN at line %d", begin_start)

            # elif line_content.endswith("END;"):
            #     begin_end_start = line_info["line_no"]
            #     logger.debug("Found END at line %d", begin_end_start)

        # Set section boundaries
        if declare_start != -1:
            declare_end = begin_start - 1
            self.declare_section = [declare_start, declare_end]
            logger.debug("DECLARE section: lines %d-%d", declare_start, declare_end)
        else:
            self.declare_section = [0, 0]
            logger.debug("No DECLARE section found")

        # Process declarations if DECLARE section exists
        if self.declare_section[0] > 0 and self.declare_section[1] >= self.declare_section[0]:
            self._parse_declarations()

        # Process main section if main section exists
        if begin_start != len(self.structured_lines):
            self._process_main_section()

    def _parse_declarations(self) -> None:
        """
        Parse the DECLARE section and categorize declarations into:
        - Variables
        - Constants
        - Exceptions


        This method:
        1. Splits declaration section by semicolons
        2. Processes each segment to identify its type
        3. Extracts metadata about each declaration
        4. Removes comments and stores them separately
        5. Populates self.variables, self.constants, and self.exceptions
        """
        logger.debug("Starting declaration parsing")

        # Get all lines from the DECLARE section
        decl_lines = []
        for line_info in self.structured_lines:
            if (
                self.declare_section[0] + 1
                <= line_info["line_no"]
                <= self.declare_section[1]
            ):
                decl_lines.append(line_info["line"])

        # Join lines and split by semicolons
        full_declaration = " ".join(decl_lines)
        segments = [seg.strip() for seg in full_declaration.split(";") if seg.strip()]

        for segment in segments:
            segment_upper = segment.upper()

            # Skip empty segments and comments
            if not segment or segment.startswith("--") or segment.startswith("/*"):
                continue

            # Determine declaration type and process accordingly
            if "CONSTANT" in segment_upper:
                self._process_constant_declaration(segment)
            elif segment_upper.endswith("EXCEPTION"):
                self._process_exception_declaration(segment)
            else:
                # Assume it's a variable declaration
                self._process_variable_declaration(segment)

    def _process_variable_declaration(self, segment: str) -> None:
        """
        Process a variable declaration segment.


        Args:
            segment (str): The segment containing a variable declaration
        """
        try:
            parsed_var = self._parse_variable(segment)
            if parsed_var:
                self.variables.append(parsed_var)
                logger.debug("Processed variable: %s", parsed_var["name"])
        except Exception as e:
            logger.debug("Failed to process variable declaration '%s': %s", segment, e)
            print(f"Failed to process variable declaration '{segment}': {e}")

    def _process_constant_declaration(self, segment: str) -> None:
        """
        Process a constant declaration segment.


        Args:
            segment (str): The segment containing a constant declaration
        """
        try:
            parsed_const = self._parse_constant(segment)
            if parsed_const:
                self.constants.append(parsed_const)
                logger.debug("Processed constant: %s", parsed_const["name"])
        except Exception as e:
            logger.debug("Failed to process constant declaration '%s': %s", segment, e)
            print(f"Failed to process constant declaration '{segment}': {e}")

    def _process_exception_declaration(self, segment: str) -> None:
        """
        Process an exception declaration segment.


        Args:
            segment (str): The segment containing an exception declaration
        """
        try:
            parsed_exc = self._parse_exception(segment)
            if parsed_exc:
                self.exceptions.append(parsed_exc)
                logger.debug("Processed exception: %s", parsed_exc["name"])
        except Exception as e:
            logger.debug("Failed to process exception declaration '%s': %s", segment, e)
            print(f"Failed to process exception declaration '{segment}': {e}")

    def _parse_variable(self, line: str) -> Dict[str, Any]:
        """
        Parse a variable declaration line and extract name, data type, and default value.


        Handles variable declarations in the format:
        - variable_name data_type [NOT NULL] [:= default_value];


        Args:
            line (str): The line containing a variable declaration


        Returns:
            dict: Dictionary with variable name, data type, and default value (if present)


        Examples of supported formats:
        - v_count NUMBER;
        - v_name VARCHAR2(100) := 'John';
        - v_date DATE NOT NULL := SYSDATE;
        - v_result sys.object_type;
        """
        # Remove trailing semicolon if present
        line = line.strip().rstrip(";")

        # Check for default value assignment
        default_value = None
        if " := " in line:
            parts = line.split(" := ", 1)
            declaration_part = parts[0].strip()
            default_value = parts[1].strip()
            default_value = self.format_values(default_value)
        else:
            declaration_part = line

        # Split declaration into name and type
        words = declaration_part.split()
        if len(words) < 2:
            logger.debug("Invalid variable declaration format: %s", line)
            return None

        var_name = words[0]

        # Handle complex data types with parameters (e.g., VARCHAR2(100))
        # type_parts = words[1:]
        data_type = ""
        i = 1
        while i < len(words):
            data_type += words[i]
            if "(" in words[i] and ")" not in words[i]:
                # Multi-word type with parameters
                i += 1
                while i < len(words) and ")" not in words[i]:
                    data_type += " " + words[i]
                    i += 1
                if i < len(words):
                    data_type += " " + words[i]
            i += 1

        return {
            "name": var_name,
            "data_type": data_type.strip(),
            "default_value": default_value,
        }

    def _parse_constant(self, line: str) -> Dict[str, Any]:
        """
        Parse a constant declaration line and extract name, data type, and value.


        Handles constant declarations in the format:
        - constant_name CONSTANT data_type [:= value];


        Args:
            line (str): The line containing a constant declaration


        Returns:
            dict: Dictionary with constant name, data type, and value (if present)


        Examples of supported formats:
        - C_MAX_RECORDS CONSTANT NUMBER := 100;
        - C_DEFAULT_NAME CONSTANT VARCHAR2(50) := 'Unknown';
        - C_FLAG CONSTANT BOOLEAN := TRUE;
        """
        # Remove trailing semicolon if present
        line = line.strip().rstrip(";")

        # Check for value assignment
        value = None
        if " := " in line:
            parts = line.split(" := ", 1)
            declaration_part = parts[0].strip()
            value = parts[1].strip()
            value = self.format_values(value)
        else:
            declaration_part = line

        # Split declaration: constant_name CONSTANT data_type
        words = declaration_part.split()
        if len(words) < 3 or words[1].upper() != "CONSTANT":
            logger.debug("Invalid constant declaration format: %s", line)
            return None

        const_name = words[0]

        # Handle complex data types with parameters
        # type_parts = words[2:]
        data_type = ""
        i = 2
        while i < len(words):
            data_type += words[i]
            if "(" in words[i] and ")" not in words[i]:
                # Multi-word type with parameters
                i += 1
                while i < len(words) and ")" not in words[i]:
                    data_type += " " + words[i]
                    i += 1
                if i < len(words):
                    data_type += " " + words[i]
            i += 1

        return {"name": const_name, "data_type": data_type.strip(), "value": value}

    def _parse_exception(self, line: str) -> Dict[str, Any]:
        """
        Parse an exception declaration line.


        This extracts the exception name from declarations like:
        - my_exception exception;


        Args:
            line (str): The line containing an exception declaration


        Returns:
            dict: Dictionary with the exception name and type
        """
        # Remove trailing semicolon if present
        line = line.strip().rstrip(";")

        # Split by whitespace
        words = line.split()
        if len(words) < 2 or words[-1].upper() != "EXCEPTION":
            logger.debug("Invalid exception declaration format: %s", line)
            return None

        # Exception name is everything before "EXCEPTION"
        exc_name = " ".join(words[:-1])

        return {"name": exc_name, "type": "EXCEPTION"}

    def _process_main_section(self) -> None:
        """
        Process the main section (BEGIN...END) to extract structured lines.


        This method populates self.main_section_lines with the lines from
        the main section of the Oracle PL/SQL trigger.
        """

        self._parse_begin_blocks()
        self._parse_begin_end_statements()
        self._parse_with_statements()
        self._parse_case_when()
        self._parse_if_else()
        self._parse_for_loop()
        self._parse_function_calling_statements()
        self._parse_sql_statements()
        self.rest_strings()
        
    def _parse_with_statements(self):
        """
        Parse with statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        def parse_with_statements(working_lines: List[Dict[str, Any]]):
            with_statements = []
            i = 0
            while i < len(working_lines):
                item = working_lines[i]
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("WITH "):
                        logger.debug(f"with_indent: {item['line_no']}")
                        for j in range(i + 1, len(working_lines)):
                            line_info = working_lines[j]
                            if "line" in line_info:
                                line_upper = line_info["line"].strip().upper()
                                if line_upper.endswith(")") and line_info["indent"] == item["indent"]:
                                    logger.debug(f"with_i: {item['line_no']} i: {line_info['line_no']}")
                                    with_statement = self._parse_with_statement(working_lines[i : j+1])
                                    with_statements.append(with_statement)
                                    i = j
                                    break
                    else:
                        with_statements.append(item)
                elif "type" in item:
                    if item["type"] == "begin_end":
                        # Process IF statements in begin_end_statements
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_with_statements(item["begin_end_statements"])
                        # Process IF statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_with_statements(handler["exception_statements"])

                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_with_statements(clause["then_statements"])
                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_with_statements(item["else_statements"])

                    elif item["type"] == "if_else":
                        # Process CASE statements in then_statements, if_elses, and else_statements
                        if "then_statements" in item:
                            item["then_statements"] = parse_with_statements(item["then_statements"])   
                        if "if_elses" in item:
                            for elsif_block in item["if_elses"]:
                                if "then_statements" in elsif_block:
                                        elsif_block["then_statements"] = parse_with_statements(elsif_block["then_statements"])
                        if "else_statements" in item:
                            item["else_statements"] = parse_with_statements(item["else_statements"])
                    # Process SQL statements in for_loop
                    elif item["type"] == "for_loop" and "for_statements" in item:
                        item["for_statements"] = parse_with_statements(item["for_statements"])
                    with_statements.append(item)
                i += 1
            return with_statements
        self.main_section_lines["begin_end_statements"] = parse_with_statements(self.main_section_lines["begin_end_statements"])
        for k, handler in enumerate(self.main_section_lines["exception_handlers"]):
            if "exception_statements" in handler:
                self.main_section_lines['exception_handlers'][k]["exception_statements"] = parse_with_statements(handler["exception_statements"])
    def _parse_with_statement(self, working_lines: List[Dict[str, Any]]):
        """
        Parse with statement from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        with_statement = {
            "type": "with_statement",
            "with_line_no": working_lines[0]["line_no"],
            "with_indent": working_lines[0]["indent"],
            "with_values": "",
            "with_statements": "",
            "with_end_line_no": working_lines[-1]["line_no"],
        }
        as_i = -1
        if working_lines[0]["line"].strip().upper().endswith("("):
            with_statement['with_values'] = working_lines[0]["line"].strip()[3:-4]
            as_i = 0
        else:
            with_statement['with_values'] = working_lines[0]["line"].strip()[3:]
            for j in range(1, len(working_lines)):
                line_info = working_lines[j]
                line_upper = line_info["line"].strip().upper()
                logger.debug(f"line_info : {line_info}")
                if line_upper.endswith("("):
                    with_statement['with_values'] += " " + line_info["line"].strip()[:-4]
                    as_i = j
                    break
                with_statement['with_values'] += " " + line_info["line"].strip()
        with_statement['with_statements'] = self.combine_lines(working_lines[as_i+1:])
        if with_statement['with_statements'].strip().upper().endswith(")"):
            with_statement['with_statements'] = with_statement['with_statements'][:-1]
        return with_statement
    
    def _parse_function_calling_statements(self):
        """
        Parse function calling statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.


        Detects function calling statements in the main section of SQL.
        """
        def parse_function_calling_statements(working_lines: List[Dict[str, Any]]):
            function_calling = []
            function_calling_names = self.load_function_name()
            i = 0
            logger.debug(f"working_lines: {working_lines}")
            function_calling_i = -1
            call_type = -1
            perform_type = -1
            function_calling_name = ""
            while i < len(working_lines):
                logger.debug(f"i: {i}")
                item = working_lines[i]
                if "line" in item:
                    logger.debug(f"item: {item}")
                    line_upper = item["line"].strip().upper()
                    if function_calling_i == -1:
                        for name in function_calling_names:
                            # Handle function names with and without quotes
                            # name_with_quotes = name.replace("'", "''")  # Escape single quotes
                            name_patterns = [
                                name,
                                f"'{name}'",
                                f"\"{name}\"",
                                f"CALL {name}",
                                f"CALL '{name}'",
                                f"CALL \"{name}\"",
                                f"PERFORM {name}",
                                f"PERFORM '{name}'",
                                f"PERFORM \"{name}\""
                            ]
                            
                            for pattern in name_patterns:
                                if line_upper.startswith(pattern.upper()):
                                    if "CALL " in line_upper:
                                        call_type = i
                                    elif "PERFORM " in line_upper:
                                        perform_type = i
                                    function_calling_i = i
                                    function_calling_name = name
                                    # print(f"function_calling_name: {function_calling_name}")
                                    break
                    if call_type != -1:
                        function_calling_name = "CALL " + function_calling_name
                    elif perform_type != -1:
                        function_calling_name = "PERFORM " + function_calling_name
                    if function_calling_i != -1:
                        logger.debug(f"item: {line_upper}")
                        logger.debug(f"function calling start: {item['line_no']}")
                        if line_upper.endswith(";"):
                            logger.debug(f"function calling end: {item['line_no']}")                         
                            function_calling.append(self._parse_function_calling([item],function_calling_name))
                            function_calling_i = -1  # Reset for next iteration
                            call_type = -1
                            perform_type = -1
                        else:
                            for j in range(i + 1, len(working_lines)):
                                line_info = working_lines[j]
                                if "line" in line_info:
                                    line_upper = line_info["line"].strip().upper()
                                    if line_upper.endswith(";"):
                                        logger.debug(f"function calling end: {line_info['line_no']}")                          
                                        function_calling.append(self._parse_function_calling(working_lines[i:j+1],function_calling_name))
                                        i = j
                                        function_calling_i = -1
                                        call_type = -1
                                        perform_type = -1
                                        break
                    else:
                        function_calling.append(item)
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                # Process IF statements in begin_end_statements
                elif "type" in item:
                    if item["type"] == "begin_end":
                        # Process IF statements in begin_end_statements
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_function_calling_statements(item["begin_end_statements"])
                        # Process IF statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_function_calling_statements(handler["exception_statements"])

                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_function_calling_statements(clause["then_statements"])
                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_function_calling_statements(item["else_statements"])

                    elif item["type"] == "if_else":
                        # Process CASE statements in then_statements, if_elses, and else_statements
                        if "then_statements" in item:
                            item["then_statements"] = parse_function_calling_statements(item["then_statements"])   
                        if "if_elses" in item:
                            for elsif_block in item["if_elses"]:
                                if "then_statements" in elsif_block:
                                        elsif_block["then_statements"] = parse_function_calling_statements(elsif_block["then_statements"])
                        if "else_statements" in item:
                            item["else_statements"] = parse_function_calling_statements(item["else_statements"])
                    # Process SQL statements in for_loop
                    elif item["type"] == "for_loop" and "for_statements" in item:
                        item["for_statements"] = parse_function_calling_statements(item["for_statements"])
                    function_calling.append(item)
                i += 1
            return function_calling
        self.main_section_lines["begin_end_statements"] = parse_function_calling_statements(self.main_section_lines["begin_end_statements"])
        for k, handler in enumerate(self.main_section_lines["exception_handlers"]):
            if "exception_statements" in handler:
                self.main_section_lines['exception_handlers'][k]["exception_statements"] = parse_function_calling_statements(handler["exception_statements"])

    def _parse_sql_statements(self):
        """
        Parse SQL statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        Unified method to group both SQL statements (SELECT, INSERT, UPDATE, DELETE)
        and RAISE statements. Uses structured line dictionaries.
        STMT_TYPE_MAP = {
            "SELECT": "select_statement",
            "INSERT": "insert_statement",
            "UPDATE": "update_statement",
            "DELETE": "delete_statement",
            "RAISE": "raise_statement",
            "NULL": "null_statement",
            "RETURN": "return_statement",
            ":=": "assignment",
            }
        """
        def parse_sql_statements(working_lines: List[Dict[str, Any]]):
            STMT_TYPE_MAP = {
                "SELECT": "select_statement",
                "INSERT": "insert_statement",
                "UPDATE": "update_statement",
                "DELETE": "delete_statement",
                "RAISE": "raise_statement",
                "NULL": "null_statement",
                "RETURN": "return_statement",
                "MERGE": "merge_statement",
            }
            sql_statements = []
            i = 0
            stmt_i = -1
            stmt_type = ""
            logger.debug(f"working_lines: {working_lines}")
            while i < len(working_lines):
                logger.debug(f"i: {i}")
                item = working_lines[i]
                if "line" in item:
                    logger.debug(f"item: {item['line']} || {item['line_no']} || {item['indent']}")
                    line_upper = item["line"].strip().upper()
                    for type_name, type_value in STMT_TYPE_MAP.items():
                        name_patterns = [
                                type_name,
                                f"{type_name} ",
                                f"{type_name};",
                        ]
                        for pattern in name_patterns:
                            if line_upper.startswith(pattern.upper()):
                                logger.debug(f"stmt start: {item['line_no']} || {type_value} || {pattern}")
                                stmt_i = i
                                stmt_type = type_value
                                logger.debug(f"stmt start: {item['line_no']} || {stmt_type}")
                                break
                    if stmt_i != -1:
                        logger.debug(f"stmt start: {item['line_no']} || {stmt_type}")
                        if line_upper.endswith(";"):
                            logger.debug(f"stmt end: {item['line_no']} || {stmt_type}")                         
                            sql_statements.append(self._parse_sql_statement([item], stmt_type))
                            stmt_i = -1
                        else:
                            for j in range(i + 1, len(working_lines)):
                                line_info = working_lines[j]
                                line_upper = line_info["line"].strip().upper()
                                if line_upper.endswith(";"):
                                    logger.debug(f"stmt end: {line_info['line_no']} || {stmt_type}")                         
                                    sql_statements.append(self._parse_sql_statement(working_lines[i:j+1], stmt_type))
                                    stmt_i = -1
                                    i = j
                                    break
                    elif ":=" in line_upper:
                        stmt_type = "assignment"
                        logger.debug(f"stmt start: {item['line_no']} || assignment")
                        if line_upper.endswith(";"):
                            logger.debug(f"stmt end: {item['line_no']} || assignment")                         
                            sql_statements.append(self._parse_assignment_statement([item]))
                            stmt_i = -1
                        else:
                            for j in range(i + 1, len(working_lines)):
                                line_info = working_lines[j]
                                line_upper = line_info["line"].strip().upper()
                                if line_upper.endswith(";"):
                                    logger.debug(f"stmt end: {line_info['line_no']} || assignment")                         
                                    sql_statements.append(self._parse_assignment_statement(working_lines[i:j+1]))
                                    stmt_i = -1
                                    i = j
                                    break
                    else:
                        sql_statements.append(item)
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                # Process IF statements in begin_end_statements
                elif "type" in item:
                    if item["type"] == "begin_end":
                        # Process IF statements in begin_end_statements
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_sql_statements(item["begin_end_statements"])
                        # Process IF statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_sql_statements(handler["exception_statements"])

                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_sql_statements(clause["then_statements"])
                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_sql_statements(item["else_statements"])

                    elif item["type"] == "if_else":
                        # Process CASE statements in then_statements, if_elses, and else_statements
                        if "then_statements" in item:
                            item["then_statements"] = parse_sql_statements(item["then_statements"])   
                        if "if_elses" in item:
                            for elsif_block in item["if_elses"]:
                                if "then_statements" in elsif_block:
                                        elsif_block["then_statements"] = parse_sql_statements(elsif_block["then_statements"])
                        if "else_statements" in item:
                            item["else_statements"] = parse_sql_statements(item["else_statements"])
                    # Process SQL statements in for_loop
                    elif item["type"] == "for_loop" and "for_statements" in item:
                        item["for_statements"] = parse_sql_statements(item["for_statements"])
                    sql_statements.append(item)
                i += 1
            return sql_statements
        self.main_section_lines["begin_end_statements"] = parse_sql_statements(self.main_section_lines["begin_end_statements"])
        for k, handler in enumerate(self.main_section_lines["exception_handlers"]):
            if "exception_statements" in handler:
                self.main_section_lines['exception_handlers'][k]["exception_statements"] = parse_sql_statements(handler["exception_statements"])

    def _parse_sql_statement(self, working_lines: List[Dict[str, Any]], stmt_type: str):
        """
        Parse SQL statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        sql_statement = {
            "type": stmt_type,
            "sql_statement": self.combine_lines(working_lines),
            "statement_line_no": working_lines[0]["line_no"],
            "statement_indent": working_lines[0]["indent"],
        }
        return sql_statement

    def _parse_assignment_statement(self, working_lines: List[Dict[str, Any]]):
        """
        Parse assignment statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        Group assignment statements (:=) in the SQL code.
        Uses structured line dictionaries.
        """
        line = self.combine_lines(working_lines)
        assignment_statement = {
            "type": "assignment",
            "variable_name": line.split(":=")[0].strip(),
            "assignment_operator": ":=",
            "expression": line.split(":=")[1].strip(),
            "assignment_line_no": working_lines[0]["line_no"],
            "assignment_indent": working_lines[0]["indent"],
        }
        logger.debug(f"assignment_statement: {assignment_statement}")
        return assignment_statement

        
    def _parse_for_loop(self):
        """
        Parse FOR loop statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.

        Detects FOR loop patterns in the format:
        FOR loop_variable IN (cursor_query) LOOP
            statements...
        END LOOP;

        And converts them to a structured JSON representation.
        """ 
        def parse_for_loop(working_lines: List[Dict[str, Any]]):
            for_loop_statements = []
            i = 0
            while i < len(working_lines):
                item = working_lines[i]
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("FOR") :
                        for j in range(i + 1, len(working_lines)):
                            line_info = working_lines[j]
                            if "line" in line_info:
                                line_upper = line_info["line"].strip().upper()
                                if line_upper.startswith("END LOOP;") and line_info["indent"] == item["indent"]:
                                    logger.debug(f"for_i: {working_lines[i]["line_no"]} i: {item["line_no"]}")
                                    for_loop_statements.append(self._parse_for_loop_statement(working_lines[i:j+1]))
                                    i = j
                                    break
                    else:
                        for_loop_statements.append(item)
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                # Process FOR loop statements in begin_end_statements
                elif "type" in item:
                    if item["type"] == "begin_end":
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_for_loop(item["begin_end_statements"])
                        # Process FOR loop statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_for_loop(handler["exception_statements"])
                    # Process FOR loop statements in case_when
                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_for_loop(clause["then_statements"])
                        # Process FOR loop statements in else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_for_loop(item["else_statements"])
                    # Process FOR loop statements in if_else
                    elif item["type"] == "if_else":
                        if "then_statements" in item:
                            item["then_statements"] = parse_for_loop(item["then_statements"])
                        if "if_elses" in item:
                            for elsif_block in item["if_elses"]:
                                if "then_statements" in elsif_block:
                                    elsif_block["then_statements"] = parse_for_loop(elsif_block["then_statements"])
                        if "else_statements" in item:
                            item["else_statements"] = parse_for_loop(item["else_statements"])
                    # Process FOR loop statements in for_loop
                    elif item["type"] == "for_loop" and "for_statements" in item:
                        item["for_statements"] = parse_for_loop(item["for_statements"])
                    for_loop_statements.append(item)
                i += 1
            return for_loop_statements
        self.main_section_lines["begin_end_statements"] = parse_for_loop(self.main_section_lines["begin_end_statements"])
        for k, handler in enumerate(self.main_section_lines["exception_handlers"]):
            if "exception_statements" in handler:
                self.main_section_lines['exception_handlers'][k]["exception_statements"] = parse_for_loop(handler["exception_statements"])

    def _parse_for_loop_statement(self, working_lines: List[Dict[str, Any]]):
        """
        Parse FOR loop statement from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        for_loop_statement = {
            "for_expression": "",
            "type": "for_loop",
            "for_line_no": working_lines[0]["line_no"],
            "for_indent": working_lines[0]["indent"],
            "end_for_line_no": working_lines[-1]["line_no"],
            "loop_variable": "",
            "for_statements": [],
        }
        in_i = -1
        if "IN" in working_lines[0]["line"]:
            in_position = working_lines[0]["line"].strip().upper().find("IN")
            for_loop_statement["loop_variable"] = working_lines[0]["line"].strip()[3:in_position].strip()
            in_i = 0
        else:
            for_loop_statement["loop_variable"] = working_lines[0]["line"].strip()[3:]
            for j in range(1, len(working_lines)):
                line_info = working_lines[j]
                line_upper = line_info["line"].strip().upper()
                if "IN" in line_upper:
                    in_position = line_upper.find("IN")
                    for_loop_statement["loop_variable"] += " " + line_info["line"].strip()[:in_position].strip()
                    in_i = j
                    break
                for_loop_statement["loop_variable"] += " " + line_info["line"].strip()
        if working_lines[in_i]["line"].strip().upper().endswith("LOOP"):
            in_position = working_lines[in_i]["line"].strip().upper().find("IN")
            loop_position = working_lines[in_i]["line"].strip().upper().find("LOOP")
            for_loop_statement["for_expression"] = working_lines[in_i]["line"].strip()[in_position+2:loop_position].strip()
            loop_i = in_i
        else:
            in_position = working_lines[in_i]["line"].strip().upper().find("IN")
            for_loop_statement["for_expression"] = working_lines[in_i]["line"].strip()[in_position+2:].strip()
            for k in range(in_i, len(working_lines)):
                line_info = working_lines[k]
                line_upper = line_info["line"].strip().upper()
                if "LOOP" in line_upper:
                    loop_position = line_upper.find("LOOP")
                    for_loop_statement["for_expression"] += " " + line_info["line"].strip()[:loop_position].strip()
                    loop_i = k
                    break
                for_loop_statement["for_expression"] += " " + line_info["line"].strip()
        logger.debug(f"for_loop_statement: {for_loop_statement} {working_lines[in_i]['line_no']} {working_lines[loop_i]['line_no']}")
        return for_loop_statement

    def _parse_if_else(self):
        """
        Parse IF-ELSIF-ELSE statements from the main section of SQL with proper nested structure based on indentation.
        First detects IF and END IF; line numbers, then finds all ELSIF and ELSE statements at the same indentation level.
        Maintains the hierarchical structure of IF-ELSIF-ELSE blocks by checking indentation levels.
        Updates self.main_section_lines with parsed blocks.
        """

        def parse_if_else(working_lines: List[Dict[str, Any]]):
            if_else_statements = []
            i = 0
            while i < len(working_lines):
                item = working_lines[i]
                logger.debug(f"item: {item}")
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("IF"):
                        logger.debug(f"if_indent: {item['line_no']}")
                        for j in range(i + 1, len(working_lines)):
                            line_info = working_lines[j]
                            if "line" in line_info:
                                line_upper = line_info["line"].strip().upper()
                                if line_upper.startswith("END IF;") and line_info["indent"] == item["indent"]:
                                    logger.debug(f"if_i: {item['line_no']} i: {line_info['line_no']}")
                                    logger.debug(f"if_elses working_lines lenght: {len(working_lines[i : j+1])}")
                                    if_else_statement = self._parse_if_else_statements(working_lines[i : j+1])
                                    if_else_statement["then_statements"] = parse_if_else(if_else_statement["then_statements"])
                                    for elif_clause in if_else_statement["if_elses"]:
                                        elif_clause["then_statements"] = parse_if_else(elif_clause["then_statements"])
                                    if_else_statement["else_statements"] = parse_if_else(if_else_statement["else_statements"])
                                    if_else_statements.append(if_else_statement)
                                    i = j
                                    break
                    else:
                        if_else_statements.append(item)
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                # Process IF statements in begin_end_statements
                elif "type" in item:
                    if item["type"] == "begin_end":
                        # Process IF statements in begin_end_statements
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_if_else(item["begin_end_statements"])
                        # Process IF statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_if_else(handler["exception_statements"])

                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_if_else(clause["then_statements"])
                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_if_else(item["else_statements"])

                    elif item["type"] == "if_else":
                        # Process CASE statements in then_statements, if_elses, and else_statements
                        if "then_statements" in item:
                            item["then_statements"] = parse_if_else(item["then_statements"])
                        if "if_elses" in item:
                            for elsif_block in item["if_elses"]:
                                if "then_statements" in elsif_block:
                                    elsif_block["then_statements"] = parse_if_else(elsif_block["then_statements"])
                        if "else_statements" in item:
                            item["else_statements"] = parse_if_else(item["else_statements"])
                    # Process IF statements in for_loop
                    elif item["type"] == "for_loop" and "for_statements" in item:
                        item["for_statements"] = parse_if_else(item["for_statements"])
                    if_else_statements.append(item)
                i += 1
            return if_else_statements

        self.main_section_lines["begin_end_statements"] = parse_if_else(self.main_section_lines["begin_end_statements"])
        for k, handler in enumerate(self.main_section_lines["exception_handlers"]):
            if "exception_statements" in handler:
                self.main_section_lines['exception_handlers'][k]["exception_statements"] = parse_if_else(handler["exception_statements"])

    def _parse_if_else_statements(self, working_lines: List[Dict[str, Any]]):
        """
        Parse elif and else statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        if_else_statements = {
        "condition": "",
        "type": "if_else",
        "if_line_no": working_lines[0]["line_no"],
        "then_line_no": 0,
        "if_indent": working_lines[0]["indent"],
        "end_if_line_no": working_lines[-1]["line_no"],
        "then_statements": [],
        "if_elses": [],
        "else_statements": [],
        }
        then_i = -1
        elif_line_indent = working_lines[0]["indent"]
        if working_lines[0]["line"].strip().upper().endswith("THEN"):
            if_else_statements['condition'] = working_lines[0]["line"].strip()[2:-4]
            then_i = 0
        else:
            if_else_statements['condition'] = working_lines[0]["line"].strip()[2:]
            for j in range(1, len(working_lines)):
                line_info = working_lines[j]
                line_upper = line_info["line"].strip().upper()
                logger.debug(f"line_info : {line_info}")
                if line_upper.endswith("THEN"):
                    if_else_statements['condition'] += " " + line_info["line"].strip()[:-4]
                    then_i = j
                    break
                if_else_statements['condition'] += " " + line_info["line"].strip()
        if_else_statements['then_line_no'] = working_lines[then_i]["line_no"]
        i = then_i + 1
        elif_i = -1
        else_i = -1
        while i < len(working_lines):
            item = working_lines[i]
            if "line" in item:
                line_upper = item["line"].strip().upper()
                if line_upper.startswith("ELSIF") and item["indent"] == elif_line_indent:
                    if elif_i == -1:
                        logger.debug(f"then_statements: {0} {i}")
                        if_else_statements['then_statements'].extend(working_lines[then_i+1:i])
                    elif_i = i
                    j = i + 1
                    while j < len(working_lines):
                        line_info = working_lines[j]
                        logger.debug(f"line_info: {line_info}")
                        if "line" in line_info:
                            line_upper = line_info["line"].strip().upper()
                            if line_upper.startswith("ELSIF") and line_info["indent"] == elif_line_indent:
                                logger.debug(working_lines[elif_i],working_lines[j])
                                if_else_statements['if_elses'].append(self._parse_elif_else_then_statements(working_lines[elif_i : j]))
                                elif_i = j
                            elif line_upper.startswith("ELSE") and line_info["indent"] == elif_line_indent:
                                logger.debug(working_lines[elif_i],working_lines[j - 1])
                                if_else_statements['if_elses'].append(self._parse_elif_else_then_statements(working_lines[elif_i:j]))
                                logger.debug(working_lines[j + 1],working_lines[-1])
                                if_else_statements['else_statements'].append(working_lines[j + 1 :])
                                i = len(working_lines)
                                break
                            elif line_upper.startswith("END IF;") and line_info["indent"] == elif_line_indent:
                                logger.debug(working_lines[elif_i],working_lines[j])
                                if_else_statements['if_elses'].append(self._parse_elif_else_then_statements(working_lines[elif_i : j]))
                                i = len(working_lines)
                                break
                        j += 1
                elif line_upper.startswith("ELSE") and item["indent"] == elif_line_indent:
                    else_i = i
                    if elif_i == -1:
                        if_else_statements['then_statements'].extend(working_lines[then_i+1:i])
                    # logger.debug(f"else_statements: {working_lines[i+1]["line_no"]}, {working_lines[-1]["line_no"]}")
                    if_else_statements['else_statements'].append(working_lines[i + 1 :])
                    i = len(working_lines)
            i += 1
        if else_i == -1 and elif_i == -1:
            logger.debug(f"else_i: {else_i} elif_i: {elif_i} then_statements: { working_lines[then_i+1:-1]}")
            # if then_i+1 == len(working_lines):
            if_else_statements['then_statements'].extend(working_lines[then_i+1:-1])
        logger.debug(f"if_else_statements: {if_else_statements}")
        return if_else_statements

    def _parse_elif_else_then_statements(self, working_lines: List[Dict[str, Any]]):
        """
        Parse elif and else then statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        elif_else_then_statements = working_lines
        print(f"elif_else_then_statements: {elif_else_then_statements}")
        logger.debug(elif_else_then_statements)
        condition = ""
        then_i = 0
        logger.debug(f"elif_else_then_statements[0]: {elif_else_then_statements[0]}")
        if elif_else_then_statements[0]["line"].strip().upper().endswith("THEN"):
            then_i = 0
            condition = self._extract_value_from_when_then(
                [elif_else_then_statements[0]], ["ELSIF", "THEN"]
            )
        else:
            # Multi-line: WHEN value ... THEN
            # Find the THEN clause on subsequent lines
            then_i = -1
            j = 1
            while j < len(elif_else_then_statements):
                # Extract value from current line
                logger.debug(f"elif_else_then_statements[j]: {elif_else_then_statements[j]}")
                if (
                    elif_else_then_statements[j]["line"]
                    .strip()
                    .upper()
                    .endswith("THEN")
                ):
                    then_i = j
                    break
                j += 1
            if then_i != -1:
                condition = self._extract_value_from_when_then(
                    elif_else_then_statements[: then_i + 1], ["ELSIF", "THEN"]
                )
        logger.debug(f"elif_else_then_statements 0: {elif_else_then_statements[0]['line_no']} then_i: {elif_else_then_statements[then_i]['line_no']}")
        logger.debug(f"case_when_then_statements: {elif_else_then_statements}")
        logger.debug(f"elif_else_then_statements[0]['indent']: {elif_else_then_statements[0]['indent']}")
        elif_statements = {
            "type": "elif_statement",
            "elif_line_no": elif_else_then_statements[0]["line_no"],
            "elif_indent": elif_else_then_statements[0]["indent"],
            "condition": condition,
            "then_line_no": elif_else_then_statements[then_i]["line_no"],
            "then_statements": elif_else_then_statements[then_i + 1 :],
        }
        return elif_statements

    def _parse_case_when(self):
        """
        Parse CASE WHEN ELSE statements from the main section of SQL with proper nested structure based on indentation.
        First detects CASE and END CASE; line numbers, then finds all WHEN and ELSE statements at the same indentation level.
        Maintains the hierarchical structure of CASE-WHEN-ELSE blocks by checking indentation levels.
        Updates self.main_section_lines with parsed blocks.
        """

        def parse_case_when(working_lines: List[Dict[str, Any]]):
            case_when_statements = []
            i = 0
            while i < len(working_lines):
                item = working_lines[i]
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("CASE"):
                        for j in range(i + 1, len(working_lines)):
                            line_info = working_lines[j]
                            if "line" in line_info:
                                line_upper = line_info["line"].strip().upper()
                                if line_upper.startswith("END CASE;") and line_info["indent"] == item["indent"]:
                                    logger.debug(f"case_i: {item["line_no"]} i: {line_info["line_no"]}")
                                    case_when_statement = self._parse_case_when_statements(working_lines[i: j+1])
                                    for when_clause in case_when_statement["when_clauses"]:
                                        when_clause["then_statements"] = parse_case_when(when_clause["then_statements"])
                                    case_when_statement["else_statements"] = parse_case_when(case_when_statement["else_statements"])
                                    case_when_statements.append(case_when_statement)
                                    i = j
                                    break
                    else:
                        case_when_statements.append(item)
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                # Process CASE statements in begin_end_statements
                elif "type" in item:
                    if item["type"] == "begin_end":
                        # Process CASE statements in begin_end_statements
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_case_when(item["begin_end_statements"])
                        # Process CASE statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_case_when(handler["exception_statements"])
                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_case_when(clause["then_statements"])
                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_case_when(item["else_statements"])
                    # Process CASE statements in for_loop
                    elif item["type"] == "for_loop" and "for_statements" in item:
                        item["for_statements"] = parse_case_when(item["for_statements"])
                    # Process CASE statements in if_else
                    elif item["type"] == "if_else":
                        if "then_statements" in item:
                            item["then_statements"] = parse_case_when(item["then_statements"])
                        if "if_elses" in item:
                            for elsif_block in item["if_elses"]:
                                if "then_statements" in elsif_block:
                                    elsif_block["then_statements"] = parse_case_when(elsif_block["then_statements"])
                        if "else_statements" in item:
                            item["else_statements"] = parse_case_when(item["else_statements"])
                    case_when_statements.append(item)
                i += 1
            return case_when_statements

        self.main_section_lines["begin_end_statements"] = parse_case_when(self.main_section_lines["begin_end_statements"])
        for k, handler in enumerate(self.main_section_lines["exception_handlers"]):
            if "exception_statements" in handler:
                self.main_section_lines['exception_handlers'][k]["exception_statements"] = parse_case_when(handler["exception_statements"])

    def _parse_case_when_statements(self, working_lines: List[Dict[str, Any]]):
        """
        Parse case when statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        case_when_statement = {
            "condition": working_lines[0]["line"].strip()[4:],
            "type": "case_when",
            "case_line_no": working_lines[0]["line_no"],
            "case_indent": working_lines[0]["indent"],
            "end_case_line_no": working_lines[-1]["line_no"],
            "when_clauses": [],
            "else_statements": [],
        }
        then_i = 0
        for j in range(1, len(working_lines)):
            line_info = working_lines[j]
            line_upper = line_info["line"].strip().upper()
            logger.debug(f"line_info : {line_info}")
            if line_upper.startswith("WHEN") or line_upper.startswith("ELSE"):
                then_i = j
                break
            case_when_statement["condition"] += line_info["line"].strip()
        when_line_indent = working_lines[then_i]["indent"]
        when_i = -1
        i = then_i
        while i < len(working_lines):
            line_info = working_lines[i]
            line_upper = line_info["line"].strip().upper()
            if line_upper.startswith("WHEN") and line_info["indent"] == when_line_indent:
                when_i = i
                i += 1
                while i < len(working_lines):
                    line_info = working_lines[i]
                    line_upper = line_info["line"].strip().upper()
                    if line_upper.startswith("WHEN") and line_info["indent"] == when_line_indent:
                        i -= 1
                        # logger.debug(working_lines[when_i] working_lines[i])
                        case_when_statement["when_clauses"].append(self._parse_case_when_then_statements(working_lines[when_i : i + 1]))
                        break
                    if line_upper.startswith("ELSE") and line_info["indent"] == when_line_indent:
                        # logger.debug(working_lines[when_i], working_lines[i - 1])
                        case_when_statement["when_clauses"].append(self._parse_case_when_then_statements(working_lines[when_i:i]))
                        logger.debug(working_lines[i + 1], working_lines[-1])
                        case_when_statement["else_statements"] = working_lines[i + 1 : len(working_lines)-1]
                        i = len(working_lines)
                        break
                    i += 1
            i += 1
        return case_when_statement

    def _parse_case_when_then_statements(self, working_lines: List[Dict[str, Any]]):
        """
        Parse case when then statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        case_when_then_statements = working_lines
        logger.debug(case_when_then_statements)
        condition = ""
        then_i = 0
        if case_when_then_statements[0]["line"].strip().upper().endswith("THEN"):
            then_i = 0
            condition = self._extract_value_from_when_then(
                [case_when_then_statements[0]], ["WHEN", "THEN"]
            )
        else:
            # Multi-line: WHEN value ... THEN
            # Find the THEN clause on subsequent lines
            then_i = -1
            j = 1
            while j < len(case_when_then_statements):
                # Extract value from current line
                if (
                    case_when_then_statements[j]["line"]
                    .strip()
                    .upper()
                    .endswith("THEN")
                ):
                    then_i = j
                    break
                j += 1
            if then_i != -1:
                condition = self._extract_value_from_when_then(
                    case_when_then_statements[: then_i + 1], ["WHEN", "THEN"]
                )
        logger.debug(f"case_when_then_statements 0: {case_when_then_statements[0]['line_no']} then_i: {case_when_then_statements[then_i]['line_no']}")
        logger.debug(f"case_when_then_statements: {case_when_then_statements}")
        when_statements = {
            "type": "when_statement",
            "when_line_no": case_when_then_statements[0]["line_no"],
            "when_indent": case_when_then_statements[0]["indent"],
            "condition": condition,
            "then_line_no": case_when_then_statements[then_i]["line_no"],
            "then_statements": case_when_then_statements[then_i + 1 :],
        }
        return when_statements

    def _parse_begin_blocks(self):
        """
        Parse top-level BEGIN blocks from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Uses the structured line format.
        """
        logger.debug("Starting top-level BEGIN blocks parsing")

        # Initialize main_section_lines with lines from the main section
        begin_line_no = -1
        begin_line_indent = -1
        exception_lines_no = -1
        end_line_no = -1
        for i in range(len(self.structured_lines)):
            line_info = self.structured_lines[i]
            line_upper = line_info["line"].strip().upper()
            if line_upper.startswith("BEGIN") and begin_line_no == -1:
                begin_line_no = i
                begin_line_indent = line_info["indent"]
            if line_upper.startswith("EXCEPTION") and line_info["indent"] == begin_line_indent:
                exception_lines_no = i
            if line_upper.endswith("END;") and line_info["indent"] == begin_line_indent:
                end_line_no = i
        self.main_section_lines = {
            "type": "begin_end",
            "begin_line_no": self.structured_lines[begin_line_no]["line_no"],
            "begin_indent": self.structured_lines[begin_line_no]["indent"],
            "begin_end_statements": self.structured_lines[begin_line_no + 1 : exception_lines_no] if exception_lines_no != -1 else self.structured_lines[begin_line_no + 1 : end_line_no],
            "exception_handlers": self._parse_exception_handlers(self.structured_lines[exception_lines_no + 1 : end_line_no]) if exception_lines_no != -1 else [],
            "exception_line_no": self.structured_lines[exception_lines_no]["line_no"] if exception_lines_no != -1 else -1,
            "end_line_no": self.structured_lines[end_line_no]["line_no"],
        }

    def _parse_begin_end_statements(self):
        """
        Parse begin_end_statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """

        def parse_begin_end_statements(working_lines: List[Dict[str, Any]]):
            begin_end_statements = []
            i = 0
            begin_i = -1
            begin_line_indent = -1
            exception_i = -1
            while i < len(working_lines):
                item = working_lines[i]
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("BEGIN") and begin_i == -1:
                        logger.debug(f"Begin line: {item} {i}")
                        begin_i = i
                        begin_line_indent = item["indent"]
                        while i < len(working_lines):
                            item = working_lines[i]
                            line_upper = item["line"].strip().upper()
                            if line_upper.startswith("EXCEPTION") and item["indent"] == begin_line_indent:
                                logger.debug(f"Exception line: {item} {i}")
                                exception_i = i
                            if line_upper.endswith("END;") and item["indent"] == begin_line_indent:
                                        logger.debug(f"End line: {item} {i}")
                                        begin_end_statements.append(
                                            {
                                                "type": "begin_end",
                                                "begin_line_no": working_lines[begin_i]["line_no"],
                                                "begin_indent": begin_line_indent,
                                                "begin_end_statements": parse_begin_end_statements(working_lines[begin_i + 1 : exception_i] if exception_i != -1 else working_lines[begin_i + 1 : i]),
                                                "exception_handlers": self._parse_exception_handlers(working_lines[exception_i + 1 : i]) if exception_i != -1 else [],
                                                "exception_line_no": working_lines[exception_i]["line_no"] if exception_i != -1 else -1,
                                                "end_line_no": item["line_no"],
                                            }
                                        )
                                        begin_i = -1
                                        begin_line_indent = -1
                                        exception_i = -1
                                        break
                            i += 1
                    else:
                        begin_end_statements.append(item)
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                # Process CASE statements in begin_end_statements
                elif "type" in item:
                    if item["type"] == "begin_end":
                        # Process CASE statements in begin_end_statements
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_begin_end_statements(item["begin_end_statements"])
                        # Process CASE statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_begin_end_statements(handler["exception_statements"])
                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_begin_end_statements(clause["then_statements"])
                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_begin_end_statements(item["else_statements"])
                    # Process CASE statements in for_loop
                    elif item["type"] == "for_loop" and "for_statements" in item:
                        item["for_statements"] = parse_begin_end_statements(item["for_statements"])
                    # Process CASE statements in if_else
                    elif item["type"] == "if_else":
                        if "then_statements" in item:
                            item["then_statements"] = parse_begin_end_statements(item["then_statements"])
                        if "if_elses" in item:
                            for elsif_block in item["if_elses"]:
                                if "then_statements" in elsif_block:
                                    elsif_block["then_statements"] = parse_begin_end_statements(elsif_block["then_statements"])
                        if "else_statements" in item:
                            item["else_statements"] = parse_begin_end_statements(item["else_statements"])
                    begin_end_statements.append(item)
                i += 1
            return begin_end_statements

        self.main_section_lines["begin_end_statements"] = parse_begin_end_statements(self.main_section_lines["begin_end_statements"])
        for k, handler in enumerate(self.main_section_lines["exception_handlers"]):
            if "exception_statements" in handler:
                self.main_section_lines['exception_handlers'][k]["exception_statements"] = parse_begin_end_statements(handler["exception_statements"])

    def _parse_exception_handlers(self, working_lines: List[Dict[str, Any]]):
        """
        Parse exception_handlers from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        exception_handlers = []
        i = 0
        while i < len(working_lines):
            line_info = working_lines[i]
            line_upper = line_info["line"].strip().upper()
            if line_upper.startswith("WHEN"):
                when_i = i
                # Check if WHEN and THEN are on the same line
                if line_upper.endswith("THEN"):
                    # Same line: WHEN exception_name THEN
                    then_i = i
                else:
                    # Multi-line: WHEN exception_name ... THEN
                    # Find the THEN clause on subsequent lines
                    then_i = -1
                    j = i + 1
                    while j < len(working_lines):
                        j_line_info = working_lines[j]
                        j_line_upper = j_line_info["line"].strip().upper()
                        # Extract exception name from current line
                        if j_line_upper.endswith("THEN"):
                            then_i = j
                            break
                        j += 1
                    if then_i == -1:
                        # No THEN found, skip this WHEN
                        i += 1
                        continue
                # Create exception handler structure
                exception_handler = {
                    "type": "exception_handler",
                    "exception_name": (
                        self._extract_value_from_when_then([working_lines[when_i]], ["WHEN", "THEN"])
                        if when_i == then_i
                        else self._extract_value_from_when_then(working_lines[when_i : then_i + 1], ["WHEN", "THEN"])
                    ),
                    "when_line_no": working_lines[when_i]["line_no"],
                    "when_indent": working_lines[when_i]["indent"],
                    "then_line_no": working_lines[then_i]["line_no"],
                    "exception_statements": [],
                }

                # Collect exception statements (lines after THEN until next WHEN or end)
                k = then_i + 1
                while k < len(working_lines):
                    k_line_info = working_lines[k]
                    k_line_upper = k_line_info["line"].strip().upper()

                    # Stop if we encounter another WHEN clause at the same indentation level
                    if (
                        k_line_upper.startswith("WHEN")
                        and k_line_info["indent"] == working_lines[when_i]["indent"]
                    ):
                        break

                    # Add the line to exception statements
                    exception_handler["exception_statements"].append(k_line_info)
                    k += 1
                exception_handlers.append(exception_handler)
                i = k  # Continue from where we left off
            else:
                i += 1

        logger.debug(f"exception_handler: {exception_handlers}")
        return exception_handlers

    def _parse_function_calling(self, working_lines: List[Dict[str, Any]], function_name: str):
        """
        Parse function calling statements from the main section of SQL.
        Extracts the structure and converts to a structured format.

        Handles patterns like:
        - RAISE_APPLICATION_ERROR(-20101, 'Invalid theme number format');
        - MDM_UTIL_ADDRESSES.MODIFY_COMPANY_ADDRESS(P_COMPANY_CD => :NEW.COMPANY_CD, ...);
        - Multi-line function calls

        Returns:
            dict: Structured representation of the function call
        """
        # Combine all lines into a single string
        combined_line = self.combine_lines(working_lines)
        logger.debug(f"combined_line: {combined_line}")
        # Remove trailing semicolon if present
        combined_line = combined_line.rstrip(";").strip()

        # # Extract the function name
        # if not combined_line.upper().startswith(function_name.upper()):
        #     return combined_line

        # Find the opening parenthesis after function name
        open_paren_pos = combined_line.find("(")
        if open_paren_pos == -1:
            return combined_line

        # Extract the parameters part (everything between parentheses)
        params_start = open_paren_pos + 1
        params_end = self._find_matching_closing_paren(combined_line, open_paren_pos)
        if params_end == -1:
            return combined_line

        params_text = combined_line[params_start:params_end].strip()

        # Parse the parameters using the enhanced parser
        parameters = self._parse_function_calling_params(params_text, function_name)

        # Create the structured representation
        result = {
            "type": "function_calling",
            "function_name": function_name,
            "parameters": parameters,
        }
        # print(f"function_calling: {result}")

        return result

    def _find_matching_closing_paren(self, text: str, open_pos: int) -> int:
        """
        Find the matching closing parenthesis for an opening parenthesis.
        Handles nested parentheses correctly.

        Args:
            text (str): The text to search in
            open_pos (int): Position of the opening parenthesis

        Returns:
            int: Position of the matching closing parenthesis, or -1 if not found
        """
        stack = 0
        for i in range(open_pos, len(text)):
            if text[i] == "(":
                stack += 1
            elif text[i] == ")":
                stack -= 1
                if stack == 0:
                    return i
        return -1

    def _parse_function_calling_params(self, params_text: str, function_name: str) -> Dict[str, Any]:
        """
        Parse the parameters of a function call.
        
        Handles various parameter patterns:
        - RAISE_APPLICATION_ERROR: (-20101, 'Error message') - positional parameters
        - MDM_UTIL functions: (P_PARAM => value, P_PARAM2 => value2) - named parameters
        - Simple calls: (V_TRIGGER_NAME) - single parameter
        - Complex expressions: ('Error: ' || SQLERRM) - string concatenation
        
        Args:
            params_text (str): The text between parentheses of function call
            function_name (str): The name of the function being called
            
        Returns:
            Dict[str, Any]: Structured representation of parameters
        """
        # Remove leading/trailing whitespace
        params_text = params_text.strip()
        
        # Initialize parameters structure
        parameters = {
            "parameter_type": "unknown",
            "positional_params": [],
            "named_params": {},
            "raw_text": params_text
        }
        
        # Handle empty parameters
        if not params_text:
            parameters["parameter_type"] = "empty"
            return parameters
        
        # Determine parameter type based on function name and content
        if self._is_named_parameter_function(params_text):
            parameters.update(self._parse_named_parameters(params_text))
        elif self._is_positional_parameter_function(function_name, params_text):
            parameters.update(self._parse_positional_parameters(params_text))
        else:
            # Try to auto-detect parameter type
            if "=>" in params_text:
                parameters.update(self._parse_named_parameters(params_text))
            else:
                parameters.update(self._parse_positional_parameters(params_text))
        
        return parameters

    def _is_named_parameter_function(self, params_text: str) -> bool:
        """
        Check if the function uses named parameters.
        
        Args:
            params_text (str): The parameter text
            
        Returns:
            bool: True if named parameters are detected
        """
        return "=>" in params_text

    def _is_positional_parameter_function(self, function_name: str, params_text: str) -> bool:
        """
        Check if the function uses positional parameters.
        
        Args:
            function_name (str): The function name
            params_text (str): The parameter text
            
        Returns:
            bool: True if positional parameters are expected
        """
        # RAISE_APPLICATION_ERROR typically uses positional parameters
        if function_name.upper() == "RAISE_APPLICATION_ERROR":
            return True
        
        # Functions with simple parameters
        if "," in params_text and "=>" not in params_text:
            return True
        
        return False

    def _parse_named_parameters(self, params_text: str) -> Dict[str, Any]:
        """
        Parse named parameters in the format P_PARAM => value.
        
        Args:
            params_text (str): The parameter text
            
        Returns:
            Dict[str, Any]: Parsed named parameters
        """
        result = {
            "parameter_type": "named",
            "named_params": {},
            "positional_params": []
        }
        
        # Split parameters by comma, handling nested parentheses
        param_parts = self._split_parameters_by_comma(params_text)
        
        for part in param_parts:
            part = part.strip()
            if "=>" in part:
                # Named parameter: P_PARAM => value
                param_name, param_value = self._extract_named_parameter(part)
                if param_name:
                    result["named_params"][param_name] = param_value
            else:
                # Positional parameter (fallback)
                result["positional_params"].append(part)
        
        return result

    def _parse_positional_parameters(self, params_text: str) -> Dict[str, Any]:
        """
        Parse positional parameters in the format value1, value2, value3.
        
        Args:
            params_text (str): The parameter text
            
        Returns:
            Dict[str, Any]: Parsed positional parameters
        """
        result = {
            "parameter_type": "positional",
            "named_params": {},
            "positional_params": []
        }
        
        # Split parameters by comma, handling nested parentheses
        param_parts = self._split_parameters_by_comma(params_text)
        
        for part in param_parts:
            part = part.strip()
            result["positional_params"].append(part)
        
        return result

    def _split_parameters_by_comma(self, params_text: str) -> List[str]:
        """
        Split parameters by comma, respecting parentheses and quotes.
        
        Args:
            params_text (str): The parameter text
            
        Returns:
            List[str]: List of parameter parts
        """
        parts = []
        current_part = ""
        paren_stack = 0
        in_single_quote = False
        in_double_quote = False
        
        for char in params_text:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "(" and not in_single_quote and not in_double_quote:
                paren_stack += 1
            elif char == ")" and not in_single_quote and not in_double_quote:
                paren_stack -= 1
            elif char == "," and paren_stack == 0 and not in_single_quote and not in_double_quote:
                parts.append(current_part.strip())
                current_part = ""
                continue
            
            current_part += char
        
        # Add the last part
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts

    def _extract_named_parameter(self, param_part: str) -> Tuple[str, str]:
        """
        Extract parameter name and value from a named parameter.
        
        Args:
            param_part (str): The parameter part (e.g., "P_PARAM => value")
            
        Returns:
            Tuple[str, str]: (parameter_name, parameter_value)
        """
        # Find the first occurrence of "=>" (not inside quotes or parentheses)
        arrow_pos = -1
        paren_stack = 0
        in_single_quote = False
        in_double_quote = False
        
        for i, char in enumerate(param_part):
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "(" and not in_single_quote and not in_double_quote:
                paren_stack += 1
            elif char == ")" and not in_single_quote and not in_double_quote:
                paren_stack -= 1
            elif char == "=" and i + 1 < len(param_part) and param_part[i + 1] == ">" and paren_stack == 0 and not in_single_quote and not in_double_quote:
                arrow_pos = i
                break
        
        if arrow_pos == -1:
            return "", param_part
        
        # Extract parameter name and value
        param_name = param_part[:arrow_pos].strip()
        param_value = param_part[arrow_pos + 2:].strip()
        
        return param_name, param_value

    def _extract_value_from_when_then(self, working_lines: List[Dict[str, Any]], change_blocks: [str, str]) -> str:
        """
        Extract the value from a WHEN clause.

        Handles both formats:
        - Single line: "WHEN value THEN"
        - Multi-line: "WHEN value" followed by "THEN" on next line
        - Multi-line: "WHEN value" followed by "THEN" on next line

        Args:
            working_lines (List[Dict[str, Any]]): The lines to extract the value from
            change_blocks (List[str]): The blocks to change

        Returns:
            str: The extracted value

        Examples:
            "WHEN ERR_UPD THEN" -> "ERR_UPD"
            "WHEN OTHERS THEN" -> "OTHERS"
            "WHEN NO_DATA_FOUND THEN" -> "NO_DATA_FOUND"
            "WHEN value" -> "value"
        """
        # Remove leading/trailing whitespace and convert to uppercase for consistency
        line = self.combine_lines(working_lines)
        # Remove "WHEN" prefix
        if line.startswith(change_blocks[0]):
            line = line[len(change_blocks[0]) :].strip()

        # If line ends with "THEN", remove it
        if line.endswith(change_blocks[1]):
            line = line[: -len(change_blocks[1])].strip()

        # For multi-line cases, just return the value part
        return line.strip()

    def combine_lines(self, working_lines: List[Dict[str, Any]]):
        """
        Combine lines from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        if len(working_lines) == 0:
            return ""
        elif len(working_lines) == 1:
            line = working_lines[0]["line"].strip()
        elif len(working_lines) > 1:
            line = ""
            for i in range(len(working_lines)):
                line += working_lines[i]["line"].strip() + " "
            line = line.strip()
            logger.debug(line)
        return line.strip()

    def rest_strings(self) -> List[str]:
        """
        Find all "rest string" content in various statement types within the JSON structure.


        This method recursively searches through:
        - begin_end_statements
        - exception_statements
        - then_statements
        - else_statements


        Returns:
            List[str]: List of all rest string content found
        """
        rest_strings_list = []

        def extract_rest_strings_from_item(item):
            """Recursively extract rest strings from any item"""
            if isinstance(item, dict):
                # Check for "indent" field which contains rest string content
                if "indent" in item:
                    print(item["line"])
                    rest_strings_list.append(item)

                if "type" in item:
                    # print(f"item: {item}")
                    self.strng_convert_json[item["type"]] += 1
                # Recursively process all values in the dictionary
                for value in item.values():
                    extract_rest_strings_from_item(value)

            elif isinstance(item, list):
                # Recursively process all items in the list
                for sub_item in item:
                    extract_rest_strings_from_item(sub_item)

        # Process main_section_lines
        extract_rest_strings_from_item(self.main_section_lines)
        # print(f'rest_strings_list {rest_strings_list}')	
        self.rest_string_list = rest_strings_list
        # # rest_strings_list to covert like ("filename","line","line_no") and add to available_rest_strings
        # dataframe_rest_strings = pd.DataFrame(columns=["filename", "line", "line_no"])
        # for i in rest_strings_list:
        #     dataframe_rest_strings._append({"filename": self.file_details["filename"], "line": i["line"], "line_no": i["line_no"]},ignore_index=True)
        # # print(dataframe_rest_strings)
        
        # append_to_excel_sheet(dataframe_rest_strings, sheet_name="non_parse")

    def to_json(self):
        """
        Convert the analyzed trigger structure to a JSON-serializable dictionary.


        This method prepares the final structured representation of the Oracle trigger,
        including declarations, main blocks, and conversion statistics. If rule violations
        were detected, it returns an error structure instead of the parsed content.


        Returns:
            Dict: JSON-serializable dictionary representing the analyzed trigger structure
                 or error information if validation failed
        """

        # Step 4: Construct the result dictionary
        result = {
            "declarations": {
                "variables": self.variables,
                "constants": self.constants,
                "exceptions": self.exceptions,
            },
            "main": self.main_section_lines,
            "sql_comments": self.sql_comments,
            # "sql_lines": self.structured_lines,
            "rest_string_list": self.rest_string_list,
        }

        # # Step 5: Add additional metadata to the result
        # # Include structured lines for clients that need them
        # result["structured_lines"] = self.structured_lines

        # Add conversion statistics
        result["conversion_stats"] = {
            "declaration_count": len(self.variables)
            + len(self.constants)
            + len(self.exceptions),
            "comment_count": len(self.sql_comments),
            "sql_convert_count": self.strng_convert_json,
        }

        # Include parse timestamp and file details
        result["metadata"] = {
            "parse_timestamp": self._get_timestamp(),
            "parser_version": "1.0",  # Increment when making significant parser changes
            "file_details": self.file_details,
        }

        # Log detailed statistics for troubleshooting
        logger.debug(f"JSON conversion complete: {len(self.variables)} vars, {len(self.constants)} consts, {len(self.exceptions)} excs, {len(self.sql_comments)} comments")
        return result

    def _get_timestamp(self):
        """Get current timestamp in ISO format for metadata"""
        from datetime import datetime

        return datetime.now().isoformat()


    def extract_file_details(self,filepath: str) -> Dict[str, Any]:
        """
        Extract file details from a file path.
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            Dict[str, Any]: Dictionary containing file details
        """
        import os
        from pathlib import Path
        
        try:
            file_path = Path(filepath)
            stat = file_path.stat()
            
            return {
                "filename": file_path.name,
                "filepath": str(file_path.absolute()),
                "filesize": stat.st_size,
                "file_extension": file_path.suffix,
                "last_modified": stat.st_mtime,
                "created_time": stat.st_ctime,
                "is_file": file_path.is_file(),
                "is_readable": os.access(filepath, os.R_OK),
            }
        except (OSError, ValueError) as e:
            return {
                "filename": os.path.basename(filepath) if filepath else "unknown",
                "filepath": filepath,
                "error": f"Could not extract file details: {str(e)}"
            }

    # @classmethod
    # def from_file(cls, filepath: str, encoding: str = 'utf-8') -> 'OracleTriggerAnalyzer':
    #     """
    #     Create an OracleTriggerAnalyzer instance from a file.
        
    #     Args:
    #         filepath (str): Path to the SQL file
    #         encoding (str): File encoding (default: 'utf-8')
            
    #     Returns:
    #         OracleTriggerAnalyzer: Analyzer instance with file details
            
    #     Raises:
    #         FileNotFoundError: If the file doesn't exist
    #         UnicodeDecodeError: If the file can't be decoded with the specified encoding
    #     """
    #     import os
        
    #     if not os.path.exists(filepath):
    #         raise FileNotFoundError(f"File not found: {filepath}")
        
    #     # Extract file details
    #     file_details = cls.extract_file_details(filepath)
        
    #     # Read file content
    #     with open(filepath, 'r', encoding=encoding) as f:
    #         sql_content = f.read()
        
    #     # Create analyzer instance with file details
    #     return cls(sql_content, file_details)

    def format_values(self, values: str):
        """
        Format a list of values with proper quotes.

        Args:
            values (str): The values to format

        Returns:
            str: The formatted values
        """
        if values is None:
            return None
        formatted_msg = values.strip()
        if "||" in values:
            formatted_msg = formatted_msg.split("||")
            for i in range(len(formatted_msg)):
                formatted_msg[i] = formatted_msg[i].strip()
                logger.debug(formatted_msg[i])
                if formatted_msg[i].startswith("'") and not formatted_msg[i].endswith(
                    "'"
                ):
                    formatted_msg[i] = formatted_msg[i] + "'"
                elif not formatted_msg[i].startswith("'") and formatted_msg[i].endswith(
                    "'"
                ):
                    formatted_msg[i] = "'" + formatted_msg[i]
            formatted_msg = " || ".join(formatted_msg)
        # else:

        #         formatted_msg = formatted_msg
        #     else:
        #         formatted_msg = "'" + formatted_msg + "'"
        return formatted_msg



