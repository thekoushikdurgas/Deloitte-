import json
import os
import re
from typing import Any, Dict, List, Tuple
from utilities.common import logger, setup_logging


class OracleTriggerAnalyzer:
    """
    Parser and analyzer for Oracle PL/SQL trigger bodies.

    Architecture and flow:
    - Constructor receives raw SQL text and splits it into `DECLARE` and main sections.
    - Rule validation runs immediately to catch formatting violations (e.g., IF/THEN split lines).
    - Declaration parsing extracts variables, constants, exceptions into structured lists.
    - Main body is tokenized into lines, strip comments, then grouped into structured nodes:
      begin_block, if_else, case_when_statements, for_loop, DML/select, assignment, raise.
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
        logger.debug(
            "Initializing OracleTriggerAnalyzer with %d characters of SQL",
            len(sql_content),
        )
        self.sql_content: str = sql_content
        self.declare_section: List[int] = [0, 0]
        self.main_section: List[int] = [0, 0]
        self.main_section_lines: List[Dict] = []
        self.variables: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []
        self.exceptions: List[Dict[str, Any]] = []
        self.sql_comments: List[str] = []
        self.rule_errors: List[Dict[str, Any]] = []
        self.structured_lines: List[Dict[str, Any]] = []

        # Step 2: Parse SQL into declare and main sections
        logger.debug("Starting SQL section parsing")
        self._parse_sql()

        # Step 3: Validate formatting rules
        logger.debug("Starting rule validation")
        self.rule_errors = self._validate_rules()
        if self.rule_errors:
            logger.debug("Found %d rule violation(s)", len(self.rule_errors))

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
        logger.debug("Converting SQL content to structured lines")
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

        logger.debug(
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
        self._convert_to_structured_lines()

        # Step 2: Remove block comments (/* ... */)
        self._strip_block_comments()
        logger.debug("Removed block comments from main section")

        # Step 3: Remove inline comments (-- ...)
        self._strip_inline_comments_from_lines()
        logger.debug("Removed inline comments from main section")

        # Find DECLARE and BEGIN sections
        declare_start = -1
        begin_start = -1
        end_start = self.structured_lines[-1]["line_no"]

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

        if begin_start != -1 and end_start != -1:
            self.main_section = [begin_start, end_start]
            logger.debug("Main section: lines %d-%d", begin_start, end_start)
        else:
            self.main_section = [0, 0]
            logger.debug("Could not identify main section (BEGIN/END)")

        # Process declarations if DECLARE section exists
        if self.declare_section[0] > 0:
            self._parse_declarations()

        # Process main section if main section exists
        if self.main_section[0] > 0:
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
        else:
            declaration_part = line

        # Split declaration: constant_name CONSTANT data_type
        words = declaration_part.split()
        if len(words) < 3 or words[1].upper() != "CONSTANT":
            logger.debug("Invalid constant declaration format: %s", line)
            return None

        const_name = words[0]

        # Handle complex data types with parameters
        type_parts = words[2:]
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
            if line_upper == "IF":
                if i + 1 < len(self.structured_lines):
                    next_line_upper = (
                        self.structured_lines[i + 1]["line"].strip().upper()
                    )
                    if next_line_upper == "THEN":
                        errors.append(
                            {
                                "type": "if_then_split",
                                "message": "IF and THEN must be on the same line",
                                "line_no": line_no,
                                "line": line,
                                "solution": f"Combine lines {line_no} and {line_no + 1}: IF ... THEN",
                            }
                        )

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
        logger.debug(
            "Processing main section from lines %d-%d",
            self.main_section[0],
            self.main_section[1],
        )

        # Clear any existing main section lines
        # self.main_section_lines = []
        # Extract lines from the main section
        # for line_info in self.structured_lines:
        #     if self.main_section[0] <= line_info["line_no"] <= self.main_section[1]:
        #         if line_info["line"].strip().upper() == "BEGIN":
        #             self.main_section_lines.append(line_info)
        #             break
        #         else:
        #             self.main_section_lines.append(line_info)

        logger.debug(
            "Main section processing complete: %d lines extracted",
            len(self.main_section_lines),
        )
        # Step 3: Parse BEGIN blocks from the main section
        logger.debug("Parsing BEGIN blocks for JSON conversion")
        self._parse_begin_blocks()

    def _parse_begin_blocks(self):
        """
        Parse top-level BEGIN blocks from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        logger.debug("Starting BEGIN block parsing")
        
        # if not self.main_section_lines:
        #     logger.debug("No main section lines to parse")
        #     return
        current_block = None
        block_stack = []
        self.main_section_lines = []
        
        for line_info in self.structured_lines:
            if self.main_section[0] <= line_info["line_no"] <= self.main_section[1]:
                line = line_info["line"].strip()
                line_upper = line.upper()
                
                # Check for BEGIN block start
                if line_upper == "BEGIN":
                    # Start a new block
                    current_block = {
                        "sqls": [],
                        "type": "begin_block",
                        "exception_handlers": []
                    }
                    block_stack.append(current_block)
                    logger.debug("Found BEGIN block at line %d", line_info["line_no"])
                
                # Check for END block
                elif line_upper == "END;":
                    if block_stack:
                        # Complete the current block
                        completed_block = block_stack.pop()
                        
                        # If this is a top-level block, add to results
                        if not block_stack:
                            self.main_section_lines.append(completed_block)
                            logger.debug("Completed top-level BEGIN block")
                        else:
                            # This is a nested block, add to parent's sqls
                            block_stack[-1]["sqls"].append(completed_block)
                            logger.debug("Completed nested BEGIN block")
                
                # Check for EXCEPTION section
                elif line_upper == "EXCEPTION":
                    if block_stack:
                        # Start exception handling section
                        current_block = block_stack[-1]
                        current_block["exception_handlers"] = []
                        logger.debug("Found EXCEPTION section at line %d", line_info["line_no"])
                
                # Check for exception handlers
                elif line_upper.startswith("WHEN ") and " THEN" in line_upper:
                    if block_stack and "exception_handlers" in block_stack[-1]:
                        # Parse exception handler
                        exception_handler = self._parse_exception_handler(line)
                        if exception_handler:
                            block_stack[-1]["exception_handlers"].append(exception_handler)
                            logger.debug("Parsed exception handler: %s", exception_handler["exception_name"])
                
                # Check for RAISE_APPLICATION_ERROR in exception handlers
                elif "RAISE_APPLICATION_ERROR" in line_upper and block_stack:
                    if block_stack[-1]["exception_handlers"]:
                        # Add RAISE_APPLICATION_ERROR to the last exception handler
                        last_handler = block_stack[-1]["exception_handlers"][-1]
                        if "raise_application_error" not in last_handler:
                            last_handler["raise_application_error"] = {
                                "handler_code": "",
                                "handler_string": ""
                            }
                        
                        # Parse RAISE_APPLICATION_ERROR parameters
                        rae_info = self._parse_raise_application_error(line)
                        if rae_info:
                            last_handler["raise_application_error"].update(rae_info)
                            logger.debug("Parsed RAISE_APPLICATION_ERROR: %s", rae_info)
                
                # Add regular SQL statements to current block
                elif block_stack and line and not line.startswith("--"):
                    # Add to the current block's sqls
                    block_stack[-1]["sqls"].append(line)
        
        # # Update self.main_section_lines with the parsed blocks
        # self.main_section_lines = blocks
        
        logger.debug("BEGIN block parsing complete: updated main_section_lines with %d blocks", len(self.main_section_lines))
    
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
                
                return {
                    "exception_name": exception_name
                }
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
                    params = line[start_paren + 1:end_paren]
                    
                    # Split by comma, but be careful with quoted strings
                    parts = self._split_params_safely(params)
                    
                    if len(parts) >= 2:
                        handler_code = parts[0].strip()
                        handler_string = parts[1].strip()
                        
                        # Remove quotes if present
                        if handler_string.startswith("'") and handler_string.endswith("'"):
                            handler_string = handler_string[1:-1]
                        
                        return {
                            "handler_code": handler_code,
                            "handler_string": handler_string
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
            elif char == ',' and not in_quotes:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts

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
        }

        # # Step 5: Add additional metadata to the result
        # # Include structured lines for clients that need them
        # result["structured_lines"] = self.structured_lines

        # Add conversion statistics
        result["conversion_stats"] = {
            "declaration_count": len(self.variables)
            + len(self.constants)
            + len(self.exceptions),
            "main_block_count": len(self.main_section_lines),
            "comment_count": len(self.sql_comments),
        }

        # Include parse timestamp
        result["metadata"] = {
            "parse_timestamp": self._get_timestamp(),
            "parser_version": "1.0",  # Increment when making significant parser changes
        }

        # Log detailed statistics for troubleshooting
        logger.info(
            "JSON conversion complete: %d vars, %d consts, %d excs, %d main_blocks, %d comments",
            len(self.variables),
            len(self.constants),
            len(self.exceptions),
            len(self.main_section_lines),
            len(self.sql_comments),
        )
        return result

    def _get_timestamp(self):
        """Get current timestamp in ISO format for metadata"""
        from datetime import datetime

        return datetime.now().isoformat()


