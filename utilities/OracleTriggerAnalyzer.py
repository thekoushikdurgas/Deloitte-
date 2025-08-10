import re
from typing import Any, Dict, List, Tuple
from utilities.common import debug


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
        self.sql_content: str = sql_content
        self.declare_section: str = ""
        self.main_section: str = ""
        self.variables: List[Dict[str, Any]] = []
        self.constants: List[Dict[str, Any]] = []
        self.exceptions: List[Dict[str, Any]] = []
        self.sql_comments: List[str] = []
        self.rule_errors: List[Dict[str, Any]] = []
        debug("Initializing OracleTriggerAnalyzer and parsing SQL")
        self._parse_sql()
        debug("Running rule validation")
        # Run rule validation as soon as the analyzer is created
        self.rule_errors = self._validate_rules()

    def _strip_inline_sql_comment(self, text: str) -> Tuple[str, str]:
        """
        Remove inline -- comments occurring outside of single-quoted strings.
        Returns a tuple of (code_without_comments, extracted_comment)
        """
        # If the entire line is a comment, return empty code and the comment
        if text.lstrip().startswith("--"):
            return "", text.strip()
        
        # Handle strings with single quotes to avoid removing comments inside strings
        in_string = False
        i = 0
        result_chars = []
        comment = ""
        
        while i < len(text):
            ch = text[i]
            
            # Toggle in_string when encountering quotes, handle escaped quotes
            if ch == "'":
                result_chars.append(ch)
                i += 1
                if in_string:
                    # Check for escaped quotes (two single quotes in a row)
                    if i < len(text) and text[i] == "'":
                        result_chars.append("'")
                        i += 1
                        continue
                    in_string = False
                else:
                    in_string = True
                continue
                
            # Detect comment start when not inside a string
            if not in_string and ch == '-' and i + 1 < len(text) and text[i + 1] == '-':
                comment = text[i:].strip()
                break
                
            result_chars.append(ch)
            i += 1
            
        return "".join(result_chars).rstrip(), comment

    def _parse_sql(self) -> None:
        # Find the "declare" section (everything between "declare" and "begin")
        debug("Parsing SQL into declare and main sections")
        pattern = re.compile(r"declare(.*?)begin", re.DOTALL | re.IGNORECASE)
        match = pattern.search(self.sql_content)

        if match:
            # Store declare section without the "declare" keyword
            self.declare_section = match.group(1).strip()
            # Main section is everything from "begin" to the end
            begin_pos = match.end() - 5  # subtract 5 to keep the "begin" keyword
            self.main_section = self.sql_content[begin_pos:].strip()
            debug(f"Found DECLARE section length={len(self.declare_section)}, main length={len(self.main_section)}")

            # Parse the declarations into categories
            self._parse_declarations()
        else:
            # If no declare section found, assume everything is main section
            self.declare_section = ""
            self.main_section = self.sql_content.strip()
            debug("No DECLARE section found; entire text treated as main section")

    # -----------------------------
    # Grouping pipeline (ORDERED)
    # -----------------------------
    def _apply_grouping_pipeline(self, elements):
        """
        Apply the detection/grouping passes in a strict order:
        1) IF / ELSIF / ELSE blocks
        2) CASE / WHEN / ELSE blocks
        3) FOR loops
        4) Assignment statements
        5) SQL statements (DML/SELECT/RAISE combined)

        NOTE: BEGIN/END nested blocks are handled by callers via _extract_nested_blocks
        and _parse_begin_blocks before this pipeline is applied.
        """
        # Detect IF blocks first
        grouped = self._group_if_else_statements(elements)
        # Then detect CASE blocks
        grouped = self._group_case_statements(grouped)
        # Then FOR loops
        grouped = self._group_for_loops(grouped)
        # Then assignments
        grouped = self._group_assignment_statements(grouped)
        # Then SQL statements (DML/SELECT and RAISE combined)
        grouped = self._group_sql_statements(grouped)
        return grouped

    # --- Rule validation ---
    def _validate_rules(self):
        """
        Validate formatting rules directly on the raw SQL text and return a list
        of violations in the form required by the caller.

        Rules enforced:
        - IF and THEN must be on the same line
        - ELSIF and THEN must be on the same line
        - WHEN and THEN must be on the same line (for CASE statements)
        """
        errors: List[Dict[str, Any]] = []

        def append_error(line_no: int, rule_text: str, solution_text: str):
            errors.append({
                "line_no": line_no,
                "rule": rule_text,
                "solution": solution_text,
            })

        in_block_comment = False
        lines = self.sql_content.splitlines()
        debug(f"Validating {len(lines)} lines for IF/THEN, ELSIF/THEN, WHEN/THEN rules")
        for idx, original_line in enumerate(lines, start=1):
            line = original_line
            # Remove all code segments that are within /* ... */ comments while
            # preserving anything outside so we keep accurate line numbers
            processed_segments = []
            cursor = 0
            s = line
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
            # Join remaining code outside block comments
            code_outside_blocks = "".join(processed_segments)

            # Strip inline -- comments outside of strings
            code, comment = self._strip_inline_sql_comment(code_outside_blocks)

            # Skip empty or pure comment lines
            if comment.lstrip().startswith("--"):
                continue

            # Enforce: IF ... THEN must be on the same line
            if re.match(r"^\s*IF\b", code, re.IGNORECASE):
                if not re.search(r"\bTHEN\b", code, re.IGNORECASE):
                    append_error(
                        idx,
                        "IF and THEN must be on the same line",
                        "Place THEN on the same line as the IF condition, e.g., IF <condition> THEN",
                    )

            # Enforce: ELSIF ... THEN must be on the same line
            if re.match(r"^\s*ELSIF\b", code, re.IGNORECASE):
                if not re.search(r"\bTHEN\b", code, re.IGNORECASE):
                    append_error(
                        idx,
                        "ELSIF and THEN must be on the same line",
                        "Place THEN on the same line as the ELSIF condition, e.g., ELSIF <condition> THEN",
                    )

            # Enforce: WHEN ... THEN must be on the same line (CASE)
            if re.match(r"^\s*WHEN\b", code, re.IGNORECASE):
                if not re.search(r"\bTHEN\b", code, re.IGNORECASE):
                    append_error(
                        idx,
                        "WHEN and THEN must be on the same line",
                        "Place THEN on the same line as the WHEN condition, e.g., WHEN <condition> THEN",
                    )

        return errors

    def _parse_declarations(self) -> None:
        """
        Parse declarations section and categorize into variables, constants, and exceptions,
        while removing any comments.
        """
        # Split the declare section into lines by semicolon
        lines = self.declare_section.split(";")
        debug(f"Parsing declarations: {len(lines)} segment(s)")
        
        # Process each declaration segment
        for line in lines:
            if not line.strip():
                continue
                
            # Add semicolon back for consistent formatting
            line = line.strip() + ";"
            
            # Strip any inline comments
            code, comment = self._strip_inline_sql_comment(line)
            if comment:
                self.sql_comments.append(comment)
                
            # Skip empty lines after comment removal
            if not code.strip():
                continue
                
            line = code

            # Parse exceptions
            if re.search(r"\s*exception\s*;", line, re.IGNORECASE):
                parsed_exception = self._parse_exception(line)
                if parsed_exception:
                    self.exceptions.append(parsed_exception)
                    debug(f"Parsed exception: {parsed_exception}")
            # Parse constants
            elif "constant" in line.lower():
                parsed_const = self._parse_constant(line)
                if parsed_const:
                    self.constants.append(parsed_const)
                    debug(f"Parsed constant: {parsed_const}")
            # Parse variables (anything else)
            else:
                parsed_var = self._parse_variable(line)
                if parsed_var:
                    self.variables.append(parsed_var)
                    debug(f"Parsed variable: {parsed_var}")

    def _parse_exception(self, line):
        # Clean up the line
        line = line.strip()

        # Basic pattern: exception_name exception;
        exception_pattern = re.compile(
            r"([a-zA-Z0-9_]+)\s+exception\s*;", re.IGNORECASE
        )
        match = exception_pattern.search(line)

        if match:
            name = match.group(1).strip()
            result = {"name": name, "type": "exception"}
            return result
        else:
            # For more complex exceptions or ones we can't parse cleanly
            result = {
                "name": line.replace("exception", "").replace(";", "").strip(),
                "type": "exception",
            }
            return result

    def _parse_variable(self, line):
        # Clean up common comment patterns at the start of the line
        line = re.sub(r"^--.*\n", "", line)
        line = line.strip()

        # Skip empty lines
        if not line:
            return None

        # Handle multi-line comments within variable declarations
        line = re.sub(r"/\*.*?\*/", "", line)

        # Basic pattern: variable_name data_type [DEFAULT value];
        var_pattern = re.compile(
            r"([a-zA-Z0-9_]+)\s+([\w\(\)\%\.]+)(?:\s*:=\s*(.+?))?\s*;", re.IGNORECASE
        )
        match = var_pattern.search(line)

        if match:
            name = match.group(1).strip()
            data_type = match.group(2).strip()
            default_value = match.group(3).strip() if match.group(3) else None

            result = {
                "name": name,
                "data_type": data_type,
                "default_value": default_value,
            }
            return result
        else:
            # Handle more complex declarations with special patterns
            # For example: "v_counter simple_integer := 0;"
            complex_pattern = re.compile(
                r"([a-zA-Z0-9_]+)\s+([\w\(\)\%\.]+(?:\s+[\w\(\)\%\.]+)*)(?:\s*:=\s*(.+?))?\s*;",
                re.IGNORECASE,
            )
            match = complex_pattern.search(line)

            if match:
                name = match.group(1).strip()
                data_type = match.group(2).strip()
                default_value = match.group(3).strip() if match.group(3) else None

                result = {
                    "name": name,
                    "data_type": data_type,
                    "default_value": default_value,
                }
                return result

        # If we couldn't parse it properly, return the raw line
        result = {
            "name": "UNPARSED",
            "data_type": "UNKNOWN",
            "default_value": line,
        }
        return result

    def _parse_constant(self, line):
        # Clean up common comment patterns
        line = re.sub(r"--.*$", "", line)
        line = line.strip()

        # Pattern: const_name CONSTANT data_type := value;
        const_pattern = re.compile(
            r"([a-zA-Z0-9_]+)\s+constant\s+([\w\(\)\%\.]+)(?:\s*:=\s*(.+?))?\s*;",
            re.IGNORECASE,
        )
        match = const_pattern.search(line)

        if match:
            name = match.group(1).strip()
            data_type = match.group(2).strip()
            value = match.group(3).strip() if match.group(3) else None
            result = {"name": name, "data_type": data_type, "value": value}
            return result
        else:
            # If we couldn't parse it properly, return the raw line
            result = {
                "name": "UNPARSED",
                "data_type": "UNKNOWN",
                "value": line,
            }
            return result

    # --- Helpers for handling block comments in SQL body ---
    def _strip_block_comments(self, lines):
        clean_lines = []
        comments = []
        in_block = False
        current = []
        for line in lines:
            s = line
            while True:
                if not in_block:
                    start = s.find("/*")
                    if start == -1:
                        if s.strip():
                            clean_lines.append(s.strip())
                        break
                    else:
                        # add code before comment start
                        before = s[:start].strip()
                        if before:
                            clean_lines.append(before)
                        s = s[start + 2 :]
                        in_block = True
                        current = []
                else:
                    end = s.find("*/")
                    if end == -1:
                        current.append(s)
                        s = ""
                        break
                    else:
                        current.append(s[:end])
                        comments.append("\n".join(current).strip())
                        s = s[end + 2 :]
                        in_block = False
                        # continue scanning remainder of this line for more blocks
                        if not s:
                            break
        # if an unterminated block comment remains, capture it
        if in_block and current:
            comments.append("\n".join(current).strip())
        debug(f"Stripped block comments: kept_lines={len(clean_lines)}, comments_found={len(comments)}")
        return clean_lines, comments

    # --- New helpers for parsing main begin...exception...end blocks ---
    def _get_main_lines(self):
        """
        Process the main section of SQL by removing both block and inline comments.
        Returns a list of clean code lines ready for further analysis.
        """
        # First split the main section into raw lines
        raw_lines = [line.rstrip() for line in self.main_section.split("\n")]
        
        # Step 1: Remove block comments (/* ... */)
        clean_block, block_comments = self._strip_block_comments(raw_lines)
        if block_comments:
            self.sql_comments.extend(block_comments)
            
        # Step 2: Process each line to remove inline comments (-- ...)
        clean_lines = []
        inline_comments = []
        
        for line in clean_block:
            if not line.strip():
                continue
                
            code, comment = self._strip_inline_sql_comment(line)
            if code.strip():
                clean_lines.append(code.strip())
            if comment:
                inline_comments.append(comment)
                
        # Store collected inline comments
        if inline_comments:
            self.sql_comments.extend(inline_comments)
            
        debug(f"Prepared {len(clean_lines)} main lines after comment stripping (block and inline)")
        return clean_lines

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
                msg_match = re.search(r"'([^']*)'", param2, re.DOTALL)
                message = msg_match.group(1) if msg_match else param2
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
        debug(f"Parsed {len(handlers)} exception handler(s)")
        return handlers

    def _extract_nested_blocks(self, lines):
        """
        Extract nested BEGIN blocks from the lines of SQL code,
        removing comments and handling proper nesting of blocks.
        """
        # First remove both block and inline comments
        clean_lines = []
        all_comments = []
        
        # Process block comments first
        block_clean, block_comments = self._strip_block_comments(lines)
        if block_comments:
            all_comments.extend(block_comments)
            
        # Then process inline comments
        for line in block_clean:
            if not line.strip():
                continue
                
            code, comment = self._strip_inline_sql_comment(line)
            if code.strip():
                clean_lines.append(code.strip())
            if comment:
                all_comments.append(comment)
        
        # Store all extracted comments
        if all_comments:
            self.sql_comments.extend(all_comments)
        
        # Compile regex patterns for block detection
        begin_re = re.compile(r"^\s*begin\b", re.IGNORECASE)
        exception_re = re.compile(r"^\s*exception\s*$", re.IGNORECASE)
        end_re = re.compile(r"^\s*end\s*;\s*$", re.IGNORECASE)
        
        # Process the cleaned lines
        result = []
        i = 0
        while i < len(clean_lines):
            if begin_re.match(clean_lines[i]):
                # Consume nested block
                depth = 1
                i += 1
                body_lines = []
                exception_lines = []
                in_exception = False
                while i < len(clean_lines) and depth > 0:
                    cur = clean_lines[i]
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
                        exception_lines.append(cur)
                    else:
                        body_lines.append(cur)
                    i += 1
                    
                # Store the original SQL for the begin block
                original_begin = "BEGIN"
                original_body = "\n".join(body_lines)
                original_exception = ""
                if exception_lines:
                    original_exception = "EXCEPTION\n" + "\n".join(exception_lines)
                original_sql = f"{original_begin}\n{original_body}\n{original_exception}\nEND;"
                
                # Recursively process body_lines for further nested blocks,
                # then apply the ordered grouping pipeline (IF -> CASE -> FOR -> ASSIGN -> SQL -> RAISE)
                nested_sqls = self._apply_grouping_pipeline(
                    self._extract_nested_blocks(body_lines)
                )
                
                result.append(
                    {
                        "sqls": nested_sqls if nested_sqls else body_lines,
                        "type": "begin_block",
                        "exception_handlers": self._parse_exception_handlers(
                            exception_lines
                        ),
                        "o_sql": original_sql  # Add the original SQL
                    }
                )
            else:
                line = clean_lines[i]
                result.append(line)
                i += 1
                
        debug(f"Extracted nested blocks/elements: count={len(result)}")
        return result

    def _parse_begin_blocks(self):
        lines = self._get_main_lines()
        begin_re = re.compile(r"^\s*begin\b", re.IGNORECASE)
        exception_re = re.compile(r"^\s*exception\s*$", re.IGNORECASE)
        end_re = re.compile(r"^\s*end\s*;\s*$", re.IGNORECASE)
        blocks = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if begin_re.match(line):
                depth = 1
                i += 1
                body_lines = []
                exception_lines = []
                in_exception = False
                while i < len(lines) and depth > 0:
                    cur = lines[i]
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
                        exception_lines.append(cur)
                    else:
                        body_lines.append(cur)
                    i += 1
                # Store the original SQL for the begin block
                original_begin = "BEGIN"
                original_body = "\n".join(body_lines)
                original_exception = ""
                if exception_lines:
                    original_exception = "EXCEPTION\n" + "\n".join(exception_lines)
                original_sql = f"{original_begin}\n{original_body}\n{original_exception}\nEND;"
                
                blocks.append(
                    {
                        "sqls": self._apply_grouping_pipeline(
                            self._extract_nested_blocks(body_lines)
                        ),
                        "type": "begin_block",
                        "exception_handlers": self._parse_exception_handlers(
                            exception_lines
                        ),
                        "o_sql": original_sql  # Add the original SQL
                    }
                )
            else:
                # Non-begin top-level lines are ignored for now
                i += 1
        # No cleanup needed, return blocks directly
        debug(f"Top-level begin blocks parsed: {len(blocks)}")
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
        and RAISE statements.
        """
        def process_elif_chain(chain):
            """Helper function to process ELSIF chains in IF/ELSE blocks."""
            if not isinstance(chain, dict):
                return chain
            if "then_sql" in chain:
                chain["then_sql"] = self._group_sql_statements(chain["then_sql"])
            if "else_if_statement" in chain and isinstance(
                chain["else_if_statement"], dict
            ):
                chain["else_if_statement"] = process_elif_chain(
                    chain["else_if_statement"]
                )
            return chain

        grouped = []
        i = 0
        while i < len(elements):
            el = elements[i]
            # Recurse into nested begin blocks
            if isinstance(el, dict) and el.get("type") == "begin_block":
                el_sqls = el.get("sqls", [])
                el["sqls"] = self._group_sql_statements(el_sqls)
                grouped.append(el)
                i += 1
                continue
                
            # Recurse for if_else
            if isinstance(el, dict) and el.get("type") == "if_else":
                el["then_sql"] = self._group_sql_statements(el.get("then_sql", []))
                if "else_statement" in el and isinstance(el["else_statement"], list):
                    el["else_statement"] = self._group_sql_statements(
                        el["else_statement"]
                    )
                if "else_if_statement" in el and isinstance(
                    el["else_if_statement"], dict
                ):
                    el["else_if_statement"] = process_elif_chain(
                        el["else_if_statement"]
                    )
                grouped.append(el)
                i += 1
                continue
                
            # Preserve comment objects and other pre-grouped dicts
            if isinstance(el, dict):
                grouped.append(el)
                i += 1
                continue
                
            # Process string elements that could be SQL or RAISE statements
            if isinstance(el, str):
                upper = el.strip().upper()
                
                # First check if it's a RAISE statement
                if upper.startswith("RAISE "):
                    buffer_lines = [el]
                    i += 1
                    while i < len(elements):
                        nxt = elements[i]
                        if isinstance(nxt, str):
                            buffer_lines.append(nxt)
                            i += 1
                            if nxt.strip().endswith(";"):
                                break
                        else:
                            break
                    
                    # Store the original SQL
                    original_sql = "\n".join(buffer_lines)
                    
                    # Join lines with a single space
                    sql_flat = " ".join(line for line in buffer_lines if line)
                    # Preserve semicolons in RAISE statements
                    sql_flat = self._strip_trailing_semicolon(sql_flat)
                    
                    # Extract exception name after RAISE
                    m = re.search(r"\bRAISE\s+([A-Za-z0-9_]+)", sql_flat, re.IGNORECASE)
                    if m:
                        exc_name = m.group(1).strip()
                        grouped.append(
                            {
                                "exception_name": exc_name,
                                "sqls": [
                                    {
                                        "sql": sql_flat,
                                        "type": "RAISE_statements",
                                        "o_sql": original_sql  # Add the original SQL
                                    }
                                ],
                            }
                        )
                        debug(f"Grouped RAISE for exception: {exc_name}")
                    else:
                        # Fallback: keep as a flat RAISE statement
                        grouped.append({
                            "sql": sql_flat, 
                            "type": "RAISE_statements",
                            "o_sql": original_sql  # Add the original SQL
                        })
                        debug("Grouped flat RAISE statement")
                    continue
                
                # Check if it's a DML or SELECT statement
                stmt_type = None
                if upper.startswith("SELECT"):
                    stmt_type = "select_statements"
                elif upper.startswith("INSERT"):
                    stmt_type = "insert_statements"
                elif upper.startswith("UPDATE"):
                    stmt_type = "update_statements"
                elif upper.startswith("DELETE"):
                    stmt_type = "delete_statements"

                if stmt_type is not None:
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
                    # Store the original SQL before cleaning
                    original_sql = "\n".join(buffer_lines)
                    
                    # Join lines with a single space
                    sql_flat = " ".join(line for line in buffer_lines if line)
                    # Preserve semicolons with minimal cleanup
                    sql_flat = self._strip_trailing_semicolon(sql_flat)
                    grouped.append({
                        "sql": sql_flat, 
                        "type": stmt_type,
                        "o_sql": original_sql  # Add the original SQL
                    })
                    debug(f"Grouped {stmt_type}: {sql_flat[:60]}{'...' if len(sql_flat)>60 else ''}")
                    continue
            
            # Default passthrough for elements that aren't SQL or RAISE statements
            grouped.append(el)
            i += 1
        return grouped

    def _group_assignment_statements(self, elements):
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
            # Recurse into if_else branches
            if isinstance(el, dict) and el.get("type") == "if_else":
                el["then_sql"] = self._group_assignment_statements(el.get("then_sql", []))
                if "else_statement" in el and isinstance(el["else_statement"], list):
                    el["else_statement"] = self._group_assignment_statements(el["else_statement"])
                if "else_if_statement" in el and isinstance(el["else_if_statement"], dict):
                    chain = el["else_if_statement"]
                    while isinstance(chain, dict):
                        if "then_sql" in chain:
                            chain["then_sql"] = self._group_assignment_statements(chain["then_sql"])
                        chain = chain.get("else_if_statement")
                grouped.append(el)
                i += 1
                continue
            # Recurse into for_loop bodies
            if isinstance(el, dict) and el.get("type") == "for_loop":
                el["loop_body"] = self._group_assignment_statements(el.get("loop_body", []))
                grouped.append(el)
                i += 1
                continue
            # Recurse into case_when_statements
            if isinstance(el, dict) and el.get("type") == "case_when_statements":
                when_clauses = el.get("when_clauses", [])
                for w in when_clauses:
                    if isinstance(w, dict):
                        if "then_statement" in w and isinstance(w["then_statement"], list):
                            w["then_statement"] = self._group_assignment_statements(w["then_statement"])
                        if "else_statement" in w and isinstance(w["else_statement"], list):
                            w["else_statement"] = self._group_assignment_statements(w["else_statement"])
                grouped.append(el)
                i += 1
                continue
            # Process next element
            # Handle strings potentially containing assignment
            if isinstance(el, str):
                buffer_lines = [el]
                i += 1
                if not el.strip().endswith(";"):
                    while i < len(elements):
                        nxt = elements[i]
                        if isinstance(nxt, str):
                            buffer_lines.append(nxt)
                            i += 1
                            if nxt.strip().endswith(";"):
                                break
                        else:
                            break
                flat = " ".join(line.strip() for line in buffer_lines)
                if ":=" in flat:
                    # Store the original SQL
                    original_sql = "\n".join(buffer_lines)
                    
                    var_part, val_part = flat.split(":=", 1)
                    var_part = var_part.strip()
                    # Preserve semicolons in assignment values
                    val_part = self._strip_trailing_semicolon(val_part.strip())
                    grouped.append({
                        "variable": var_part,
                        "value": val_part,
                        "type": "assignment_statements",
                        "o_sql": original_sql  # Add the original SQL
                    })
                    debug(f"Grouped assignment: {var_part} := {val_part}")
                    continue
                # Not an assignment, append original buffered strings
                for s in buffer_lines:
                    grouped.append(s)
                continue
            # Default passthrough
            grouped.append(el)
            i += 1
        return grouped

    def _group_if_else_statements(self, elements):
        def build_elif_chain(elif_items):
            if not elif_items:
                return None
            head = {
                "condition": elif_items[0]["condition"],
                "then_sql": self._group_sql_statements(
                    self._group_assignment_statements(
                        self._group_if_else_statements(elif_items[0]["then_lines"])
                    )
                ),
            }
            next_chain = build_elif_chain(elif_items[1:])
            if next_chain:
                head["else_if_statement"] = next_chain
            return head

        result = []
        i = 0
        while i < len(elements):
            el = elements[i]
            # Recurse into nested begin blocks
            if isinstance(el, dict) and el.get("type") == "begin_block":
                el["sqls"] = self._group_sql_statements(
                    self._group_if_else_statements(el.get("sqls", []))
                )
                result.append(el)
                i += 1
                continue

            if isinstance(el, str) and el.strip().upper().startswith("IF"):
                # Parse IF condition up to THEN (can span lines)
                condition_parts = []
                # consume the IF line
                line = el
                upper_line = line.upper()
                # Extract after IF up to THEN if present
                if "THEN" in upper_line:
                    before_then = line[: upper_line.find("THEN")]
                    # remove leading IF
                    idx_if = upper_line.find("IF")
                    condition_parts.append(before_then[idx_if + 2 :].strip())
                    i += 1
                else:
                    # consume lines until THEN is found
                    idx_if = upper_line.find("IF")
                    condition_parts.append(line[idx_if + 2 :].strip())
                    i += 1
                    while i < len(elements):
                        nxt = elements[i]
                        if isinstance(nxt, str):
                            up = nxt.upper()
                            if "THEN" in up:
                                condition_parts.append(nxt[: up.find("THEN")].strip())
                                i += 1
                                break
                            else:
                                condition_parts.append(nxt.strip())
                                i += 1
                                continue
                        else:
                            # Unexpected non-string before THEN; stop
                            break
                condition = " ".join(part for part in condition_parts if part)
                debug(f"Detected IF condition: {condition}")

                # Now collect bodies until matching END IF; with nesting support
                depth = 1
                mode = "then"
                then_lines = []
                elif_items = []  # list of {condition, then_lines}
                current_elif = None
                else_lines = []

                while i < len(elements) and depth > 0:
                    cur = elements[i]
                    if isinstance(cur, str):
                        up = cur.strip().upper()
                        # Detect nested IF
                        if up.startswith("IF"):
                            depth += 1
                            # add to current body
                            target = (
                                then_lines
                                if mode == "then"
                                else (
                                    current_elif["then_lines"]
                                    if mode == "elsif" and current_elif
                                    else else_lines
                                )
                            )
                            target.append(cur)
                            i += 1
                            continue
                        # Top-level ELSIF
                        if up.startswith("ELSIF") and depth == 1:
                            # finalize previous elif if any
                            if current_elif is not None:
                                elif_items.append(current_elif)
                            # parse elsif condition up to THEN (can span lines)
                            cond_parts = []
                            line2 = cur
                            up2 = up
                            if "THEN" in up2:
                                cond_parts.append(
                                    line2[: up2.find("THEN")].strip()[5:].strip()
                                )  # remove 'ELSIF'
                                i += 1
                            else:
                                # remove ELSIF prefix
                                cond_parts.append(line2.strip()[5:].strip())
                                i += 1
                                while i < len(elements):
                                    nxt2 = elements[i]
                                    if isinstance(nxt2, str):
                                        upn = nxt2.upper()
                                        if "THEN" in upn:
                                            cond_parts.append(
                                                nxt2[: upn.find("THEN")].strip()
                                            )
                                            i += 1
                                            break
                                        else:
                                            cond_parts.append(nxt2.strip())
                                            i += 1
                                            continue
                                    else:
                                        break
                            current_elif = {
                                "condition": " ".join(p for p in cond_parts if p),
                                "then_lines": [],
                            }
                            mode = "elsif"
                            continue
                        # Top-level ELSE
                        if up.startswith("ELSE") and depth == 1:
                            if current_elif is not None:
                                elif_items.append(current_elif)
                                current_elif = None
                            mode = "else"
                            i += 1
                            continue
                        # Top-level END IF;
                        if depth == 1 and (
                            "END IF;" in up
                            or up.startswith("END IF")
                            and cur.strip().endswith(";")
                        ):
                            if current_elif is not None:
                                elif_items.append(current_elif)
                                current_elif = None
                            i += 1
                            depth -= 1
                            break
                        # Nested END IF;
                        if "END IF;" in up or (
                            up.startswith("END IF") and cur.strip().endswith(";")
                        ):
                            depth -= 1
                            # include this line as content if nested
                            target = (
                                then_lines
                                if mode == "then"
                                else (
                                    current_elif["then_lines"]
                                    if mode == "elsif" and current_elif
                                    else else_lines
                                )
                            )
                            target.append(cur)
                            i += 1
                            continue
                        # Regular content line
                        target = (
                            then_lines
                            if mode == "then"
                            else (
                                current_elif["then_lines"]
                                if mode == "elsif" and current_elif
                                else else_lines
                            )
                        )
                        target.append(cur)
                        i += 1
                    else:
                        # Non-string element (e.g., begin_block or comment or grouped statements)
                        target = (
                            then_lines
                            if mode == "then"
                            else (
                                current_elif["then_lines"]
                                if mode == "elsif" and current_elif
                                else else_lines
                            )
                        )
                        target.append(cur)
                        i += 1

                # Capture the original if-else block SQL
                original_lines = []
                # Start with the IF line
                original_lines.append(el)  # This is the original IF line
                
                # Add all the lines from then, elsif, and else blocks
                original_lines.extend(then_lines)
                for elif_item in elif_items:
                    # Add the ELSIF line
                    original_lines.extend([f"ELSIF {elif_item['condition']} THEN"])
                    # Add the ELSIF body lines
                    original_lines.extend(elif_item.get('then_lines', []))
                if else_lines:
                    original_lines.append("ELSE")
                    original_lines.extend(else_lines)
                original_lines.append("END IF;")
                
                original_sql = "\n".join(str(line) for line in original_lines)

                # Build the if_else object with recursively grouped bodies
                if_else_obj = {
                    "type": "if_else",
                    "condition": condition,
                    "then_sql": self._group_sql_statements(
                        self._group_assignment_statements(
                            self._group_if_else_statements(then_lines)
                        )
                    ),
                    "o_sql": original_sql  # Add the original SQL
                }
                elif_chain = build_elif_chain(elif_items)
                if elif_chain:
                    if_else_obj["else_if_statement"] = elif_chain
                if else_lines:
                    if_else_obj["else_statement"] = self._group_sql_statements(
                        self._group_assignment_statements(
                            self._group_if_else_statements(else_lines)
                        )
                    )
                result.append(if_else_obj)
                debug("Grouped IF/ELSIF/ELSE structure")
                continue

            # default passthrough
            result.append(el)
            i += 1
        return result

    # _group_raise_statements has been merged into _group_sql_statements

    def _group_for_loops(self, elements):
        grouped = []
        i = 0
        while i < len(elements):
            el = elements[i]
            # Recurse into nested begin blocks first
            if isinstance(el, dict) and el.get("type") == "begin_block":
                el_sqls = el.get("sqls", [])
                el["sqls"] = self._group_for_loops(el_sqls)
                grouped.append(el)
                i += 1
                continue
            # Recurse into if_else branches
            if isinstance(el, dict) and el.get("type") == "if_else":
                el["then_sql"] = self._group_for_loops(el.get("then_sql", []))
                if "else_statement" in el and isinstance(el["else_statement"], list):
                    el["else_statement"] = self._group_for_loops(el["else_statement"])
                if "else_if_statement" in el and isinstance(
                    el["else_if_statement"], dict
                ):
                    # process chained elif recursively
                    chain = el["else_if_statement"]
                    while isinstance(chain, dict):
                        if "then_sql" in chain:
                            chain["then_sql"] = self._group_for_loops(chain["then_sql"])
                        chain = chain.get("else_if_statement")
                grouped.append(el)
                i += 1
                continue
            # Preserve comment objects
            # if isinstance(el, dict) and el.get("type") == "comment":
            #     grouped.append(el)
            #     i += 1
            #     continue
            # Handle strings
            if isinstance(el, str) and el.strip().upper().startswith("FOR "):
                buffer_lines = [el]
                i += 1
                depth = 1
                # Accumulate until matching END LOOP;
                while i < len(elements) and depth > 0:
                    nxt = elements[i]
                    if isinstance(nxt, str):
                        up = nxt.strip().upper()
                        if up.startswith("FOR "):
                            depth += 1
                        if "END LOOP;" in up:
                            depth -= 1
                            buffer_lines.append(nxt)
                            i += 1
                            if depth == 0:
                                break
                            continue
                        buffer_lines.append(nxt)
                        i += 1
                    else:
                        # Include nested objects as part of loop body verbatim
                        buffer_lines.append(nxt)
                        i += 1
                # Build header text to extract loop signature
                # Extract header to parse loop variable and cursor query
                header_text = ""
                for part in buffer_lines:
                    if isinstance(part, str):
                        header_text += part + "\n"
                        if re.search(r"\bLOOP\b", part, re.IGNORECASE):
                            break
                var_name = None
                cursor_query = None
                m = re.search(
                    r"FOR\s+([A-Za-z0-9_]+)\s+IN\s*\((.*?)\)\s*LOOP",
                    header_text,
                    re.IGNORECASE | re.DOTALL,
                )
                if m:
                    var_name = m.group(1).strip()
                    cursor_query = " ".join(
                        line.strip() for line in m.group(2).splitlines()
                    )
                # Extract loop body elements (strings and dicts) between first LOOP and matching END LOOP;
                body_elems = []
                in_body = False
                depth2 = 0
                for part in buffer_lines:
                    if isinstance(part, str):
                        up = part.upper()
                        if not in_body and "LOOP" in up:
                            in_body = True
                            depth2 = 1
                            continue
                        if in_body:
                            if up.strip().startswith("FOR "):
                                depth2 += 1
                            if "END LOOP;" in up:
                                depth2 -= 1
                                if depth2 == 0:
                                    break
                                else:
                                    body_elems.append(part)
                            else:
                                body_elems.append(part)
                    else:
                        if in_body:
                            body_elems.append(part)
                # Run grouping pipeline on loop body to get a list
                grouped_body = self._group_sql_statements(
                    self._group_assignment_statements(
                        self._group_for_loops(
                            self._group_case_statements(
                                self._group_if_else_statements(body_elems)
                            )
                        )
                    )
                )
                # Store the original SQL
                original_sql = "\n".join(str(line) for line in buffer_lines if isinstance(line, str))
                
                grouped.append(
                    {
                        "type": "for_loop",
                        "loop_variable": var_name,
                        "loop_body": grouped_body,
                        "cursor_query": cursor_query,
                        "o_sql": original_sql  # Add the original SQL
                    }
                )
                debug(f"Grouped FOR loop var={var_name}, body_len={len(grouped_body)}")
            else:
                grouped.append(el)
                i += 1
        return grouped

    def _group_case_statements(self, elements):
        # Group CASE ... END CASE; into structured objects with when_clauses
        def recurse(elems):
            return self._group_sql_statements(
                self._group_assignment_statements(
                    self._group_for_loops(
                        self._group_case_statements(
                            self._group_if_else_statements(elems)
                        )
                    )
                )
            )

        grouped = []
        i = 0
        while i < len(elements):
            el = elements[i]
            # Recurse into containers
            if isinstance(el, dict) and el.get("type") == "begin_block":
                el["sqls"] = self._group_case_statements(el.get("sqls", []))
                grouped.append(el)
                i += 1
                continue
            if isinstance(el, dict) and el.get("type") == "if_else":
                el["then_sql"] = self._group_case_statements(el.get("then_sql", []))
                if "else_statement" in el and isinstance(el["else_statement"], list):
                    el["else_statement"] = self._group_case_statements(
                        el["else_statement"]
                    )
                chain = el.get("else_if_statement")
                while isinstance(chain, dict):
                    if "then_sql" in chain:
                        chain["then_sql"] = self._group_case_statements(
                            chain["then_sql"]
                        )
                    chain = chain.get("else_if_statement")
                grouped.append(el)
                i += 1
                continue
            if isinstance(el, dict):
                grouped.append(el)
                i += 1
                continue
            # Handle strings
            if isinstance(el, str) and el.strip().upper().startswith("CASE"):
                buffer = [el]
                i += 1
                depth = 1
                while i < len(elements) and depth > 0:
                    part = elements[i]
                    if isinstance(part, str):
                        up = part.strip().upper()
                        if up.startswith("CASE"):
                            depth += 1
                        if "END CASE;" in up:
                            depth -= 1
                            buffer.append(part)
                            i += 1
                            if depth == 0:
                                break
                            continue
                        buffer.append(part)
                        i += 1
                    else:
                        buffer.append(part)
                        i += 1
                # Build flat sql
                flat_pieces = []
                for p in buffer:
                    if isinstance(p, str):
                        flat_pieces.append(p.strip())
                    # elif isinstance(p, dict) and p.get("type") == "comment":
                    #     flat_pieces.append(p.get("sql", ""))
                sql_flat = " ".join(piece for piece in flat_pieces if piece)
                # Extract case_expression up to first WHEN
                header_text = ""
                case_expression = ""
                for p in buffer:
                    if isinstance(p, str):
                        header_text += p + "\n"
                        if re.search(r"\bWHEN\b", p, re.IGNORECASE):
                            break
                header_upper = header_text.upper()
                if header_upper.startswith("CASE"):
                    after_case = header_text[4:]
                    m_when = re.search(r"\bWHEN\b", after_case, re.IGNORECASE)
                    case_expression = (
                        after_case[: m_when.start()].strip()
                        if m_when
                        else after_case.strip()
                    )
                # Parse WHEN clauses into arrays
                # Work on a linearized sequence marking strings for depth detection
                inner_elems = []
                # skip first header until first WHEN
                seen_first_when = False
                for p in buffer:
                    if isinstance(p, str):
                        if not seen_first_when:
                            if re.search(r"\bWHEN\b", p, re.IGNORECASE):
                                seen_first_when = True
                                inner_elems.append(p)
                            continue
                        inner_elems.append(p)
                    else:
                        if seen_first_when:
                            inner_elems.append(p)
                when_clauses = []
                idx = 0
                nested_case_depth = 0
                else_array = None
                while idx < len(inner_elems):
                    item = inner_elems[idx]
                    if isinstance(item, str):
                        up = item.strip().upper()
                        if up.startswith("CASE"):
                            nested_case_depth += 1
                            idx += 1
                            continue
                        if "END CASE;" in up and nested_case_depth > 0:
                            nested_case_depth -= 1
                            idx += 1
                            continue
                        if up.startswith("WHEN ") and nested_case_depth == 0:
                            # parse condition up to THEN
                            cond_parts = []
                            line = item
                            upline = up
                            if "THEN" in upline:
                                cond_parts.append(
                                    line[: upline.find("THEN")].strip()[4:].strip()
                                )
                                idx += 1
                            else:
                                cond_parts.append(line.strip()[4:].strip())
                                idx += 1
                                while idx < len(inner_elems):
                                    nxt = inner_elems[idx]
                                    if isinstance(nxt, str):
                                        upn = nxt.upper()
                                        if "THEN" in upn:
                                            cond_parts.append(
                                                nxt[: upn.find("THEN")].strip()
                                            )
                                            idx += 1
                                            break
                                        else:
                                            cond_parts.append(nxt.strip())
                                            idx += 1
                                            continue
                                    else:
                                        # stop if non-string encountered before THEN
                                        break
                            # collect then body until next WHEN/ELSE/END CASE at depth 0
                            then_body = []
                            while idx < len(inner_elems):
                                nxt = inner_elems[idx]
                                if isinstance(nxt, str):
                                    upn = nxt.strip().upper()
                                    if upn.startswith("CASE"):
                                        nested_case_depth += 1
                                    if "END CASE;" in upn and nested_case_depth > 0:
                                        nested_case_depth -= 1
                                        then_body.append(nxt)
                                        idx += 1
                                        continue
                                    if (
                                        upn.startswith("WHEN ")
                                        or upn.startswith("ELSE")
                                        or "END CASE;" in upn
                                    ) and nested_case_depth == 0:
                                        break
                                    then_body.append(nxt)
                                    idx += 1
                                else:
                                    then_body.append(nxt)
                                    idx += 1
                            when_clauses.append(
                                {
                                    "when_value": " ".join(p for p in cond_parts if p),
                                    "then_statement": recurse(then_body),
                                    "else_statement": None,
                                }
                            )
                            continue
                        if up.startswith("ELSE") and nested_case_depth == 0:
                            # collect else body until END CASE;
                            idx += 1
                            body = []
                            while idx < len(inner_elems):
                                nxt = inner_elems[idx]
                                if isinstance(nxt, str):
                                    upn = nxt.strip().upper()
                                    if upn.startswith("CASE"):
                                        nested_case_depth += 1
                                    if "END CASE;" in upn and nested_case_depth == 0:
                                        break
                                    if "END CASE;" in upn and nested_case_depth > 0:
                                        nested_case_depth -= 1
                                        body.append(nxt)
                                        idx += 1
                                        continue
                                    body.append(nxt)
                                    idx += 1
                                else:
                                    body.append(nxt)
                                    idx += 1
                            else_array = recurse(body)
                            # move past potential END CASE; if next is string containing it
                            if (
                                idx < len(inner_elems)
                                and isinstance(inner_elems[idx], str)
                                and "END CASE;" in inner_elems[idx].upper()
                            ):
                                idx += 1
                            break
                    idx += 1
                if else_array and when_clauses:
                    when_clauses[-1]["else_statement"] = else_array
                # Store the original SQL
                original_sql = "\n".join(str(line) for line in buffer if isinstance(line, str))
                
                grouped.append(
                    {
                        "type": "case_when_statements",
                        "case_expression": " ".join(case_expression.split()),
                        "when_clauses": when_clauses,
                        "o_sql": original_sql  # Add the original SQL
                    }
                )
                debug(f"Grouped CASE with {len(when_clauses)} WHEN clause(s)")
            else:
                grouped.append(el)
                i += 1
        return grouped



    def to_json(self):
        # If rule violations exist, return them instead of attempting conversion
        if self.rule_errors:
            debug(f"Rule violations detected: {len(self.rule_errors)} error(s)")
            return {"error": self.rule_errors}

        main_blocks = self._parse_begin_blocks()
        result = {
            "declarations": {
                "variables": self.variables,
                "constants": self.constants,
                "exceptions": self.exceptions,
            },
            "main": main_blocks,
            "sql_comments": self.sql_comments,
        }
        debug(
            "JSON ready: vars=%d, consts=%d, excs=%d, main_blocks=%d, comments=%d"
            % (
                len(self.variables),
                len(self.constants),
                len(self.exceptions),
                len(main_blocks),
                len(self.sql_comments),
            )
        )
        return result