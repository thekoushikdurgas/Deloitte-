import psycopg2
from psycopg2.extensions import quote_ident
import json
import logging
import time
import re
import pandas as pd
import os
from typing import Dict, List, Any, Union
from datetime import datetime
from utilities.common import (
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type alias for JSON nodes
JsonNode = Union[Dict[str, Any], List[Dict[str, Any]]]

class FormatSQL:
    """
    Enhanced Oracle Trigger Analyzer that converts JSON analysis back to properly formatted SQL.
    
    This class takes the JSON analysis output from OracleTriggerAnalyzer and converts it back to 
    well-formatted Oracle PL/SQL trigger code with proper indentation, structure, and formatting.
    
    Key Features:
    - Comprehensive statement type support (IF-ELSE, CASE-WHEN, FOR loops, assignments, etc.)
    - Enhanced function calling with parameter handling
    - Robust error handling and validation
    - Performance monitoring and logging
    - Edge case handling for unknown statement types
    - Fallback mechanisms for backward compatibility
    - Support for both Oracle and PostgreSQL output formats
    - Excel-based type and function mappings
    
    Supported Statement Types:
    - select_statement, insert_statement, update_statement, delete_statement
    - assignment_statement (with variable_name/expression support)
    - raise_statement
    - if_else (with nested ELSIF support)
    - case_when (both simple and searched CASE)
    - for_loop
    - begin_end (nested blocks with exception handlers)
    - function_calling (with parameter parsing)
    - null_statement, return_statement, exit_statement
    - unknown_statement (fallback handling)
    
    JSON Structure Requirements:
    - Must contain 'declarations' and 'main' sections
    - Declarations: variables, constants, exceptions
    - Main: begin_end blocks with nested statements
    
    Performance Features:
    - Timing breakdown for slow operations
    - Detailed logging for debugging
    - Validation of JSON structure integrity
    
    """

    def __init__(self, analysis: Dict[str, Any]):
        """
        Initialize the analyzer with JSON analysis data.
        
        Args:
            analysis (Dict[str, Any]): The JSON analysis data
        """
        self.analysis = analysis
        self.indent_unit = "  "  # 2 spaces for indentation
        self.json_convert_sql: Dict = {
            "select_statement": 0,
            "insert_statement": 0,
            "update_statement": 0,
            "delete_statement": 0,
            "raise_statement": 0,
            "assignment": 0,
            "for_loop": 0,
            "if_else": 0,
            "case_when": 0,
            "begin_end": 1,
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
        }
        
        # Load mappings from Excel file
        self.func_mapping = self.load_mapping("function_mappings")
        self.type_mapping = self.load_mapping("data_type_mappings")
        # self.exception_mapping = self.load_mapping("exception_mappings")
        
        # Validate analysis structure
        if not isinstance(analysis, dict):
            raise ValueError("Analysis must be a dictionary")
        
        if "declarations" not in analysis or "main" not in analysis:
            raise ValueError("Analysis must contain 'declarations' and 'main' sections")
            
        logger.debug("FORMATOracleTriggerAnalyzer initialized successfully")

    def load_mapping(self, sheet_name: str) -> Dict[str, str]:
        """
        Load mappings from Excel file for type, function, and exception conversions.
        
        This function reads the Excel file containing Oracle to PostgreSQL mappings
        and returns a dictionary for the specified sheet. If the Excel file is not
        found or cannot be read, it falls back to default mappings.
        
        Args:
            sheet_name (str): Name of the Excel sheet to load ("data_type_mappings", 
                            "function_mappings", or "exception_mappings")
            
        Returns:
            Dict[str, str]: Mapping dictionary with Oracle keys and PostgreSQL values
        """
        mapping_file = main_excel_file
        
        try:
            if os.path.exists(mapping_file):
                debug(f"Loading {sheet_name} from Excel file: {mapping_file}")
                df = pd.read_excel(mapping_file, sheet_name=sheet_name)
                
                # Convert DataFrame to dictionary
                if len(df.columns) >= 2:
                    # Try to use column names first, fall back to index-based access
                    if 'Oracle_Type' in df.columns and 'PostgreSQL_Type' in df.columns:
                        mapping_dict = dict(zip(df['Oracle_Type'], df['PostgreSQL_Type']))
                    else:
                        mapping_dict = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
                    
                    # Remove any None or NaN values
                    mapping_dict = {k: v for k, v in mapping_dict.items() if k is not None and v is not None and str(k).strip() and str(v).strip()}
                    
                    debug(f"Loaded {len(mapping_dict)} {sheet_name} mappings from Excel")
                    return mapping_dict
                else:
                    warning(f"Excel sheet {sheet_name} has insufficient columns, using defaults")
            else:
                warning(f"Excel mapping file not found: {mapping_file}, using defaults")
                
        except Exception as e:
            error(f"Error loading {sheet_name} from Excel: {str(e)}, using defaults")
        
        # Return default mappings if Excel loading fails
        return self._get_default_mappings(sheet_name)

    def _get_default_mappings(self, sheet_name: str) -> Dict[str, str]:
        """
        Get default mappings when Excel file is not available.
        
        Args:
            sheet_name (str): Type of mappings to return
            
        Returns:
            Dict[str, str]: Default mapping dictionary
        """
        if sheet_name == "data_type_mappings":
            return {
                "VARCHAR2": "VARCHAR",
                "NVARCHAR2": "VARCHAR",
                "CHAR": "CHAR",
                "NCHAR": "CHAR",
                "NUMBER": "NUMERIC",
                "FLOAT": "REAL",
                "BINARY_FLOAT": "REAL",
                "BINARY_DOUBLE": "DOUBLE PRECISION",
                "DATE": "TIMESTAMP",
                "TIMESTAMP": "TIMESTAMP",
                "CLOB": "TEXT",
                "NCLOB": "TEXT",
                "BLOB": "BYTEA",
                "RAW": "BYTEA",
                "LONG": "TEXT",
                "LONG RAW": "BYTEA",
                "BFILE": "TEXT",
                "BINARY_INTEGER": "INTEGER",
                "PLS_INTEGER": "INTEGER",
                "NATURAL": "INTEGER",
                "POSITIVE": "INTEGER",
                "SIGNTYPE": "SMALLINT",
                "BOOLEAN": "BOOLEAN"
            }
        elif sheet_name == "function_mappings":
            return {
                "SYSDATE": "CURRENT_TIMESTAMP",
                "SYSTIMESTAMP": "CURRENT_TIMESTAMP",
                "USER": "CURRENT_USER",
                "UID": "CURRENT_USER",
                "ROWNUM": "ROW_NUMBER() OVER()",
                "ROWID": "CTID",
                "NVL": "COALESCE",
                "NVL2": "CASE WHEN",
                "DECODE": "CASE",
                "TO_CHAR": "TO_CHAR",
                "TO_DATE": "TO_TIMESTAMP",
                "TO_NUMBER": "CAST",
                "SUBSTR": "SUBSTRING",
                "INSTR": "POSITION",
                "LENGTH": "LENGTH",
                "UPPER": "UPPER",
                "LOWER": "LOWER",
                "TRIM": "TRIM",
                "LTRIM": "LTRIM",
                "RTRIM": "RTRIM",
                "REPLACE": "REPLACE",
                "CONCAT": "||",
                "ROUND": "ROUND",
                "TRUNC": "TRUNC",
                "MOD": "MOD",
                "POWER": "POWER",
                "SQRT": "SQRT",
                "ABS": "ABS",
                "CEIL": "CEILING",
                "FLOOR": "FLOOR",
                "SIGN": "SIGN",
                "GREATEST": "GREATEST",
                "LEAST": "LEAST"
            }
        elif sheet_name == "exception_mappings":
            return {
                "NO_DATA_FOUND": "EXCEPTION WHEN NO_DATA_FOUND THEN",
                "TOO_MANY_ROWS": "EXCEPTION WHEN TOO_MANY_ROWS THEN",
                "DUP_VAL_ON_INDEX": "EXCEPTION WHEN UNIQUE_VIOLATION THEN",
                "INVALID_CURSOR": "EXCEPTION WHEN INVALID_CURSOR THEN",
                "CURSOR_ALREADY_OPEN": "EXCEPTION WHEN CURSOR_ALREADY_OPEN THEN",
                "INVALID_NUMBER": "EXCEPTION WHEN INVALID_NUMBER THEN",
                "VALUE_ERROR": "EXCEPTION WHEN VALUE_ERROR THEN",
                "ZERO_DIVIDE": "EXCEPTION WHEN ZERO_DIVIDE THEN",
                "STORAGE_ERROR": "EXCEPTION WHEN STORAGE_ERROR THEN",
                "PROGRAM_ERROR": "EXCEPTION WHEN PROGRAM_ERROR THEN",
                "OTHERS": "EXCEPTION WHEN OTHERS THEN"
            }
        else:
            warning(f"Unknown mapping type: {sheet_name}")
            return {}

    def to_sql(self, db_type: str = "Oracle") -> str:
        """
        Convert the JSON analysis to formatted SQL code for the specified database type.
        
        This method orchestrates the entire SQL generation process:
        1. Creates header comments with timestamp
        2. Renders the declarations section (variables, constants, exceptions)
        3. Renders the main execution block with proper structure
        4. Adds footer comments
        
        The code is formatted with proper indentation and structure according to
        the specified database type (Oracle or PostgreSQL).
        
        Args:
            db_type (str): Database type - "Oracle" or "PostgreSQL" (default: "Oracle")
            
        Returns:
            str: Formatted SQL code ready for execution
        """
        start_time = time.time()
        logger.debug(f"SQL generation: Converting JSON analysis to formatted {db_type} SQL")
        debug(f"Analysis contains {len(self.analysis.get('declarations', {}).get('variables', []))} variables, "
              f"{len(self.analysis.get('declarations', {}).get('constants', []))} constants, "
              f"{len(self.analysis.get('declarations', {}).get('exceptions', []))} exceptions")
        
        lines: List[str] = []
        
        # Step 1: Add header comment
        debug(f"Adding header comments with timestamp for {db_type}")
        lines.append(f"-- Generated from JSON analysis for {db_type}")
        lines.append(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Step 2: Render declarations
        debug("Starting declarations section rendering")
        declaration_start = time.time()
        decl_lines = self._render_declarations(self.analysis["declarations"], db_type)
        debug(f"Generated {len(decl_lines)} lines of declarations")
        lines.extend(decl_lines)
        debug(f"Declarations rendering took {time.time() - declaration_start:.3f}s")
        
        # Step 3: Render main execution block
        debug("Starting main execution block rendering")
        main_start = time.time()
        main_lines = self._render_main_block(self.analysis["main"], 0, wrap_begin_end=True, db_type=db_type)
        debug(f"Generated {len(main_lines)} lines in main execution block")
        lines.extend(main_lines)
        debug(f"Main block rendering took {time.time() - main_start:.3f}s")
        
        # Step 4: Add footer
        debug("Adding footer comments")
        lines.append("")
        lines.append(f"-- End of generated {db_type} SQL")
        
        # Combine all lines into the final SQL string
        result = "\n".join(lines)
        debug(f"Final SQL contains {len(lines)} lines, {len(result)} characters")
        if self.analysis['conversion_stats'] is None:
            print(f"sql_convert_count: {self.analysis['conversion_stats']}")
        final_sql = {
            "sql": result,
            "json_convert_sql": self.json_convert_sql
        }
        duration = time.time() - start_time
        debug(f"{db_type} SQL generation: {len(lines)} lines generated in {duration:.3f}s")
        return final_sql

    # -----------------------------
    # Declaration Rendering Methods
    # -----------------------------
    def _render_declarations(self, decl: Dict[str, Any], db_type: str) -> List[str]:
        """
        Render variable, constant, and exception declarations for the specified database type.
        
        Args:
            decl (Dict[str, Any]): Declarations section
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted declaration lines
        """
        logger.debug(f"=== Rendering {db_type} declarations ===")
        lines: List[str] = []
        
        if db_type == "Oracle":
            # Oracle uses DECLARE...BEGIN...END; structure
            lines.append("DECLARE")
            
            # Variables
            variables = decl.get("variables", []) or []
            if variables:
                logger.debug(f"Rendering {len(variables)} variables")
                for var in variables:
                    name = var.get("name", "")
                    data_type = var.get("data_type", "")
                    default_value = var.get("default_value")
                    
                    if name and data_type:
                        # Oracle variable declaration syntax
                        if default_value is not None and str(default_value).upper() != "NULL":
                            lines.append(f"   {name} {data_type} := {default_value};")
                        else:
                            lines.append(f"   {name} {data_type};")
            
            # Constants - Oracle uses CONSTANT keyword
            constants = decl.get("constants", []) or []
            if constants:
                logger.debug(f"Rendering {len(constants)} constants")
                for const in constants:
                    name = const.get("name", "")
                    data_type = const.get("data_type", "")
                    value = const.get("value", "")
                    
                    if name and data_type and value is not None:
                        lines.append(f"   {name} CONSTANT {data_type} := {value};")
            
            # Exceptions - Oracle exception declarations
            exceptions = decl.get("exceptions", []) or []
            if exceptions:
                logger.debug(f"Rendering {len(exceptions)} exceptions")
                for exc in exceptions:
                    name = exc.get("name", "")
                    if name:
                        lines.append(f"   {name} EXCEPTION;")
                        
        elif db_type == "PostgreSQL":
            # PostgreSQL uses DO $$ DECLARE...BEGIN...END $$; structure
            # Note: Variable declarations will be handled in the main block
            # This section is kept empty for PostgreSQL as declarations are handled differently
            pass
        
        logger.debug(f"=== {db_type} declarations complete ===")
        return lines

    # -----------------------------
    # Main Block Rendering Methods
    # -----------------------------
    def _render_main_block(self, node: Dict[str, Any], indent_level: int, wrap_begin_end: bool = False, db_type: str = "Oracle") -> List[str]:
        """
        Render the main execution block with proper database-specific structure.
        
        Args:
            node (Dict[str, Any]): Main block node
            indent_level (int): Current indentation level
            wrap_begin_end (bool): Whether to wrap in BEGIN-END
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted main block lines
        """
        logger.debug(f"=== Rendering main block for {db_type} ===")
        lines: List[str] = []
        
        # Handle PostgreSQL structure
        if db_type == "PostgreSQL" and wrap_begin_end:
            lines.append("DO $$")
            lines.append("DECLARE")
            # Add variable declarations for PostgreSQL
            variables = self.analysis.get("declarations", {}).get("variables", []) or []
            if variables:
                logger.debug(f"Rendering {len(variables)} variables for PostgreSQL")
                for var in variables:
                    name = var.get("name", "")
                    data_type = var.get("data_type", "")
                    default_value = var.get("default_value")
                    
                    if name and data_type:
                        # Apply type mapping for PostgreSQL (case-insensitive)
                        mapped_type = data_type
                        for oracle_type, postgres_type in self.type_mapping.items():
                            if oracle_type.upper() == data_type.upper():
                                mapped_type = postgres_type
                                break
                        
                        # PostgreSQL variable declaration syntax
                        if default_value is not None and str(default_value).upper() != "NULL":
                            # Handle string values properly
                            if isinstance(default_value, str):
                                default_str = f"'{default_value}'"
                            else:
                                default_str = str(default_value)
                            lines.append(f"   {name} {mapped_type} := {default_str};")
                        else:
                            lines.append(f"   {name} {mapped_type};")
            lines.append("BEGIN")
        elif wrap_begin_end:
            lines.append(self._indent("BEGIN", indent_level))
        
        # Process begin_end_statements
        statements = node.get("begin_end_statements", [])
        if statements:
            logger.debug(f"Processing {len(statements)} statements in main block")
            statement_lines = self._render_statement_list(statements, indent_level + 1, db_type)
            lines.extend(statement_lines)
        
        # Process exception handlers
        exception_handlers = node.get("exception_handlers", [])
        if exception_handlers:
            logger.debug(f"Processing {len(exception_handlers)} exception handlers")
            lines.append(self._indent("EXCEPTION", indent_level))
            for handler in exception_handlers:
                handler_lines = self._render_exception_handler(handler, indent_level + 1, db_type)
                lines.extend(handler_lines)
        
        if wrap_begin_end:
            if db_type == "PostgreSQL":
                lines.append("END;")
                lines.append("$$ LANGUAGE plpgsql;")
            else:
                lines.append(self._indent("END;", indent_level))
        
        logger.debug(f"=== Main block complete for {db_type} ===")
        return lines

    def _render_statement_list(self, statements: List[Dict[str, Any]], indent_level: int, db_type: str) -> List[str]:
        """
        Render a list of statements with proper indentation and database-specific formatting.
        
        Args:
            statements (List[Dict[str, Any]]): List of statement nodes
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted statement lines
        """
        lines: List[str] = []
        
        for statement in statements:
            # Handle case where statement might be a string instead of dict
            if isinstance(statement, str):
                logger.warning(f"Found string statement instead of dict: {statement[:50]}...")
                lines.append(self._indent(f"-- String statement: {statement}", indent_level))
                continue
            
            if not isinstance(statement, dict):
                logger.warning(f"Found non-dict statement: {type(statement)}")
                lines.append(self._indent(f"-- Non-dict statement: {statement}", indent_level))
                continue
            
            statement_type = statement.get("type", "")
            logger.debug(f"Rendering statement type: {statement_type}")
            if statement_type in self.json_convert_sql:
                self.json_convert_sql[statement_type] += 1
            
            try:
                if statement_type == "if_else":
                    statement_lines = self._render_if_else(statement, indent_level, db_type)
                elif statement_type == "case_when":
                    statement_lines = self._render_case_when(statement, indent_level, db_type)
                elif statement_type == "for_loop":
                    statement_lines = self._render_for_loop(statement, indent_level, db_type)
                elif statement_type == "begin_end":
                    statement_lines = self._render_begin_end_block(statement, indent_level, db_type)
                elif statement_type == "select_statement":
                    statement_lines = self._render_sql_statement(statement, indent_level, db_type)
                elif statement_type == "insert_statement":
                    statement_lines = self._render_sql_statement(statement, indent_level, db_type)
                elif statement_type == "update_statement":
                    statement_lines = self._render_sql_statement(statement, indent_level, db_type)
                elif statement_type == "delete_statement":
                    statement_lines = self._render_sql_statement(statement, indent_level, db_type)
                elif statement_type == "assignment":
                    statement_lines = self._render_assignment(statement, indent_level, db_type)
                elif statement_type == "raise_statement":
                    statement_lines = self._render_raise_statement(statement, indent_level, db_type)
                elif statement_type == "function_calling":
                    statement_lines = self._render_function_call(statement, indent_level, db_type)
                elif statement_type == "null_statement":
                    statement_lines = self._render_null_statement(statement, indent_level, db_type)
                elif statement_type == "return_statement":
                    # print(statement)
                    statement_lines = self._render_return_statement(statement, indent_level, db_type)
                else:
                    # Fallback for unknown statement types
                    # print(statement)
                    statement_lines = self._render_unknown_statement(statement, indent_level, db_type)
                
                lines.extend(statement_lines)
            except Exception as e:
                logger.error(f"Error rendering statement type '{statement_type}': {str(e)}")
                lines.append(self._indent(f"-- Error rendering statement: {str(e)}", indent_level))
        
        return lines

    # -----------------------------
    # Statement Rendering Methods
    # -----------------------------
    def _render_if_else(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render IF-ELSE statements with ELSIF support for the specified database type.
        
        Args:
            node (Dict[str, Any]): IF-ELSE node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted IF-ELSE lines
        """
        lines: List[str] = []
        
        # Main IF condition
        condition = node.get("condition", "")
        if db_type == "PostgreSQL":
            # Apply function mappings for PostgreSQL
            condition = self._apply_function_mappings(condition)
        
        lines.append(self._indent(f"IF {condition} THEN", indent_level))
        
        # THEN statements
        then_statements = node.get("then_statements", [])
        if then_statements:
            then_lines = self._render_statement_list(then_statements, indent_level + 1, db_type)
            lines.extend(then_lines)
        
        # ELSIF statements
        if_elses = node.get("if_elses", [])
        for elif_stmt in if_elses:
            elif_condition = elif_stmt.get("condition", "")
            if elif_condition:
                self.json_convert_sql['elif_statement'] += 1
            if db_type == "PostgreSQL":
                elif_condition = self._apply_function_mappings(elif_condition)
            
            lines.append(self._indent(f"ELSIF {elif_condition} THEN", indent_level))
            
            elif_then_statements = elif_stmt.get("then_statements", [])
            if elif_then_statements:
                elif_lines = self._render_statement_list(elif_then_statements, indent_level + 1, db_type)
                lines.extend(elif_lines)
        
        # ELSE statements
        else_statements = node.get("else_statements", [])
        if else_statements:
            lines.append(self._indent("ELSE", indent_level))
            else_lines = self._render_statement_list(else_statements, indent_level + 1, db_type)
            lines.extend(else_lines)
        
        lines.append(self._indent("END IF;", indent_level))
        return lines

    def _render_case_when(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render CASE-WHEN statements for the specified database type.
        
        Args:
            node (Dict[str, Any]): CASE-WHEN node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted CASE-WHEN lines
        """
        lines: List[str] = []
        
        condition = node.get("condition", "")
        if condition and db_type == "PostgreSQL":
            condition = self._apply_function_mappings(condition)
            
        if condition:
            lines.append(self._indent(f"CASE {condition}", indent_level))
        else:
            lines.append(self._indent("CASE", indent_level))
        
        # WHEN clauses
        when_clauses = node.get("when_clauses", [])
        for when_clause in when_clauses:
            when_condition = when_clause.get("condition", "")
            if db_type == "PostgreSQL":
                when_condition = self._apply_function_mappings(when_condition)
                
            lines.append(self._indent(f"WHEN {when_condition} THEN", indent_level))
            
            when_statements = when_clause.get("then_statements", [])
            if when_statements:
                self.json_convert_sql['when_statement'] += 1
            if when_statements:
                when_lines = self._render_statement_list(when_statements, indent_level + 1, db_type)
                lines.extend(when_lines)
        
        # ELSE statements
        else_statements = node.get("else_statements", [])
        if else_statements:
            lines.append(self._indent("ELSE", indent_level))
            else_lines = self._render_statement_list(else_statements, indent_level + 1, db_type)
            lines.extend(else_lines)
        
        lines.append(self._indent("END CASE;", indent_level))
        return lines

    def _render_for_loop(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render FOR loop statements for the specified database type.
        
        Args:
            node (Dict[str, Any]): FOR loop node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted FOR loop lines
        """
        lines: List[str] = []
        
        loop_variable = node.get("loop_variable", "")
        for_expression = node.get("for_expression", "")
        
        if db_type == "PostgreSQL":
            for_expression = self._apply_function_mappings(for_expression)
        
        lines.append(self._indent(f"FOR {loop_variable} IN {for_expression} LOOP", indent_level))
        
        # Loop statements
        for_statements = node.get("for_statements", [])
        if for_statements:
            for_lines = self._render_statement_list(for_statements, indent_level + 1, db_type)
            lines.extend(for_lines)
        
        lines.append(self._indent("END LOOP;", indent_level))
        return lines

    def _render_begin_end_block(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render nested BEGIN-END blocks for the specified database type.
        
        Args:
            node (Dict[str, Any]): BEGIN-END block node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted BEGIN-END block lines
        """
        return self._render_main_block(node, indent_level, wrap_begin_end=True, db_type=db_type)

    def _render_sql_statement(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render SQL statements (SELECT, INSERT, UPDATE, DELETE) for the specified database type.
        
        Args:
            node (Dict[str, Any]): SQL statement node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted SQL statement lines
        """
        sql_statement = node.get("sql_statement", "")
        if sql_statement:
            if db_type == "PostgreSQL":
                sql_statement = self._apply_function_mappings(sql_statement)
            return [self._indent(f"{sql_statement}", indent_level)]
        return []

    def _render_assignment(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render variable assignment statements for the specified database type.
        
        Args:
            node (Dict[str, Any]): Assignment node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted assignment lines
        """
        variable_name = node.get("variable_name", "")
        expression = node.get("expression", "")
        
        if variable_name and expression:
            # Remove trailing semicolon from expression if present
            if expression.endswith(';'):
                expression = expression[:-1]
            
            if db_type == "PostgreSQL":
                expression = self._apply_function_mappings(expression)
                
            return [self._indent(f"{variable_name} := {expression};", indent_level)]
        return []

    def _render_raise_statement(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render RAISE statements for the specified database type.
        
        Args:
            node (Dict[str, Any]): RAISE statement node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted RAISE statement lines
        """
        sql_statement = node.get("sql_statement", "")
        if sql_statement:
            if db_type == "PostgreSQL":
                sql_statement = self._apply_function_mappings(sql_statement)
            return [self._indent(f"{sql_statement}", indent_level)]
        return []

    def _render_function_call(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render function call statements for the specified database type.
        
        Args:
            node (Dict[str, Any]): Function call node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted function call lines
        """
        function_name = node.get("function_name", "")
        parameters = node.get("parameters", {})
        
        if function_name:
            # Apply function mapping for PostgreSQL
            if db_type == "PostgreSQL":
                mapped_function = self.func_mapping.get(function_name.upper(), function_name)
                function_name = mapped_function
            
            # Handle parameters
            param_text = ""
            if parameters:
                param_type = parameters.get("parameter_type", "positional")
                if param_type == "positional":
                    pos_params = parameters.get("positional_params", [])
                    param_text = ", ".join(pos_params)
                elif param_type == "named":
                    named_params = parameters.get("named_params", {})
                    param_pairs = [f"{k} => {v}" for k, v in named_params.items()]
                    param_text = ", ".join(param_pairs)
            
            if param_text:
                return [self._indent(f"{function_name}({param_text});", indent_level)]
            else:
                return [self._indent(f"{function_name}();", indent_level)]
        
        return []

    def _render_null_statement(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render NULL statements for the specified database type.
        
        Args:
            node (Dict[str, Any]): NULL statement node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted NULL statement lines
        """
        return [self._indent("NULL;", indent_level)]

    def _render_return_statement(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render RETURN statements for the specified database type.
        
        Args:
            node (Dict[str, Any]): RETURN statement node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted RETURN statement lines
        """
        sql_statement = node.get("sql_statement", "")
        if sql_statement:
            if db_type == "PostgreSQL":
                sql_statement = self._apply_function_mappings(sql_statement)
            return [self._indent(f"{sql_statement}", indent_level)]
        return []

    def _render_unknown_statement(self, node: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render unknown statement types as fallback for the specified database type.
        
        Args:
            node (Dict[str, Any]): Unknown statement node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted unknown statement lines
        """
        statement_type = node.get("type", "unknown")
        logger.warning(f"Unknown statement type: {statement_type}")
        
        # Try to extract any SQL content
        sql_statement = node.get("sql_statement", "")
        if sql_statement:
            if db_type == "PostgreSQL":
                sql_statement = self._apply_function_mappings(sql_statement)
            return [self._indent(f"{sql_statement}", indent_level)]
        
        return [self._indent(f"-- Unknown statement type: {statement_type}", indent_level)]

    def _render_exception_handler(self, handler: Dict[str, Any], indent_level: int, db_type: str) -> List[str]:
        """
        Render exception handlers for the specified database type.
        
        Args:
            handler (Dict[str, Any]): Exception handler node
            indent_level (int): Current indentation level
            db_type (str): Database type ("Oracle" or "PostgreSQL")
            
        Returns:
            List[str]: List of formatted exception handler lines
        """
        lines: List[str] = []
        
        exception_name = handler.get("exception_name", "")
        if exception_name:
            self.json_convert_sql['exception_handler'] += 1
        # if db_type == "PostgreSQL":
        #     # Apply exception mapping for PostgreSQL
        #     mapped_exception = self.exception_mapping.get(exception_name.upper(), exception_name)
        #     exception_name = mapped_exception
        
        lines.append(self._indent(f"WHEN {exception_name} THEN", indent_level))
        
        # Exception statements
        exception_statements = handler.get("exception_statements", [])
        if exception_statements:
            exception_lines = self._render_statement_list(exception_statements, indent_level + 1, db_type)
            lines.extend(exception_lines)
        
        return lines

    def _apply_function_mappings(self, text: str) -> str:
        """
        Apply function mappings to convert Oracle functions to PostgreSQL equivalents.
        
        Args:
            text (str): Text containing Oracle functions
            
        Returns:
            str: Text with PostgreSQL function mappings applied
        """
        if not text:
            return text
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
            
        result = text
        
        # Apply function mappings (case-insensitive)
        for oracle_func, postgres_func in self.func_mapping.items():
            try:
                # Use regex to match whole words only
                pattern = re.compile(r'\b' + re.escape(str(oracle_func)) + r'\b', re.IGNORECASE)
                result = pattern.sub(str(postgres_func), result)
            except Exception as e:
                # Log the error and continue with next mapping
                debug(f"Error applying function mapping {oracle_func} -> {postgres_func}: {str(e)}")
                continue
        
        return result

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