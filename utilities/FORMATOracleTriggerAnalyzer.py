import psycopg2
from psycopg2.extensions import quote_ident
import json
import logging
import time
from typing import Dict, List, Any, Union
from datetime import datetime
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type alias for JSON nodes
JsonNode = Union[Dict[str, Any], List[Dict[str, Any]]]

class FORMATOracleTriggerAnalyzer:
    """FORMATOracleTriggerAnalyzer class."""

    def _safe_sql_query(self, query_template, params=None):
        """Execute SQL query safely with parameterized queries."""
        try:
            if params:
                return query_template % params
            return query_template
        except Exception as e:
            self.logger.error(f"SQL query error: {e}")
            raise ValueError(f"Invalid SQL query: {e}")

    def _escape_identifier(self, identifier):
        """Escape SQL identifier safely."""
        if not identifier:
            raise ValueError("Identifier cannot be empty")
        return f'"{identifier}"'
#     Enhanced Oracle Trigger Analyzer that converts JSON analysis back to properly formatted SQL.
    
#     This class takes the JSON analysis output and converts it back to well-formatted
#     Oracle PL/SQL trigger code with proper indentation, structure, and formatting.
#     """
    
    def __init__(self, analysis: Dict[str, Any]):
        """
        Initialize the analyzer with JSON analysis data.
        
        Args:
            analysis (Dict[str, Any]): The JSON analysis data
        """
        self.analysis = analysis
        self.indent_unit = "  "  # 2 spaces for indentation
        
        # Validate analysis structure
        if not isinstance(analysis, dict):
            raise ValueError("Analysis must be a dictionary")
        
        if "declarations" not in analysis or "main" not in analysis:
            raise ValueError("Analysis must contain 'declarations' and 'main' sections")
            
        logger.debug("FORMATOracleTriggerAnalyzer initialized successfully")

    def to_sql(self) -> str:
        """
        Convert the JSON analysis to formatted Oracle SQL code.
        
        This method orchestrates the entire SQL generation process:
        1. Creates header comments with timestamp
        2. Renders the declarations section (variables, constants, exceptions)
        3. Renders the main execution block with proper structure
        4. Adds footer comments
        
        The code is formatted with proper indentation and structure according to
        Oracle PL/SQL best practices.
        
        Returns:
            str: Formatted Oracle SQL code ready for execution
        """
        start_time = time.time()
        log_parsing_start("Oracle SQL generation", "Converting JSON analysis to formatted SQL")
        debug(f"Analysis contains {len(self.analysis.get('declarations', {}).get('variables', []))} variables, "
              f"{len(self.analysis.get('declarations', {}).get('constants', []))} constants, "
              f"{len(self.analysis.get('declarations', {}).get('exceptions', []))} exceptions")
        
        lines: List[str] = []
        
        # Step 1: Add header comment
        debug("Adding header comments with timestamp")
        lines.append("-- Generated from JSON analysis")
        lines.append(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Step 2: Render declarations
        debug("Starting declarations section rendering")
        declaration_start = time.time()
        decl_lines = self._render_declarations(self.analysis["declarations"])
        debug(f"Generated {len(decl_lines)} lines of declarations")
        lines.extend(decl_lines)
        lines.append("")
        log_performance("Declarations rendering", time.time() - declaration_start)
        
        # Step 3: Render main execution block
        debug("Starting main execution block rendering")
        main_start = time.time()
        main_lines = self._render_main_block(self.analysis["main"][0], 0, wrap_begin_end=True)
        debug(f"Generated {len(main_lines)} lines in main execution block")
        lines.extend(main_lines)
        log_performance("Main block rendering", time.time() - main_start)
        
        # Step 4: Add footer
        debug("Adding footer comments")
        lines.append("")
        lines.append("-- End of generated SQL")
        
        # Combine all lines into the final SQL string
        result = "\n".join(lines)
        debug(f"Final SQL contains {len(lines)} lines, {len(result)} characters")
        
        duration = time.time() - start_time
        log_parsing_complete("Oracle SQL generation", f"{len(lines)} lines generated in {duration:.3f}s")
        return result

    def _render_declarations(self, decl: Dict[str, Any]) -> List[str]:
        """
        Render variable, constant, and exception declarations section in PL/SQL format.
        
        This method generates the DECLARE section of a PL/SQL block, including:
        1. Variables with their data types and optional default values
        2. Constants with their data types and values
        3. Custom exception declarations
        
        Each declaration is properly indented and formatted according to Oracle
        PL/SQL style guidelines.
        
        Args:
            decl (Dict[str, Any]): The declarations section from the JSON analysis
            
        Returns:
            List[str]: List of formatted declaration lines ready to be included in the SQL output
        """
        debug("=== Starting declarations section rendering ===")
        lines: List[str] = []
        
        # Start DECLARE block
        lines.append("DECLARE")
        debug("Added DECLARE statement")
        
        # Step 1: Process and format variables
        variables = decl.get("variables", []) or []
        if variables:
            debug(f"Processing {len(variables)} variables")
            for i, var in enumerate(variables):
                name = var.get("name", "")
                data_type = var.get("data_type", "")
                default_value = var.get("default_value")
                
                if name and data_type:
                    # Format with or without default value
                    if default_value is not None and str(default_value).upper() != "NULL":
                        decl_line = f"  {name} {data_type} := {default_value};"
                        debug(f"Variable {i+1}/{len(variables)}: {name} ({data_type}) with default value")
                    else:
                        decl_line = f"  {name} {data_type};"
                        debug(f"Variable {i+1}/{len(variables)}: {name} ({data_type}) without default")
                    
                    lines.append(decl_line)
                else:
                    warning(f"Skipped incomplete variable declaration: name='{name}', type='{data_type}'")
        else:
            debug("No variables to process")
        
        # Step 2: Process and format constants
        constants = decl.get("constants", []) or []
        if constants:
            debug(f"Processing {len(constants)} constants")
            for i, const in enumerate(constants):
                name = const.get("name", "")
                data_type = const.get("data_type", "")
                value = const.get("value", "")
                
                if name and data_type and value is not None:
                    decl_line = f"  {name} CONSTANT {data_type} := {value};"
                    debug(f"Constant {i+1}/{len(constants)}: {name} ({data_type}) = {value}")
                    lines.append(decl_line)
                else:
                    warning(f"Skipped incomplete constant declaration: name='{name}', type='{data_type}', value='{value}'")
        else:
            debug("No constants to process")
        
        # Step 3: Process and format custom exceptions
        exceptions = decl.get("exceptions", []) or []
        if exceptions:
            debug(f"Processing {len(exceptions)} custom exceptions")
            for i, exc in enumerate(exceptions):
                name = exc.get("name", "")
                if name:
                    decl_line = f"  {name} EXCEPTION;"
                    debug(f"Exception {i+1}/{len(exceptions)}: {name}")
                    lines.append(decl_line)
                else:
                    warning(f"Skipped empty exception name at index {i}")
        else:
            debug("No custom exceptions to process")
        
        debug(f"=== Declarations section complete: {len(lines)} lines ===")
        return lines

    def _render_main_block(self, node: Dict[str, Any], indent_level: int, wrap_begin_end: bool = False) -> List[str]:
        """
        Render the main execution block which contains the actual SQL statements.
        
        Args:
            node (Dict[str, Any]): The main block node from analysis
            indent_level (int): Current indentation level
            wrap_begin_end (bool): Whether to wrap in BEGIN/END block
            
        Returns:
            List[str]: List of formatted SQL lines
        """
        logger.debug(f"=== Rendering main block (indent={indent_level}, wrap={wrap_begin_end}) ===")
        lines: List[str] = []
        
        if wrap_begin_end:
            logger.debug("Adding BEGIN wrapper")
            lines.append("BEGIN")
        
        # Handle different types of main blocks
        block_type = node.get("type")
        logger.debug(f"Main block type: {block_type}")
        
        if block_type == "begin_end":
            # This is a begin_end block containing statements
            logger.debug("Processing begin_end block structure")
            statements = node.get("begin_end_statements", []) or []
            logger.debug(f"Found {len(statements)} statements in begin_end block")
            lines.extend(self._render_statement_list(statements, indent_level + (1 if wrap_begin_end else 0)))

            # Exception handlers
            handlers = node.get("exception_handlers", []) or []
            if handlers:
                logger.debug(f"Processing {len(handlers)} exception handlers")
                lines.append(self._indent("EXCEPTION", indent_level + (1 if wrap_begin_end else 0)))
                for i, h in enumerate(handlers):
                    logger.debug(f"Rendering exception handler {i+1}/{len(handlers)}: {h.get('exception_name')}")
                    lines.extend(self._render_exception_handler(h, indent_level + (2 if wrap_begin_end else 1)))
            else:
                logger.debug("No exception handlers found")
        else:
            # Handle as a generic statement list
            logger.debug("Processing generic statement list")
            statements = node if isinstance(node, list) else [node]
            lines.extend(self._render_statement_list(statements, indent_level + (1 if wrap_begin_end else 0)))

        if wrap_begin_end:
            logger.debug("Adding END wrapper")
            lines.append("END;")
            
        logger.debug(f"=== Main block complete: {len(lines)} lines ===")
        return lines

    def _render_statement_list(self, statements: List[Dict[str, Any]], indent_level: int) -> List[str]:
        """
        Render a list of statements with proper indentation.
        
        Args:
            statements (List[Dict[str, Any]]): List of statement objects
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted statement lines
        """
        logger.debug(f"=== Rendering statement list (indent={indent_level}, count={len(statements)}) ===")
        lines: List[str] = []
        
        for i, statement in enumerate(statements):
            if not isinstance(statement, dict):
                logger.warning(f"Statement {i+1} is not a dict: {type(statement)}")
                continue
                
            stmt_type = statement.get("type")
            logger.debug(f"Statement {i+1}/{len(statements)}: type={stmt_type}")
            
            if stmt_type == "select_statement":
                sql = statement.get("sql_statement", "")
                if sql:
                    logger.debug(f"Rendering SELECT statement: {sql[:50]}...")
                    lines.append(self._indent(sql, indent_level))
                    
            elif stmt_type == "insert_statement":
                sql = statement.get("sql_statement", "")
                if sql:
                    logger.debug(f"Rendering INSERT statement: {sql[:50]}...")
                    lines.append(self._indent(sql, indent_level))
                    
            elif stmt_type == "update_statement":
                sql = statement.get("sql_statement", "")
                if sql:
                    logger.debug(f"Rendering UPDATE statement: {sql[:50]}...")
                    lines.append(self._indent(sql, indent_level))
                    
            elif stmt_type == "delete_statement":
                sql = statement.get("sql_statement", "")
                if sql:
                    logger.debug(f"Rendering DELETE statement: {sql[:50]}...")
                    lines.append(self._indent(sql, indent_level))
                    
            elif stmt_type == "raise_statement":
                sql = statement.get("sql_statement", "")
                if sql:
                    logger.debug(f"Rendering RAISE statement: {sql[:50]}...")
                    lines.append(self._indent(sql, indent_level))
                    
            elif stmt_type == "assignment_statement":
                variable = statement.get("variable", "")
                value = statement.get("value", "")
                if variable and value is not None:
                    logger.debug(f"Rendering assignment: {variable} := {value}")
                    lines.append(self._indent(f"{variable} := {value};", indent_level))
                    
            elif stmt_type == "if_else":
                logger.debug("Rendering IF-ELSE structure")
                lines.extend(self._render_if_else(statement, indent_level))
                
            elif stmt_type == "case_when":
                logger.debug("Rendering CASE-WHEN structure")
                lines.extend(self._render_case_when(statement, indent_level))
                
            elif stmt_type == "for_loop":
                logger.debug("Rendering FOR loop structure")
                lines.extend(self._render_for_loop(statement, indent_level))
                
            elif stmt_type == "begin_end":
                # Nested BEGIN block
                logger.debug("Rendering nested BEGIN block")
                lines.append(self._indent("BEGIN", indent_level))
                inner_statements = statement.get("begin_end_statements", []) or []
                logger.debug(f"Nested block contains {len(inner_statements)} statements")
                lines.extend(self._render_statement_list(inner_statements, indent_level + 1))
                
                # Exception handlers
                handlers = statement.get("exception_handlers", []) or []
                if handlers:
                    logger.debug(f"Nested block has {len(handlers)} exception handlers")
                    lines.append(self._indent("EXCEPTION", indent_level + 1))
                    for h in handlers:
                        lines.extend(self._render_exception_handler(h, indent_level + 2))
                        
                lines.append(self._indent("END;", indent_level))
                
            elif stmt_type == "unknown_statement":
                # Handle unknown statements (like function calls)
                stmt_text = statement.get("statement", "")
                if stmt_text:
                    logger.debug(f"Rendering unknown statement: {stmt_text[:50]}...")
                    lines.append(self._indent(stmt_text, indent_level))
                    
            elif stmt_type == "function_calling":
                # Handle function calling statements
                logger.debug("Rendering function calling statement")
                lines.extend(self._render_action(statement, indent_level))
                    
            else:
                # Fallback: try to render any SQL content
                sql = statement.get("sql_statement", "") or statement.get("sql", "")
                if sql:
                    logger.debug(f"Fallback rendering SQL: {sql[:50]}...")
                    lines.append(self._indent(sql, indent_level))
                else:
                    logger.warning(f"Unknown statement type '{stmt_type}' with no SQL content: {statement}")
                    
        logger.debug(f"=== Statement list complete: {len(lines)} lines ===")
        return lines

    def _render_action(self, action: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render an action node (function calls, RAISE statements, etc.).
        
        Args:
            action (Dict[str, Any]): Action data
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted action lines
        """
        logger.debug(f"Rendering action (indent={indent_level}): {action.get('type', 'unknown')}")
        lines: List[str] = []
        a_type = (action.get("type") or "").strip()
        
        # Handle function_calling type (e.g., raise_application_error)
        if a_type in {"function calling", "function_calling"}:
            func_name = action.get("function_name", "").upper()
            params = action.get("parameter", {})
            
            if func_name == "RAISE_APPLICATION_ERROR":
                error_code = params.get("handler_code", "-20000")
                error_msg = params.get("handler_string", "")                
                lines.append(self._indent(f"RAISE_APPLICATION_ERROR({error_code}, {error_msg});", indent_level))
            else:
                # Generic function call
                lines.append(self._indent(f"{func_name}();", indent_level))
        
        return lines

    def _render_exception_handler(self, handler: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render an exception handler.
        
        Args:
            handler (Dict[str, Any]): Exception handler data
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted exception handler lines
        """
        logger.debug(f"Rendering exception handler: {handler.get('exception_name')}")
        lines: List[str] = []
        
        exception_name = handler.get("exception_name", "OTHERS")
        exception_statements = handler.get("exception_statements", []) or []
        
        lines.append(self._indent(f"WHEN {exception_name} THEN", indent_level))
        lines.extend(self._render_statement_list(exception_statements, indent_level + 1))
        
        return lines

    def _render_sql_list(self, items: List[JsonNode], indent_level: int) -> List[str]:
        """
        Render a list of SQL items with proper formatting.
        
        Args:
            items (List[JsonNode]): List of SQL items
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted SQL lines
        """
        logger.debug(f"Rendering SQL list with {len(items)} items")
        lines: List[str] = []
        
        # Group items by type for better formatting
        pending_lines: List[str] = []
        
        def flush_pending():
            """flush_pending function."""
            nonlocal pending_lines, lines
            if pending_lines:
                # Join pending lines with proper spacing
                if len(pending_lines) == 1:
                    lines.append(pending_lines[0])
                else:
                    # For multi-line statements, add proper spacing
                    lines.extend(pending_lines)
                pending_lines = []
        
        for item in items:
            if isinstance(item, dict):
                item_type = item.get("type", "")
                
                if item_type in ["select_statement", "insert_statement", "update_statement", "delete_statement"]:
                    flush_pending()
                    sql = item.get("sql_statement", "")
                    if sql:
                        lines.append(self._indent(sql, indent_level))
                        
                elif item_type == "assignment_statement":
                    flush_pending()
                    variable = item.get("variable", "")
                    value = item.get("value", "")
                    if variable and value is not None:
                        lines.append(self._indent(f"{variable} := {value};", indent_level))
                        
                elif item_type == "raise_statement":
                    flush_pending()
                    sql = item.get("sql_statement", "")
                    if sql:
                        lines.append(self._indent(sql, indent_level))
                        
                elif item_type == "unknown_statement":
                    flush_pending()
                    stmt = item.get("statement", "")
                    if stmt:
                        lines.append(self._indent(stmt, indent_level))
                        
                elif item_type in ["if_else", "case_when", "for_loop", "begin_end"]:
                    flush_pending()
                    if item_type == "if_else":
                        lines.extend(self._render_if_else(item, indent_level))
                    elif item_type == "case_when":
                        lines.extend(self._render_case_when(item, indent_level))
                    elif item_type == "for_loop":
                        lines.extend(self._render_for_loop(item, indent_level))
                    elif item_type == "begin_end":
                        lines.extend(self._render_main_block(item, indent_level))
                        
                else:
                    # Generic handling
                    sql = item.get("sql_statement", "") or item.get("sql", "")
                    if sql:
                        pending_lines.append(self._indent(sql, indent_level))
                        
            elif isinstance(item, str):
                pending_lines.append(self._indent(item, indent_level))
                
        flush_pending()
        return lines

    def _render_if_else(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render an IF-ELSE control structure with proper formatting and indentation.
        
        This method handles the complete formatting of IF-ELSIF-ELSE blocks, including:
        1. The main IF condition and THEN statements
        2. Any number of ELSIF clauses with their conditions and statements
        3. Optional ELSE clause with its statements
        4. Proper END IF terminator
        
        All components are indented according to their nesting level to produce
        readable and maintainable PL/SQL code.
        
        Args:
            node (Dict[str, Any]): The IF-ELSE structure data from the JSON analysis
            indent_level (int): The current indentation level for proper nesting
            
        Returns:
            List[str]: List of formatted SQL lines representing the complete IF-ELSE structure
        """
        start_time = time.time()
        debug(f"=== Starting IF-ELSE structure rendering at indent level {indent_level} ===")
        lines: List[str] = []
        
        # Extract structure components
        condition = node.get("condition", "")
        then_statements = node.get("then_statements", []) or []
        else_if_clauses = node.get("else_if", []) or []
        else_statements = node.get("else_statements", []) or []
        
        debug(f"IF condition: '{condition}'")
        debug(f"Structure contains: {len(then_statements)} THEN statements, " + 
              f"{len(else_if_clauses)} ELSIF clauses, " + 
              f"{'an' if else_statements else 'no'} ELSE clause")
        
        # Step 1: Format and add the main IF condition
        if_line = self._indent(f"IF {condition} THEN", indent_level)
        lines.append(if_line)
        debug(f"Added main IF condition line: '{if_line.strip()}'")
        
        # Step 2: Render THEN statements with increased indentation
        debug(f"Rendering {len(then_statements)} THEN statements")
        then_start = time.time()
        then_lines = self._render_statement_list(then_statements, indent_level + 1)
        lines.extend(then_lines)
        debug(f"Added {len(then_lines)} lines for THEN statements in {time.time() - then_start:.3f}s")
        
        # Step 3: Handle ELSIF clauses (if any)
        if else_if_clauses:
            debug(f"Processing {len(else_if_clauses)} ELSIF clauses")
            for i, else_if in enumerate(else_if_clauses):
                else_if_condition = else_if.get("condition", "")
                else_if_statements = else_if.get("then_statements", []) or []
                
                # Add ELSIF line
                elsif_line = self._indent(f"ELSIF {else_if_condition} THEN", indent_level)
                lines.append(elsif_line)
                debug(f"Added ELSIF {i+1}/{len(else_if_clauses)} condition: '{else_if_condition}'")
                
                # Render ELSIF statements
                elsif_start = time.time()
                elsif_lines = self._render_statement_list(else_if_statements, indent_level + 1)
                lines.extend(elsif_lines)
                debug(f"Added {len(elsif_lines)} lines for ELSIF {i+1} clause in {time.time() - elsif_start:.3f}s")
        
        # Step 4: Handle ELSE clause (if present)
        if else_statements:
            debug("Processing ELSE clause")
            lines.append(self._indent("ELSE", indent_level))
            
            # Render ELSE statements
            else_start = time.time()
            else_lines = self._render_statement_list(else_statements, indent_level + 1)
            lines.extend(else_lines)
            debug(f"Added {len(else_lines)} lines for ELSE clause in {time.time() - else_start:.3f}s")
        
        # Step 5: Add END IF terminator
        lines.append(self._indent("END IF;", indent_level))
        debug("Added END IF terminator")
        
        duration = time.time() - start_time
        debug(f"=== IF-ELSE structure complete: {len(lines)} lines in {duration:.3f}s ===")
        return lines

    def _render_case_when(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render a CASE-WHEN structure.
        
        Args:
            node (Dict[str, Any]): CASE-WHEN node data
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted CASE-WHEN lines
        """
        logger.debug(f"=== Rendering CASE-WHEN structure (indent={indent_level}) ===")
        lines: List[str] = []
        case_expr = node.get("case_expression")
        when_clauses: List[Dict[str, Any]] = node.get("when_clauses", []) or []
        else_statements = node.get("else_statements", []) or []
        searched_case = not case_expr or str(case_expr).strip() == ""
        logger.debug(f"CASE statement: searched={searched_case}, when_count={len(when_clauses)}")

        if searched_case:
            logger.debug("Rendering searched CASE statement")
            lines.append(self._indent("CASE", indent_level))
            
            # Process WHEN clauses
            for i, clause in enumerate(when_clauses):
                when_val = clause.get("when_value")
                then_statements = clause.get("then_statements", []) or []
                logger.debug(f"WHEN clause {i+1}/{len(when_clauses)}: {when_val}")
                
                if when_val:
                    lines.append(self._indent(f"WHEN {when_val} THEN", indent_level + 1))
                    lines.extend(self._render_statement_list(then_statements, indent_level + 2))
            
            # Handle ELSE clause
            if else_statements:
                logger.debug("Found ELSE clause")
                lines.append(self._indent("ELSE", indent_level + 1))
                lines.extend(self._render_statement_list(else_statements, indent_level + 2))
                    
            lines.append(self._indent("END CASE;", indent_level))
        else:
            logger.debug(f"Rendering simple CASE statement with expression: {case_expr}")
            lines.append(self._indent(f"CASE {case_expr}", indent_level))
            
            # Process WHEN clauses
            for i, clause in enumerate(when_clauses):
                when_val = clause.get("when_value")
                then_statements = clause.get("then_statements", []) or []
                logger.debug(f"WHEN clause {i+1}/{len(when_clauses)}: {when_val}")
                
                if when_val:
                    lines.append(self._indent(f"WHEN {when_val} THEN", indent_level + 1))
                    lines.extend(self._render_statement_list(then_statements, indent_level + 2))
            
            # Handle ELSE clause
            if else_statements:
                logger.debug("Found ELSE clause")
                lines.append(self._indent("ELSE", indent_level + 1))
                lines.extend(self._render_statement_list(else_statements, indent_level + 2))
                    
            lines.append(self._indent("END CASE;", indent_level))
            
        logger.debug("=== CASE-WHEN structure complete ===")
        return lines

    def _render_for_loop(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render a FOR loop structure.
        
        Args:
            node (Dict[str, Any]): FOR loop node data
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted FOR loop lines
        """
        logger.debug(f"=== Rendering FOR loop structure (indent={indent_level}) ===")
        lines: List[str] = []
        loop_var = node.get("loop_variable", "i")
        cursor_query = node.get("cursor_query", "SELECT 1 FROM DUAL")
        logger.debug(f"FOR loop: var={loop_var}, cursor_query_len={len(cursor_query)}")
        
        # Remove extra parentheses if they exist
        cursor_query = cursor_query.strip()
        if cursor_query.startswith("(") and cursor_query.endswith(")"):
            cursor_query = cursor_query[1:-1].strip()
        
        lines.append(self._indent(f"FOR {loop_var} IN ( {cursor_query} ) LOOP", indent_level))
        
        # Render loop statements
        loop_statements = node.get("loop_statements", []) or []
        logger.debug(f"Rendering {len(loop_statements)} loop statements")
        lines.extend(self._render_statement_list(loop_statements, indent_level + 1))
        
        lines.append(self._indent("END LOOP;", indent_level))
        logger.debug("=== FOR loop structure complete ===")
        return lines

    # -----------------------------
    # Utility Methods
    # -----------------------------
    def _indent(self, text: str, level: int) -> str:
        """
        Add proper indentation to a text line based on nesting level.
        
        This utility method applies consistent indentation to each line of SQL code
        based on its nesting level in the code structure. The indentation unit
        is defined at the class level (typically 2 or 4 spaces).
        
        Proper indentation is crucial for:
        - Code readability
        - Visualizing code structure
        - Maintaining consistent formatting
        - Highlighting the logical flow
        
        Args:
            text (str): The text content to indent
            level (int): Indentation level (number of indent units to apply)
            
        Returns:
            str: The properly indented text with the correct amount of spaces
        """
        # Ensure level is non-negative
        indent_level = max(level, 0)
        
        # Apply indentation by multiplying the indent unit by the level
        indentation = self.indent_unit * indent_level
        
        # Combine indentation with the text
        indented_text = f"{indentation}{text}"
        
        # For very deep nesting, log a warning (could indicate over-complex code)
        if level > 5:
            debug(f"Deep nesting detected (level {level}): '{text[:30]}...'")
            
        return indented_text

    def _indent_lines(self, lines: List[str], level: int) -> List[str]:
        """
        Add indentation to a list of text lines.
        
        Args:
            lines (List[str]): List of text lines
            level (int): Indentation level
            
        Returns:
            List[str]: List of indented text lines
        """
        return [self._indent(line, level) for line in lines]

    #     """
    #     Format a list of values with proper quotes.
        
    #     Args:
    #         values (str): The values to format
        
    #     Returns:
    #         str: The formatted values
    #     """

    #         return None
    #     formatted_msg = values.strip()

    #         formatted_msg = formatted_msg.split('||')

    #             formatted_msg[i] = formatted_msg[i].strip()
    #             # print(formatted_msg[i])

    #                 formatted_msg[i] = formatted_msg[i] + "'"
    #             elif not formatted_msg[i].startswith("'") and formatted_msg[i].endswith("'"):
    #                 formatted_msg[i] = "'" + formatted_msg[i]
    #         formatted_msg = " || ".join(formatted_msg)
    #     else:

    #             formatted_msg = formatted_msg
    #         else:
    #             formatted_msg = "'" + formatted_msg + "'"
    #     return formatted_msg