def ensure_dir(directory: str) -> None:
    """Ensure that the specified directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.debug(f"Created directory: {directory}")


def process_files(
    source_dir: str,
    target_dir: str,
    file_pattern: str,
    output_suffix: str,
    processor_func,
) -> None:
    """Process files from source_dir to target_dir using the provided processor function."""
    logger.info(f"Processing files from '{source_dir}' to '{target_dir}'")

    # Ensure directories exist
    ensure_dir(target_dir)

    # Get all matching files from the source directory
    try:
        files = [f for f in os.listdir(source_dir) if f.endswith(file_pattern)]
    except FileNotFoundError:
        logger.error(f"Source directory not found: {source_dir}")
        return

    logger.debug(f"Found {len(files)} files matching pattern: {files}")

    # Process each file
    for file_name in files:
        logger.debug(f"Processing file: {file_name}")
        try:
            # Extract trigger number from filename using regex
            match = re.search(r"trigger(\d+)", file_name)
            if not match:
                logger.debug(
                    f"Filename '{file_name}' does not match expected pattern; skipping"
                )
                continue

            trigger_num = match.group(1)
            logger.debug(f"Extracted trigger number: {trigger_num}")

            # Process the file
            src_path = os.path.join(source_dir, file_name)
            output_filename = f"trigger{trigger_num}{output_suffix}"
            out_path = os.path.join(target_dir, output_filename)

            # Run the processor function
            processor_func(src_path, out_path, trigger_num)

            logger.info(f"Created {output_filename}")
        except Exception as exc:
            logger.error(f"Failed to process {file_name}: {exc}", exc_info=True)


def sql_to_json_processor(src_path: str, out_path: str, _trigger_num: str) -> None:
    """Process a SQL file to JSON analysis."""
    # Read the SQL file content
    with open(src_path, "r", encoding="utf-8") as f:
        sql_content: str = f.read()
    logger.debug(f"Read {len(sql_content)} characters from {src_path}")

    # Analyze the SQL content
    analyzer = OracleTriggerAnalyzer(sql_content)
    logger.debug("Generating JSON analysis...")
    json_content: Dict[str, Any] = analyzer.to_json()
    logger.debug(f"Generated JSON with keys: {list(json_content.keys())}")

    # Write to JSON file
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2)
    logger.debug(f"Wrote analysis JSON to {out_path}")


def read_oracle_triggers_to_json() -> None:
    """Convert all Oracle trigger SQL files into analysis JSON files."""
    process_files(
        source_dir="files/oracle",
        target_dir="files/format_json",
        file_pattern=".sql",
        output_suffix="_analysis.json",
        processor_func=sql_to_json_processor,
    )


if __name__ == "__main__":
    # Set up logging for the main script
    main_logger, log_path = setup_logging()
    logger.info(
        f"Starting batch conversion: SQL -> JSON -> SQL (Logging to {log_path})"
    )

    read_oracle_triggers_to_json()
    logger.info("JSON conversion complete!")
