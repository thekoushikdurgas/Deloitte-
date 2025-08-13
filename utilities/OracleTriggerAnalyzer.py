import json
import os
import re
import time
from typing import Any, Dict, List, Tuple
from utilities.common import (
    logger,
    setup_logging,
    debug,
    info,
    warning,
    error,
    critical,
    alert,
    log_parsing_start,
    log_parsing_complete,
    log_parsing_error,
    log_structure_found,
    log_nesting_level,
    log_performance,
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
        self.main_section: int = 0
        self.main_section_lines: List[Dict] = []
        self.variables: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []
        self.exceptions: List[Dict[str, Any]] = []
        self.sql_comments: List[str] = []
        self.rule_errors: List[Dict[str, Any]] = []
        self.structured_lines: List[Dict[str, Any]] = []
        self.rest_strings_line: List[Dict] = []
        self.strng_convert_json: int = 0

        log_parsing_complete(
            "structured lines conversion",
            f"{len(self.structured_lines)} lines processed",
        )

        # Step 2: Parse SQL into declare and main sections
        log_parsing_start("SQL section parsing")
        self._parse_sql()
        log_parsing_complete("SQL section parsing")

        # Step 3: Validate formatting rules
        log_parsing_start("rule validation")
        self.rule_errors = self._validate_rules()
        if self.rule_errors:
            warning("Found %d rule violation(s)", len(self.rule_errors))
        log_parsing_complete("rule validation")

        duration = time.time() - start_time
        log_performance("OracleTriggerAnalyzer initialization", duration)

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
        # total_lines = len(raw_lines)

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
            original_line = line

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
        log_parsing_start("structured lines conversion")
        self._convert_to_structured_lines()
        log_parsing_complete("structured lines conversion")

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
            if line_content == "DECLARE":
                declare_start = line_info["line_no"]
                logger.debug("Found DECLARE at line %d", declare_start)

            # Find BEGIN section
            elif line_content == "BEGIN" and begin_start == -1:
                begin_start = line_info["line_no"]
                logger.debug("Found BEGIN at line %d", begin_start)

        # Set section boundaries
        if declare_start != -1:
            declare_end = begin_start - 1
            self.declare_section = [declare_start, declare_end]
            logger.debug("DECLARE section: lines %d-%d", declare_start, declare_end)
        else:
            self.declare_section = [0, 0]
            logger.debug("No DECLARE section found")

        if begin_start != -1:
            self.main_section = begin_start
            logger.debug("Main section: lines %d", begin_start)
        else:
            self.main_section = 0
            logger.debug("Could not identify main section (BEGIN/END)")

        # Process declarations if DECLARE section exists
        if self.declare_section[0] > 0:
            self._parse_declarations()

        # Process main section if main section exists
        if self.main_section > 0:
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
        type_parts = words[1:]
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

    def _validate_rules(self) -> List[Dict[str, Any]]:
        """
        Validate Oracle PL/SQL formatting rules on the structured lines.

        This method checks for common formatting violations that would cause
        issues during conversion or interpretation. It returns a list of
        violations with line numbers and suggested fixes.

        Rules enforced:
        - IF and THEN must be on the same line
        - ELSIF and THEN must be on the same line
        - WHEN and THEN must be on the same line (for CASE statements)
        - RAISE_APPLICATION_ERROR must have all parameters on the same line and end with a semicolon

        Returns:
            List[Dict[str, Any]]: List of rule violations with line numbers and solutions
        """
        errors = []

        for i, line_info in enumerate(self.structured_lines):
            line = line_info["line"]
            line_no = line_info["line_no"]
            line_upper = line.strip().upper()

            # Rule 1: IF and THEN must be on the same line
            if line_upper.startswith("IF "):
                # Check if this line ends with THEN
                if not line_upper.endswith(" THEN"):
                    # Look for THEN on subsequent lines
                    j = i + 1
                    found_then = False
                    while j < len(self.structured_lines) and j < i + 10:  # Check next 10 lines
                        next_line = self.structured_lines[j]["line"].strip()
                        next_line_upper = next_line.upper()
                        
                        # Check if this line contains THEN
                        if " THEN" in next_line_upper:
                            found_then = True
                            errors.append(
                                {
                                    "type": "if_then_split",
                                    "message": "IF and THEN must be on the same line",
                                    "line_no": line_no,
                                    "line": line,
                                    "solution": f"Combine lines {line_no} and {self.structured_lines[j]['line_no']}: IF ... THEN",
                                }
                            )
                            break
                        
                        # Stop if we hit another statement at the same or lower indentation
                        # that doesn't start with continuation keywords
                        if (self.structured_lines[j]["indent"] <= line_info["indent"] and 
                            not (next_line_upper.startswith("AND") or 
                                 next_line_upper.startswith("OR") or 
                                 next_line_upper.startswith("(") or 
                                 next_line_upper.startswith(")") or 
                                 next_line_upper == "")):
                            break
                        
                        j += 1

            # Rule 2: ELSIF and THEN must be on the same line
            elif line_upper.startswith("ELSIF") and not line_upper.endswith("THEN"):
                if i + 1 < len(self.structured_lines):
                    next_line_upper = (
                        self.structured_lines[i + 1]["line"].strip().upper()
                    )
                    if next_line_upper == "THEN":
                        errors.append(
                            {
                                "type": "elsif_then_split",
                                "message": "ELSIF and THEN must be on the same line",
                                "line_no": line_no,
                                "line": line,
                                "solution": f"Combine lines {line_no} and {line_no + 1}: ELSIF ... THEN",
                            }
                        )

            # Rule 3: WHEN and THEN must be on the same line (for CASE statements)
            elif line_upper.startswith("WHEN") and not line_upper.endswith("THEN"):
                if i + 1 < len(self.structured_lines):
                    next_line_upper = (
                        self.structured_lines[i + 1]["line"].strip().upper()
                    )
                    if next_line_upper == "THEN":
                        errors.append(
                            {
                                "type": "when_then_split",
                                "message": "WHEN and THEN must be on the same line",
                                "line_no": line_no,
                                "line": line,
                                "solution": f"Combine lines {line_no} and {line_no + 1}: WHEN ... THEN",
                            }
                        )

            # Rule 4: RAISE_APPLICATION_ERROR must have all parameters on the same line and end with semicolon
            elif "RAISE_APPLICATION_ERROR" in line_upper:
                # Check if the statement is complete (ends with semicolon)
                if not line.strip().endswith(";"):
                    # Check if it continues on the next line
                    if i + 1 < len(self.structured_lines):
                        next_line = self.structured_lines[i + 1]["line"].strip()
                        if not next_line.endswith(";"):
                            errors.append(
                                {
                                    "type": "raise_application_error_incomplete",
                                    "message": "RAISE_APPLICATION_ERROR statement must be complete and end with semicolon",
                                    "line_no": line_no,
                                    "line": line,
                                    "solution": "Complete the RAISE_APPLICATION_ERROR statement on the same line or ensure it ends with semicolon",
                                }
                            )
                    else:
                        errors.append(
                            {
                                "type": "raise_application_error_incomplete",
                                "message": "RAISE_APPLICATION_ERROR statement must end with semicolon",
                                "line_no": line_no,
                                "line": line,
                                "solution": "Add semicolon to complete the statement",
                            }
                        )

                # Check for proper parameter structure
                if "RAISE_APPLICATION_ERROR" in line_upper:
                    # Look for opening and closing parentheses
                    open_paren = line.find("(")
                    close_paren = line.rfind(")")

                    if open_paren == -1 or close_paren == -1:
                        errors.append(
                            {
                                "type": "raise_application_error_params",
                                "message": "RAISE_APPLICATION_ERROR must have proper parentheses",
                                "line_no": line_no,
                                "line": line,
                                "solution": "Ensure RAISE_APPLICATION_ERROR has proper parameter structure: RAISE_APPLICATION_ERROR(error_code, message)",
                            }
                        )
                    elif open_paren > close_paren:
                        errors.append(
                            {
                                "type": "raise_application_error_params",
                                "message": "RAISE_APPLICATION_ERROR has mismatched parentheses",
                                "line_no": line_no,
                                "line": line,
                                "solution": "Fix parentheses matching in RAISE_APPLICATION_ERROR statement",
                            }
                        )

        logger.debug("Rule validation complete: found %d violations", len(errors))
        return errors

    def _process_main_section(self) -> None:
        """
        Process the main section (BEGIN...END) to extract structured lines.

        This method populates self.main_section_lines with the lines from
        the main section of the Oracle PL/SQL trigger.
        """
        debug("Processing main section from lines %d", self.main_section)

        # Step 3: Parse BEGIN blocks from the main section
        log_parsing_start("First BEGIN blocks")
        self._parse_begin_blocks()
        log_parsing_complete("First BEGIN blocks")
        
        log_parsing_start("CASE-WHEN statements in main section")
        self._parse_case_when()
        log_parsing_complete("CASE-WHEN statements in main section")


        log_parsing_start("IF-ELSE statements in main section")
        self._parse_if_else()
        log_parsing_complete("IF-ELSE statements in main section")

        log_parsing_start("BEGIN blocks in main section")
        self._parse_begin_end()
        log_parsing_complete("BEGIN blocks in main section")

        log_parsing_start("FOR loops in main section")
        self._parse_for_loop()
        log_parsing_complete("FOR loops in main section")

        log_parsing_start("assignment statements in main section")
        self._parse_assignment_statement()
        log_parsing_complete("assignment statements in main section")

        log_parsing_start("SQL statements in main section")
        self._parse_sql_statements()
        log_parsing_complete("SQL statements in main section")

        log_parsing_start("final statement in main section")
        self._parse_final_statement()
        log_parsing_complete("final statement in main section")

        # to check how many rest strings are in main section
        self.rest_strings_line = self.rest_strings()
        
        # Remove duplicate case_when structures
        logger.debug("About to remove duplicate case_when structures")
        self._remove_duplicate_case_when_structures()
        logger.debug("Finished removing duplicate case_when structures")

    def _parse_begin_blocks(self):
        """
        Parse top-level BEGIN blocks from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Uses the structured line format.
        """
        logger.debug("Starting top-level BEGIN blocks parsing")

        # Initialize main_section_lines with lines from the main section
        self.main_section_lines = []

        # Collect all lines from the main section (after BEGIN)
        for line_info in self.structured_lines:
            if self.main_section <= line_info["line_no"]:
                self.main_section_lines.append(line_info)

        logger.debug(
            "Collected %d lines from main section", len(self.main_section_lines)
        )

        # Now parse only top-level BEGIN-END blocks
        i = 0
        while i < len(self.main_section_lines):
            item = self.main_section_lines[i]

            # Check if this is a line_info object with a BEGIN statement
            if isinstance(item, dict) and "line" in item:
                line = item["line"].strip()
                line_upper = line.upper()

                # Check for top-level BEGIN block (indent should be minimal for top-level)
                if line_upper == "BEGIN":
                    begin_line_no = item["line_no"]
                    begin_indent = item.get("indent", 0)

                    logger.debug(
                        "Found top-level BEGIN block at line %d (indent %d)",
                        begin_line_no,
                        begin_indent,
                    )

                    # Parse the complete BEGIN-END block structure
                    begin_end_result = self._parse_top_level_begin_end_structure(i)
                    if begin_end_result:
                        begin_end_block, end_idx = begin_end_result

                        # Replace the BEGIN line with the complete block structure
                        self.main_section_lines[i] = begin_end_block

                        # Remove all the lines that were part of this BEGIN-END block
                        # (they are now included in the begin_end_block structure)
                        j = i + 1
                        while j < len(self.main_section_lines):
                            next_item = self.main_section_lines[j]
                            if isinstance(next_item, dict) and "line_no" in next_item:
                                # Check if this line is beyond the end of our BEGIN-END block
                                if next_item["line_no"] > end_idx:
                                    break
                                # Remove this line as it's part of the BEGIN-END block
                                self.main_section_lines.pop(j)
                            else:
                                j += 1

                        logger.debug(
                            "Successfully parsed top-level BEGIN-END block from line %d to %d",
                            begin_line_no,
                            end_idx,
                        )
                        continue  # Don't increment i since we replaced the current item

            i += 1

        logger.debug(
            "Top-level BEGIN blocks parsing complete: %d items in main_section_lines",
            len(self.main_section_lines),
        )

    def _parse_top_level_begin_end_structure(self, start_idx):
        """
        Parse a complete top-level BEGIN-END block structure starting from the given index.
        Returns (begin_end_block, end_line_no) or None if parsing fails.

        Args:
            start_idx (int): Index in main_section_lines where the BEGIN statement starts

        Returns:
            tuple: (begin_end_block, end_line_no) if successful, None otherwise
        """
        if start_idx < 0 or start_idx >= len(self.main_section_lines):
            return None

        start_item = self.main_section_lines[start_idx]
        if not (isinstance(start_item, dict) and "line" in start_item):
            return None

        start_line = start_item["line"].strip()
        start_line_upper = start_line.upper()

        # Verify this is a BEGIN statement
        if start_line_upper != "BEGIN":
            return None

        begin_line_no = start_item["line_no"]
        begin_indent = start_item.get("indent", 0)

        logger.debug(
            "Parsing top-level BEGIN-END block starting at line %d (indent %d)",
            begin_line_no,
            begin_indent,
        )

        # Initialize the block structure
        begin_end_block = {
            "type": "begin_end",
            "begin_line_no": begin_line_no,
            "begin_indent": begin_indent,
            "begin_end_statements": [],
            "exception_handlers": [],
            "exception_line_no": 0,
            "end_line_no": 0,
        }

        # Find the matching END; at the same indentation level
        end_line_no = None
        exception_line_no = None

        i = start_idx + 1
        while i < len(self.main_section_lines):
            item = self.main_section_lines[i]

            if isinstance(item, dict) and "line" in item:
                line = item["line"].strip()
                line_upper = line.upper()
                current_indent = item.get("indent", 0)
                current_line_no = item["line_no"]

                # Check for EXCEPTION at the same indentation level
                if line_upper == "EXCEPTION" and current_indent == begin_indent:
                    exception_line_no = current_line_no
                    begin_end_block["exception_line_no"] = exception_line_no
                    logger.debug("Found EXCEPTION at line %d", exception_line_no)

                # Check for END; at the same indentation level
                elif line_upper == "END;" and current_indent == begin_indent:
                    end_line_no = current_line_no
                    begin_end_block["end_line_no"] = end_line_no
                    logger.debug("Found END; at line %d", end_line_no)
                    break

                # Add regular statements to begin_end_statements (before EXCEPTION)
                elif (
                    line and not line.startswith("--") and current_indent > begin_indent
                ):
                    if not exception_line_no or current_line_no < exception_line_no:
                        begin_end_block["begin_end_statements"].append(item)

            i += 1

        if end_line_no is None:
            logger.warning(
                "Could not find matching END; for top-level BEGIN block at line %d",
                begin_line_no,
            )
            return None

        # Process exception handlers if EXCEPTION section exists
        if exception_line_no:
            begin_end_block["exception_handlers"] = self._parse_exception_section(
                exception_line_no, end_line_no
            )

        logger.debug(
            "Successfully parsed top-level BEGIN-END block: %d statements, %d exception handlers",
            len(begin_end_block["begin_end_statements"]),
            len(begin_end_block["exception_handlers"]),
        )

        return begin_end_block, end_line_no

    def _parse_final_statement(self):
        """
        Parse the final statement of the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.

        Detects the final statement of the main section of SQL.
        """

        def process_final_statements_in_list(statements_list, parent_context=""):
            """Recursively process final statements in a list of statements"""
            if not statements_list:
                return

            i = 0
            while i < len(statements_list):
                item = statements_list[i]

                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item:
                    line = item["line"].strip()
                    
                    # Check if this line doesn't end with semicolon
                    if not item["is_end_semicolon"]:
                        logger.debug("Found multi-line statement starting at line %d in %s: %s", item["line_no"], parent_context, line[:30])
                        
                        # Multi-line statement - find the end
                        statement_lines = [line]
                        j = i + 1
                        
                        # Collect all lines until we find a semicolon
                        while j < len(statements_list):
                            next_item = statements_list[j]
                            if isinstance(next_item, dict) and "line" in next_item:
                                next_line = next_item["line"].strip()
                                statement_lines.append(next_line)
                                
                                if next_item["is_end_semicolon"]:
                                    # Found the end of the statement
                                    break
                                j += 1
                            else:
                                # Not a line_info object, stop here
                                break
                        
                        # Create the complete statement
                        complete_statement = " ".join(statement_lines)
                        final_statement = {
                            "statement": complete_statement,
                            "type": "unknown_statement",
                            "indent": item["indent"],
                            "line_no": item["line_no"]
                        }
                        
                        # Replace the first line with the complete statement
                        statements_list[i] = final_statement
                        
                        # Remove the subsequent lines that were part of this statement
                        for k in range(j, i, -1):
                            if k < len(statements_list):
                                statements_list.pop(k)
                        
                        logger.debug("Parsed multi-line final statement: %s", complete_statement[:30])
                        continue
                    else:
                        # Single line statement that ends with semicolon
                        final_statement = {
                            "statement": line,
                            "type": "unknown_statement",
                            "indent": item["indent"],
                            "line_no": item["line_no"]
                        }
                        statements_list[i] = final_statement
                        logger.debug("Parsed single-line final statement: %s", line[:30])

                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process final statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_final_statements_in_list(
                                item["begin_end_statements"],
                                f"{parent_context}.begin_end_statements",
                            )

                        # Process final statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_final_statements_in_list(
                                        handler["exception_statements"],
                                        f"{parent_context}.exception_statements",
                                    )

                    elif item["type"] == "case_when":
                        # Process final statements in when_clauses (then_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if (
                                    "when_value" in clause
                                    and "then_statements" in clause
                                ):
                                    process_final_statements_in_list(
                                        clause["then_statements"],
                                        f"{parent_context}.then_statements",
                                    )

                        # Process final statements in top-level else_statements
                        if "else_statements" in item:
                            process_final_statements_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "if_else":
                        # Process final statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_final_statements_in_list(
                                item["then_statements"],
                                f"{parent_context}.then_statements",
                            )

                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_final_statements_in_list(
                                        elsif_block["then_statements"],
                                        f"{parent_context}.else_if.then_statements",
                                    )

                        if "else_statements" in item:
                            process_final_statements_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "for_loop":
                        # Process final statements in loop_statements
                        if "loop_statements" in item:
                            process_final_statements_in_list(
                                item["loop_statements"],
                                f"{parent_context}.loop_statements",
                            )

                i += 1

        # Process the main_section_lines
        process_final_statements_in_list(self.main_section_lines, "main_section_lines")

        logger.debug("Final statement parsing complete")

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
        logger.debug("Starting FOR loop parsing")

        # Process existing main_section_lines to find and parse FOR loops
        # in various contexts: begin_end_statements, exception_statements, then_statements, else_statements

        def process_for_loops_in_list(statements_list, parent_context=""):
            """Recursively process FOR loops in a list of statements"""
            if not statements_list:
                return

            i = 0
            while i < len(statements_list):
                item = statements_list[i]

                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()

                    # Check for FOR loop start
                    if line_upper.startswith("FOR ") and " IN " in line_upper:
                        logger.debug(
                            "Found FOR loop at line %d in %s",
                            item["line_no"],
                            parent_context,
                        )
                        for_loop_result = self._parse_for_loop_structure(
                            self._find_line_index(item["line_no"])
                        )
                        if for_loop_result:
                            for_loop_block, end_idx = for_loop_result
                            # Replace the line_info with the parsed for_loop_block
                            statements_list[i] = for_loop_block
                            logger.debug(
                                "Parsed complete FOR loop structure in %s",
                                parent_context,
                            )
                            # Remove any subsequent line_info objects that are part of the FOR loop
                            # (they will be included in the for_loop_block)
                            j = i + 1
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if (
                                    isinstance(next_item, dict)
                                    and "line_no" in next_item
                                ):
                                    if next_item["line_no"] > end_idx:
                                        break
                                    statements_list.pop(j)
                                else:
                                    j += 1
                            continue

                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process FOR loops in begin_end_statements
                        if "begin_end_statements" in item:
                            process_for_loops_in_list(
                                item["begin_end_statements"],
                                f"{parent_context}.begin_end_statements",
                            )

                        # Process FOR loops in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_for_loops_in_list(
                                        handler["exception_statements"],
                                        f"{parent_context}.exception_statements",
                                    )

                    elif item["type"] == "case_when":
                        # Process FOR loops in when_clauses (then_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if (
                                    "when_value" in clause
                                    and "then_statements" in clause
                                ):
                                    process_for_loops_in_list(
                                        clause["then_statements"],
                                        f"{parent_context}.then_statements",
                                    )

                        # Process FOR loops in top-level else_statements
                        if "else_statements" in item:
                            process_for_loops_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "if_else":
                        # Process FOR loops in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_for_loops_in_list(
                                item["then_statements"],
                                f"{parent_context}.then_statements",
                            )

                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_for_loops_in_list(
                                        elsif_block["then_statements"],
                                        f"{parent_context}.else_if.then_statements",
                                    )

                        if "else_statements" in item:
                            process_for_loops_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "for_loop":
                        # Process nested FOR loops in loop_statements
                        if "loop_statements" in item:
                            process_for_loops_in_list(
                                item["loop_statements"],
                                f"{parent_context}.loop_statements",
                            )

                i += 1

        # Process the main_section_lines
        process_for_loops_in_list(self.main_section_lines, "main_section_lines")

        logger.debug("FOR loop parsing complete")

    def _parse_for_loop_structure(self, start_idx):
        """
        Parse a complete FOR loop structure starting from the given index.
        Returns (for_loop_block, end_line_index) or None if parsing fails.
        """
        if start_idx < 0 or start_idx >= len(self.structured_lines):
            return None

        start_line_info = self.structured_lines[start_idx]
        start_line = start_line_info["line"].strip()
        start_line_upper = start_line.upper()

        # Validate that this is a FOR loop start
        if not start_line_upper.startswith("FOR ") or " IN " not in start_line_upper:
            return None

        logger.debug(
            "Parsing FOR loop structure starting at line %d: %s",
            start_line_info["line_no"],
            start_line[:50],
        )

        # Extract loop variable and cursor query
        loop_parts = self._parse_for_loop_header(start_line)
        if not loop_parts:
            logger.warning("Failed to parse FOR loop header: %s", start_line)
            return None

        loop_variable = loop_parts["loop_variable"]
        cursor_query = loop_parts["cursor_query"]

        # Handle multi-line FOR loops where the cursor query continues on subsequent lines
        if (
            not cursor_query
            or cursor_query.strip() == ""
            or cursor_query.strip() == "("
        ):
            # The cursor query is on subsequent lines, collect them
            cursor_lines = []
            i = start_idx + 1
            loop_start_indent = start_line_info.get("indent", 0)
            found_loop = False

            while i < len(self.structured_lines):
                line_info = self.structured_lines[i]
                line = line_info["line"].strip()
                line_upper = line.upper()
                current_indent = line_info.get("indent", 0)

                # Check if we've found the LOOP keyword
                if " LOOP" in line_upper:
                    # Extract the part before LOOP as the end of the cursor query
                    loop_pos = line_upper.find(" LOOP")
                    if loop_pos > 0:
                        cursor_lines.append(line[:loop_pos].strip())
                    found_loop = True
                    break

                # Add this line to the cursor query
                cursor_lines.append(line)
                i += 1

            if cursor_lines:
                cursor_query = " ".join(cursor_lines).strip()
                # Remove outer parentheses if present
                if cursor_query.startswith("(") and cursor_query.endswith(")"):
                    cursor_query = cursor_query[1:-1].strip()

        # Find the end of the FOR loop (END LOOP;)
        loop_start_indent = start_line_info.get("indent", 0)
        end_idx = start_idx
        loop_statements = []

        # First, find where the LOOP keyword is to know where the cursor query ends
        loop_keyword_idx = start_idx
        for i in range(start_idx + 1, len(self.structured_lines)):
            line_info = self.structured_lines[i]
            line = line_info["line"].strip()
            line_upper = line.upper()

            if " LOOP" in line_upper:
                loop_keyword_idx = i
                break

        # Look for END LOOP; with matching or lower indentation
        for i in range(loop_keyword_idx + 1, len(self.structured_lines)):
            line_info = self.structured_lines[i]
            line = line_info["line"].strip()
            line_upper = line.upper()
            current_indent = line_info.get("indent", 0)

            # Check if this is the END LOOP; statement
            if line_upper == "END LOOP;" and current_indent <= loop_start_indent:
                end_idx = i
                logger.debug("Found END LOOP at line %d", line_info["line_no"])
                break

            # Collect statements within the loop body (after the LOOP keyword)
            if current_indent > loop_start_indent:
                loop_statements.append(line_info)

        if end_idx == start_idx:
            logger.warning(
                "Could not find END LOOP for FOR loop starting at line %d",
                start_line_info["line_no"],
            )
            return None

        # Create the FOR loop structure
        # Ensure cursor_query has proper parentheses without duplication
        formatted_cursor_query = cursor_query
        if not formatted_cursor_query.startswith("("):
            formatted_cursor_query = f"({formatted_cursor_query}"
        if not formatted_cursor_query.endswith(")"):
            formatted_cursor_query = f"{formatted_cursor_query})"

        for_loop_block = {
            "type": "for_loop",
            "loop_variable": loop_variable,
            "cursor_query": formatted_cursor_query,
            "loop_statements": loop_statements,
        }

        logger.debug(
            "Successfully parsed FOR loop: %s IN (%s)", loop_variable, cursor_query[:30]
        )
        return for_loop_block, self.structured_lines[end_idx]["line_no"]

    def _parse_for_loop_header(self, line):
        """
        Parse the FOR loop header to extract loop variable and cursor query.
        Expected format: FOR variable IN (query) LOOP
        or: FOR variable IN (query) (with LOOP on subsequent lines)
        """
        line_upper = line.upper()

        # Find the FOR keyword
        for_start = line_upper.find("FOR ")
        if for_start == -1:
            return None

        # Find the IN keyword
        in_start = line_upper.find(" IN ")
        if in_start == -1:
            return None

        # Extract loop variable (between FOR and IN)
        loop_variable_start = for_start + 4  # Skip "FOR "
        loop_variable_end = in_start
        loop_variable = line[loop_variable_start:loop_variable_end].strip()

        # Check if LOOP is on the same line
        loop_start = line_upper.find(" LOOP")
        if loop_start != -1:
            # LOOP is on the same line, extract cursor query between IN and LOOP
            cursor_start = in_start + 4  # Skip " IN "
            cursor_end = loop_start
            cursor_query = line[cursor_start:cursor_end].strip()
        else:
            # LOOP is on a subsequent line, extract everything after IN
            cursor_start = in_start + 4  # Skip " IN "
            cursor_query = line[cursor_start:].strip()

        # Remove outer parentheses from cursor query if present
        if cursor_query.startswith("(") and cursor_query.endswith(")"):
            cursor_query = cursor_query[1:-1].strip()

        return {"loop_variable": loop_variable, "cursor_query": cursor_query}

    def _parse_if_else(self):
        """
        Parse IF-ELSIF-ELSE statements from the main section of SQL with proper nested structure based on indentation.
        First detects IF and END IF; line numbers, then finds all ELSIF and ELSE statements at the same indentation level.
        Maintains the hierarchical structure of IF-ELSIF-ELSE blocks by checking indentation levels.
        Updates self.main_section_lines with parsed blocks.
        """
        logger.debug("Starting IF-ELSIF-ELSE parsing with indentation-based nesting")

        def process_if_else_in_list(statements_list, parent_context=""):
            """Recursively process IF-ELSE statements in a list of statements"""
            if not statements_list:
                return

            i = 0
            while i < len(statements_list):
                item = statements_list[i]

                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()

                    # Check for IF statement start
                    if line_upper.startswith("IF "):
                        logger.debug(
                            "Found IF statement at line %d in %s",
                            item["line_no"],
                            parent_context,
                        )
                        if_result = self._parse_if_statement_enhanced(
                            self._find_line_index(item["line_no"])
                        )
                        if if_result:
                            if_block, end_idx = if_result
                            # Replace the line_info with the parsed if_block
                            statements_list[i] = if_block
                            logger.debug(
                                "Parsed complete IF statement structure in %s",
                                parent_context,
                            )
                            # Remove any subsequent line_info objects that are part of the IF statement
                            # (they will be included in the if_block)
                            j = i + 1
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if (
                                    isinstance(next_item, dict)
                                    and "line_no" in next_item
                                ):
                                    # Get the end line number from the if_block
                                    end_line_no = if_block.get("end_if_line_no")
                                    if (
                                        end_line_no
                                        and next_item["line_no"] > end_line_no
                                    ):
                                        break
                                    statements_list.pop(j)
                                else:
                                    j += 1
                            continue

                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process IF statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_if_else_in_list(
                                item["begin_end_statements"],
                                f"{parent_context}.begin_end_statements",
                            )

                        # Process IF statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_if_else_in_list(
                                        handler["exception_statements"],
                                        f"{parent_context}.exception_statements",
                                    )

                    elif item["type"] == "if_else":
                        # Process IF statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_if_else_in_list(
                                item["then_statements"],
                                f"{parent_context}.then_statements",
                            )

                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_if_else_in_list(
                                        elsif_block["then_statements"],
                                        f"{parent_context}.else_if.then_statements",
                                    )

                        if "else_statements" in item:
                            process_if_else_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "case_when":
                        # Process IF statements in when_clauses (then_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if (
                                    "when_value" in clause
                                    and "then_statements" in clause
                                ):
                                    process_if_else_in_list(
                                        clause["then_statements"],
                                        f"{parent_context}.then_statements",
                                    )

                        # Process IF statements in top-level else_statements
                        if "else_statements" in item:
                            process_if_else_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "for_loop":
                        # Process IF statements in loop_statements
                        if "loop_statements" in item:
                            process_if_else_in_list(
                                item["loop_statements"],
                                f"{parent_context}.loop_statements",
                            )

                i += 1

        # Process the main_section_lines
        process_if_else_in_list(self.main_section_lines, "main_section_lines")

        logger.debug("IF-ELSIF-ELSE parsing complete")

    def _parse_if_statement_enhanced(self, start_idx):
        """
        Parse an IF statement from structured_lines with enhanced line number detection and indentation-based nesting.
        First detects IF and END IF; line numbers, then finds all ELSIF and ELSE statements at the same indentation level.

        Args:
            start_idx (int): Index in structured_lines where the IF statement starts

        Returns:
            tuple: (if_block, end_idx) if successful, None otherwise
        """
        logger.debug("Starting enhanced IF statement parsing from index %d", start_idx)

        # Check if we have a valid IF statement
        if start_idx >= len(self.structured_lines):
            logger.debug("Invalid start index for IF statement")
            return None

        if_line_info = self.structured_lines[start_idx]
        if_line = if_line_info["line"].strip()
        if_indent = if_line_info["indent"]
        if_line_no = if_line_info["line_no"]

        # Extract the IF condition (handle multi-line conditions)
        if_condition_parts = [if_line[3:].strip()]  # Remove "IF " prefix
        
        # Check if the first line ends with THEN
        if if_condition_parts[0].upper().endswith(" THEN"):
            # Single line IF condition
            if_condition = if_condition_parts[0][:-5].strip()  # Remove " THEN" suffix
        else:
            # Multi-line IF condition - collect all lines until we find THEN
            j = start_idx + 1
            while j < len(self.structured_lines):
                line_info = self.structured_lines[j]
                line = line_info["line"].strip()
                line_upper = line.upper()
                indent = line_info["indent"]
                
                # Check if this line contains THEN
                if " THEN" in line_upper:
                    # Found the end of the condition
                    then_pos = line_upper.find(" THEN")
                    if then_pos > 0:
                        if_condition_parts.append(line[:then_pos].strip())
                    break
                
                # Add this line to the condition
                if_condition_parts.append(line)
                
                # Stop if we hit another statement at the same or lower indentation
                if (indent <= if_indent and 
                    line_upper not in ["AND", "OR", "(", ")", ""] and
                    not line_upper.startswith("AND") and
                    not line_upper.startswith("OR")):
                    break
                
                j += 1
            
            # Join all condition parts
            if_condition = " ".join(if_condition_parts)

        logger.debug(
            "IF statement - Condition: '%s', Indent: %d", if_condition, if_indent
        )

        # Step 1: Find the matching END IF; at the same indentation level
        end_if_line_no = None
        end_if_idx = -1

        i = start_idx + 1
        while i < len(self.structured_lines):
            line_info = self.structured_lines[i]
            line = line_info["line"].strip()
            line_upper = line.upper()
            indent = line_info["indent"]

            # Check for END IF; at the same indentation level
            if line_upper == "END IF;" and indent == if_indent:
                end_if_line_no = line_info["line_no"]
                end_if_idx = i
                logger.debug(
                    "Found END IF; at line %d (indent %d)", end_if_line_no, indent
                )
                break

            # Handle nested IF statements - skip to their END IF;
            elif line_upper.startswith("IF ") and indent > if_indent:
                nested_indent = indent
                j = i + 1
                while j < len(self.structured_lines):
                    nested_line_info = self.structured_lines[j]
                    nested_line = nested_line_info["line"].strip()
                    nested_line_upper = nested_line.upper()
                    nested_indent_level = nested_line_info["indent"]

                    if (
                        nested_line_upper == "END IF;"
                        and nested_indent_level == nested_indent
                    ):
                        i = j  # Skip to the end of nested IF
                        break
                    j += 1

            i += 1

        if end_if_line_no is None:
            logger.warning(
                "Could not find matching END IF; for IF statement at line %d",
                if_line_no,
            )
            return None

        # Step 2: Find all ELSIF and ELSE statements between IF and END IF; at the same indentation level
        else_if_line_nos = []
        else_line_no = None

        for k in range(start_idx + 1, end_if_idx):
            line_info = self.structured_lines[k]
            line = line_info["line"].strip()
            line_upper = line.upper()
            indent = line_info["indent"]

            # Check for ELSIF statements at the same indentation level as IF
            if line_upper.startswith("ELSIF ") and indent == if_indent:
                else_if_line_nos.append(line_info["line_no"])
                logger.debug(
                    "Found ELSIF clause at line %d (indent %d)",
                    line_info["line_no"],
                    indent,
                )

            # Check for ELSE statement at the same indentation level as IF
            elif line_upper == "ELSE" and indent == if_indent:
                else_line_no = line_info["line_no"]
                logger.debug(
                    "Found ELSE clause at line %d (indent %d)",
                    line_info["line_no"],
                    indent,
                )

        # Step 3: Build the enhanced if statement structure
        if_statement = {
            "type": "if_else",
            "condition": if_condition,
            "then_statements": [],
            "else_if": [],
            "else_statements": [],
            "if_line_no": if_line_no,
            "if_indent": if_indent,
            "else_if_line_nos": else_if_line_nos,
            "else_line_no": else_line_no,
            "end_if_line_no": end_if_line_no,
        }

        # Step 4: Process THEN statements (between IF and first ELSIF/ELSE/END IF)
        then_end_line_no = (
            else_if_line_nos[0]
            if else_if_line_nos
            else (else_line_no if else_line_no else end_if_line_no)
        )
        then_statements = self._parse_then_statements(
            if_line_no, if_indent, then_end_line_no
        )
        if_statement["then_statements"] = then_statements

        # Step 5: Process ELSIF clauses
        for i, else_if_line_no in enumerate(else_if_line_nos):
            next_line_no = (
                else_if_line_nos[i + 1]
                if i + 1 < len(else_if_line_nos)
                else (else_line_no if else_line_no else end_if_line_no)
            )
            else_if_clause = self._parse_else_if_clause(
                else_if_line_no, if_indent, next_line_no
            )
            if else_if_clause:
                if_statement["else_if"].append(else_if_clause)

        # Step 6: Process ELSE clause if exists
        if else_line_no:
            else_statements = self._parse_else_statements(
                else_line_no, if_indent, end_if_line_no
            )
            if_statement["else_statements"] = else_statements

        # Step 7: Process nested structures in each section
        self._process_nested_structures_in_if_else_enhanced(if_statement)

        logger.debug(
            "Completed enhanced IF statement parsing: %d else_if clauses, ELSE at line %s, end at line %d",
            len(else_if_line_nos),
            else_line_no or "None",
            end_if_line_no,
        )

        return if_statement, end_if_idx

    def _parse_if_else_structure(self, statements_list, start_idx, parent_context=""):
        """
        Parse a complete IF-ELSE structure from statements starting at start_idx.

        Returns a dictionary with:
        - parsed_block: The structured IF-ELSE block
        - end_index: The index of the END IF statement

        Handles IF-THEN-ELSIF-ELSE-END IF structures with proper nesting.
        """
        if start_idx >= len(statements_list):
            log_parsing_error(
                "IF-ELSE structure", f"Invalid start_idx {start_idx}", None
            )
            return None

        start_item = statements_list[start_idx]
        if not (isinstance(start_item, dict) and "line" in start_item):
            log_parsing_error(
                "IF-ELSE structure", "Start item is not a line_info object", None
            )
            return None

        start_line = start_item["line"].strip()
        start_indent = start_item.get("indent", 0)
        start_line_no = start_item["line_no"]

        if not start_line.upper().startswith("IF "):
            log_parsing_error(
                "IF-ELSE structure",
                f"Start line is not an IF statement: {start_line}",
                None,
            )
            return None

        debug(
            "Parsing IF-ELSE structure starting at line %d (indent %d): %s",
            start_line_no,
            start_indent,
            start_line[:50],
        )

        # Extract IF condition
        if_condition = start_line[3:].strip()  # Remove "IF " prefix
        if if_condition.upper().endswith(" THEN"):
            if_condition = if_condition[:-5].strip()  # Remove " THEN" suffix

        # Initialize structure
        if_block = {
            "type": "if_else",
            "condition": if_condition,
            "then_statements": [],
            "else_if": [],
            "else_statements": [],
            "line_no": start_line_no,
            "indent": start_indent,
        }

        current_section = "then"  # Track which section we're currently in
        current_statements = if_block["then_statements"]

        # Find the matching END IF
        i = start_idx + 1
        nest_level = 0  # Track nested IF blocks

        while i < len(statements_list):
            item = statements_list[i]

            if isinstance(item, dict) and "line" in item:
                line = item["line"].strip()
                indent = item.get("indent", 0)
                line_no = item["line_no"]

                # Check for nested IF statements (increase nest level)
                if line.upper().startswith("IF "):
                    if indent > start_indent:
                        nest_level += 1
                        log_nesting_level(nest_level, f"nested IF at line {line_no}")
                        current_statements.append(item)
                    elif indent == start_indent:
                        # Same level IF - we've gone too far
                        debug("Found same-level IF at line %d, stopping parse", line_no)
                        break
                    else:
                        # Lower indent IF - we've gone too far
                        debug(
                            "Found lower-indent IF at line %d, stopping parse", line_no
                        )
                        break

                # Check for nested END IF (decrease nest level)
                elif line.upper() == "END IF;":
                    if nest_level > 0:
                        nest_level -= 1
                        log_nesting_level(
                            nest_level, f"nested END IF at line {line_no}"
                        )
                        current_statements.append(item)
                    elif indent == start_indent:
                        # This is our matching END IF
                        debug(
                            "Found matching END IF at line %d for IF at line %d",
                            line_no,
                            start_line_no,
                        )
                        return {"parsed_block": if_block, "end_index": i}
                    else:
                        # Wrong indent level
                        warning(
                            "Found END IF with wrong indent at line %d (expected %d, got %d)",
                            line_no,
                            start_indent,
                            indent,
                        )
                        current_statements.append(item)

                # Check for ELSIF at the same level
                elif (
                    line.upper().startswith("ELSIF ")
                    and indent == start_indent
                    and nest_level == 0
                ):
                    log_structure_found("ELSIF", line_no)

                    # Extract ELSIF condition
                    elsif_condition = line[6:].strip()  # Remove "ELSIF " prefix
                    if elsif_condition.upper().endswith(" THEN"):
                        elsif_condition = elsif_condition[
                            :-5
                        ].strip()  # Remove " THEN" suffix

                    # Add to else_if list
                    elsif_block = {
                        "condition": elsif_condition,
                        "then_statements": [],
                        "line_no": line_no,
                    }
                    if_block["else_if"].append(elsif_block)

                    # Switch to ELSIF statements
                    current_section = "elsif"
                    current_statements = elsif_block["then_statements"]

                # Check for ELSE at the same level
                elif (
                    line.upper() == "ELSE"
                    and indent == start_indent
                    and nest_level == 0
                ):
                    log_structure_found("ELSE", line_no)

                    # Switch to else statements
                    current_section = "else"
                    current_statements = if_block["else_statements"]

                else:
                    # Regular statement - add to current section
                    current_statements.append(item)
            else:
                # Non-line item - add to current section
                current_statements.append(item)

            i += 1

        # If we get here, we didn't find a matching END IF
        log_parsing_error(
            "IF-ELSE structure",
            f"Could not find matching END IF for IF statement",
            start_line_no,
        )
        return None

    def _parse_then_statements(self, if_line_no, if_indent, then_end_line_no):
        """
        Parse THEN statements between IF and the next ELSIF/ELSE/END IF.

        Args:
            if_line_no (int): Line number where IF statement starts
            if_indent (int): Indentation level of the parent IF statement
            then_end_line_no (int): Line number where THEN section ends

        Returns:
            list: Parsed THEN statements
        """
        then_statements = []

        # Collect statements between IF and next clause
        for line_info in self.structured_lines:
            line_no = line_info["line_no"]
            if if_line_no < line_no < then_end_line_no:
                line = line_info["line"].strip()
                indent = line_info["indent"]

                # Only include statements that are more indented than the IF
                if indent > if_indent and line and not line.startswith("--"):
                    then_statements.append(line_info)

        return then_statements

    def _parse_else_if_clause(self, else_if_line_no, if_indent, next_line_no):
        """
        Parse an ELSIF clause starting at the given line number.

        Args:
            else_if_line_no (int): Line number where ELSIF clause starts
            if_indent (int): Indentation level of the parent IF statement
            next_line_no (int): Line number where this ELSIF section ends

        Returns:
            dict: Parsed ELSIF clause structure
        """
        else_if_clause = {
            "condition": "",
            "then_statements": [],
            "else_if_line_no": else_if_line_no,
        }

        # Find the ELSIF line and extract the condition
        else_if_line_info = None
        for line_info in self.structured_lines:
            if line_info["line_no"] == else_if_line_no:
                else_if_line_info = line_info
                break

        if not else_if_line_info:
            logger.warning("Could not find ELSIF line %d", else_if_line_no)
            return None

        else_if_line = else_if_line_info["line"].strip()
        else_if_line_upper = else_if_line.upper()

        # Extract the else_if condition
        if else_if_line_upper.startswith("ELSIF "):
            else_if_condition = else_if_line[6:].strip()  # Remove "ELSIF " prefix
            if else_if_condition.upper().endswith(" THEN"):
                else_if_condition = else_if_condition[
                    :-5
                ].strip()  # Remove " THEN" suffix
            else_if_clause["condition"] = else_if_condition
            logger.debug("Parsed ELSIF clause: %s", else_if_condition)

        # Collect statements between ELSIF and next clause
        for line_info in self.structured_lines:
            line_no = line_info["line_no"]
            if else_if_line_no < line_no < next_line_no:
                line = line_info["line"].strip()
                indent = line_info["indent"]

                # Only include statements that are more indented than the IF
                if indent > if_indent and line and not line.startswith("--"):
                    else_if_clause["then_statements"].append(line_info)

        return else_if_clause

    def _parse_else_statements(self, else_line_no, if_indent, end_if_line_no):
        """
        Parse ELSE statements starting at the given line number.

        Args:
            else_line_no (int): Line number where ELSE clause starts
            if_indent (int): Indentation level of the parent IF statement
            end_if_line_no (int): Line number where END IF; is located

        Returns:
            list: Parsed ELSE statements
        """
        else_statements = []

        # Collect statements between ELSE and END IF;
        for line_info in self.structured_lines:
            line_no = line_info["line_no"]
            if else_line_no < line_no < end_if_line_no:
                line = line_info["line"].strip()
                indent = line_info["indent"]

                # Only include statements that are more indented than the IF
                if indent > if_indent and line and not line.startswith("--"):
                    else_statements.append(line_info)

        logger.debug("Parsed ELSE clause with %d statements", len(else_statements))
        return else_statements

    def _process_nested_structures_in_if_else_enhanced(self, if_statement):
        """
        Process any nested structures within the enhanced if statement.

        Args:
            if_statement (dict): The enhanced if statement structure to process
        """
        logger.debug("Processing nested structures in enhanced IF statement")

        # Process then_statements
        if if_statement.get("then_statements"):
            processed_statements = self._process_statements_for_nested_structures(
                if_statement["then_statements"]
            )
            if_statement["then_statements"] = processed_statements

        # Process else_if statements
        if if_statement.get("else_if"):
            for else_if_block in if_statement["else_if"]:
                if else_if_block.get("then_statements"):
                    processed_statements = (
                        self._process_statements_for_nested_structures(
                            else_if_block["then_statements"]
                        )
                    )
                    else_if_block["then_statements"] = processed_statements

        # Process else_statements
        if if_statement.get("else_statements"):
            processed_statements = self._process_statements_for_nested_structures(
                if_statement["else_statements"]
            )
            if_statement["else_statements"] = processed_statements

    def _process_nested_structures_in_if_else(self, if_block):
        """
        Process nested structures within an IF-ELSE block recursively.
        This includes nested BEGIN-END, CASE-WHEN, FOR loops, and other IF-ELSE blocks.
        """
        debug("Processing nested structures in IF-ELSE block")

        # Process then_statements
        if if_block.get("then_statements"):
            debug("Processing nested structures in then_statements")
            self._process_statements_for_nested_structures(if_block["then_statements"])

        # Process else_if statements
        if if_block.get("else_if"):
            for elsif_block in if_block["else_if"]:
                if elsif_block.get("then_statements"):
                    debug("Processing nested structures in elsif then_statements")
                    self._process_statements_for_nested_structures(
                        elsif_block["then_statements"]
                    )

        # Process else_statements
        if if_block.get("else_statements"):
            debug("Processing nested structures in else_statements")
            self._process_statements_for_nested_structures(if_block["else_statements"])

    def _process_nested_structures_recursively(self, parsed_structure):
        """
        Recursively process nested structures within a parsed structure.
        This handles structures like if_else, case_when, begin_end, etc.
        """
        debug(
            "Processing nested structures recursively in %s",
            parsed_structure.get("type", "unknown"),
        )

        # Handle IF-ELSE structures
        if parsed_structure.get("type") == "if_else":
            self._process_nested_structures_in_if_else(parsed_structure)

        # Handle CASE-WHEN structures
        elif parsed_structure.get("type") == "case_when":
            self._process_nested_structures_in_case(parsed_structure)

        # Handle BEGIN-END structures
        elif parsed_structure.get("type") == "begin_end":
            if parsed_structure.get("begin_end_statements"):
                self._process_statements_for_nested_structures(
                    parsed_structure["begin_end_statements"]
                )
            if parsed_structure.get("exception_statements"):
                self._process_statements_for_nested_structures(
                    parsed_structure["exception_statements"]
                )

        # Handle FOR LOOP structures
        elif parsed_structure.get("type") == "for_loop":
            if parsed_structure.get("loop_statements"):
                self._process_statements_for_nested_structures(
                    parsed_structure["loop_statements"]
                )

        # Handle other statement lists
        for key in [
            "statements",
            "then_statements",
            "else_statements",
            "when_statements",
        ]:
            if key in parsed_structure and isinstance(parsed_structure[key], list):
                self._process_statements_for_nested_structures(parsed_structure[key])

    def _parse_assignment_statement(self):
        """
        Parse assignment statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        Group assignment statements (:=) in the SQL code.
        Uses structured line dictionaries.
        """
        logger.debug("Starting assignment statements parsing")

        def process_assignment_statement_in_list(statements_list, parent_context=""):
            """Recursively process assignment statements in a list of statements"""
            if not statements_list:
                return

            i = 0
            while i < len(statements_list):
                item = statements_list[i]

                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item:
                    line = item["line"].strip()

                    # Check if this line contains an assignment operator (:=)
                    if " := " in line:
                        logger.debug(
                            "Found assignment statement at line %d in %s: %s",
                            item["line_no"],
                            parent_context,
                            line[:30],
                        )

                        # Check if this assignment ends with semicolon on the same line
                        if item["is_end_semicolon"]:
                            # Single line assignment statement
                            assignment_parts = self._parse_assignment_line(line)
                            if assignment_parts:
                                assignment_statement = {
                                    "variable": assignment_parts["variable"],
                                    "value": assignment_parts["value"],
                                    "type": "assignment_statement",
                                    "statement_indent": item["indent"],
                                    "statement_line_no": item["line_no"]
                                }
                                statements_list[i] = assignment_statement
                                logger.debug(
                                    "Parsed single-line assignment statement: %s",
                                    assignment_parts["variable"],
                                )
                        else:
                            # Multi-line assignment statement - find the end
                            assignment_lines = [line]
                            j = i + 1

                            # Collect all lines until we find a semicolon
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if isinstance(next_item, dict) and "line" in next_item:
                                    next_line = next_item["line"].strip()
                                    assignment_lines.append(next_line)

                                    if next_item["is_end_semicolon"]:
                                        # Found the end of the assignment statement
                                        break
                                    j += 1
                                else:
                                    # Not a line_info object, stop here
                                    break

                            # Create the complete assignment statement
                            complete_assignment = " ".join(assignment_lines)
                            assignment_parts = self._parse_assignment_line(
                                complete_assignment
                            )

                            if assignment_parts:
                                assignment_statement = {
                                    "variable": assignment_parts["variable"],
                                    "value": assignment_parts["value"],
                                    "type": "assignment_statement",
                                    "statement_indent": item["indent"],
                                    "statement_line_no": item["line_no"]	
                                }

                                # Replace the first line with the complete statement
                                statements_list[i] = assignment_statement

                                # Remove the subsequent lines that were part of this assignment statement
                                for k in range(j, i, -1):
                                    if k < len(statements_list):
                                        statements_list.pop(k)

                                logger.debug(
                                    "Parsed multi-line assignment statement: %s",
                                    assignment_parts["variable"],
                                )
                                continue

                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process assignment statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_assignment_statement_in_list(
                                item["begin_end_statements"],
                                f"{parent_context}.begin_end_statements",
                            )

                        # Process assignment statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_assignment_statement_in_list(
                                        handler["exception_statements"],
                                        f"{parent_context}.exception_statements",
                                    )

                    elif item["type"] == "case_when":
                        # Process assignment statements in when_clauses (then_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if (
                                    "when_value" in clause
                                    and "then_statements" in clause
                                ):
                                    process_assignment_statement_in_list(
                                        clause["then_statements"],
                                        f"{parent_context}.then_statements",
                                    )

                        # Process assignment statements in top-level else_statements
                        if "else_statements" in item:
                            process_assignment_statement_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "if_else":
                        # Process assignment statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_assignment_statement_in_list(
                                item["then_statements"],
                                f"{parent_context}.then_statements",
                            )

                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_assignment_statement_in_list(
                                        elsif_block["then_statements"],
                                        f"{parent_context}.else_if.then_statements",
                                    )

                        if "else_statements" in item:
                            process_assignment_statement_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "for_loop":
                        # Process assignment statements in loop_statements
                        if "loop_statements" in item:
                            process_assignment_statement_in_list(
                                item["loop_statements"],
                                f"{parent_context}.loop_statements",
                            )

                i += 1

        # Process the main_section_lines
        process_assignment_statement_in_list(
            self.main_section_lines, "main_section_lines"
        )

        logger.debug("Assignment statements parsing complete")

    def _parse_assignment_line(self, line):
        """
        Parse an assignment line to extract variable name and value.

        Args:
            line (str): The assignment line (e.g., "v_count := 10;")

        Returns:
            dict: Dictionary with variable name and value, or None if parsing fails
        """
        try:
            # Remove trailing semicolon if present
            line = line.strip().rstrip(";")

            # Split by " := " to separate variable and value
            if " := " in line:
                parts = line.split(" := ", 1)
                if len(parts) == 2:
                    variable = parts[0].strip()
                    value = parts[1].strip()
                    value = self.format_values(value)
                    return {"variable": variable, "value": value}
        except Exception as e:
            logger.debug("Failed to parse assignment line '%s': %s", line, e)

        return None

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
        logger.debug("Starting SQL statements parsing")

        # Define SQL statement type mapping
        STMT_TYPE_MAP = {
            "SELECT": "select_statement",
            "INSERT": "insert_statement",
            "UPDATE": "update_statement",
            "DELETE": "delete_statement",
            "RAISE": "raise_statement",
        }

        def process_sql_statements_in_list(statements_list, parent_context=""):
            """Recursively process SQL statements in a list of statements"""
            if not statements_list:
                return

            i = 0
            while i < len(statements_list):
                item = statements_list[i]

                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()

                    # Check if this line starts with a SQL statement type
                    sql_type = None
                    for stmt_keyword, stmt_type in STMT_TYPE_MAP.items():
                        if line_upper.startswith(stmt_keyword):
                            sql_type = stmt_type
                            break

                    if sql_type:
                        logger.debug(
                            "Found SQL statement at line %d in %s: %s",
                            item["line_no"],
                            parent_context,
                            line_upper[:20],
                        )

                        # Check if this statement ends with semicolon on the same line
                        if item["is_end_semicolon"]:
                            # Single line SQL statement
                            sql_statement = {"sql_statement": line, "type": sql_type, "statement_indent": item["indent"], "statement_line_no": item["line_no"]}
                            statements_list[i] = sql_statement
                            logger.debug(
                                "Parsed single-line SQL statement: %s", sql_type
                            )
                        else:
                            # Multi-line SQL statement - find the end
                            sql_lines = [line]
                            j = i + 1

                            # Collect all lines until we find a semicolon
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if isinstance(next_item, dict) and "line" in next_item:
                                    next_line = next_item["line"].strip()
                                    sql_lines.append(next_line)

                                    if next_item["is_end_semicolon"]:
                                        # Found the end of the SQL statement
                                        break
                                    j += 1
                                else:
                                    # Not a line_info object, stop here
                                    break

                            # Create the complete SQL statement
                            complete_sql = " ".join(sql_lines)
                            sql_statement = {"sql_statement": complete_sql, "type": sql_type, "statement_indent": item["indent"], "statement_line_no": item["line_no"]}

                            # Replace the first line with the complete statement
                            statements_list[i] = sql_statement

                            # Remove the subsequent lines that were part of this SQL statement
                            for k in range(j, i, -1):
                                if k < len(statements_list):
                                    statements_list.pop(k)

                            logger.debug(
                                "Parsed multi-line SQL statement: %s", sql_type
                            )
                            continue

                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process SQL statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_sql_statements_in_list(
                                item["begin_end_statements"],
                                f"{parent_context}.begin_end_statements",
                            )

                        # Process SQL statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_sql_statements_in_list(
                                        handler["exception_statements"],
                                        f"{parent_context}.exception_statements",
                                    )

                    elif item["type"] == "case_when":
                        # Process SQL statements in when_clauses (then_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if (
                                    "when_value" in clause
                                    and "then_statements" in clause
                                ):
                                    process_sql_statements_in_list(
                                        clause["then_statements"],
                                        f"{parent_context}.then_statements",
                                    )

                        # Process SQL statements in top-level else_statements
                        if "else_statements" in item:
                            process_sql_statements_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "if_else":
                        # Process SQL statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_sql_statements_in_list(
                                item["then_statements"],
                                f"{parent_context}.then_statements",
                            )

                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_sql_statements_in_list(
                                        elsif_block["then_statements"],
                                        f"{parent_context}.else_if.then_statements",
                                    )

                        if "else_statements" in item:
                            process_sql_statements_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "for_loop":
                        # Process SQL statements in loop_statements
                        if "loop_statements" in item:
                            process_sql_statements_in_list(
                                item["loop_statements"],
                                f"{parent_context}.loop_statements",
                            )

                i += 1

        # Process the main_section_lines
        process_sql_statements_in_list(self.main_section_lines, "main_section_lines")

        logger.debug("SQL statements parsing complete")

    def _parse_case_when(self):
        """
        Parse CASE WHEN ELSE statements from the main section of SQL with proper nested structure based on indentation.
        First detects CASE and END CASE; line numbers, then finds all WHEN and ELSE statements at the same indentation level.
        Maintains the hierarchical structure of CASE-WHEN-ELSE blocks by checking indentation levels.
        Updates self.main_section_lines with parsed blocks.
        """
        logger.debug("Starting CASE WHEN ELSE parsing with indentation-based nesting")

        def process_case_statements_in_list(statements_list, parent_context=""):
            """Recursively process CASE statements in a list of statements"""
            if not statements_list:
                return

            i = 0
            while i < len(statements_list):
                item = statements_list[i]

                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()

                    # Check for CASE statement start
                    if line_upper == "CASE" or line_upper.startswith("CASE "):
                        logger.debug(
                            "Found CASE statement at line %d in %s",
                            item["line_no"],
                            parent_context,
                        )
                        case_result = self._parse_case_statement_enhanced(
                            self._find_line_index(item["line_no"])
                        )
                        if case_result:
                            case_block, end_idx = case_result
                            # Replace the line_info with the parsed case_block
                            statements_list[i] = case_block
                            logger.debug(
                                "Parsed complete CASE statement structure in %s",
                                parent_context,
                            )
                            # Remove any subsequent line_info objects that are part of the CASE statement
                            # (they will be included in the case_block)
                            j = i + 1
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if (
                                    isinstance(next_item, dict)
                                    and "line_no" in next_item
                                ):
                                    # Get the end line number from the case_block
                                    end_line_no = case_block.get("end_case_line_no")
                                    if (
                                        end_line_no
                                        and next_item["line_no"] > end_line_no
                                    ):
                                        break
                                    statements_list.pop(j)
                                else:
                                    j += 1
                            continue

                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process CASE statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_case_statements_in_list(
                                item["begin_end_statements"],
                                f"{parent_context}.begin_end_statements",
                            )

                        # Process CASE statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_case_statements_in_list(
                                        handler["exception_statements"],
                                        f"{parent_context}.exception_statements",
                                    )

                    elif item["type"] == "case_when":
                        # Process CASE statements in when_clauses (then_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if (
                                    "when_value" in clause
                                    and "then_statements" in clause
                                ):
                                    process_case_statements_in_list(
                                        clause["then_statements"],
                                        f"{parent_context}.then_statements",
                                    )

                        # Process CASE statements in top-level else_statements
                        if "else_statements" in item:
                            process_case_statements_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "if_else":
                        # Process CASE statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_case_statements_in_list(
                                item["then_statements"],
                                f"{parent_context}.then_statements",
                            )

                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_case_statements_in_list(
                                        elsif_block["then_statements"],
                                        f"{parent_context}.else_if.then_statements",
                                    )

                        if "else_statements" in item:
                            process_case_statements_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "for_loop":
                        # Process CASE statements in loop_statements
                        if "loop_statements" in item:
                            process_case_statements_in_list(
                                item["loop_statements"],
                                f"{parent_context}.loop_statements",
                            )

                i += 1

        # Process the main_section_lines
        process_case_statements_in_list(self.main_section_lines, "main_section_lines")

        logger.debug("CASE WHEN ELSE parsing complete")

    def _find_line_index(self, line_no):
        """Find the index in structured_lines for a given line number"""
        for i, line_info in enumerate(self.structured_lines):
            if line_info["line_no"] == line_no:
                return i
        return -1

    def _parse_begin_end(self):
        """
        Parse nested BEGIN blocks from the main section of SQL.
        This method processes nested BEGIN-END blocks within the already parsed structure.
        Updates self.main_section_lines with parsed nested blocks.
        """
        logger.debug("Starting nested BEGIN block parsing")

        def process_begin_end_in_list(statements_list, parent_context=""):
            """Recursively process BEGIN blocks in a list of statements"""
            if not statements_list:
                return

            i = 0
            while i < len(statements_list):
                item = statements_list[i]

                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()

                    # Check for BEGIN block start
                    if line_upper == "BEGIN":
                        logger.debug(
                            "Found nested BEGIN block at line %d in %s",
                            item["line_no"],
                            parent_context,
                        )
                        # Parse the BEGIN block structure
                        begin_end_result = self._parse_begin_end_structure(
                            self._find_line_index(item["line_no"])
                        )
                        if begin_end_result:
                            begin_end_block, end_idx = begin_end_result
                            # Replace the line_info with the parsed begin_end_block
                            statements_list[i] = begin_end_block
                            logger.debug(
                                "Parsed complete nested BEGIN block structure in %s",
                                parent_context,
                            )
                            # Remove any subsequent line_info objects that are part of the BEGIN block
                            # (they will be included in the begin_end_block)
                            j = i + 1
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if (
                                    isinstance(next_item, dict)
                                    and "line_no" in next_item
                                ):
                                    if next_item["line_no"] > end_idx:
                                        break
                                    statements_list.pop(j)
                                else:
                                    j += 1
                            continue

                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process BEGIN blocks in begin_end_statements
                        if "begin_end_statements" in item:
                            process_begin_end_in_list(
                                item["begin_end_statements"],
                                f"{parent_context}.begin_end_statements",
                            )

                        # Process BEGIN blocks in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_begin_end_in_list(
                                        handler["exception_statements"],
                                        f"{parent_context}.exception_statements",
                                    )

                    elif item["type"] == "case_when":
                        # Process BEGIN blocks in when_clauses (then_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if (
                                    "when_value" in clause
                                    and "then_statements" in clause
                                ):
                                    process_begin_end_in_list(
                                        clause["then_statements"],
                                        f"{parent_context}.then_statements",
                                    )

                        # Process BEGIN blocks in top-level else_statements
                        if "else_statements" in item:
                            process_begin_end_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "if_else":
                        # Process BEGIN blocks in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_begin_end_in_list(
                                item["then_statements"],
                                f"{parent_context}.then_statements",
                            )

                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_begin_end_in_list(
                                        elsif_block["then_statements"],
                                        f"{parent_context}.else_if.then_statements",
                                    )

                        if "else_statements" in item:
                            process_begin_end_in_list(
                                item["else_statements"],
                                f"{parent_context}.else_statements",
                            )

                    elif item["type"] == "for_loop":
                        # Process BEGIN blocks in loop_statements
                        if "loop_statements" in item:
                            process_begin_end_in_list(
                                item["loop_statements"],
                                f"{parent_context}.loop_statements",
                            )

                i += 1

        # Process the main_section_lines recursively for nested BEGIN structures
        process_begin_end_in_list(self.main_section_lines, "main_section_lines")

        logger.debug("Nested BEGIN block parsing complete")

    def _parse_begin_end_structure(self, start_idx):
        """
        Parse a complete BEGIN-END block structure starting from the given index.
        Returns (begin_end_block, end_line_index) or None if parsing fails.
        """
        if start_idx < 0 or start_idx >= len(self.structured_lines):
            return None

        start_line_info = self.structured_lines[start_idx]
        start_line = start_line_info["line"].strip()
        start_line_upper = start_line.upper()

        # Verify this is a BEGIN statement
        if start_line_upper != "BEGIN":
            return None

        logger.debug(
            "Parsing BEGIN-END block starting at line %d", start_line_info["line_no"]
        )

        # Initialize the block structure
        begin_end_block = {
            "type": "begin_end",
            "begin_end_statements": [],
            "exception_handlers": [],
        }

        # Track block nesting
        block_stack = [begin_end_block]
        current_block = begin_end_block

        i = start_idx + 1
        while i < len(self.structured_lines):
            line_info = self.structured_lines[i]
            line = line_info["line"].strip()
            line_upper = line.upper()

            # Check for nested BEGIN
            if line_upper == "BEGIN":
                # Start a new nested block
                nested_block = {
                    "type": "begin_end",
                    "begin_end_statements": [],
                    "exception_handlers": [],
                }
                current_block["begin_end_statements"].append(nested_block)
                block_stack.append(nested_block)
                current_block = nested_block
                logger.debug(
                    "Found nested BEGIN block at line %d", line_info["line_no"]
                )

            # Check for END
            elif line_upper == "END;":
                if len(block_stack) > 1:
                    # End of nested block
                    block_stack.pop()
                    current_block = block_stack[-1]
                    logger.debug(
                        "Ended nested BEGIN block at line %d", line_info["line_no"]
                    )
                else:
                    # End of main block
                    logger.debug(
                        "Ended main BEGIN block at line %d", line_info["line_no"]
                    )
                    return begin_end_block, line_info["line_no"]

            # Check for EXCEPTION section
            elif line_upper == "EXCEPTION":
                # Start exception handling section
                current_block["exception_handlers"] = []
                logger.debug("Found EXCEPTION section at line %d", line_info["line_no"])

            # Check for exception handlers
            elif line_upper.startswith("WHEN ") and " THEN" in line_upper:
                if "exception_handlers" in current_block:
                    # Parse exception handler
                    exception_handler = self._parse_exception_handler(line)
                    if exception_handler:
                        # Initialize exception_statements array for the exception handler
                        exception_handler["exception_statements"] = []
                        current_block["exception_handlers"].append(exception_handler)
                        logger.debug(
                            "Parsed exception handler: %s",
                            exception_handler["exception_name"],
                        )

            # Add regular statements to current block
            elif line and not line.startswith("--"):
                if (
                    "exception_handlers" in current_block
                    and current_block["exception_handlers"]
                ):
                    # Add to the last exception handler's exception_statements
                    last_handler = current_block["exception_handlers"][-1]
                    if "exception_statements" not in last_handler:
                        last_handler["exception_statements"] = []
                    last_handler["exception_statements"].append(line_info)
                else:
                    # Add to the current block's begin_end_statements
                    current_block["begin_end_statements"].append(line_info)

            i += 1

        # If we reach here, the block wasn't properly closed
        logger.warning(
            "BEGIN block starting at line %d was not properly closed",
            start_line_info["line_no"],
        )
        return None

    def _process_block_sqls(self, block):
        """
        Process a block's SQL statements to identify and structure CASE statements.
        This is called after a complete block has been parsed.

        Args:
            block (dict): The parsed block containing SQL statements
        """
        if not block or "begin_end_statements" not in block:
            return

        # Skip if there are no begin_end_statements in the block
        if not block["begin_end_statements"]:
            return

        logger.debug(
            "Processing block begin_end_statements for potential nested CASE statements"
        )

        # No additional processing needed here as we now process CASE statements
        # during initial parsing

    def _parse_case_statement_enhanced(self, start_idx):
        """
        Parse a CASE statement from structured_lines with enhanced line number detection and indentation-based nesting.
        First detects CASE and END CASE; line numbers, then finds all WHEN and ELSE statements at the same indentation level.

        Args:
            start_idx (int): Index in structured_lines where the CASE statement starts

        Returns:
            tuple: (case_block, end_idx) if successful, None otherwise
        """
        logger.debug(
            "Starting enhanced CASE statement parsing from index %d", start_idx
        )

        # Check if we have a valid CASE statement
        if start_idx >= len(self.structured_lines):
            logger.debug("Invalid start index for CASE statement")
            return None

        case_line_info = self.structured_lines[start_idx]
        case_line = case_line_info["line"].strip()
        case_indent = case_line_info["indent"]
        case_line_no = case_line_info["line_no"]

        # Determine if this is a CASE with expression or a simple CASE
        case_expression = ""
        if case_line.upper() != "CASE":
            # Extract expression part after "CASE "
            case_expression = case_line[5:].strip()

        logger.debug(
            "CASE statement - Type: %s, Expression: '%s', Indent: %d",
            "simple" if not case_expression else "with expression",
            case_expression,
            case_indent,
        )

        # Step 1: Find the matching END CASE; at the same indentation level
        end_case_line_no = None
        end_case_idx = -1

        i = start_idx + 1
        while i < len(self.structured_lines):
            line_info = self.structured_lines[i]
            line = line_info["line"].strip()
            line_upper = line.upper()
            indent = line_info["indent"]

            # Check for END CASE; at the same indentation level
            if line_upper == "END CASE;" and indent == case_indent:
                end_case_line_no = line_info["line_no"]
                end_case_idx = i
                logger.debug(
                    "Found END CASE; at line %d (indent %d)", end_case_line_no, indent
                )
                break

            # Handle nested CASE statements - skip to their END CASE;
            elif line_upper == "CASE" and indent > case_indent:
                nested_indent = indent
                j = i + 1
                while j < len(self.structured_lines):
                    nested_line_info = self.structured_lines[j]
                    nested_line = nested_line_info["line"].strip()
                    nested_line_upper = nested_line.upper()
                    nested_indent_level = nested_line_info["indent"]

                    if (
                        nested_line_upper == "END CASE;"
                        and nested_indent_level == nested_indent
                    ):
                        i = j  # Skip to the end of nested CASE
                        break
                    j += 1

            i += 1

        if end_case_line_no is None:
            logger.warning(
                "Could not find matching END CASE; for CASE statement at line %d",
                case_line_no,
            )
            return None

        # Step 2: Find all WHEN and ELSE statements between CASE and END CASE; at the same or higher indentation level
        when_line_nos = []
        else_line_no = None

        for k in range(start_idx + 1, end_case_idx):
            line_info = self.structured_lines[k]
            line = line_info["line"].strip()
            line_upper = line.upper()
            indent = line_info["indent"]

            # Check for WHEN statements at the same or higher indentation level than CASE
            if (
                line_upper.startswith("WHEN ")
                and " THEN" in line_upper
                and indent >= case_indent
            ):
                when_line_nos.append(line_info["line_no"])
                logger.debug(
                    "Found WHEN clause at line %d (indent %d, case indent %d)",
                    line_info["line_no"],
                    indent,
                    case_indent,
                )

            # Check for ELSE statement at the same or higher indentation level than CASE
            elif line_upper == "ELSE" and indent >= case_indent:
                else_line_no = line_info["line_no"]
                logger.debug(
                    "Found ELSE clause at line %d (indent %d, case indent %d)",
                    line_info["line_no"],
                    indent,
                    case_indent,
                )

        # Step 3: Build the enhanced case statement structure
        case_statement = {
            "type": "case_when",
            "case_expression": case_expression,
            "when_clauses": [],
            "else_statements": [],
            "case_line_no": case_line_no,
            "case_indent": case_indent,
            "when_line_nos": when_line_nos,
            "else_line_no": else_line_no,
            "end_case_line_no": end_case_line_no,
        }

        # Step 4: Process WHEN clauses
        for when_line_no in when_line_nos:
            when_clause = self._parse_when_clause(
                when_line_no, case_indent, end_case_line_no
            )
            if when_clause:
                case_statement["when_clauses"].append(when_clause)

        # Step 5: Process ELSE clause if exists
        if else_line_no:
            else_clause = self._parse_else_clause(
                else_line_no, case_indent, end_case_line_no
            )
            if else_clause:
                case_statement["else_statements"] = else_clause.get("else_statements", [])

        # Step 6: Process nested structures in each clause
        self._process_nested_structures_in_case_enhanced(case_statement)

        logger.debug(
            "Completed enhanced CASE statement parsing: %d when clauses, ELSE at line %s, end at line %d",
            len(when_line_nos),
            else_line_no or "None",
            end_case_line_no,
        )

        return case_statement, end_case_idx

    def _parse_case_statement(self, start_idx):
        """
        Parse a CASE statement from structured_lines, starting at the given index.

        Args:
            start_idx (int): Index in structured_lines where the CASE statement starts

        Returns:
            tuple: (case_block, end_idx) if successful, None otherwise
        """
        logger.debug("Starting CASE statement parsing from index %d", start_idx)

        # Initialize case statement structure
        case_statement = {
            "type": "case_when",
            "case_expression": "",
            "when_clauses": [],
        }

        # Collect the full CASE statement text for debugging and the 'sql' field
        full_case_text = []

        # Check if we have a valid CASE statement
        if start_idx >= len(self.structured_lines):
            logger.debug("Invalid start index for CASE statement")
            return None

        case_line = self.structured_lines[start_idx]["line"].strip()
        case_indent = self.structured_lines[start_idx]["indent"]
        full_case_text.append(case_line)

        # Determine if this is a CASE with expression or a simple CASE
        if case_line.upper() == "CASE":
            case_statement["case_expression"] = ""
        else:
            # Extract expression part after "CASE "
            case_statement["case_expression"] = case_line[5:].strip()

        logger.debug(
            "CASE statement - Type: %s, Expression: '%s'",
            "simple" if not case_statement["case_expression"] else "with expression",
            case_statement["case_expression"],
        )

        # Find matching END CASE; at the same indentation level
        end_idx = -1
        current_when_clause = None
        collecting_then_statements = False
        current_statements = []

        # Stack to track nested blocks inside CASE
        nested_blocks = []
        in_nested_block = False

        i = start_idx + 1
        while i < len(self.structured_lines):
            line_info = self.structured_lines[i]
            line = line_info["line"].strip()
            line_upper = line.upper()
            indent = line_info["indent"]

            # Track the original line with indentation preserved
            original_line = self.structured_lines[i]["line"]
            full_case_text.append(original_line)

            # Check for END CASE; at the same indentation as CASE
            if line_upper == "END CASE;" and indent == case_indent:
                end_idx = i
                break

            # Handle nested BEGIN blocks
            if line_upper == "BEGIN":
                logger.debug(
                    "Found nested BEGIN block in CASE statement at line %d",
                    line_info["line_no"],
                )
                nested_blocks.append(("BEGIN", indent))
                in_nested_block = True

                if collecting_then_statements:
                    # Start collecting the nested block as a single statement
                    current_nested_block = ["BEGIN"]

            elif line_upper == "END;" and in_nested_block:
                if nested_blocks and nested_blocks[-1][0] == "BEGIN":
                    logger.debug("Found end of nested BEGIN block in CASE statement")
                    nested_blocks.pop()

                    if not nested_blocks:
                        in_nested_block = False

                        if (
                            collecting_then_statements
                            and current_when_clause is not None
                        ):
                            # Add the complete nested block to the current clause
                            # Create a line_info object for the END; statement
                            end_line_info = {
                                "indent": indent,
                                "line": "END;",
                                "line_no": line_info["line_no"],
                                "is_end_semicolon": True,
                            }
                            current_nested_block.append(end_line_info)

                            if "when_value" in current_when_clause:
                                current_when_clause["then_statements"].extend(
                                    current_nested_block
                                )
                            else:
                                current_when_clause["else_statements"].extend(
                                    current_nested_block
                                )

                            current_nested_block = []

            # Process WHEN clause - ensure it's at the same indentation level as CASE
            # or slightly more indented (common formatting style)
            elif (
                line_upper.startswith("WHEN ")
                and " THEN" in line_upper
                and (indent == case_indent or indent == case_indent + 3)
            ):
                # If we were collecting statements for previous WHEN or ELSE,
                # save them to the current clause
                if collecting_then_statements and current_when_clause is not None:
                    if "when_value" in current_when_clause:
                        current_when_clause["then_statements"] = current_statements
                    else:
                        current_when_clause["then_statements"] = current_statements
                    current_statements = []

                # Extract the when value/condition
                when_value = line[5:].split(" THEN", 1)[0].strip()
                logger.debug("Found WHEN clause: %s", when_value)

                # Create a new when clause
                current_when_clause = {"when_value": when_value, "then_statements": []}
                case_statement["when_clauses"].append(current_when_clause)
                collecting_then_statements = True

            # Process ELSE clause - ensure it's at the same indentation level as WHEN clauses
            elif line_upper == "ELSE" and (
                indent == case_indent or indent == case_indent + 3
            ):
                # Save any pending WHEN clause statements
                if collecting_then_statements and current_when_clause is not None:
                    if "when_value" in current_when_clause:
                        current_when_clause["then_statements"] = current_statements
                    current_statements = []

                # Create the ELSE clause
                logger.debug(
                    "Found ELSE clause at indent %d (case indent: %d)",
                    indent,
                    case_indent,
                )
                current_when_clause = {"else_statements": []}
                case_statement["when_clauses"].append(current_when_clause)
                collecting_then_statements = True

            # Collect statements for the current WHEN or ELSE clause
            elif collecting_then_statements:
                if in_nested_block:
                    # Collecting lines for a nested block
                    current_nested_block.append(line_info)
                elif indent > case_indent:
                    # Regular statement in a WHEN/ELSE clause
                    # Keep original line indentation relative to the CASE statement
                    # to preserve the structure in the statement array
                    current_statements.append(line_info)

            i += 1

        # Save any remaining statements for the last clause
        if collecting_then_statements and current_when_clause is not None:
            if "when_value" in current_when_clause:
                current_when_clause["then_statements"] = current_statements
            else:
                current_when_clause["else_statements"] = current_statements

        # Check if we found a complete CASE statement
        if end_idx == -1:
            logger.debug(
                "Could not find matching END CASE; for CASE statement at index %d",
                start_idx,
            )
            return None

        # Process the statements in each clause to handle nested structures
        self._process_nested_structures_in_case(case_statement)

        # Add the full SQL text to the case_statement, preserving original indentation
        case_statement["sql"] = "\n".join(full_case_text)

        logger.debug(
            "Completed CASE statement parsing: %d when clauses, end at index %d",
            len(case_statement["when_clauses"]),
            end_idx,
        )

        return case_statement, end_idx

    def _parse_when_clause(self, when_line_no, case_indent, end_case_line_no):
        """
        Parse a WHEN clause starting at the given line number.

        Args:
            when_line_no (int): Line number where WHEN clause starts
            case_indent (int): Indentation level of the parent CASE statement
            end_case_line_no (int): Line number where END CASE; is located

        Returns:
            dict: Parsed WHEN clause structure
        """
        when_clause = {
            "when_value": "",
            "then_statements": [],
            "when_line_no": when_line_no,
        }

        # Find the WHEN line and extract the condition
        when_line_info = None
        for line_info in self.structured_lines:
            if line_info["line_no"] == when_line_no:
                when_line_info = line_info
                break

        if not when_line_info:
            logger.warning("Could not find WHEN line %d", when_line_no)
            return None

        when_line = when_line_info["line"].strip()
        when_line_upper = when_line.upper()

        # Extract the when value/condition
        if when_line_upper.startswith("WHEN ") and " THEN" in when_line_upper:
            when_value = when_line[5:].split(" THEN", 1)[0].strip()
            when_clause["when_value"] = when_value
            logger.debug("Parsed WHEN clause: %s", when_value)

        # Find the next WHEN or ELSE or END CASE; to determine the end of this clause
        next_clause_line_no = end_case_line_no

        for line_info in self.structured_lines:
            line_no = line_info["line_no"]
            if when_line_no < line_no < end_case_line_no:
                line = line_info["line"].strip()
                line_upper = line.upper()
                indent = line_info["indent"]

                # Check for next WHEN or ELSE at the same or higher indentation level
                if (
                    line_upper.startswith("WHEN ")
                    and " THEN" in line_upper
                    and indent >= case_indent
                ) or (line_upper == "ELSE" and indent >= case_indent):
                    next_clause_line_no = line_no
                    break

        # Collect statements between WHEN and next clause
        for line_info in self.structured_lines:
            line_no = line_info["line_no"]
            if when_line_no < line_no < next_clause_line_no:
                line = line_info["line"].strip()
                indent = line_info["indent"]

                # Only include statements that are more indented than the CASE
                if indent > case_indent and line and not line.startswith("--"):
                    when_clause["then_statements"].append(line_info)

        return when_clause

    def _parse_else_clause(self, else_line_no, case_indent, end_case_line_no):
        """
        Parse an ELSE clause starting at the given line number.

        Args:
            else_line_no (int): Line number where ELSE clause starts
            case_indent (int): Indentation level of the parent CASE statement
            end_case_line_no (int): Line number where END CASE; is located

        Returns:
            dict: Parsed ELSE clause structure
        """
        else_clause = {"else_statements": [], "else_line_no": else_line_no}

        # Collect statements between ELSE and END CASE;
        for line_info in self.structured_lines:
            line_no = line_info["line_no"]
            if else_line_no < line_no < end_case_line_no:
                line = line_info["line"].strip()
                indent = line_info["indent"]

                # Only include statements that are more indented than the CASE
                if indent > case_indent and line and not line.startswith("--"):
                    else_clause["else_statements"].append(line_info)

        logger.debug(
            "Parsed ELSE clause with %d statements", len(else_clause["else_statements"])
        )
        return else_clause

    def _process_nested_structures_in_case_enhanced(self, case_statement):
        """
        Process any nested structures within the enhanced case statement.

        Args:
            case_statement (dict): The enhanced case statement structure to process
        """
        logger.debug("Processing nested structures in enhanced CASE statement")

        # Process each when clause
        for clause in case_statement["when_clauses"]:
            if "when_value" in clause and "then_statements" in clause:
                # Process WHEN clause statements
                statements = clause["then_statements"]
                processed_statements = self._process_statements_for_nested_structures(
                    statements
                )
                clause["then_statements"] = processed_statements

        # Process top-level else_statements
        if case_statement.get("else_statements"):
            statements = case_statement["else_statements"]
            processed_statements = self._process_statements_for_nested_structures(
                statements
            )
            case_statement["else_statements"] = processed_statements

    def _process_nested_structures_in_case(self, case_statement):
        """
        Process any nested structures (like nested CASE statements or BEGIN blocks)
        within the statements of each WHEN/ELSE clause.

        Args:
            case_statement (dict): The case statement structure to process
        """
        logger.debug("Processing nested structures in CASE statement")

        # Process each when clause
        for clause in case_statement["when_clauses"]:
            if "when_value" in clause and "then_statements" in clause:
                # Process WHEN clause statements
                statements = clause["then_statements"]
                processed_statements = self._process_statements_for_nested_structures(
                    statements
                )
                clause["then_statements"] = processed_statements
            elif "else_statements" in clause:
                # Process ELSE clause statements
                statements = clause["else_statements"]
                processed_statements = self._process_statements_for_nested_structures(
                    statements
                )
                clause["else_statements"] = processed_statements

    def _process_statements_for_nested_structures(self, statements):
        """
        Process a list of statements to identify and parse any nested structures
        such as CASE statements or BEGIN blocks.

        Args:
            statements (list): List of statement line_info objects and parsed structures

        Returns:
            list: Processed list of statements with nested structures converted to proper format
        """
        processed = []
        i = 0

        while i < len(statements):
            stmt_info = statements[i]

            # Check if this is a line_info object or already parsed structure
            if isinstance(stmt_info, dict) and "line" in stmt_info:
                stmt = stmt_info["line"].strip()
            elif isinstance(stmt_info, dict) and "type" in stmt_info:
                # This is already a parsed structure (e.g., if_else, case_when, etc.)
                # Process it recursively for nested structures
                self._process_nested_structures_recursively(stmt_info)
                processed.append(stmt_info)
                i += 1
                continue
            else:
                # Unknown structure, keep as is
                processed.append(stmt_info)
                i += 1
                continue

            # Check for nested CASE statements
            if stmt.upper().startswith("CASE"):
                # Check if this CASE statement has already been parsed by looking ahead
                # to see if the next few statements are already parsed structures
                already_parsed = False
                j = i + 1
                while j < len(statements) and j < i + 10:  # Check next 10 statements
                    if isinstance(statements[j], dict) and "type" in statements[j]:
                        if statements[j]["type"] == "case_when":
                            # This CASE statement has already been parsed, skip it
                            already_parsed = True
                            break
                    j += 1
                
                if already_parsed:
                    # Skip this CASE statement as it's already been parsed
                    processed.append(stmt_info)
                    i += 1
                    continue
                
                # Found potential nested CASE statement that hasn't been parsed yet
                # Try to use the enhanced parsing method for nested CASE statements
                case_start_line_no = stmt_info["line_no"]
                
                # Find the corresponding line in structured_lines
                case_start_idx = -1
                for idx, line_info in enumerate(self.structured_lines):
                    if line_info["line_no"] == case_start_line_no:
                        case_start_idx = idx
                        break
                
                if case_start_idx != -1:
                    # Use the enhanced parsing method
                    case_result = self._parse_case_statement_enhanced(case_start_idx)
                    if case_result:
                        nested_case, end_idx = case_result
                        # Add this nested CASE structure as a single entity
                        processed.append(nested_case)
                        
                        # Skip past this CASE statement in the statements list
                        # Find the end line number and skip to it
                        end_line_no = nested_case.get("end_case_line_no")
                        if end_line_no:
                            j = i + 1
                            while j < len(statements):
                                if isinstance(statements[j], dict) and "line_no" in statements[j]:
                                    if statements[j]["line_no"] > end_line_no:
                                        break
                                j += 1
                            i = j
                            continue
                
                # Fallback: if enhanced parsing failed, use the old method
                case_text = [stmt]
                end_idx = -1

                # Find the end of the nested CASE statement
                for j in range(i + 1, len(statements)):
                    if isinstance(statements[j], dict) and "line" in statements[j]:
                        case_text.append(statements[j]["line"])
                        if statements[j]["line"].strip().upper() == "END CASE;":
                            end_idx = j
                            break

                if end_idx != -1:
                    # Found a complete nested CASE statement
                    logger.debug("Found nested CASE statement in clause (fallback method)")

                    # Create a nested case structure
                    nested_case = {
                        "type": "case_when",
                        "case_expression": "",
                        "when_clauses": [],
                        "else_statements": [],
                        "case_line_no": stmt_info["line_no"],
                        "case_indent": stmt_info["indent"],
                        "when_line_nos": [],
                        "else_line_no": None,
                        "end_case_line_no": statements[end_idx]["line_no"],
                        "sql": "\n".join(case_text),
                    }

                    # Add this nested CASE structure as a single entity
                    processed.append(nested_case)

                    # Skip past this CASE statement
                    i = end_idx + 1
                    continue

            # Regular statement
            processed.append(stmt_info)
            i += 1

        return processed

    def _parse_exception_section(
        self, exception_start_line_no: int, end_line_no: int
    ) -> List[Dict[str, Any]]:
        """
        Parse exception handling section from EXCEPTION to END.

        Args:
            exception_start_line_no (int): Line number where EXCEPTION starts
            end_line_no (int): Line number where END; is located

        Returns:
            List[Dict[str, Any]]: List of exception handlers with their statements
        """
        exception_handlers = []
        current_handler = None

        for line_info in self.structured_lines:
            line_no = line_info["line_no"]

            # Only process lines within the exception section
            if exception_start_line_no < line_no < end_line_no:
                line = line_info["line"].strip()
                line_upper = line.upper()

                # Check for exception handler (WHEN ... THEN)
                if line_upper.startswith("WHEN ") and " THEN" in line_upper:
                    # Save previous handler if exists
                    if current_handler:
                        exception_handlers.append(current_handler)

                    # Parse new exception handler
                    exception_handler = self._parse_exception_handler(line)
                    if exception_handler:
                        current_handler = exception_handler
                        current_handler["exception_statements"] = []
                        logger.debug(
                            "Found exception handler: %s",
                            exception_handler["exception_name"],
                        )

                # Check for RAISE statements in exception handlers
                elif line_upper.startswith("RAISE") and current_handler:
                    if "RAISE_APPLICATION_ERROR" in line_upper:
                        rae_info = self._parse_raise_application_error(line)
                        if rae_info:
                            # Create function_calling structure for RAISE_APPLICATION_ERROR
                            function_call = {
                                "type": "function_calling",
                                "function_name": "raise_application_error",
                                "parameter": {
                                    "handler_code": rae_info["handler_code"],
                                    "handler_string": rae_info["handler_string"],
                                },
                            }
                            current_handler["exception_statements"].append(
                                function_call
                            )
                            logger.debug(
                                "Added RAISE_APPLICATION_ERROR function call: %s",
                                rae_info,
                            )
                    else:
                        # Regular RAISE statement
                        raise_statement = {"sql_statement": line, "type": "raise_statement", "statement_indent": line_info["indent"], "statement_line_no": line_info["line_no"]}
                        current_handler["exception_statements"].append(raise_statement)
                        logger.debug("Added RAISE statement: %s", line)

                # Add regular SQL statements to current exception handler
                elif current_handler and line and not line.startswith("--"):
                    sql_statement = {"sql_statement": line, "type": "unknown_statement", "statement_indent": line_info["indent"], "statement_line_no": line_info["line_no"]}
                    current_handler["exception_statements"].append(sql_statement)
                    logger.debug("Added SQL statement to exception handler: %s", line)

        # Add the last handler if exists
        if current_handler:
            exception_handlers.append(current_handler)

        logger.debug("Parsed exception section: %d handlers", len(exception_handlers))
        return exception_handlers

    def _parse_exception_handler(self, line: str) -> Dict[str, Any]:
        """
        Parse an exception handler line.

        Args:
            line (str): The exception handler line (e.g., "WHEN no_data_found THEN")

        Returns:
            dict: Parsed exception handler information
        """
        try:
            # Extract exception name from "WHEN exception_name THEN"
            if line.upper().startswith("WHEN ") and " THEN" in line.upper():
                exception_part = line[5:]  # Remove "WHEN "
                exception_name = exception_part.split(" THEN")[0].strip()

                return {"exception_name": exception_name}
        except Exception as e:
            logger.debug("Failed to parse exception handler '%s': %s", line, e)

        return None

    def _parse_raise_application_error(self, line: str) -> Dict[str, str]:
        """
        Parse RAISE_APPLICATION_ERROR statement.

        Args:
            line (str): The RAISE_APPLICATION_ERROR line

        Returns:
            dict: Parsed error code and message
        """
        try:
            # Extract parameters from RAISE_APPLICATION_ERROR(error_code, message)
            if "RAISE_APPLICATION_ERROR" in line.upper():
                # Find the parentheses
                start_paren = line.find("(")
                end_paren = line.rfind(")")

                if start_paren != -1 and end_paren != -1:
                    params = line[start_paren + 1 : end_paren]

                    # Split by comma, but be careful with quoted strings
                    parts = self._split_params_safely(params)

                    if len(parts) >= 2:
                        handler_code = parts[0].strip()
                        handler_string = parts[1].strip()
                        handler_string = self.format_values(handler_string)
                        return {
                            "handler_code": handler_code,
                            "handler_string": handler_string,
                        }
        except Exception as e:
            logger.debug("Failed to parse RAISE_APPLICATION_ERROR '%s': %s", line, e)

        return None

    def _split_params_safely(self, params: str) -> List[str]:
        """
        Safely split parameters by comma, respecting quoted strings.

        Args:
            params (str): Parameter string

        Returns:
            list: List of parameter parts
        """
        parts = []
        current_part = ""
        in_quotes = False
        quote_char = None

        for char in params:
            if char in ["'", '"'] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_part += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current_part += char
            elif char == "," and not in_quotes:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char

        if current_part.strip():
            parts.append(current_part.strip())

        return parts

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
        # Step 1: Check for rule violations
        if self.rule_errors:
            logger.debug(
                "Rule violations detected: %d error(s), conversion aborted",
                len(self.rule_errors),
            )
            return {"error": self.rule_errors}

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
            # "strng_convert_json": self.strng_convert_json,
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
            "sql_convert_count": self.strng_convert_json
        }

        # Include parse timestamp
        result["metadata"] = {
            "parse_timestamp": self._get_timestamp(),
            "parser_version": "1.0",  # Increment when making significant parser changes
        }

        # Log detailed statistics for troubleshooting
        info(
            "JSON conversion complete: %d vars, %d consts, %d excs, %d comments",
            len(self.variables),
            len(self.constants),
            len(self.exceptions),
            len(self.sql_comments),
        )
        return result

    def _remove_duplicate_case_when_structures(self):
        """
        Remove duplicate case_when structures from the parsed result.
        This method identifies and removes duplicate case_when structures that have
        the same case_line_no and end_case_line_no.
        """
        logger.debug("Removing duplicate case_when structures")
        
        # Track seen case_when structures by their line numbers (global to all recursive calls)
        seen_case_when = set()
        
        def remove_duplicates_from_list(statements_list):
            """Recursively remove duplicate case_when structures from a list"""
            if not statements_list:
                return statements_list
            
            filtered_list = []
            
            for item in statements_list:
                if isinstance(item, dict) and item.get("type") == "case_when":
                    case_line_no = item.get("case_line_no")
                    end_case_line_no = item.get("end_case_line_no")
                    
                    logger.debug(f"Found case_when structure: case_line_no={case_line_no}, end_case_line_no={end_case_line_no}")
                    
                    if case_line_no and end_case_line_no:
                        case_key = f"{case_line_no}-{end_case_line_no}"
                        
                        if case_key in seen_case_when:
                            # This is a duplicate, skip it
                            logger.debug(f"Removing duplicate case_when structure: lines {case_line_no}-{end_case_line_no}")
                            continue
                        else:
                            # First time seeing this case_when structure
                            logger.debug(f"Adding new case_when structure: lines {case_line_no}-{end_case_line_no}")
                            seen_case_when.add(case_key)
                            # Process nested structures recursively
                            if "when_clauses" in item:
                                for clause in item["when_clauses"]:
                                    if "then_statements" in clause:
                                        clause["then_statements"] = remove_duplicates_from_list(clause["then_statements"])
                            if "else_statements" in item:
                                item["else_statements"] = remove_duplicates_from_list(item["else_statements"])
                            filtered_list.append(item)
                    else:
                        # No line numbers, keep as is
                        logger.debug(f"case_when structure without line numbers, keeping as is")
                        filtered_list.append(item)
                elif isinstance(item, dict) and "type" in item:
                    # Process other structured types recursively
                    if item["type"] == "if_else":
                        if "then_statements" in item:
                            item["then_statements"] = remove_duplicates_from_list(item["then_statements"])
                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    elsif_block["then_statements"] = remove_duplicates_from_list(elsif_block["then_statements"])
                        if "else_statements" in item:
                            item["else_statements"] = remove_duplicates_from_list(item["else_statements"])
                    elif item["type"] == "begin_end":
                        if "begin_end_statements" in item:
                            item["begin_end_statements"] = remove_duplicates_from_list(item["begin_end_statements"])
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = remove_duplicates_from_list(handler["exception_statements"])
                    elif item["type"] == "for_loop":
                        if "loop_statements" in item:
                            item["loop_statements"] = remove_duplicates_from_list(item["loop_statements"])
                    
                    filtered_list.append(item)
                else:
                    # Regular item, keep as is
                    filtered_list.append(item)
            
            return filtered_list
        
        # Remove duplicates from main_section_lines
        self.main_section_lines = remove_duplicates_from_list(self.main_section_lines)
        
        logger.debug("Duplicate case_when structures removal complete")

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
        if '||' in values:
            formatted_msg = formatted_msg.split('||')
            for i in range(len(formatted_msg)):
                formatted_msg[i] = formatted_msg[i].strip()
                # print(formatted_msg[i])
                if formatted_msg[i].startswith("'") and not formatted_msg[i].endswith("'"):
                    formatted_msg[i] = formatted_msg[i] + "'"
                elif not formatted_msg[i].startswith("'") and formatted_msg[i].endswith("'"):
                    formatted_msg[i] = "'" + formatted_msg[i]
            formatted_msg = " || ".join(formatted_msg)
        # else:
        #     if formatted_msg.startswith("'") or formatted_msg.endswith("'"):
        #         formatted_msg = formatted_msg
        #     else:
        #         formatted_msg = "'" + formatted_msg + "'"
        return formatted_msg

