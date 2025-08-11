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
        logger.debug(
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
            "Processing main section from lines %d",
            self.main_section
        )

        logger.debug(
            "Main section processing complete: %d lines extracted",
            len(self.main_section_lines),
        )
        # Step 3: Parse BEGIN blocks from the main section
        logger.debug("Parsing BEGIN blocks for JSON conversion")
        self._parse_begin_end()
        self._parse_case_when()
        self._parse_for_loop()
        self._parse_if_else()
        self._parse_sql_statements()
        self._parse_assignment_statement()

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
                if isinstance(item, dict) and "line" in item and "line_no" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()
                    
                    # Check for FOR loop start
                    if line_upper.startswith("FOR ") and " IN " in line_upper:
                        logger.debug("Found FOR loop at line %d in %s", item["line_no"], parent_context)
                        for_loop_result = self._parse_for_loop_structure(self._find_line_index(item["line_no"]))
                        if for_loop_result:
                            for_loop_block, end_idx = for_loop_result
                            # Replace the line_info with the parsed for_loop_block
                            statements_list[i] = for_loop_block
                            logger.debug("Parsed complete FOR loop structure in %s", parent_context)
                            # Remove any subsequent line_info objects that are part of the FOR loop
                            # (they will be included in the for_loop_block)
                            j = i + 1
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if isinstance(next_item, dict) and "line_no" in next_item:
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
                            process_for_loops_in_list(item["begin_end_statements"], f"{parent_context}.begin_end_statements")
                        
                        # Process FOR loops in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_for_loops_in_list(handler["exception_statements"], f"{parent_context}.exception_statements")
                    
                    elif item["type"] == "case_when":
                        # Process FOR loops in when_clauses (then_statements and else_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "when_value" in clause and "then_statements" in clause:
                                    process_for_loops_in_list(clause["then_statements"], f"{parent_context}.then_statements")
                                elif "else_statements" in clause:
                                    process_for_loops_in_list(clause["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "if_else":
                        # Process FOR loops in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_for_loops_in_list(item["then_statements"], f"{parent_context}.then_statements")
                        
                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_for_loops_in_list(elsif_block["then_statements"], f"{parent_context}.else_if.then_statements")
                        
                        if "else_statements" in item:
                            process_for_loops_in_list(item["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "for_loop":
                        # Process nested FOR loops in loop_statements
                        if "loop_statements" in item:
                            process_for_loops_in_list(item["loop_statements"], f"{parent_context}.loop_statements")
                
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
            
        logger.debug("Parsing FOR loop structure starting at line %d: %s", start_line_info["line_no"], start_line[:50])
        
        # Extract loop variable and cursor query
        loop_parts = self._parse_for_loop_header(start_line)
        if not loop_parts:
            logger.warning("Failed to parse FOR loop header: %s", start_line)
            return None
            
        loop_variable = loop_parts["loop_variable"]
        cursor_query = loop_parts["cursor_query"]
        
        # Handle multi-line FOR loops where the cursor query continues on subsequent lines
        if not cursor_query or cursor_query.strip() == "" or cursor_query.strip() == "(":
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
            logger.warning("Could not find END LOOP for FOR loop starting at line %d", start_line_info["line_no"])
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
            "loop_statements": loop_statements
        }
        
        logger.debug("Successfully parsed FOR loop: %s IN (%s)", loop_variable, cursor_query[:30])
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
        
        return {
            "loop_variable": loop_variable,
            "cursor_query": cursor_query
        }

    def _parse_if_else(self):
        """
        Parse IF ELSE statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        
        This method recursively processes all statement lists (begin_end_statements,
        exception_statements, then_statements, else_statements, etc.) to find and
        parse IF-ELSE blocks, including nested blocks.
        
        The parsed blocks are structured as:
        {
            "type": "if_else",
            "condition": "...",
            "then_statements": [...],
            "else_if": [
                {
                    "condition": "...",
                    "then_statements": [...]
                },
                ...
            ],
            "else_statements": [...]
        }
        """
        logger.debug("Starting IF ELSE parsing")
        
        def process_if_else_in_list(statements_list, parent_context=""):
            """Recursively process IF-ELSE statements in a list of statements"""
            if not statements_list:
                return
            
            i = 0
            while i < len(statements_list):
                item = statements_list[i]
                
                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item and "line_no" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()
                    
                    # Check for IF statement start
                    if line_upper.startswith("IF ") and not line_upper.endswith("END IF;"):
                        logger.debug("Found IF statement at line %d in %s", item["line_no"], parent_context)
                        if_else_result = self._parse_if_else_structure(self._find_line_index(item["line_no"]))
                        if if_else_result:
                            if_else_block, end_idx = if_else_result
                            # Replace the line_info with the parsed if_else_block
                            statements_list[i] = if_else_block
                            logger.debug("Parsed complete IF-ELSE structure in %s", parent_context)
                            # Remove any subsequent line_info objects that are part of the IF-ELSE block
                            # (they will be included in the if_else_block)
                            j = i + 1
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if isinstance(next_item, dict) and "line_no" in next_item:
                                    if next_item["line_no"] > end_idx:
                                        break
                                    statements_list.pop(j)
                                else:
                                    j += 1
                            continue
                
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process IF-ELSE statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_if_else_in_list(item["begin_end_statements"], f"{parent_context}.begin_end_statements")
                        
                        # Process IF-ELSE statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_if_else_in_list(handler["exception_statements"], f"{parent_context}.exception_statements")
                    
                    elif item["type"] == "case_when":
                        # Process IF-ELSE statements in when_clauses (then_statements and else_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "when_value" in clause and "then_statements" in clause:
                                    process_if_else_in_list(clause["then_statements"], f"{parent_context}.then_statements")
                                elif "else_statements" in clause:
                                    process_if_else_in_list(clause["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "if_else":
                        # Process nested IF-ELSE statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_if_else_in_list(item["then_statements"], f"{parent_context}.then_statements")
                        
                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_if_else_in_list(elsif_block["then_statements"], f"{parent_context}.else_if.then_statements")
                        
                        if "else_statements" in item:
                            process_if_else_in_list(item["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "for_loop":
                        # Process IF-ELSE statements in loop_statements
                        if "loop_statements" in item:
                            process_if_else_in_list(item["loop_statements"], f"{parent_context}.loop_statements")
                
                i += 1
        
        # Process the main_section_lines
        process_if_else_in_list(self.main_section_lines, "main_section_lines")
        
        logger.debug("IF-ELSE parsing complete")
    
    def _parse_if_else_structure(self, start_idx):
        """
        Parse a complete IF-ELSE structure starting from the given index.
        Uses a stack-based approach to handle nested IF statements.
        
        Args:
            start_idx (int): Index in structured_lines where the IF statement starts
            
        Returns:
            tuple: (if_else_block, end_line_index) or None if parsing fails
        """
        if start_idx < 0 or start_idx >= len(self.structured_lines):
            return None
            
        start_line_info = self.structured_lines[start_idx]
        start_line = start_line_info["line"].strip()
        start_line_upper = start_line.upper()
        
        # Validate that this is an IF statement start
        if not start_line_upper.startswith("IF "):
            return None
            
        logger.debug("Parsing IF-ELSE structure starting at line %d: %s", start_line_info["line_no"], start_line[:50])
        
        # Extract condition (between IF and THEN)
        condition_text = ""
        if " THEN" in start_line_upper:
            condition_text = start_line[3:start_line_upper.find(" THEN")].strip()
        else:
            # Multi-line condition, try to find the THEN keyword in subsequent lines
            j = start_idx + 1
            condition_part = start_line[3:].strip()  # Skip "IF "
            condition_lines = [condition_part]
            
            while j < len(self.structured_lines):
                next_line = self.structured_lines[j]["line"].strip()
                next_line_upper = next_line.upper()
                
                if " THEN" in next_line_upper:
                    then_pos = next_line_upper.find(" THEN")
                    condition_lines.append(next_line[:then_pos].strip())
                    break
                else:
                    condition_lines.append(next_line)
                j += 1
                
            condition_text = " ".join(condition_lines)
        
        if not condition_text:
            logger.warning("Failed to extract condition from IF statement: %s", start_line)
            return None
            
        # Initialize IF-ELSE block structure
        if_else_block = {
            "type": "if_else",
            "condition": condition_text,
            "then_statements": [],
            "else_if": [],
            "else_statements": []
        }
        
        # Find the matching END IF; using a stack to handle nested IF statements
        stack = [("IF", start_line_info["indent"])]
        current_section = "then_statements"  # Current section being processed: 'then_statements', 'elsif', 'else'
        current_stmt_list = if_else_block["then_statements"]
        current_elsif_block = None
        end_idx = -1
        i = start_idx + 1
        
        while i < len(self.structured_lines) and stack:
            line_info = self.structured_lines[i]
            line = line_info["line"].strip()
            line_upper = line.upper()
            indent = line_info["indent"]
            
            # Skip the initial THEN if it's on a separate line
            if line_upper == "THEN" and i == start_idx + 1:
                i += 1
                continue
                
            # Check for nested IF statements
            if line_upper.startswith("IF "):
                # Push to stack to track nested IF
                stack.append(("IF", indent))
                
                # If we're inside an active section, add this line to that section
                if current_section == "then_statements":
                    if_else_block["then_statements"].append(line_info)
                elif current_section == "elsif" and current_elsif_block is not None:
                    current_elsif_block["then_statements"].append(line_info)
                elif current_section == "else":
                    if_else_block["else_statements"].append(line_info)
            
            # Check for ELSIF (at the same indentation level as the original IF)
            elif line_upper.startswith("ELSIF ") and indent == stack[0][1] and len(stack) == 1:
                current_section = "elsif"
                
                # Extract the ELSIF condition
                elsif_condition = ""
                if " THEN" in line_upper:
                    elsif_condition = line[6:line_upper.find(" THEN")].strip()
                else:
                    # Multi-line ELSIF condition
                    j = i + 1
                    elsif_part = line[6:].strip()  # Skip "ELSIF "
                    elsif_lines = [elsif_part]
                    
                    while j < len(self.structured_lines):
                        next_line = self.structured_lines[j]["line"].strip()
                        next_line_upper = next_line.upper()
                        
                        if " THEN" in next_line_upper:
                            then_pos = next_line_upper.find(" THEN")
                            elsif_lines.append(next_line[:then_pos].strip())
                            break
                        else:
                            elsif_lines.append(next_line)
                        j += 1
                        
                    elsif_condition = " ".join(elsif_lines)
                
                # Create a new ELSIF block
                current_elsif_block = {
                    "condition": elsif_condition,
                    "then_statements": []
                }
                if_else_block["else_if"].append(current_elsif_block)
                current_stmt_list = current_elsif_block["then_statements"]
            
            # Check for ELSE (at the same indentation level as the original IF)
            elif line_upper == "ELSE" and indent == stack[0][1] and len(stack) == 1:
                current_section = "else"
                current_stmt_list = if_else_block["else_statements"]
            
            # Check for END IF; (matching the current IF level)
            elif line_upper == "END IF;" or line_upper == "END IF":
                # Pop from the stack
                if stack and stack[-1][0] == "IF":
                    stack.pop()
                    
                    # If this was the outermost IF, we're done
                    if not stack:
                        end_idx = i
                        break
                    
                # Add this END IF to the current section if we're still inside a nested IF
                if stack:  # Still inside a nested IF
                    if current_section == "then_statements":
                        if_else_block["then_statements"].append(line_info)
                    elif current_section == "elsif" and current_elsif_block is not None:
                        current_elsif_block["then_statements"].append(line_info)
                    elif current_section == "else":
                        if_else_block["else_statements"].append(line_info)
            
            # Regular line - add to the current section
            else:
                if stack:  # Only add if we're inside an IF block
                    if current_section == "then_statements":
                        if_else_block["then_statements"].append(line_info)
                    elif current_section == "elsif" and current_elsif_block is not None:
                        current_elsif_block["then_statements"].append(line_info)
                    elif current_section == "else":
                        if_else_block["else_statements"].append(line_info)
            
            i += 1
        
        # Check if we found a complete IF-ELSE structure
        if end_idx == -1:
            logger.warning("Could not find matching END IF; for IF statement at line %d", start_line_info["line_no"])
            return None
        
        # Recursively process nested structures in the IF-ELSE blocks
        self._process_nested_if_else_blocks(if_else_block)
        
        logger.debug("Successfully parsed IF-ELSE structure from line %d to %d", 
                   start_line_info["line_no"], self.structured_lines[end_idx]["line_no"])
        
        return if_else_block, self.structured_lines[end_idx]["line_no"]
    
    def _process_nested_if_else_blocks(self, if_else_block):
        """
        Process nested structures within an IF-ELSE block recursively.
        This converts any nested IF-ELSE blocks from line_info objects to structured blocks.
        
        Args:
            if_else_block (dict): The IF-ELSE block structure to process
        """
        # Process then_statements section
        if "then_statements" in if_else_block:
            i = 0
            while i < len(if_else_block["then_statements"]):
                item = if_else_block["then_statements"][i]
                
                if isinstance(item, dict) and "line" in item and "line_no" in item:
                    line = item["line"].strip()
                    if line.upper().startswith("IF "):
                        # Found a nested IF statement
                        nested_if_idx = self._find_line_index(item["line_no"])
                        if nested_if_idx >= 0:
                            nested_result = self._parse_if_else_structure(nested_if_idx)
                            if nested_result:
                                nested_block, end_idx = nested_result
                                # Replace with parsed nested block
                                if_else_block["then_statements"][i] = nested_block
                                
                                # Remove subsequent statements that are part of this nested IF
                                j = i + 1
                                while j < len(if_else_block["then_statements"]):
                                    next_item = if_else_block["then_statements"][j]
                                    if isinstance(next_item, dict) and "line_no" in next_item:
                                        if next_item["line_no"] <= end_idx:
                                            if_else_block["then_statements"].pop(j)
                                        else:
                                            break
                                    else:
                                        j += 1
                i += 1
        
        # Process each ELSIF block
        if "else_if" in if_else_block:
            for elsif_block in if_else_block["else_if"]:
                if "then_statements" in elsif_block:
                    i = 0
                    while i < len(elsif_block["then_statements"]):
                        item = elsif_block["then_statements"][i]
                        
                        if isinstance(item, dict) and "line" in item and "line_no" in item:
                            line = item["line"].strip()
                            if line.upper().startswith("IF "):
                                # Found a nested IF statement
                                nested_if_idx = self._find_line_index(item["line_no"])
                                if nested_if_idx >= 0:
                                    nested_result = self._parse_if_else_structure(nested_if_idx)
                                    if nested_result:
                                        nested_block, end_idx = nested_result
                                        # Replace with parsed nested block
                                        elsif_block["then_statements"][i] = nested_block
                                        
                                        # Remove subsequent statements that are part of this nested IF
                                        j = i + 1
                                        while j < len(elsif_block["then_statements"]):
                                            next_item = elsif_block["then_statements"][j]
                                            if isinstance(next_item, dict) and "line_no" in next_item:
                                                if next_item["line_no"] <= end_idx:
                                                    elsif_block["then_statements"].pop(j)
                                                else:
                                                    break
                                            else:
                                                j += 1
                        i += 1
        
        # Process else_statements section
        if "else_statements" in if_else_block:
            i = 0
            while i < len(if_else_block["else_statements"]):
                item = if_else_block["else_statements"][i]
                
                if isinstance(item, dict) and "line" in item and "line_no" in item:
                    line = item["line"].strip()
                    if line.upper().startswith("IF "):
                        # Found a nested IF statement
                        nested_if_idx = self._find_line_index(item["line_no"])
                        if nested_if_idx >= 0:
                            nested_result = self._parse_if_else_structure(nested_if_idx)
                            if nested_result:
                                nested_block, end_idx = nested_result
                                # Replace with parsed nested block
                                if_else_block["else_statements"][i] = nested_block
                                
                                # Remove subsequent statements that are part of this nested IF
                                j = i + 1
                                while j < len(if_else_block["else_statements"]):
                                    next_item = if_else_block["else_statements"][j]
                                    if isinstance(next_item, dict) and "line_no" in next_item:
                                        if next_item["line_no"] <= end_idx:
                                            if_else_block["else_statements"].pop(j)
                                        else:
                                            break
                                    else:
                                        j += 1
                i += 1
        
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
                if isinstance(item, dict) and "line" in item and "line_no" in item:
                    line = item["line"].strip()
                    
                    # Check if this line contains an assignment operator (:=)
                    if " := " in line:
                        logger.debug("Found assignment statement at line %d in %s: %s", item["line_no"], parent_context, line[:30])
                        
                        # Check if this assignment ends with semicolon on the same line
                        if item["is_end_semicolon"]:
                            # Single line assignment statement
                            assignment_parts = self._parse_assignment_line(line)
                            if assignment_parts:
                                assignment_statement = {
                                    "variable": assignment_parts["variable"],
                                    "value": assignment_parts["value"],
                                    "type": "assignment_statement"
                                }
                                statements_list[i] = assignment_statement
                                logger.debug("Parsed single-line assignment statement: %s", assignment_parts["variable"])
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
                            assignment_parts = self._parse_assignment_line(complete_assignment)
                            
                            if assignment_parts:
                                assignment_statement = {
                                    "variable": assignment_parts["variable"],
                                    "value": assignment_parts["value"],
                                    "type": "assignment_statement"
                                }
                                
                                # Replace the first line with the complete statement
                                statements_list[i] = assignment_statement
                                
                                # Remove the subsequent lines that were part of this assignment statement
                                for k in range(j, i, -1):
                                    if k < len(statements_list):
                                        statements_list.pop(k)
                                
                                logger.debug("Parsed multi-line assignment statement: %s", assignment_parts["variable"])
                                continue
                
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process assignment statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_assignment_statement_in_list(item["begin_end_statements"], f"{parent_context}.begin_end_statements")
                        
                        # Process assignment statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_assignment_statement_in_list(handler["exception_statements"], f"{parent_context}.exception_statements")
                    
                    elif item["type"] == "case_when":
                        # Process assignment statements in when_clauses (then_statements and else_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "when_value" in clause and "then_statements" in clause:
                                    process_assignment_statement_in_list(clause["then_statements"], f"{parent_context}.then_statements")
                                elif "else_statements" in clause:
                                    process_assignment_statement_in_list(clause["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "if_else":
                        # Process assignment statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_assignment_statement_in_list(item["then_statements"], f"{parent_context}.then_statements")
                        
                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_assignment_statement_in_list(elsif_block["then_statements"], f"{parent_context}.else_if.then_statements")
                        
                        if "else_statements" in item:
                            process_assignment_statement_in_list(item["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "for_loop":
                        # Process assignment statements in loop_statements
                        if "loop_statements" in item:
                            process_assignment_statement_in_list(item["loop_statements"], f"{parent_context}.loop_statements")
                
                i += 1
        
        # Process the main_section_lines
        process_assignment_statement_in_list(self.main_section_lines, "main_section_lines")
        
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
                    
                    return {
                        "variable": variable,
                        "value": value
                    }
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
            "RAISE": "raise_statement"
        }
        
        def process_sql_statements_in_list(statements_list, parent_context=""):
            """Recursively process SQL statements in a list of statements"""
            if not statements_list:
                return
                
            i = 0
            while i < len(statements_list):
                item = statements_list[i]
                
                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item and "line_no" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()
                    
                    # Check if this line starts with a SQL statement type
                    sql_type = None
                    for stmt_keyword, stmt_type in STMT_TYPE_MAP.items():
                        if line_upper.startswith(stmt_keyword):
                            sql_type = stmt_type
                            break
                    
                    if sql_type:
                        logger.debug("Found SQL statement at line %d in %s: %s", item["line_no"], parent_context, line_upper[:20])
                        
                        # Check if this statement ends with semicolon on the same line
                        if item["is_end_semicolon"]:
                            # Single line SQL statement
                            sql_statement = {
                                "sql": line,
                                "type": sql_type
                            }
                            statements_list[i] = sql_statement
                            logger.debug("Parsed single-line SQL statement: %s", sql_type)
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
                            sql_statement = {
                                "sql": complete_sql,
                                "type": sql_type
                            }
                            
                            # Replace the first line with the complete statement
                            statements_list[i] = sql_statement
                            
                            # Remove the subsequent lines that were part of this SQL statement
                            for k in range(j, i, -1):
                                if k < len(statements_list):
                                    statements_list.pop(k)
                            
                            logger.debug("Parsed multi-line SQL statement: %s", sql_type)
                            continue
                
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                elif isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process SQL statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_sql_statements_in_list(item["begin_end_statements"], f"{parent_context}.begin_end_statements")
                        
                        # Process SQL statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_sql_statements_in_list(handler["exception_statements"], f"{parent_context}.exception_statements")
                    
                    elif item["type"] == "case_when":
                        # Process SQL statements in when_clauses (then_statements and else_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "when_value" in clause and "then_statements" in clause:
                                    process_sql_statements_in_list(clause["then_statements"], f"{parent_context}.then_statements")
                                elif "else_statements" in clause:
                                    process_sql_statements_in_list(clause["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "if_else":
                        # Process SQL statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_sql_statements_in_list(item["then_statements"], f"{parent_context}.then_statements")
                        
                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_sql_statements_in_list(elsif_block["then_statements"], f"{parent_context}.else_if.then_statements")
                        
                        if "else_statements" in item:
                            process_sql_statements_in_list(item["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "for_loop":
                        # Process SQL statements in loop_statements
                        if "loop_statements" in item:
                            process_sql_statements_in_list(item["loop_statements"], f"{parent_context}.loop_statements")
                
                i += 1
        
        # Process the main_section_lines
        process_sql_statements_in_list(self.main_section_lines, "main_section_lines")
        
        logger.debug("SQL statements parsing complete")
    
    def _parse_case_when(self):
        """
        Parse CASE WHEN statements from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        logger.debug("Starting CASE WHEN parsing")
        
        # Process existing main_section_lines to find and parse CASE statements
        # in various contexts: begin_end_statements, exception_statements, then_statements, else_statements
        
        def process_case_statements_in_list(statements_list, parent_context=""):
            """Recursively process CASE statements in a list of statements"""
            if not statements_list:
                return
                
            i = 0
            while i < len(statements_list):
                item = statements_list[i]
                
                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item and "line_no" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()
                    
                    # Check for CASE statement start
                    if line_upper == "CASE" or line_upper.startswith("CASE "):
                        logger.debug("Found CASE statement at line %d in %s", item["line_no"], parent_context)
                        case_result = self._parse_case_statement(self._find_line_index(item["line_no"]))
                        if case_result:
                            case_block, end_idx = case_result
                            # Replace the line_info with the parsed case_block
                            statements_list[i] = case_block
                            logger.debug("Parsed complete CASE statement structure in %s", parent_context)
                            # Remove any subsequent line_info objects that are part of the CASE statement
                            # (they will be included in the case_block)
                            j = i + 1
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if isinstance(next_item, dict) and "line_no" in next_item:
                                    if next_item["line_no"] > end_idx:
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
                            process_case_statements_in_list(item["begin_end_statements"], f"{parent_context}.begin_end_statements")
                        
                        # Process CASE statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_case_statements_in_list(handler["exception_statements"], f"{parent_context}.exception_statements")
                    
                    elif item["type"] == "case_when":
                        # Process CASE statements in when_clauses (then_statements and else_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "when_value" in clause and "then_statements" in clause:
                                    process_case_statements_in_list(clause["then_statements"], f"{parent_context}.then_statements")
                                elif "else_statements" in clause:
                                    process_case_statements_in_list(clause["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "if_else":
                        # Process CASE statements in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_case_statements_in_list(item["then_statements"], f"{parent_context}.then_statements")
                        
                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_case_statements_in_list(elsif_block["then_statements"], f"{parent_context}.else_if.then_statements")
                        
                        if "else_statements" in item:
                            process_case_statements_in_list(item["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "for_loop":
                        # Process CASE statements in loop_statements
                        if "loop_statements" in item:
                            process_case_statements_in_list(item["loop_statements"], f"{parent_context}.loop_statements")
                
                i += 1
        
        # Process the main_section_lines
        process_case_statements_in_list(self.main_section_lines, "main_section_lines")
        
        logger.debug("CASE WHEN parsing complete")
    
    def _find_line_index(self, line_no):
        """Find the index in structured_lines for a given line number"""
        for i, line_info in enumerate(self.structured_lines):
            if line_info["line_no"] == line_no:
                return i
        return -1
        
    def _parse_begin_end(self):
        """
        Parse top-level BEGIN blocks from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Updates self.main_section_lines with parsed blocks.
        """
        logger.debug("Starting BEGIN block parsing")

        def process_begin_end_in_list(statements_list, parent_context=""):
            """Recursively process BEGIN blocks in a list of statements"""
            if not statements_list:
                return
                
            i = 0
            while i < len(statements_list):
                item = statements_list[i]
                
                # Handle line_info objects (from structured_lines)
                if isinstance(item, dict) and "line" in item and "line_no" in item:
                    line = item["line"].strip()
                    line_upper = line.upper()
                    
                    # Check for BEGIN block start
                    if line_upper == "BEGIN":
                        logger.debug("Found BEGIN block at line %d in %s", item["line_no"], parent_context)
                        # Parse the BEGIN block structure
                        begin_end_result = self._parse_begin_end_structure(self._find_line_index(item["line_no"]))
                        if begin_end_result:
                            begin_end_block, end_idx = begin_end_result
                            # Replace the line_info with the parsed begin_end_block
                            statements_list[i] = begin_end_block
                            logger.debug("Parsed complete BEGIN block structure in %s", parent_context)
                            # Remove any subsequent line_info objects that are part of the BEGIN block
                            # (they will be included in the begin_end_block)
                            j = i + 1
                            while j < len(statements_list):
                                next_item = statements_list[j]
                                if isinstance(next_item, dict) and "line_no" in next_item:
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
                            process_begin_end_in_list(item["begin_end_statements"], f"{parent_context}.begin_end_statements")
                        
                        # Process BEGIN blocks in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_begin_end_in_list(handler["exception_statements"], f"{parent_context}.exception_statements")
                    
                    elif item["type"] == "case_when":
                        # Process BEGIN blocks in when_clauses (then_statements and else_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "when_value" in clause and "then_statements" in clause:
                                    process_begin_end_in_list(clause["then_statements"], f"{parent_context}.then_statements")
                                elif "else_statements" in clause:
                                    process_begin_end_in_list(clause["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "if_else":
                        # Process BEGIN blocks in then_statements, else_if, and else_statements
                        if "then_statements" in item:
                            process_begin_end_in_list(item["then_statements"], f"{parent_context}.then_statements")
                        
                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if "then_statements" in elsif_block:
                                    process_begin_end_in_list(elsif_block["then_statements"], f"{parent_context}.else_if.then_statements")
                        
                        if "else_statements" in item:
                            process_begin_end_in_list(item["else_statements"], f"{parent_context}.else_statements")
                    
                    elif item["type"] == "for_loop":
                        # Process BEGIN blocks in loop_statements
                        if "loop_statements" in item:
                            process_begin_end_in_list(item["loop_statements"], f"{parent_context}.loop_statements")
                
                i += 1

        current_block = None
        block_stack = []
        self.main_section_lines = []
        
        i = 0
        while i < len(self.structured_lines):
            line_info = self.structured_lines[i]
            
            if self.main_section <= line_info["line_no"]:
                line = line_info["line"].strip()
                line_upper = line.upper()
                
                # Check for BEGIN block start
                if line_upper == "BEGIN":
                    # Start a new block
                    current_block = {
                        "begin_end_statements": [],
                        "type": "begin_end",
                        "exception_handlers": []
                    }
                    block_stack.append(current_block)
                    logger.debug("Found BEGIN block at line %d", line_info["line_no"])
                
                # Check for END block
                elif line_upper == "END;":
                    if block_stack:
                        # Complete the current block
                        completed_block = block_stack.pop()
                        
                        # Process the block's begin_end_statements to identify case statements
                        self._process_block_sqls(completed_block)
                        
                        # If this is a top-level block, add to results
                        if not block_stack:
                            self.main_section_lines.append(completed_block)
                            logger.debug("Completed top-level BEGIN block")
                        else:
                            # This is a nested block, add to parent's begin_end_statements
                            block_stack[-1]["begin_end_statements"].append(completed_block)
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
                            # Initialize exception_statements array for the exception handler
                            exception_handler["exception_statements"] = []
                            block_stack[-1]["exception_handlers"].append(exception_handler)
                            logger.debug("Parsed exception handler: %s", exception_handler["exception_name"])
                
                # Check for RAISE statements in exception handlers
                elif line_upper.startswith("RAISE") and block_stack:
                    if block_stack[-1]["exception_handlers"]:
                        # Add RAISE statement to the last exception handler's exception_statements
                        last_handler = block_stack[-1]["exception_handlers"][-1]
                        if "exception_statements" not in last_handler:
                            last_handler["exception_statements"] = []
                        
                        # Check if it's RAISE_APPLICATION_ERROR
                        if "RAISE_APPLICATION_ERROR" in line_upper:
                            rae_info = self._parse_raise_application_error(line)
                            if rae_info:
                                # Create function_calling structure for RAISE_APPLICATION_ERROR
                                function_call = {
                                    "type": "function_calling",
                                    "function_name": "raise_application_error",
                                    "parameter": {
                                        "handler_code": rae_info["handler_code"],
                                        "handler_string": rae_info["handler_string"]
                                    }
                                }
                                last_handler["exception_statements"].append(function_call)
                                logger.debug("Added RAISE_APPLICATION_ERROR function call: %s", rae_info)
                        else:
                            # Regular RAISE statement
                            raise_statement = {
                                "sql": line,
                                "type": "raise_statement"
                            }
                            last_handler["exception_statements"].append(raise_statement)
                            logger.debug("Added RAISE statement: %s", line)
                
                # Add regular SQL statements to current block or exception handlers
                elif block_stack and line and not line.startswith("--"):
                    # Check if we're in an exception handler
                    if block_stack[-1]["exception_handlers"]:
                        last_handler = block_stack[-1]["exception_handlers"][-1]
                        if "exception_statements" not in last_handler:
                            last_handler["exception_statements"] = []
                        
                        # Add SQL statement to exception handler
                        sql_statement = {
                            "sql": line,
                            "type": "sql_statement"
                        }
                        last_handler["exception_statements"].append(sql_statement)
                        logger.debug("Added SQL statement to exception handler: %s", line)
                    else:
                        # Add to the current block's begin_end_statements
                        block_stack[-1]["begin_end_statements"].append(line_info)
            
            i += 1
        
        # Process the main_section_lines recursively
        process_begin_end_in_list(self.main_section_lines, "main_section_lines")
        
        logger.debug("BEGIN block parsing complete: updated main_section_lines with %d blocks", len(self.main_section_lines))
        
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
            
        logger.debug("Parsing BEGIN-END block starting at line %d", start_line_info["line_no"])
        
        # Initialize the block structure
        begin_end_block = {
            "type": "begin_end",
            "begin_end_statements": [],
            "exception_handlers": []
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
                    "exception_handlers": []
                }
                current_block["begin_end_statements"].append(nested_block)
                block_stack.append(nested_block)
                current_block = nested_block
                logger.debug("Found nested BEGIN block at line %d", line_info["line_no"])
            
            # Check for END
            elif line_upper == "END;":
                if len(block_stack) > 1:
                    # End of nested block
                    block_stack.pop()
                    current_block = block_stack[-1]
                    logger.debug("Ended nested BEGIN block at line %d", line_info["line_no"])
                else:
                    # End of main block
                    logger.debug("Ended main BEGIN block at line %d", line_info["line_no"])
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
                        logger.debug("Parsed exception handler: %s", exception_handler["exception_name"])
            
            # Add regular statements to current block
            elif line and not line.startswith("--"):
                if "exception_handlers" in current_block and current_block["exception_handlers"]:
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
        logger.warning("BEGIN block starting at line %d was not properly closed", start_line_info["line_no"])
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
            
        logger.debug("Processing block begin_end_statements for potential nested CASE statements")
        
        # No additional processing needed here as we now process CASE statements 
        # during initial parsing
    
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
            "when_clauses": []
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
        
        logger.debug("CASE statement - Type: %s, Expression: '%s'", 
                    "simple" if not case_statement["case_expression"] else "with expression",
                    case_statement["case_expression"])
        
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
                logger.debug("Found nested BEGIN block in CASE statement at line %d", line_info["line_no"])
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
                        
                        if collecting_then_statements and current_when_clause is not None:
                            # Add the complete nested block to the current clause
                            # Create a line_info object for the END; statement
                            end_line_info = {
                                "indent": indent,
                                "line": "END;",
                                "line_no": line_info["line_no"],
                                "is_end_semicolon": True
                            }
                            current_nested_block.append(end_line_info)
                            
                            if "when_value" in current_when_clause:
                                current_when_clause["then_statements"].extend(current_nested_block)
                            else:
                                current_when_clause["else_statements"].extend(current_nested_block)
                            
                            current_nested_block = []
            
            # Process WHEN clause - ensure it's at the same indentation level as CASE
            # or slightly more indented (common formatting style)
            elif line_upper.startswith("WHEN ") and " THEN" in line_upper and (indent == case_indent or indent == case_indent + 3):
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
                current_when_clause = {
                    "when_value": when_value,
                    "then_statements": []
                }
                case_statement["when_clauses"].append(current_when_clause)
                collecting_then_statements = True
                
            # Process ELSE clause - ensure it's at the same indentation level as WHEN clauses
            elif line_upper == "ELSE" and (indent == case_indent or indent == case_indent + 3):
                # Save any pending WHEN clause statements
                if collecting_then_statements and current_when_clause is not None:
                    if "when_value" in current_when_clause:
                        current_when_clause["then_statements"] = current_statements
                    current_statements = []
                
                # Create the ELSE clause
                logger.debug("Found ELSE clause at indent %d (case indent: %d)", indent, case_indent)
                current_when_clause = {
                    "else_statements": []
                }
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
            logger.debug("Could not find matching END CASE; for CASE statement at index %d", start_idx)
            return None
        
        # Process the statements in each clause to handle nested structures
        self._process_nested_structures_in_case(case_statement)
            
        # Add the full SQL text to the case_statement, preserving original indentation
        case_statement["sql"] = "\n".join(full_case_text)
        
        logger.debug("Completed CASE statement parsing: %d when clauses, end at index %d", 
                   len(case_statement["when_clauses"]), end_idx)
                   
        return case_statement, end_idx
        
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
                processed_statements = self._process_statements_for_nested_structures(statements)
                clause["then_statements"] = processed_statements
            elif "else_statements" in clause:
                # Process ELSE clause statements
                statements = clause["else_statements"]
                processed_statements = self._process_statements_for_nested_structures(statements)
                clause["else_statements"] = processed_statements
                
    def _process_statements_for_nested_structures(self, statements):
        """
        Process a list of statements to identify and parse any nested structures
        such as CASE statements or BEGIN blocks.
        
        Args:
            statements (list): List of statement line_info objects
            
        Returns:
            list: Processed list of statements with nested structures converted to proper format
        """
        processed = []
        i = 0
        
        while i < len(statements):
            stmt_info = statements[i]
            stmt = stmt_info["line"].strip()
            
            # Check for nested CASE statements
            if stmt.upper().startswith("CASE"):
                # Found potential nested CASE statement
                case_text = [stmt]
                end_idx = -1
                
                # Find the end of the nested CASE statement
                for j in range(i + 1, len(statements)):
                    case_text.append(statements[j]["line"])
                    if statements[j]["line"].strip().upper() == "END CASE;":
                        end_idx = j
                        break
                
                if end_idx != -1:
                    # Found a complete nested CASE statement
                    logger.debug("Found nested CASE statement in clause")
                    
                    # Create a nested case structure
                    nested_case = {
                        "type": "case_when",
                        "case_expression": "",
                        "when_clauses": [],
                        "sql": "\n".join(case_text)
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
                
                # Check for "line" field which contains individual SQL statements
                if "line" in item:
                    line_content = item["line"].strip()
                    if line_content and not line_content.startswith("--"):
                        rest_strings_list.append(item)
                
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
            "rest_strings" : self.rest_strings(),
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
        }

        # Include parse timestamp
        result["metadata"] = {
            "parse_timestamp": self._get_timestamp(),
            "parser_version": "1.0",  # Increment when making significant parser changes
        }

        # Log detailed statistics for troubleshooting
        logger.info(
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
