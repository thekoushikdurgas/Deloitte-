import json
import os
import re
import time
from typing import Any, Dict, List, Tuple

from numpy import copy
from utilities.common import (
    logger,
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

    def __init__(self, sql_content: str):
        """
        Initialize the OracleTriggerAnalyzer with SQL content.


        Args:
            sql_content (str): The raw SQL trigger content to analyze


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
            len(sql_content),
        )

        self.sql_content: str = sql_content
        self.declare_section: List[int] = [0, 0]
        # self.main_section: List[int] = [0, 0]
        self.main_section_lines: Dict = {}
        self.variables: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []
        self.exceptions: List[Dict[str, Any]] = []
        self.sql_comments: List[str] = []
        self.structured_lines: List[Dict[str, Any]] = []
        self.rest_strings_line: List[Dict] = []
        self.strng_convert_json: int = 0

        logger.debug(
            f"structured lines conversion {len(self.structured_lines)} lines processed",
        )

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
                    "is_end_semicolon": is_end_semicolon,
                }
            )

        debug(
            "Structured lines conversion complete: %d total, %d with semicolons, %d empty lines skipped",
            len(self.structured_lines),
            semicolon_lines,
            empty_lines,
        )

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
                        "is_end_semicolon": clean_line.rstrip().endswith(";"),
                    }
                )

        # If we end with an unclosed block comment, add it to extracted comments
        if in_block_comment and current_comment:
            extracted_comments.append(current_comment)
            logger.debug("Unclosed block comment detected")

        # Update self.structured_lines and self.sql_comments
        self.structured_lines = clean_lines
        self.sql_comments.extend(extracted_comments)

        logger.debug(
            "Block comment stripping complete: %d comments extracted, %d lines cleaned",
            len(extracted_comments),
            len(clean_lines),
        )

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
                            "is_end_semicolon": clean_part.rstrip().endswith(";"),
                        }
                    )

        # Update self.structured_lines and self.sql_comments
        self.structured_lines = clean_lines
        self.sql_comments.extend(extracted_comments)

        logger.debug(
            "Inline comment stripping complete: %d comments extracted, %d lines cleaned",
            len(extracted_comments),
            len(clean_lines),
        )

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
        if self.declare_section[0] > 0:
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
        self._parse_case_when()
        self._parse_if_else()
        # self._parse_for_loop()
        # self._parse_assignment_statement()
        self._parse_sql_statements()
        # self._parse_final_statement()

        # to check how many rest strings are in main section
        self.rest_strings_line = self.rest_strings()

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
            "RAISE": "raise_statement"
            }
        """
        STMT_TYPE_MAP = [
            ["SELECT", "select_statement"],
            ["INSERT", "insert_statement"],
            ["UPDATE", "update_statement"],
            ["DELETE", "delete_statement"],
            ["RAISE", "raise_statement"],
        ]

        def parse_sql_statements(working_lines: List[Dict[str, Any]], json_path: str):
            sql_statements = []
            i = 0
            stmt_type_i = -1
            stmt_type_type = ""
            while i < len(working_lines):
                # print(f"i: {i}")
                item = working_lines[i]
                # print(f"item: {item}")
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("SELECT") and stmt_type_i == -1:
                            stmt_type_i = i
                            stmt_type_type = "select_statement"
                            print(f"stmt_type_i: {working_lines[stmt_type_i]['line_no']} || {stmt_type_type}")
                    elif line_upper.startswith("INSERT") and stmt_type_i == -1:
                            stmt_type_i = i
                            stmt_type_type = "insert_statement"
                            print(f"stmt_type_i: {working_lines[stmt_type_i]['line_no']} || {stmt_type_type}")
                    elif line_upper.startswith("UPDATE") and stmt_type_i == -1:
                            stmt_type_i = i
                            stmt_type_type = "update_statement"
                            print(f"stmt_type_i: {working_lines[stmt_type_i]['line_no']} || {stmt_type_type}")
                    elif line_upper.startswith("DELETE") and stmt_type_i == -1:
                            stmt_type_i = i
                            stmt_type_type = "delete_statement"
                            print(f"stmt_type_i: {working_lines[stmt_type_i]['line_no']} || {stmt_type_type}")
                    elif line_upper.startswith("RAISE") and stmt_type_i == -1:
                            stmt_type_i = i
                            stmt_type_type = "raise_statement"
                            print(f"stmt_type_i: {working_lines[stmt_type_i]['line_no']} || {stmt_type_type}")
                    elif line_upper.endswith(";") and stmt_type_i != -1:
                        print(f"stmt_type: {working_lines[stmt_type_i]['line_no']} : {item['line_no']} || {stmt_type_type}")                         
                        # sql_statements.append({
                        #         "type": stmt_type_type,
                        #         "line": self.combine_lines(working_lines[stmt_type_i:i+1]),
                        #         "statement_line_no": working_lines[stmt_type_i]["line_no"],
                        #         "statement_indent": working_lines[stmt_type_i]["indent"],
                        # })
                        stmt_type_i = -1
                    # else:
                    #     stmt_type_line += " " +  item["line"].strip()
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                # Process IF statements in begin_end_statements
                elif "type" in item:
                    if item["type"] == "begin_end":
                        # Process IF statements in begin_end_statements
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_sql_statements(item["begin_end_statements"], json_path + "begin_end.begin_end_statements")
                        # Process IF statements in exception_handlers
                        if "exception_handlers" in item:
                            for k, handler in enumerate(item["exception_handlers"]):
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_sql_statements(handler["exception_statements"], json_path + f"begin_end.exception_handlers[{k}].exception_statements")

                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for k, clause in enumerate(item["when_clauses"]):
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_sql_statements(clause["then_statements"], json_path + f"case_when.when_clauses[{k}].then_statements")
                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_sql_statements(item["else_statements"], json_path + "case_when.else_statements")

                    elif item["type"] == "if_else":
                        # Process CASE statements in then_statements, if_elses, and else_statements
                        if "then_statements" in item:
                            item["then_statements"] = parse_sql_statements(item["then_statements"], json_path + "if_else.then_statements")
                        if "if_elses" in item:
                            for k, elsif_block in enumerate(item["if_elses"]):
                                if "then_statements" in elsif_block:
                                    elsif_block["then_statements"] = parse_sql_statements(elsif_block["then_statements"], json_path + f"if_else.if_elses[{k}].then_statements")
                        if "else_statements" in item:
                            item["else_statements"] = parse_sql_statements(item["else_statements"], json_path + "if_else.else_statements")
                    # Process SQL statements in for_loop
                    elif item["type"] == "for_loop":
                        if "for_statements" in item:
                            item["for_statements"] = parse_sql_statements(item["for_statements"], json_path + "for_loop.for_statements")
                    if stmt_type_i == -1:
                        sql_statements.append(item)
                i += 1
            return working_lines
        self.main_section_lines["begin_end_statements"] = parse_sql_statements(self.main_section_lines["begin_end_statements"],"main.begin_end_statements")

    def _parse_assignment_statement(self):
        """
        Parse assignment statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        Group assignment statements (:=) in the SQL code.
        Uses structured line dictionaries.
        """

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
            for_i = -1
            for_indent = -1
            while i < len(working_lines):
                item = working_lines[i]
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("FOR") and for_i == -1:
                        for_i = i
                        for_indent = item["indent"]
                        for_expression = ""
                        if line_upper.endswith("LOOP"):
                            for_expression = item["line"].strip()[3:-4]
                        else:
                            for j in range(for_i + 1, len(working_lines)):
                                line_info = working_lines[j]
                                line_upper = line_info["line"].strip().upper()
                                if line_upper.endswith("LOOP"):
                                    i = j - 1
                                    break
                                for_expression += line_info["line"].strip()
                        logger.debug(f"for_expression: {for_expression}")
                    elif (
                        line_upper.startswith("END LOOP;")
                        and item["indent"] == for_indent
                        and for_i != -1
                    ):
                        logger.debug(
                            f"for_i: {working_lines[for_i]["line_no"]} i: {item["line_no"]}"
                        )
                        for_loop_statements.append({
                            "for_expression": for_expression,
                            "type": "for_loop",
                            "for_line_no": working_lines[for_i]["line_no"],
                            "for_indent": for_indent,
                            "end_for_line_no": item["line_no"],
                        })
                        for_i = -1
                        for_indent = -1
                    elif for_i == -1:
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
                    elif item["type"] == "for_loop":
                        if "for_statements" in item:
                            item["for_statements"] = parse_for_loop(item["for_statements"])
                    if for_i == -1:
                        for_loop_statements.append(item)
                i += 1
            return for_loop_statements
        self.main_section_lines["begin_end_statements"] = parse_for_loop(self.main_section_lines["begin_end_statements"])

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
            if_i = -1
            if_indent = -1
            while i < len(working_lines):
                item = working_lines[i]
                logger.debug(f"item: {item}")
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("IF") and if_i == -1:
                        if_i = i
                        if_indent = item["indent"]
                        logger.debug(f"if_indent: {if_indent}")
                        if_expression = ""
                        if line_upper.endswith("THEN"):
                            if_expression = item["line"].strip()[2:-4]
                        else:
                            for j in range(if_i + 1, len(working_lines)):
                                line_info = working_lines[j]
                                line_upper = line_info["line"].strip().upper()
                                logger.debug(f"line_info : {line_info}")
                                if line_upper.endswith("THEN"):
                                    i = j - 1
                                    break
                                if_expression += line_info["line"].strip()
                        logger.debug(f"case_expression: {if_expression}")
                    elif (
                        line_upper.startswith("END IF;")
                        and item["indent"] == if_indent
                        and if_i != -1
                    ):
                        logger.debug(
                            f"if_i: {working_lines[if_i]["line_no"]} i: {item["line_no"]}"
                        )
                        if_then, if_elses, else_statements = (
                            self._parse_elif_else_statements(
                                working_lines[if_i + 1 : i], if_indent
                            )
                        )
                        if_then = parse_if_else(if_then)
                        for elif_clause in if_elses:
                            elif_clause["then_statements"] = parse_if_else(
                                elif_clause["then_statements"]
                            )
                        else_statements = parse_if_else(else_statements)
                        if_else_statements.append(
                            {
                                "if_expression": if_expression,
                                "type": "if_else",
                                "if_line_no": working_lines[if_i]["line_no"],
                                "then_statements": if_then,
                                "if_indent": if_indent,
                                "end_if_line_no": item["line_no"],
                                "if_elses": if_elses,
                                "else_statements": else_statements,
                            }
                        )
                        if_i = -1
                        if_indent = -1
                    elif if_i == -1:
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
                    elif item["type"] == "for_loop":
                        if "for_statements" in item:
                            item["for_statements"] = parse_if_else(item["for_statements"])
                    if if_i == -1:
                        if_else_statements.append(item)
                i += 1
            return if_else_statements

        self.main_section_lines["begin_end_statements"] = parse_if_else(self.main_section_lines["begin_end_statements"])

    def _parse_elif_else_statements(
        self, working_lines: List[Dict[str, Any]], elif_line_indent: int
    ):
        """
        Parse elif and else statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        elif_else_statements = working_lines
        i = 0
        if_then = []
        if_elses = []
        else_statements = []
        elif_i = -1
        while i < len(elif_else_statements):
            line_info = elif_else_statements[i]
            if isinstance(line_info, dict) and "line" in line_info:
                line_upper = line_info["line"].strip().upper()
                if (
                    line_upper.startswith("ELSIF")
                    and line_info["indent"] == elif_line_indent
                ):
                    if elif_i == -1:
                        if_then = elif_else_statements[0:i]
                    elif_i = i
                    i += 1
                    while i < len(elif_else_statements):
                        line_info = elif_else_statements[i]
                        logger.debug(f"line_info: {line_info}")
                        if isinstance(line_info, dict) and "line" in line_info:
                            line_upper = line_info["line"].strip().upper()
                            if (
                                line_upper.startswith("ELSIF")
                                and line_info["indent"] == elif_line_indent
                            ):
                                i -= 1
                                logger.debug(
                                    elif_else_statements[elif_i],
                                    elif_else_statements[i],
                                )
                                if_elses.append(
                                    self._parse_elif_else_then_statements(
                                        elif_else_statements[elif_i : i + 1]
                                    )
                                )
                                break
                            if (
                                line_upper.startswith("ELSE")
                                and line_info["indent"] == elif_line_indent
                            ):
                                logger.debug(
                                    elif_else_statements[elif_i],
                                    elif_else_statements[i - 1],
                                )
                                if_elses.append(
                                    self._parse_elif_else_then_statements(
                                        elif_else_statements[elif_i:i]
                                    )
                                )
                                logger.debug(
                                    elif_else_statements[i + 1],
                                    elif_else_statements[-1],
                                )
                                else_statements = elif_else_statements[
                                    i + 1 : len(elif_else_statements)
                                ]
                                i = len(elif_else_statements)
                                break
                        i += 1
                elif (
                    line_upper.startswith("ELSE")
                    and line_info["indent"] == elif_line_indent
                ):
                    if elif_i == -1:
                        if_then = elif_else_statements[0:i]
                    logger.debug(
                        f"else_statements: {elif_else_statements[i+1]["line_no"]}, {elif_else_statements[-1]["line_no"]}"
                    )
                    else_statements = elif_else_statements[
                        i + 1 : len(elif_else_statements)
                    ]
                    i = len(elif_else_statements)
            i += 1
        return if_then, if_elses, else_statements

    def _parse_elif_else_then_statements(self, working_lines: List[Dict[str, Any]]):
        """
        Parse elif and else then statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        elif_else_then_statements = working_lines
        logger.debug(elif_else_then_statements)
        elif_value = ""
        then_i = 0
        logger.debug(f"elif_else_then_statements[0]: {elif_else_then_statements[0]}")
        if elif_else_then_statements[0]["line"].strip().upper().endswith("THEN"):
            then_i = 0
            elif_value = self._extract_value_from_when_then(
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
                elif_value = self._extract_value_from_when_then(
                    elif_else_then_statements[: then_i + 1], ["ELSIF", "THEN"]
                )
        logger.debug(f"elif_else_then_statements 0: {elif_else_then_statements[0]['line_no']} then_i: {elif_else_then_statements[then_i]['line_no']}")
        logger.debug(f"case_when_then_statements: {elif_else_then_statements}")
        logger.debug(
            f"elif_else_then_statements[0]['indent']: {elif_else_then_statements[0]['indent']}"
        )
        elif_statements = {
            "type": "elif_statement",
            "elif_line_no": elif_else_then_statements[0]["line_no"],
            "elif_indent": elif_else_then_statements[0]["indent"],
            "elif_value": elif_value,
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
            case_i = -1
            case_indent = -1
            while i < len(working_lines):
                item = working_lines[i]
                if "line" in item:
                    line_upper = item["line"].strip().upper()
                    if line_upper.startswith("CASE") and case_i == -1:
                        case_i = i
                        case_indent = item["indent"]
                        case_expression = item["line"].strip()[4:]
                        for j in range(case_i + 1, len(working_lines)):
                            line_info = working_lines[j]
                            line_upper = line_info["line"].strip().upper()
                            logger.debug(f"line_info : {line_info}")
                            if line_upper.startswith("WHEN") or line_upper.startswith(
                                "ELSE"
                            ):
                                i = j - 1
                                break
                            case_expression += line_info["line"].strip()
                        logger.debug(f"case_expression: {case_expression}")
                    elif (
                        line_upper.startswith("END CASE;")
                        and item["indent"] == case_indent
                        and case_i != -1
                    ):
                        logger.debug(
                            f"case_i: {working_lines[case_i]["line_no"]} i: {item["line_no"]}"
                        )
                        when_clauses, else_statements = (
                            self._parse_case_when_statements(
                                working_lines[case_i + 1 : i]
                            )
                        )
                        for when_clause in when_clauses:
                            when_clause["then_statements"] = parse_case_when(
                                when_clause["then_statements"]
                            )
                        else_statements = parse_case_when(else_statements)
                        case_when_statements.append(
                            {
                                "case_expression": case_expression,
                                "type": "case_when",
                                "case_line_no": working_lines[case_i]["line_no"],
                                "case_indent": working_lines[case_i]["indent"],
                                "end_case_line_no": item["line_no"],
                                "when_clauses": when_clauses,
                                "else_statements": else_statements,
                            }
                        )
                        case_i = -1
                        case_indent = -1
                    elif case_i == -1:
                        case_when_statements.append(item)
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                # Process CASE statements in begin_end_statements
                elif "type" in item:
                    if item["type"] == "begin_end":
                        # Process CASE statements in begin_end_statements
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = parse_case_when(
                                item["begin_end_statements"]
                            )
                        # Process CASE statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = parse_case_when(
                                        handler["exception_statements"]
                                    )
                    elif item["type"] == "case_when":
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    clause["then_statements"] = parse_case_when(
                                        clause["then_statements"]
                                    )
                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            item["else_statements"] = parse_case_when(
                                item["else_statements"]
                            )
                    # Process CASE statements in for_loop
                    elif item["type"] == "for_loop":
                        if "for_statements" in item:
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
                    if case_i == -1:
                        case_when_statements.append(item)

                i += 1
            return case_when_statements

        self.main_section_lines["begin_end_statements"] = parse_case_when(
            self.main_section_lines["begin_end_statements"]
        )

    def _parse_case_when_statements(self, working_lines: List[Dict[str, Any]]):
        """
        Parse case when statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        case_when_statements = working_lines
        i = 0
        when_clauses = []
        else_statements = []
        when_line_indent = case_when_statements[0]["indent"]
        when_i = -1
        while i < len(case_when_statements):
            line_info = case_when_statements[i]
            line_upper = line_info["line"].strip().upper()
            if (
                line_upper.startswith("WHEN")
                and line_info["indent"] == when_line_indent
            ):
                when_i = i
                i += 1
                while i < len(case_when_statements):
                    line_info = case_when_statements[i]
                    line_upper = line_info["line"].strip().upper()
                    if (
                        line_upper.startswith("WHEN")
                        and line_info["indent"] == when_line_indent
                    ):
                        i -= 1
                        logger.debug(
                            case_when_statements[when_i], case_when_statements[i]
                        )
                        when_clauses.append(
                            self._parse_case_when_then_statements(
                                case_when_statements[when_i : i + 1]
                            )
                        )
                        break
                    if (
                        line_upper.startswith("ELSE")
                        and line_info["indent"] == when_line_indent
                    ):
                        logger.debug(
                            case_when_statements[when_i], case_when_statements[i - 1]
                        )
                        when_clauses.append(
                            self._parse_case_when_then_statements(
                                case_when_statements[when_i:i]
                            )
                        )
                        logger.debug(
                            case_when_statements[i + 1], case_when_statements[-1]
                        )
                        else_statements = case_when_statements[
                            i + 1 : len(case_when_statements)
                        ]
                        i = len(case_when_statements)
                        break
                    i += 1
            i += 1
        return when_clauses, else_statements

    def _parse_case_when_then_statements(self, working_lines: List[Dict[str, Any]]):
        """
        Parse case when then statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        case_when_then_statements = working_lines
        logger.debug(case_when_then_statements)
        when_value = ""
        then_i = 0
        if case_when_then_statements[0]["line"].strip().upper().endswith("THEN"):
            then_i = 0
            when_value = self._extract_value_from_when_then(
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
                when_value = self._extract_value_from_when_then(
                    case_when_then_statements[: then_i + 1], ["WHEN", "THEN"]
                )
        logger.debug(
            f"case_when_then_statements 0: {case_when_then_statements[0]['line_no']} then_i: {case_when_then_statements[then_i]['line_no']}"
        )
        logger.debug(f"case_when_then_statements: {case_when_then_statements}")
        when_statements = {
            "type": "when_statement",
            "when_line_no": case_when_then_statements[0]["line_no"],
            "when_indent": case_when_then_statements[0]["indent"],
            "when_value": when_value,
            "then_line_no": case_when_then_statements[then_i]["line_no"],
            "then_statements": case_when_then_statements[then_i + 1 :],
        }
        return when_statements

    def _parse_final_statement(self):
        """
        Parse the final statement of the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.


        Detects the final statement of the main section of SQL.
        """

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
            if (
                line_upper.startswith("EXCEPTION")
                and line_info["indent"] == begin_line_indent
            ):
                exception_lines_no = i
            if line_upper.endswith("END;") and line_info["indent"] == begin_line_indent:
                end_line_no = i

        self.main_section_lines = {
            "type": "begin_end",
            "begin_line_no": self.structured_lines[begin_line_no]["line_no"],
            "begin_indent": self.structured_lines[begin_line_no]["indent"],
            "begin_end_statements": self.structured_lines[
                begin_line_no + 1 : exception_lines_no
            ],
            "exception_handlers": self._parse_exception_handlers(
                self.structured_lines[exception_lines_no + 1 : end_line_no]
            ),
            "exception_line_no": self.structured_lines[exception_lines_no]["line_no"],
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
                line_info = working_lines[i]
                line_upper = line_info["line"].strip().upper()
                if line_upper.startswith("BEGIN") and begin_i == -1:
                    logger.debug(f"Begin line: {line_info} {i}")
                    begin_i = i
                    begin_line_indent = line_info["indent"]
                    while i < len(working_lines):
                        line_info = working_lines[i]
                        line_upper = line_info["line"].strip().upper()
                        if (
                            line_upper.startswith("EXCEPTION")
                            and line_info["indent"] == begin_line_indent
                        ):
                            logger.debug(f"Exception line: {line_info} {i}")
                            exception_i = i
                            while i < len(working_lines):
                                line_info = working_lines[i]
                                line_upper = line_info["line"].strip().upper()
                                if (
                                    line_upper.endswith("END;")
                                    and line_info["indent"] == begin_line_indent
                                ):
                                    logger.debug(f"End line: {line_info} {i}")
                                    begin_end_statements.append(
                                        {
                                            "type": "begin_end",
                                            "begin_line_no": working_lines[begin_i][
                                                "line_no"
                                            ],
                                            "begin_indent": begin_line_indent,
                                            "begin_end_statements": parse_begin_end_statements(
                                                working_lines[begin_i + 1 : exception_i]
                                            ),
                                            "exception_handlers": self._parse_exception_handlers(
                                                working_lines[exception_i + 1 : i]
                                            ),
                                            "exception_line_no": working_lines[
                                                exception_i
                                            ]["line_no"],
                                            "end_line_no": line_info["line_no"],
                                        }
                                    )
                                    begin_i = -1
                                    begin_line_indent = -1
                                    exception_i = -1
                                    break
                                i += 1
                            break
                        i += 1
                else:
                    begin_end_statements.append(line_info)
                i += 1
            return begin_end_statements

        self.main_section_lines["begin_end_statements"] = parse_begin_end_statements(
            self.main_section_lines["begin_end_statements"]
        )

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
                        self._extract_value_from_when_then(
                            [working_lines[when_i]], ["WHEN", "THEN"]
                        )
                        if when_i == then_i
                        else self._extract_value_from_when_then(
                            working_lines[when_i : then_i + 1], ["WHEN", "THEN"]
                        )
                    ),
                    "when_line_no": working_lines[when_i]["line_no"],
                    "when_indent": working_lines[when_i]["indent"],
                    "then_line_no": working_lines[then_i]["line_no"],
                    "exception_statements": [],
                    "exception_statements_line_no": [],
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
                    exception_handler["exception_statements_line_no"].append(
                        k_line_info["line_no"]
                    )
                    k += 1
                exception_handler["exception_statements"] = (
                    self._parse_exception_statements(
                        exception_handler["exception_statements"]
                    )
                )
                exception_handlers.append(exception_handler)
                i = k  # Continue from where we left off
            else:
                i += 1

        return exception_handlers

    def _parse_exception_statements(self, exception_statements: List[Dict[str, Any]]):
        """
        Parse exception statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        i = 0
        statements = []
        raise_application_error_i = -1
        while i < len(exception_statements):
            line_info = exception_statements[i]
            line_upper = line_info["line"].strip().upper()
            if line_upper.startswith("RAISE_APPLICATION_ERROR"):
                raise_application_error_i = i
                if line_upper.endswith(";"):
                    logger.debug(
                        exception_statements[raise_application_error_i : i + 1]
                    )
                    statements.append(self._parse_raise_application_error([line_info]))
                    raise_application_error_i = -1
            elif line_upper.endswith(";") and raise_application_error_i != -1:
                logger.debug(exception_statements[raise_application_error_i : i + 1])
                statements.append(
                    self._parse_raise_application_error(
                        exception_statements[raise_application_error_i : i + 1]
                    )
                )
                raise_application_error_i = -1
            elif raise_application_error_i == -1:
                statements.append(line_info)
            i += 1
        return statements

    def _parse_raise_application_error(self, working_lines: List[Dict[str, Any]]):
        """
        Parse RAISE_APPLICATION_ERROR calls from the main section of SQL.
        Extracts the structure and converts to a structured format.

        Handles patterns like:
        - RAISE_APPLICATION_ERROR(-20101, 'Invalid theme number format');
        - RAISE_APPLICATION_ERROR(-20117, V_TRIGGER_NAME || ' - Insert error');
        - Multi-line RAISE_APPLICATION_ERROR calls

        Returns:
            dict: Structured representation of the RAISE_APPLICATION_ERROR call
        """
        # Combine all lines into a single string
        combined_line = self.combine_lines(working_lines)
        logger.debug(combined_line)
        # Remove trailing semicolon if present
        combined_line = combined_line.rstrip(";").strip()

        logger.debug(f"Processing RAISE_APPLICATION_ERROR: {combined_line}")

        # Extract the function name (should be RAISE_APPLICATION_ERROR)
        if not combined_line.upper().startswith("RAISE_APPLICATION_ERROR"):
            logger.debug(f"Not a RAISE_APPLICATION_ERROR call: {combined_line}")
            return combined_line

        # Find the opening parenthesis after RAISE_APPLICATION_ERROR
        open_paren_pos = combined_line.find("(")
        if open_paren_pos == -1:
            logger.debug(f"No opening parenthesis found in: {combined_line}")
            return combined_line

        # Extract the parameters part (everything between parentheses)
        params_start = open_paren_pos + 1
        params_end = self._find_matching_closing_paren(combined_line, open_paren_pos)
        if params_end == -1:
            logger.debug(f"No closing parenthesis found in: {combined_line}")
            return combined_line

        params_text = combined_line[params_start:params_end].strip()
        logger.debug(f"Parameters text: {params_text}")

        # Parse the parameters (handler_code and handler_string)
        handler_code, handler_string = self._parse_raise_application_error_params(
            params_text
        )

        logger.debug(
            f"Parsed - handler_code: '{handler_code}', handler_string: '{handler_string}'"
        )

        # Create the structured representation
        result = {
            "type": "function_calling",
            "function_name": "raise_application_error",
            "parameter": {
                "handler_code": handler_code,
                "handler_string": handler_string,
            },
        }

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

    def _parse_raise_application_error_params(
        self, params_text: str
    ) -> Tuple[int, str]:
        """
        Parse the parameters of a RAISE_APPLICATION_ERROR call.

        Args:
            params_text (str): The text between parentheses of RAISE_APPLICATION_ERROR

        Returns:
            Tuple[str, str]: (handler_code, handler_string)
        """
        logger.debug(f"Parsing parameters: '{params_text}'")

        # Find the comma that separates the two parameters
        # We need to handle cases where the first parameter might contain commas
        # (like in complex expressions)

        # First, try to find a comma that's not inside quotes or parentheses
        comma_pos = -1
        paren_stack = 0
        in_single_quote = False
        in_double_quote = False

        for i, char in enumerate(params_text):
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "(" and not in_single_quote and not in_double_quote:
                paren_stack += 1
            elif char == ")" and not in_single_quote and not in_double_quote:
                paren_stack -= 1
            elif (
                char == ","
                and paren_stack == 0
                and not in_single_quote
                and not in_double_quote
            ):
                comma_pos = i
                break

        if comma_pos == -1:
            # If no comma found, assume it's a single parameter
            logger.debug(
                f"Only one parameter found in RAISE_APPLICATION_ERROR: {params_text}"
            )
            return int(params_text.strip()), ""

        # Split the parameters
        handler_code = int(params_text[:comma_pos].strip())
        handler_string = self.format_values(params_text[comma_pos + 1 :].strip())

        logger.debug(f"Handler code part: '{handler_code}'")
        logger.debug(f"Handler string part: '{handler_string}'")

        return handler_code, handler_string

    def _extract_value_from_when_then(
        self, working_lines: List[Dict[str, Any]], change_blocks: [str, str]
    ) -> str:
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
                    rest_strings_list.append(item)

                if "type" in item:
                    self.strng_convert_json += 1
                # Recursively process all values in the dictionary
                for value in item.values():
                    extract_rest_strings_from_item(value)

            elif isinstance(item, list):
                # Recursively process all items in the list
                for sub_item in item:
                    extract_rest_strings_from_item(sub_item)

        # Process main_section_lines
        extract_rest_strings_from_item(self.main_section_lines)

        return rest_strings_list

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
            "rest_strings": self.rest_strings_line,
            # "sql_lines": self.structured_lines,
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
            "rest_string_count": len(self.rest_strings_line),
            "sql_convert_count": self.strng_convert_json,
        }

        # Include parse timestamp
        result["metadata"] = {
            "parse_timestamp": self._get_timestamp(),
            "parser_version": "1.0",  # Increment when making significant parser changes
        }

        # Log detailed statistics for troubleshooting
        logger.debug(
            "JSON conversion complete: %d vars, %d consts, %d excs, %d comments",
            len(self.variables),
            len(self.constants),
            len(self.exceptions),
            len(self.sql_comments),
        )
        return result

    def _get_timestamp(self):
        """Get current timestamp in ISO format for metadata"""
        from datetime import datetime

        return datetime.now().isoformat()

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
                # logger.debug(formatted_msg[i])
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
