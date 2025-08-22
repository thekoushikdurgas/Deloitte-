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
        self._parse_final_statement()
        self._parse_case_when()
        self._parse_if_else()
        self._parse_for_loop()
        self._parse_assignment_statement()
        self._parse_sql_statements()

        # # to check how many rest strings are in main section
        # self.rest_strings_line = self.rest_strings()

    def _parse_sql_statements(self):
        """
        Parse SQL statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        Unified method to group both SQL statements (SELECT, INSERT, UPDATE, DELETE)
        and RAISE statements. Uses structured line dictionaries.
        STMT_TYPE_MAP = {
            "SELECT": "select_statements",
            "INSERT": "insert_statements",
            "UPDATE": "update_statements",
            "DELETE": "delete_statements",
            "RAISE": "raise_statements"
            }
        """

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

    def _parse_if_else(self):
        """
        Parse IF-ELSIF-ELSE statements from the main section of SQL with proper nested structure based on indentation.
        First detects IF and END IF; line numbers, then finds all ELSIF and ELSE statements at the same indentation level.
        Maintains the hierarchical structure of IF-ELSIF-ELSE blocks by checking indentation levels.
        Updates self.main_section_lines with parsed blocks.
        """

    def _parse_case_when(self):
        """
        Parse CASE WHEN ELSE statements from the main section of SQL with proper nested structure based on indentation.
        First detects CASE and END CASE; line numbers, then finds all WHEN and ELSE statements at the same indentation level.
        Maintains the hierarchical structure of CASE-WHEN-ELSE blocks by checking indentation levels.
        Updates self.main_section_lines with parsed blocks.
        """

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
                if line_upper.startswith("BEGIN"):
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
                # if when_i == then_i:
                #     exception_name = self._extract_exception_name_from_when([working_lines[when_i]])
                # else:
                #     exception_name = self._extract_exception_name_from_when(
                #         working_lines[when_i:then_i+1]
                #     )
                # Create exception handler structure
                exception_handler = {
                    "type": "exception_handler",
                    "exception_name": self._extract_exception_name_from_when([working_lines[when_i]]) if when_i == then_i else self._extract_exception_name_from_when(working_lines[when_i:then_i+1]),
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
                    exception_handler["exception_statements_line_no"].append(k_line_info["line_no"])
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
        i=0
        statements=[]
        raise_application_error_i=-1
        while i < len(exception_statements):
            line_info = exception_statements[i]
            line_upper = line_info["line"].strip().upper()
            if line_upper.startswith("RAISE_APPLICATION_ERROR"):
                raise_application_error_i = i
                if line_upper.endswith(";"):
                    # print(exception_statements[raise_application_error_i:i+1])
                    statements.append(self._parse_raise_application_error([line_info]))
                    raise_application_error_i = -1            
            elif line_upper.endswith(";") and raise_application_error_i != -1:
                # print(exception_statements[raise_application_error_i:i+1])
                statements.append(self._parse_raise_application_error(exception_statements[raise_application_error_i:i+1]))
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
        # print(combined_line)
        # Remove trailing semicolon if present
        combined_line = combined_line.rstrip(';').strip()
        
        logger.debug(f"Processing RAISE_APPLICATION_ERROR: {combined_line}")
        
        # Extract the function name (should be RAISE_APPLICATION_ERROR)
        if not combined_line.upper().startswith('RAISE_APPLICATION_ERROR'):
            logger.debug(f"Not a RAISE_APPLICATION_ERROR call: {combined_line}")
            return combined_line
        
        # Find the opening parenthesis after RAISE_APPLICATION_ERROR
        open_paren_pos = combined_line.find('(')
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
        handler_code, handler_string = self._parse_raise_application_error_params(params_text)
        
        logger.debug(f"Parsed - handler_code: '{handler_code}', handler_string: '{handler_string}'")
        
        # Create the structured representation
        result = {
            "type": "function_calling",
            "function_name": "raise_application_error",
            "parameter": {
                "handler_code": handler_code,
                "handler_string": handler_string
            }
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
            if text[i] == '(':
                stack += 1
            elif text[i] == ')':
                stack -= 1
                if stack == 0:
                    return i
        return -1
    
    def _parse_raise_application_error_params(self, params_text: str) -> Tuple[int, str]:
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
            elif char == '(' and not in_single_quote and not in_double_quote:
                paren_stack += 1
            elif char == ')' and not in_single_quote and not in_double_quote:
                paren_stack -= 1
            elif char == ',' and paren_stack == 0 and not in_single_quote and not in_double_quote:
                comma_pos = i
                break
        
        if comma_pos == -1:
            # If no comma found, assume it's a single parameter
            logger.debug(f"Only one parameter found in RAISE_APPLICATION_ERROR: {params_text}")
            return int(params_text.strip()), ""
        
        # Split the parameters
        handler_code = int(params_text[:comma_pos].strip())
        handler_string = self.format_values(params_text[comma_pos + 1:].strip())
        
        logger.debug(f"Handler code part: '{handler_code}'")
        logger.debug(f"Handler string part: '{handler_string}'")
        
        return handler_code, handler_string
    
    def _extract_exception_name_from_when(self, working_lines: List[Dict[str, Any]]) -> str:
        """
        Extract the exception name from a WHEN clause.

        Handles both formats:
        - Single line: "WHEN exception_name THEN"
        - Multi-line: "WHEN exception_name" followed by "THEN" on next line

        Args:
            when_line (str): The WHEN clause line

        Returns:
            str: The extracted exception name

        Examples:
            "WHEN ERR_UPD THEN" -> "ERR_UPD"
            "WHEN OTHERS THEN" -> "OTHERS"
            "WHEN NO_DATA_FOUND THEN" -> "NO_DATA_FOUND"
            "WHEN exception_name" -> "exception_name"
        """
        # Remove leading/trailing whitespace and convert to uppercase for consistency
        line = self.combine_lines(working_lines)

        # Remove "WHEN" prefix
        if line.startswith("WHEN"):
            line = line[4:].strip()

        # If line ends with "THEN", remove it
        if line.endswith("THEN"):
            line = line[:-4].strip()

        # For multi-line cases, just return the exception name part
        return line
    
    def combine_lines(self, working_lines: List[Dict[str, Any]]):
        """
        Combine lines from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        if len(working_lines) == 0:
            return ""
        elif len(working_lines) == 1:
            line =  working_lines[0]["line"].strip()
        elif len(working_lines) > 1:
            line =  ""
            for i in range(len(working_lines)):
                line += working_lines[i]["line"].strip() + " "
            line = line.strip()
            # print(line)
        return line
    
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
