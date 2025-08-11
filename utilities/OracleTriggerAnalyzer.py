import re
from typing import Any, Dict, List, Tuple
from utilities.common import debug, logger


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
        logger.debug("Initializing OracleTriggerAnalyzer with %d characters of SQL", len(sql_content))
        self.sql_content: str = sql_content
        self.declare_section: str = ""
        self.main_section: str = ""
        self.variables: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []
        self.exceptions: List[Dict[str, Any]] = []
        self.sql_comments: List[str] = []
        self.rule_errors: List[Dict[str, Any]] = []
        self.structured_lines: List[Dict[str, Any]] = []
        
        # Step 1: Convert raw SQL content into structured lines
        logger.debug("Starting structured line conversion")
        self._convert_to_structured_lines()
        
        # Step 2: Parse SQL into declare and main sections
        logger.debug("Starting SQL section parsing")
        self._parse_sql()
        
        # Step 3: Validate formatting rules
        logger.debug("Starting rule validation")
        self.rule_errors = self._validate_rules()
        if self.rule_errors:
            logger.warning("Found %d rule violation(s)", len(self.rule_errors))

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
            content = line.lstrip()
            
            # Skip completely empty lines from structured representation
            if not content:
                empty_lines += 1
                continue
                
            # Check if line ends with semicolon
            is_end_semicolon = content.rstrip().endswith(';')
            if is_end_semicolon:
                semicolon_lines += 1
            
            self.structured_lines.append({
                "indent": indent_level,
                "line": content,
                "line_no": i,
                "is_end_semicolon": is_end_semicolon
            })
        
        logger.debug(
            "Structured lines conversion complete: %d total, %d with semicolons, %d empty lines skipped",
            len(self.structured_lines), 
            semicolon_lines,
            empty_lines
        )

    def _strip_inline_sql_comment(self, text: str) -> Tuple[str, str]:
        """
        Remove inline SQL comments (--) while preserving content within string literals.
        
        This function carefully parses the input text character by character to:
        1. Identify comments only outside of string literals
        2. Handle escaped quotes within strings (two single quotes in a row)
        3. Separate code from comments for further processing
        
        Args:
            text (str): The SQL text to process
            
        Returns:
            Tuple[str, str]: (code_without_comments, extracted_comment)
                - First element: The SQL code with comments removed
                - Second element: The extracted comment (if any, otherwise empty string)
        """
        # Optimization 1: Fast path for entire line being a comment
        if text.lstrip().startswith("--"):
            logger.debug("Fast path: entire line is a comment")
            return "", text.strip()
            
        # Optimization 2: Fast path when no comment markers exist
        if "--" not in text:
            return text.rstrip(), ""
        
        # Main processing for lines with potential inline comments
        in_string = False
        i = 0
        result_chars = []
        comment = ""
        
        # Process character by character to properly handle strings and comments
        while i < len(text):
            ch = text[i]
            
            # Toggle in_string when encountering quotes, handle escaped quotes
            if ch == "'":
                result_chars.append(ch)
                i += 1
                if in_string:
                    # Check for escaped quotes (two single quotes in a row)
                    if i < len(text) and text[i] == "'":
                        # This is an escaped quote, not the end of the string
                        result_chars.append("'")
                        i += 1
                        continue
                    # Real end of string
                    in_string = False
                else:
                    # Start of string
                    in_string = True
                continue
                
            # Detect comment start when not inside a string
            if not in_string and ch == '-' and i + 1 < len(text) and text[i + 1] == '-':
                comment = text[i:].strip()
                break  # Stop processing - rest of line is comment
                
            # Regular character, add to result
            result_chars.append(ch)
            i += 1
        
        code = "".join(result_chars).rstrip()
        
        # Debug only for non-trivial cases
        if comment and len(code) > 0:
            logger.debug("Split inline comment: code_len=%d, comment_len=%d", len(code), len(comment))
            
        return code, comment

    def _parse_sql(self) -> None:
        """
        Split SQL content into DECLARE and main (BEGIN...END) sections.
        
        This method:
        1. Rebuilds the full SQL from structured lines
        2. Identifies the DECLARE section (if present)
        3. Sets the main section with the BEGIN block
        4. Processes declarations into categories (variables, constants, exceptions)
        
        Pattern: DECLARE ... BEGIN ... END
        """
        # Step 1: Rebuild the SQL content from structured lines for regex processing
        rebuilt_sql = "\n".join(line_dict["line"] for line_dict in self.structured_lines)
        logger.debug("Rebuilt SQL from %d structured lines: %d characters", 
                     len(self.structured_lines), len(rebuilt_sql))
        
        # Step 2: Find the "declare" section (everything between "declare" and "begin")
        logger.debug("Searching for DECLARE and BEGIN sections")
        pattern = re.compile(r"declare(.*?)begin", re.DOTALL | re.IGNORECASE)
        match = pattern.search(rebuilt_sql)

        if match:
            # Step 3a: Found DECLARE section - split into declare and main parts
            # Store declare section without the "declare" keyword
            self.declare_section = match.group(1).strip()
            
            # Main section is everything from "begin" to the end
            begin_pos = match.end() - 5  # subtract 5 to keep the "begin" keyword
            self.main_section = rebuilt_sql[begin_pos:].strip()
            
            logger.debug("Found DECLARE section (%d chars) and main section (%d chars)",
                         len(self.declare_section), len(self.main_section))

            # Step 4: Parse the declarations into categories
            self._parse_declarations()
        else:
            # Step 3b: No DECLARE section found - treat everything as main section
            self.declare_section = ""
            self.main_section = rebuilt_sql.strip()
            logger.debug("No DECLARE section found; entire SQL content (%d chars) treated as main section", 
                        len(self.main_section))

    # -----------------------------
    # Grouping pipeline (ORDERED)
    # -----------------------------
    def _apply_grouping_pipeline(self, elements):
        """
        Apply the detection/grouping passes to SQL elements in a strict processing order.
        
        The pipeline works by transforming each element in sequence:
        1) Assignment statements  (:=)
        2) SQL statements (SELECT, INSERT, UPDATE, DELETE)
        3) RAISE statements
        
        The order is critical to ensure correct parsing of nested structures.
        Each step takes the output of the previous step as input.
        
        Args:
            elements: List of SQL elements (strings or structured line dictionaries)
            
        Returns:
            List of grouped and structured SQL elements
            
        NOTE: BEGIN/END nested blocks are handled separately by callers via 
        _extract_nested_blocks and _parse_begin_blocks before this pipeline is applied.
        """
        logger.debug("Starting grouping pipeline with %d elements", len(elements))
        
        for element in elements:
            print(element)
        # Step 1: Process assignments first (variable := value)
        logger.debug("Pipeline step 1: Processing assignment statements")
        grouped = self._group_assignment_statements(elements)
        
        # Step 2: Process SQL statements (DML/SELECT and RAISE combined)
        logger.debug("Pipeline step 2: Processing SQL and RAISE statements")
        grouped = self._group_sql_statements(grouped)
        
        # Count the different types of statements for debugging
        statement_types = {}
        for item in grouped:
            if isinstance(item, dict) and "type" in item:
                stmt_type = item["type"]
                statement_types[stmt_type] = statement_types.get(stmt_type, 0) + 1
        
        logger.debug("Grouping pipeline complete. Statement types found: %s", statement_types)
        return grouped

    # --- Rule validation ---
    def _validate_rules(self):
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
        errors: List[Dict[str, Any]] = []
        
        # Helper function to add errors in a consistent format
        def append_error(line_no: int, rule_text: str, solution_text: str):
            errors.append({
                "line_no": line_no,
                "rule": rule_text,
                "solution": solution_text,
            })
            logger.warning("Rule violation on line %d: %s", line_no, rule_text)

        # Initialize tracking variables
        in_block_comment = False
        in_raise_error = False
        raise_error_start_line = 0
        
        logger.debug("Validating %d structured lines for syntax rules", len(self.structured_lines))
        
        # Define validation rules with patterns and error messages
        validation_rules = [
            {
                "pattern": r"^\s*IF\b",
                "required": r"\bTHEN\b",
                "rule": "IF and THEN must be on the same line",
                "solution": "Place THEN on the same line as the IF condition, e.g., IF <condition> THEN"
            },
            {
                "pattern": r"^\s*ELSIF\b",
                "required": r"\bTHEN\b",
                "rule": "ELSIF and THEN must be on the same line",
                "solution": "Place THEN on the same line as the ELSIF condition, e.g., ELSIF <condition> THEN"
            },
            {
                "pattern": r"^\s*WHEN\b",
                "required": r"\bTHEN\b",
                "rule": "WHEN and THEN must be on the same line",
                "solution": "Place THEN on the same line as the WHEN condition, e.g., WHEN <condition> THEN"
            }
        ]
        
        # Process each line for validation
        for line_dict in self.structured_lines:
            line_no = line_dict["line_no"]
            original_line = line_dict["line"]
            
            # Step 1: Process block comments
            processed_segments = self._process_block_comments(original_line, in_block_comment)
            code_outside_blocks = "".join(processed_segments[0])
            in_block_comment = processed_segments[1]  # Update block comment state

            # Step 2: Strip inline comments outside of strings
            code, comment = self._strip_inline_sql_comment(code_outside_blocks)

            # Skip empty or pure comment lines
            if not code.strip() or comment.lstrip().startswith("--"):
                continue

            # Step 3: Apply standard validation rules
            for rule in validation_rules:
                if re.match(rule["pattern"], code, re.IGNORECASE):
                    if not re.search(rule["required"], code, re.IGNORECASE):
                        append_error(line_no, rule["rule"], rule["solution"])

            # Step 4: Special handling for RAISE_APPLICATION_ERROR
            self._validate_raise_application_error(
                code, line_dict, line_no, 
                in_raise_error, raise_error_start_line, 
                append_error
            )
            
            # Update raise_error tracking state
            if "RAISE_APPLICATION_ERROR" in code.upper():
                if not in_raise_error:
                    in_raise_error = True
                    raise_error_start_line = line_no
                    
                # Complete statement found
                if "(" in code and ")" in code and line_dict["is_end_semicolon"]:
                    in_raise_error = False
                # Missing semicolon
                elif ")" in code and not line_dict["is_end_semicolon"]:
                    in_raise_error = False
            # Multi-line RAISE_APPLICATION_ERROR detection
            elif in_raise_error and ")" in code:
                in_raise_error = False
                
        # Check for unclosed RAISE_APPLICATION_ERROR at end of file
        if in_raise_error:
            append_error(
                raise_error_start_line,
                "Incomplete RAISE_APPLICATION_ERROR statement",
                "RAISE_APPLICATION_ERROR must have all parameters on the same line and end with a semicolon",
            )

        logger.info("Rule validation complete: found %d violation(s)", len(errors))
        return errors
        
    def _process_block_comments(self, text, in_block_comment):
        """
        Process block comments (/* ... */) in a line of SQL code.
        
        Args:
            text (str): The line of SQL code to process
            in_block_comment (bool): Whether we're currently in a block comment
            
        Returns:
            Tuple[List[str], bool]: A tuple containing:
                - List of code segments outside block comments
                - Updated in_block_comment state
        """
        processed_segments = []
        s = text
        
        while s is not None:
            if not in_block_comment:
                start = s.find("/*")
                if start == -1:
                    processed_segments.append(s)
                    s = None
                else:
                    # add code before comment start
                    if start > 0:
                        processed_segments.append(s[:start])
                    s = s[start + 2 :]
                    in_block_comment = True
            else:
                end = s.find("*/")
                if end == -1:
                    # entire remainder is inside a block comment
                    s = None
                else:
                    s = s[end + 2 :]
                    in_block_comment = False
                    # continue scanning remainder in same line
                    if s == "":
                        s = None
                        
        return processed_segments, in_block_comment
        
    def _validate_raise_application_error(self, code, line_dict, line_no, in_raise_error, 
                                          raise_error_start_line, append_error):
        """
        Validate RAISE_APPLICATION_ERROR statements.
        
        Args:
            code (str): The code to validate
            line_dict (dict): The structured line dictionary
            line_no (int): The current line number
            in_raise_error (bool): Whether we're in a RAISE_APPLICATION_ERROR statement
            raise_error_start_line (int): Line where RAISE_APPLICATION_ERROR started
            append_error (callable): Function to add errors
        """
        # Enforce: RAISE_APPLICATION_ERROR must have all parameters on the same line and end with semicolon
        if "RAISE_APPLICATION_ERROR" in code.upper():
            # If we find the start of a RAISE_APPLICATION_ERROR call
            if not in_raise_error:
                # Start already handled by caller
                pass
                
            # Check if this line contains the complete RAISE_APPLICATION_ERROR statement
            # It should have opening and closing parentheses and end with a semicolon
            if "(" in code and ")" in code and line_dict["is_end_semicolon"]:
                # Valid - complete on one line
                pass
            # If it has closing parenthesis but no semicolon
            elif ")" in code and not line_dict["is_end_semicolon"]:
                append_error(
                    line_no,
                    "RAISE_APPLICATION_ERROR must end with a semicolon",
                    "Add a semicolon after the closing parenthesis: RAISE_APPLICATION_ERROR(...);",
                )
        
        # If we're in the middle of a RAISE_APPLICATION_ERROR and this line doesn't continue it
        elif in_raise_error and ")" in code:
            # End of multi-line RAISE_APPLICATION_ERROR found
            append_error(
                raise_error_start_line,
                "RAISE_APPLICATION_ERROR parameters must be on the same line",
                "Place all parameters on the same line: RAISE_APPLICATION_ERROR(param1, param2);",
            )

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
        if not self.declare_section:
            logger.debug("No declarations to parse (empty DECLARE section)")
            return
            
        # Statistics for debugging
        total_segments = 0
        skipped_segments = 0
        
        # Rebuild the declaration section from structured lines
        declare_text = self.declare_section
        
        # Split by semicolons for declaration segmenting
        segments = declare_text.split(";")
        total_segments = len(segments)
        logger.debug("Parsing declarations: found %d raw segment(s)", total_segments)
        
        # Process each declaration segment
        for segment in segments:
            # Skip empty segments
            if not segment.strip():
                skipped_segments += 1
                continue
                
            # Add semicolon back for consistent formatting
            segment = segment.strip() + ";"
            
            # Step 1: Remove comments
            code, comment = self._strip_inline_sql_comment(segment)
            if comment:
                self.sql_comments.append(comment)
                
            # Skip empty segments after comment removal
            if not code.strip():
                skipped_segments += 1
                continue
                
            segment = code

            # Step 2: Identify declaration type and parse
            # Parse exceptions - look for EXCEPTION keyword
            if re.search(r"\s*exception\s*;", segment, re.IGNORECASE):
                self._process_exception_declaration(segment)
            # Parse constants - look for CONSTANT keyword
            elif "constant" in segment.lower():
                self._process_constant_declaration(segment)
            # Parse variables (anything else)
            else:
                self._process_variable_declaration(segment)
                
        # Log summary of declarations found
        logger.info(
            "Declarations parsed: %d variables, %d constants, %d exceptions (%d segments skipped)",
            len(self.variables), len(self.constants), len(self.exceptions), skipped_segments
        )
        
    def _process_exception_declaration(self, segment):
        """
        Process an exception declaration segment.
        
        Args:
            segment (str): The segment containing an exception declaration
        """
        parsed_exception = self._parse_exception(segment)
        if parsed_exception:
            self.exceptions.append(parsed_exception)
            logger.debug("Parsed exception: %s", parsed_exception["name"])
        
    def _process_constant_declaration(self, segment):
        """
        Process a constant declaration segment.
        
        Args:
            segment (str): The segment containing a constant declaration
        """
        parsed_const = self._parse_constant(segment)
        if parsed_const:
            self.constants.append(parsed_const)
            name = parsed_const.get("name", "UNKNOWN")
            type_str = parsed_const.get("data_type", "UNKNOWN") 
            logger.debug("Parsed constant: %s (%s)", name, type_str)
            
    def _process_variable_declaration(self, segment):
        """
        Process a variable declaration segment.
        
        Args:
            segment (str): The segment containing a variable declaration
        """
        parsed_var = self._parse_variable(segment)
        if parsed_var:
            self.variables.append(parsed_var)
            name = parsed_var.get("name", "UNKNOWN")
            type_str = parsed_var.get("data_type", "UNKNOWN")
            logger.debug("Parsed variable: %s (%s)", name, type_str)

    def _parse_exception(self, line):
        """
        Parse an exception declaration line.
        
        This extracts the exception name from declarations like:
        - my_exception exception;
        
        Args:
            line (str): The line containing an exception declaration
            
        Returns:
            dict: Dictionary with the exception name and type
        """
        # Clean up the line
        line = line.strip()
        
        logger.debug("Parsing exception declaration: %s", line)

        # Basic pattern: exception_name exception;
        exception_pattern = re.compile(
            r"([a-zA-Z0-9_]+)\s+exception\s*;", re.IGNORECASE
        )
        match = exception_pattern.search(line)

        if match:
            # Standard exception declaration
            name = match.group(1).strip()
            result = {"name": name, "type": "exception"}
            logger.debug("Successfully parsed exception: %s", name)
            return result
        else:
            # For more complex exceptions or ones we can't parse cleanly
            # Fall back to basic string processing
            name = line.replace("exception", "").replace(";", "").strip()
            logger.warning("Complex exception detected, using fallback parsing: %s", name)
            result = {
                "name": name,
                "type": "exception",
            }
            return result

    def _parse_variable(self, line):
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
        # Remove comments and whitespace
        line = re.sub(r"^--.*\n", "", line)
        line = re.sub(r"/\*.*?\*/", "", line, flags=re.DOTALL)
        line = line.strip()

        # Skip empty lines
        if not line:
            logger.debug("Skipping empty variable line")
            return None

        # Consolidated pattern for variable declarations with flexible spacing and optional default value
        var_pattern = re.compile(
            r"([a-zA-Z0-9_]+)\s+([\w\(\)\%\.]+(?:\s+[\w\(\)\%\.]+)*)(?:\s*:=\s*(.+?))?\s*;",
            re.IGNORECASE | re.DOTALL
        )
        
        match = var_pattern.search(line)
        if match:
            name = match.group(1).strip()
            data_type = match.group(2).strip()
            default_value = match.group(3).strip() if match.group(3) else None

            logger.debug(
                "Parsed variable: %s of type %s%s", 
                name, 
                data_type, 
                " with default" if default_value else ""
            )
            
            return {
                "name": name,
                "data_type": data_type,
                "default_value": default_value,
            }

        # If we couldn't parse it properly, log a warning and return as unparsed
        logger.warning("Failed to parse variable declaration: %s", line[:50] + ("..." if len(line) > 50 else ""))
        return {
            "name": "UNPARSED",
            "data_type": "UNKNOWN",
            "default_value": line,
        }

    def _parse_constant(self, line):
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
        # Clean up comments and whitespace
        line = re.sub(r"--.*$", "", line)
        line = re.sub(r"/\*.*?\*/", "", line, flags=re.DOTALL)
        line = line.strip()
        
        logger.debug("Parsing constant declaration: %s", line)

        # Pattern: const_name CONSTANT data_type := value;
        const_pattern = re.compile(
            r"([a-zA-Z0-9_]+)\s+constant\s+([\w\(\)\%\.]+(?:\s+[\w\(\)\%\.]+)*)(?:\s*:=\s*(.+?))?\s*;",
            re.IGNORECASE | re.DOTALL
        )
        
        match = const_pattern.search(line)
        if match:
            name = match.group(1).strip()
            data_type = match.group(2).strip()
            value = match.group(3).strip() if match.group(3) else None
            
            logger.debug(
                "Successfully parsed constant %s of type %s with value: %s", 
                name, data_type, value if value else "NULL"
            )
            
            return {
                "name": name, 
                "data_type": data_type, 
                "value": value
            }
            
        # If we couldn't parse it properly, log a warning and return as unparsed
        logger.warning("Failed to parse constant declaration: %s", line[:50] + ("..." if len(line) > 50 else ""))
        return {
            "name": "UNPARSED",
            "data_type": "UNKNOWN",
            "value": line,
        }

    # --- Helpers for handling block comments in SQL body ---
    def _strip_block_comments(self, structured_lines):
        """
        Strip block comments (/* ... */) from structured lines.
        
        This method processes each line to remove block comments while preserving
        the structure of the original content. It handles multi-line block comments
        that span across multiple structured lines.
        
        Args:
            structured_lines (List[Dict]): List of structured line dictionaries
            
        Returns:
            Tuple[List[Dict], List[str]]: A tuple containing:
                - List of clean structured lines without block comments
                - List of extracted comment strings
                
        Performance optimization:
            - Fast path check for lines without any block comments
            - Preserves line numbers and indentation for proper error reporting
        """
        # Initialize tracking variables
        clean_structured_lines = []
        comments = []
        in_block = False
        current_comment = []
        
        # Fast path optimization - if no lines contain '/*', return original (minus empty lines)
        if not any("/*" in line_dict["line"] for line_dict in structured_lines):
            logger.debug("No block comments found - using fast path")
            return [line_dict for line_dict in structured_lines if line_dict["line"].strip()], []
            
        logger.debug("Processing %d structured lines for block comments", len(structured_lines))
            
        # Process each structured line
        for line_dict in structured_lines:
            s = line_dict["line"]
            result_segments = []
            
            # Process this line until all comments are handled
            while s:
                if not in_block:
                    # Outside a comment block - look for comment start
                    start = s.find("/*")
                    if start == -1:
                        # No comment start found - keep the whole segment
                        if s.strip():
                            result_segments.append(s)
                        break
                    else:
                        # Comment start found
                        # Keep text before comment start
                        if s[:start].strip():
                            result_segments.append(s[:start])
                        # Start collecting comment content
                        in_block = True
                        current_comment = [s[start+2:]]
                        s = ""  # Processed the whole line
                else:
                    # Inside a comment block - look for comment end
                    end = s.find("*/")
                    if end == -1:
                        # Comment continues to next line
                        current_comment.append(s)
                        break
                    else:
                        # Found comment end
                        current_comment.append(s[:end])
                        comments.append("\n".join(current_comment).strip())
                        in_block = False
                        # Continue processing the rest of this line
                        s = s[end+2:]
                        current_comment = []
            
            # Add any collected text segments from this line (outside comments)
            if result_segments:
                # Join segments with spaces for readability
                joined = " ".join(segment.strip() for segment in result_segments)
                if joined.strip():
                    # Create a new structured line dictionary with processed content
                    clean_structured_lines.append({
                        "indent": line_dict["indent"],
                        "line": joined,
                        "line_no": line_dict["line_no"],
                        "is_end_semicolon": joined.rstrip().endswith(';')
                    })
                    
        # Handle unclosed comment block at the end of input (malformed SQL)
        if in_block and current_comment:
            logger.warning("Unclosed block comment detected at end of input")
            comments.append("\n".join(current_comment).strip())
            
        logger.debug(
            "Block comment processing complete: %d clean lines, %d comments extracted", 
            len(clean_structured_lines), 
            len(comments)
        )
        return clean_structured_lines, comments

    # --- Helpers for parsing main begin...exception...end blocks ---
    def _get_main_lines(self):
        """
        Process the main section of SQL by converting it to structured lines
        and removing both block and inline comments.
        
        This method:
        1. Converts the main section text into structured line format
        2. Removes all block comments (/* ... */)
        3. Removes all inline comments (-- ...)
        4. Preserves indentation and statement boundaries
        
        Returns:
            List[Dict]: List of clean code structured line dictionaries 
                       ready for further analysis
        """
        # Fast path: if main section is empty, return empty list
        if not self.main_section:
            logger.debug("Empty main section, returning empty lines")
            return []
            
        # Step 1: Convert the main section to structured lines
        main_structured_lines = self._convert_main_to_structured_lines()
        logger.debug("Converted main section to %d structured lines", len(main_structured_lines))
        
        # Step 2: Remove block comments (/* ... */)
        clean_block, block_comments = self._strip_block_comments(main_structured_lines)
        comment_count = len(block_comments)
        if block_comments:
            self.sql_comments.extend(block_comments)
            logger.debug("Removed %d block comment(s) from main section", comment_count)
            
        # Step 3: Remove inline comments (-- ...)
        clean_structured_lines, inline_comments = self._strip_inline_comments_from_lines(clean_block)
        if inline_comments:
            self.sql_comments.extend(inline_comments)
            logger.debug("Removed %d inline comment(s) from main section", len(inline_comments))
            
        logger.debug("Main section processing complete: %d clean structured lines", len(clean_structured_lines))
        return clean_structured_lines
        
    def _convert_main_to_structured_lines(self):
        """
        Convert the main section text into structured lines format.
        
        Returns:
            List[Dict]: List of structured line dictionaries
        """
        main_structured_lines = []
        main_lines = self.main_section.split("\n")
        print(self.main_section)
        for i, line in enumerate(main_lines, start=1):
            # Calculate indentation level
            indent_level = len(line) - len(line.lstrip())
            # Get content without leading/trailing whitespace
            content = line.lstrip().rstrip()
            # Skip empty lines
            if not content:
                continue
            # Check if line ends with semicolon
            is_end_semicolon = content.endswith(';')
            
            main_structured_lines.append({
                "indent": indent_level,
                "line": content,
                "line_no": i,  # This will be relative to main section
                "is_end_semicolon": is_end_semicolon
            })
            
        return main_structured_lines
        
    def _strip_inline_comments_from_lines(self, structured_lines):
        """
        Remove inline comments (-- ...) from a list of structured lines.
        
        Args:
            structured_lines (List[Dict]): List of structured line dictionaries
            
        Returns:
            Tuple[List[Dict], List[str]]: Clean structured lines and extracted comments
        """
        clean_structured_lines = []
        inline_comments = []
        
        # Process all lines at once
        for line_dict in structured_lines:
            if not line_dict["line"].strip():
                continue
                
            code, comment = self._strip_inline_sql_comment(line_dict["line"])
            if code.strip():
                # Create new structured line with processed content
                clean_structured_lines.append({
                    "indent": line_dict["indent"],
                    "line": code.strip(),
                    "line_no": line_dict["line_no"],
                    "is_end_semicolon": code.strip().endswith(';')
                })
            if comment:
                inline_comments.append(comment)
                
        return clean_structured_lines, inline_comments

    def _parse_exception_handlers(self, exception_lines):
        text = "\n".join(exception_lines)
        handlers = []
        # Match: when <name> then <body> ... (until next when or end)
        pattern = re.compile(
            r"when\s+([a-zA-Z0-9_]+)\s+then\s+(.*?)(?=(?:\n\s*when\s+[a-zA-Z0-9_]+\s+then)|\Z)",
            re.IGNORECASE | re.DOTALL,
        )
        for m in pattern.finditer(text):
            handler_exception_name = m.group(1).strip()
            body = m.group(2).strip()

            # Collect SQL actions under this handler
            sqls = []

            # Extract all raise_application_error calls within handler
            for rae in re.finditer(
                r"raise_application_error\s*\(\s*([\-\d]+)\s*,\s*(.*?)\)\s*;",
                body,
                re.IGNORECASE | re.DOTALL,
            ):
                code = rae.group(1).strip()
                param2 = rae.group(2).strip()
                
                # Enhanced handling for string parameters, including concatenation with ||
                # Keep the full expression for complex strings with concatenation
                if "||" in param2:
                    # For concatenated strings, keep the entire expression
                    message = param2
                else:
                    # For simple strings, extract just the string content
                    msg_match = re.search(r"'([^']*)'", param2, re.DOTALL)
                    message = msg_match.group(1) if msg_match else param2
                    
                # If the message contains a semicolon, split it into multiple statements
                # if ";" in message:
                #     # Split the message into individual statements
                #     statements = self._split_statements_by_semicolon(message)
                #     for statement in statements:
                #         sqls.append(
                #             {
                #                 "type": "function calling",
                #                 "function_name": "raise_application_error",
                #                 "parameter": {
                #                     "handler_code": code,
                #                     "handler_string": statement,
                #                 },
                #             }
                #         )
                    
                sqls.append(
                    {
                        "type": "function calling",
                        "function_name": "raise_application_error",
                        "parameter": {
                            "handler_code": code,
                            "handler_string": message,
                        },
                    }
                )

            # Extract simple RAISE <EXC_NAME>; usages and record under current handler
            for rm in re.finditer(r"\braise\s+([A-Za-z0-9_]+)\s*;", body, re.IGNORECASE):
                raised_exc = rm.group(1).strip()
                sqls.append(
                    {
                        "sql": f"RAISE {raised_exc}",
                        "type": "RAISE_statements",
                    }
                )

            # Finally, append the handler object itself (even if it had no RA E)
            handlers.append(
                {
                    "exception_name": handler_exception_name,
                    "sqls": sqls,
                }
            )
        logger.debug(f"Parsed {len(handlers)} exception handler(s)")
        return handlers

    def _extract_nested_blocks(self, structured_lines):
        """
        Extract nested BEGIN blocks from the structured lines of SQL code,
        removing comments and handling proper nesting of blocks.
        """
        # First remove both block and inline comments (already done in _get_main_lines)
        # We'll work directly with the provided structured lines
        
        # Compile regex patterns for block detection
        begin_re = re.compile(r"^\s*begin\b", re.IGNORECASE)
        exception_re = re.compile(r"^\s*exception\s*$", re.IGNORECASE)
        end_re = re.compile(r"^\s*end\s*;\s*$", re.IGNORECASE)
        
        # Process the structured lines
        result = []
        i = 0
        while i < len(structured_lines):
            line_dict = structured_lines[i]
            line_content = line_dict["line"]
            
            if begin_re.match(line_content):
                # Consume nested block
                depth = 1
                i += 1
                body_lines_dicts = []
                exception_lines_dicts = []
                in_exception = False
                
                while i < len(structured_lines) and depth > 0:
                    cur_dict = structured_lines[i]
                    cur = cur_dict["line"]
                    
                    if begin_re.match(cur):
                        depth += 1
                    if exception_re.match(cur) and depth == 1:
                        in_exception = True
                        i += 1
                        continue
                    if end_re.match(cur):
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    
                    if in_exception:
                        exception_lines_dicts.append(cur_dict)
                    else:
                        body_lines_dicts.append(cur_dict)
                    i += 1
                    
                # Store the original SQL for the begin block
                original_begin = "BEGIN"
                original_body = self._generate_original_sql(body_lines_dicts)
                original_exception = ""
                if exception_lines_dicts:
                    original_exception = "EXCEPTION\n" + self._generate_original_sql(exception_lines_dicts)
                original_sql = f"{original_begin}\n{original_body}\n{original_exception}\nEND;"
                
                # Extract just the string content from the structured dicts for exception handler parsing
                exception_lines = [d["line"] for d in exception_lines_dicts]
                
                # Recursively process body_lines for further nested blocks,
                # then apply the ordered grouping pipeline (IF -> CASE -> FOR -> ASSIGN -> SQL -> RAISE)
                nested_sqls = self._apply_grouping_pipeline(body_lines_dicts)
                
                result.append(
                    {
                        "sqls": nested_sqls if nested_sqls else [d["line"] for d in body_lines_dicts],
                        "type": "begin_block",
                        "exception_handlers": self._parse_exception_handlers(exception_lines),
                        "o_sql": original_sql  # Add the original SQL
                    }
                )
            else:
                # For non-BEGIN lines, just append the line content to the result
                result.append(line_dict["line"])
                i += 1
                
        logger.debug(f"Extracted nested blocks/elements: count={len(result)}")
        return result

    def _parse_begin_blocks(self):
        """
        Parse top-level BEGIN blocks from the main section of SQL.
        Extracts the structure and processes inner blocks recursively.
        Uses the structured line format.
        """
        structured_lines = self._get_main_lines()
        blocks = []
        
        # Process blocks from the main lines directly
        processed = self._extract_nested_blocks(structured_lines)
        
        # Filter out only the begin_block types from the processed elements
        for element in processed:
            if isinstance(element, dict) and element.get("type") == "begin_block":
                blocks.append(element)
        
        logger.debug(f"Top-level begin blocks parsed: {len(blocks)}")
        return blocks

    def _strip_trailing_semicolon(self, sql_text: str) -> str:
        """
        Cleans up SQL text by handling semicolons appropriately.
        This preserves the semicolon but removes any that are immediately 
        before an inline comment.
        """
        text = sql_text.rstrip()
        
        # Remove a semicolon immediately before an end-of-line inline comment
        # Example: "...; -- comment" => "... -- comment"
        text = re.sub(r";\s*(--\s*.*)$", r" \1", text)
        
        # Return the text without processing the semicolon further
        # (We want to preserve the semicolon for SQL statements)
        return text

    def _group_sql_statements(self, elements):
        """
        Unified method to group both SQL statements (SELECT, INSERT, UPDATE, DELETE) 
        and RAISE statements. Uses structured line dictionaries.
        """
        grouped = []
        i = 0
        
        # Statement type mapping for quick lookups
        STMT_TYPE_MAP = {
            "SELECT": "select_statements",
            "INSERT": "insert_statements",
            "UPDATE": "update_statements",
            "DELETE": "delete_statements",
            "RAISE": "raise_statements"
        }
        
        while i < len(elements):
            el = elements[i]
            # Recurse into nested begin blocks
            if isinstance(el, dict) and el.get("type") == "begin_block":
                el_sqls = el.get("sqls", [])
                el["sqls"] = self._group_sql_statements(el_sqls)
                grouped.append(el)
                i += 1
                continue
                
            # Process elements that could be SQL or RAISE statements
            if isinstance(el, dict) and "line" in el:
                # This is a structured line dictionary
                line_content = el["line"]
                # Check for recognized statement types
                upper = line_content.strip().upper()
                stmt_type = None
                
                # Determine statement type from first word
                first_word = upper.split(' ', 1)[0] if ' ' in upper else upper
                stmt_type = STMT_TYPE_MAP.get(first_word)

                if stmt_type:
                    buffer_lines = [el]
                    i += 1
                    # Accumulate subsequent lines until a line ends with semicolon
                    while i < len(elements):
                        nxt = elements[i]
                        if isinstance(nxt, dict) and "line" in nxt:
                            buffer_lines.append(nxt)
                            i += 1
                            if nxt.get("is_end_semicolon", False):
                                break
                        else:
                            # Stop grouping on non-structured line; let outer loop handle it
                            break
                            
                    # Store the original SQL
                    original_sql = self._generate_original_sql(buffer_lines)
                    
                    # Join lines with a single space and clean up
                    sql_flat = " ".join(line_dict["line"] for line_dict in buffer_lines if line_dict["line"])
                    # No need to strip trailing semicolon since we now track it in the structure
                    
                    grouped.append({
                        "sql": sql_flat, 
                        "type": stmt_type,
                        "o_sql": original_sql
                    })
                    continue
            elif isinstance(el, str):
                # For backward compatibility with string elements
                upper = el.strip().upper()
                stmt_type = None
                
                # Determine statement type from first word
                first_word = upper.split(' ', 1)[0] if ' ' in upper else upper
                stmt_type = STMT_TYPE_MAP.get(first_word)

                if stmt_type:
                    buffer_lines = [el]
                    i += 1
                    # Accumulate subsequent string lines until a line ends with ';'
                    while i < len(elements):
                        nxt = elements[i]
                        if isinstance(nxt, str):
                            buffer_lines.append(nxt)
                            i += 1
                            if nxt.strip().endswith(";"):
                                break
                        else:
                            # Stop grouping on non-string; let outer loop handle it
                            break
                            
                    # Store the original SQL
                    original_sql = self._generate_original_sql(buffer_lines)
                    
                    # Join lines with a single space and clean up
                    sql_flat = " ".join(line for line in buffer_lines if line)
                    sql_flat = self._strip_trailing_semicolon(sql_flat)
                    
                    grouped.append({
                        "sql": sql_flat, 
                        "type": stmt_type,
                        "o_sql": original_sql
                    })
                    continue
            
            # Default passthrough for elements that aren't SQL or RAISE statements
            grouped.append(el)
            i += 1
            
        return grouped

    def _group_assignment_statements(self, elements):
        """
        Group assignment statements (:=) in the SQL code.
        Uses structured line dictionaries.
        """
        grouped = []
        i = 0
        while i < len(elements):
            el = elements[i]
            
            # Recurse into nested begin blocks
            if isinstance(el, dict) and el.get("type") == "begin_block":
                el_sqls = el.get("sqls", [])
                el["sqls"] = self._group_assignment_statements(el_sqls)
                grouped.append(el)
                i += 1
                continue
                
            # Process structured line dictionaries that could be assignments
            if isinstance(el, dict) and "line" in el:
                buffer_lines = [el]
                i += 1
                
                # Continue accumulating lines until we hit a semicolon
                if not el.get("is_end_semicolon", False):
                    while i < len(elements):
                        nxt = elements[i]
                        if isinstance(nxt, dict) and "line" in nxt:
                            buffer_lines.append(nxt)
                            i += 1
                            if nxt.get("is_end_semicolon", False):
                                break
                        else:
                            # Non-structured line element encountered
                            break
                
                # Join lines and check if it's an assignment
                flat = " ".join(line_dict["line"].strip() for line_dict in buffer_lines)
                if ":=" in flat:
                    # It's an assignment
                    original_sql = self._generate_original_sql(buffer_lines)
                    
                    # Split into variable and value parts
                    var_part, val_part = flat.split(":=", 1)
                    var_part = var_part.strip()
                    # No need to strip trailing semicolon since we track it in the structure
                    val_part = val_part.strip()
                    if val_part.endswith(";"):
                        val_part = val_part[:-1].strip()
                    
                    grouped.append({
                        "variable": var_part,
                        "value": val_part,
                        "type": "assignment_statements",
                        "o_sql": original_sql
                    })
                    continue
                    
                # Not an assignment, append original line dictionaries
                grouped.extend(buffer_lines)
                continue
            elif isinstance(el, str):
                # For backward compatibility with string elements
                buffer_lines = [el]
                i += 1
                
                # Continue accumulating lines until we hit a semicolon
                if not el.strip().endswith(";"):
                    while i < len(elements):
                        nxt = elements[i]
                        if isinstance(nxt, str):
                            buffer_lines.append(nxt)
                            i += 1
                            if nxt.strip().endswith(";"):
                                break
                        else:
                            # Non-string element encountered
                            break
                
                # Join lines and check if it's an assignment
                flat = " ".join(line.strip() for line in buffer_lines)
                if ":=" in flat:
                    # It's an assignment
                    original_sql = self._generate_original_sql(buffer_lines)
                    
                    # Split into variable and value parts
                    var_part, val_part = flat.split(":=", 1)
                    var_part = var_part.strip()
                    val_part = self._strip_trailing_semicolon(val_part.strip())
                    
                    grouped.append({
                        "variable": var_part,
                        "value": val_part,
                        "type": "assignment_statements",
                        "o_sql": original_sql
                    })
                    continue
                    
                # Not an assignment, append original lines
                grouped.extend(buffer_lines)
                continue
                
            # Default passthrough for non-structured line elements
            grouped.append(el)
            i += 1
            
        return grouped
    def _split_statements_by_semicolon(self, sql_text):
        """
        Helper to split a block of SQL statements by semicolons.
        Works with either raw SQL text or a list of structured line dictionaries.
        Returns a list of statement strings.
        """
        # Handle different input types
        if isinstance(sql_text, list) and all(isinstance(item, dict) and "line" in item for item in sql_text):
            # We have a list of structured line dictionaries
            statements = []
            current_stmt = []
            
            for line_dict in sql_text:
                current_stmt.append(line_dict["line"])
                if line_dict.get("is_end_semicolon", False):
                    # This line ends with a semicolon, so this is the end of a statement
                    stmt = " ".join(current_stmt).strip()
                    if stmt:  # Skip empty statements
                        statements.append(stmt)
                    current_stmt = []
            
            # Add any remaining statement without semicolon
            if current_stmt:
                stmt = " ".join(current_stmt).strip()
                if stmt:  # Skip empty statements
                    statements.append(stmt)
                    
            return statements
        else:
            # Handle as plain text (for backward compatibility)
            # Trim the SQL text
            if isinstance(sql_text, list):
                sql_text = " ".join(sql_text)
            
            sql_text = sql_text.strip()
            
            # If empty, return an empty list
            if not sql_text:
                return []
                
            # Split by semicolons but keep them attached to the statements
            statements = []
            for stmt in re.findall(r'(.*?;)', sql_text, re.DOTALL):
                stmt = stmt.strip()
                if stmt:  # Skip empty statements
                    statements.append(stmt)
                    
            # Check if there's a trailing part without semicolon
            last_part = re.sub(r'.*?;', '', sql_text, flags=re.DOTALL).strip()
            if last_part:
                statements.append(last_part)
                
            return statements



    def _generate_original_sql(self, lines):
        """
        Generate original SQL from a list of lines, which can be either:
        - A list of strings 
        - A list of structured line dictionaries with a 'line' key
        
        Returns a string with the original SQL with newlines preserved.
        """
        if not lines:
            return ""
            
        if isinstance(lines[0], dict) and "line" in lines[0]:
            # We have structured line dictionaries
            return "\n".join(line_dict["line"] for line_dict in lines)
        else:
            # We have string lines
            return "\n".join(lines)
    
    def _count_strings_and_dicts(self, obj):
        """
        Recursively count strings and dictionaries in the result object.
        Returns tuple of (string_count, dict_count)
        """
        if isinstance(obj, str):
            return 1, 0
        elif isinstance(obj, dict):
            str_count, dict_count = 0, 1  # Count this dict
            for key, value in obj.items():
                if key != "o_sql":  # Skip original SQL to avoid double counting
                    s, d = self._count_strings_and_dicts(value)
                    str_count += s
                    dict_count += d
            return str_count, dict_count
        elif isinstance(obj, list):
            str_count, dict_count = 0, 0
            for item in obj:
                s, d = self._count_strings_and_dicts(item)
                str_count += s
                dict_count += d
            return str_count, dict_count
        else:
            return 0, 0  # Other types (int, bool, etc.)

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
            logger.warning("Rule violations detected: %d error(s), conversion aborted", len(self.rule_errors))
            return {"error": self.rule_errors}

        # Step 2: Parse begin blocks from the main section
        logger.debug("Parsing BEGIN blocks for JSON conversion")
        main_blocks = self._parse_begin_blocks()
        
        # Step 3: Construct the result dictionary
        result = {
            "declarations": {
                "variables": self.variables,
                "constants": self.constants,
                "exceptions": self.exceptions,
            },
            "main": main_blocks,
            "sql_comments": self.sql_comments,
        }
        
        # Step 4: Count strings and dictionaries for quality metrics
        strings_count, dicts_count = self._count_strings_and_dicts(result)
        
        # Step 5: Add additional metadata to the result
        # Include structured lines for clients that need them
        result["structured_lines"] = self.structured_lines
        
        # Add conversion statistics
        result["conversion_stats"] = {
            "remaining_strings": strings_count,
            "converted_to_dicts": dicts_count,
            "declaration_count": len(self.variables) + len(self.constants) + len(self.exceptions),
            "main_block_count": len(main_blocks),
            "comment_count": len(self.sql_comments)
        }
        
        # Include parse timestamp
        result["metadata"] = {
            "parse_timestamp": self._get_timestamp(),
            "parser_version": "1.0",  # Increment when making significant parser changes
        }
        
        # Log detailed statistics for troubleshooting
        logger.info(
            "JSON conversion complete: %d vars, %d consts, %d excs, %d main_blocks, %d comments, %d strings, %d dicts",
            len(self.variables),
            len(self.constants),
            len(self.exceptions),
            len(main_blocks),
            len(self.sql_comments),
            strings_count,
            dicts_count
        )
        return result
        
    def _get_timestamp(self):
        """Get current timestamp in ISO format for metadata"""
        from datetime import datetime
        return datetime.now().isoformat()