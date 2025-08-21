import os
import json
import re
import copy
import pandas as pd
from datetime import datetime

from typing import Any, Dict, List, Tuple, Union
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

class FORMATPostsqlTriggerAnalyzer:
    """
    Enhanced PostgreSQL Trigger Analyzer that converts JSON analysis back to properly formatted SQL.
    
    This class takes the JSON analysis output and converts it back to well-formatted
    PostgreSQL trigger code with proper indentation, structure, and formatting.
    """
    
    def __init__(self, json_data):
        """
        Initialize the analyzer with JSON analysis data.
        
        Args:
            json_data (Dict[str, Any]): The JSON analysis data
        """
        self.analysis = json_data
        self.indent_unit = "  "  # 2 spaces for indentation
        self.sql_content = ""
        
        # Load mappings from Excel file
        self.func_mapping = self._load_function_mappings()
        self.type_mapping = self._load_type_mappings()
        self.exception_mapping = self._load_exception_mappings()
        
        # Validate analysis structure
        if not isinstance(json_data, dict):
            raise ValueError("Analysis must be a dictionary")
        
        if "declarations" not in json_data or "main" not in json_data:
            raise ValueError("Analysis must contain 'declarations' and 'main' sections")
            
        logger.debug("FORMATPostsqlTriggerAnalyzer initialized successfully")
    
    def _load_function_mappings(self) -> Dict[str, str]:
        """
        Load function mappings from the Excel file.
        
        Returns:
            Dict[str, str]: Mapping of Oracle functions to PostgreSQL equivalents
        """
        try:
            excel_path = os.path.join(os.path.dirname(__file__), "oracle_postgresql_mappings.xlsx")
            if not os.path.exists(excel_path):
                logger.warning(f"Excel file not found at {excel_path}, using default mappings")
                return self._get_default_function_mappings()
            
            # Read the function mappings sheet
            df = pd.read_excel(excel_path, sheet_name="function_mappings")
            
            # Create mapping dictionary
            func_mapping = {}
            for _, row in df.iterrows():
                oracle_func = str(row.get('Oracle_Function', '')).strip().lower()
                postgresql_func = str(row.get('PostgreSQL_Function', '')).strip()
                
                if oracle_func and postgresql_func and oracle_func != 'nan' and postgresql_func != 'nan':
                    func_mapping[oracle_func] = postgresql_func
            
            logger.debug(f"Loaded {len(func_mapping)} function mappings from Excel file")
            return func_mapping
            
        except Exception as e:
            logger.warning(f"Failed to load function mappings from Excel: {e}, using default mappings")
            return self._get_default_function_mappings()
    
    def _load_type_mappings(self) -> Dict[str, str]:
        """
        Load data type mappings from Excel file.
        
        This function:
        1. Looks for the Excel mappings file in the same directory
        2. Reads the data_type_mappings sheet for Oracle to PostgreSQL type conversions
        3. Creates a dictionary mapping Oracle types (keys) to PostgreSQL types (values)
        4. Falls back to default mappings if file not found or errors occur
        
        Returns:
            Dict[str, str]: Mapping of Oracle data types to PostgreSQL data types
        """
        debug("Starting to load data type mappings from Excel...")
        
        try:
            # Step 1: Locate the Excel file
            excel_path = os.path.join(os.path.dirname(__file__), "oracle_postgresql_mappings.xlsx")
            debug(f"Looking for mappings file at: {excel_path}")
            
            if not os.path.exists(excel_path):
                logger.warning(f"Excel file not found at {excel_path}, using default mappings")
                default_mappings = self._get_default_type_mappings()
                debug(f"Using {len(default_mappings)} default type mappings")
                return default_mappings
            
            # Step 2: Read the Excel data
            debug(f"Reading 'data_type_mappings' sheet from Excel file")
            df = pd.read_excel(excel_path, sheet_name="data_type_mappings")
            debug(f"Excel sheet loaded with {len(df)} rows")
            
            # Step 3: Create mapping dictionary
            type_mapping = {}
            for idx, row in df.iterrows():
                oracle_type = str(row.get('Oracle_Type', '')).strip().upper()
                postgresql_type = str(row.get('PostgreSQL_Type', '')).strip()
                
                # Skip invalid mappings
                if oracle_type and postgresql_type and oracle_type != 'NAN' and postgresql_type != 'NAN':
                    type_mapping[oracle_type] = postgresql_type
                    debug(f"Mapping: {oracle_type} → {postgresql_type}")
            
            logger.debug(f"Loaded {len(type_mapping)} type mappings from Excel file")
            return type_mapping
            
        except FileNotFoundError as e:
            logger.error(f"Excel file not found: {e}")
            default_mappings = self._get_default_type_mappings()
            debug(f"Using {len(default_mappings)} default type mappings due to file not found")
            return default_mappings
        except pd.errors.EmptyDataError:
            logger.error("Excel file exists but contains no data")
            default_mappings = self._get_default_type_mappings()
            debug(f"Using {len(default_mappings)} default type mappings due to empty data")
            return default_mappings  
        except Exception as e:
            logger.warning(f"Failed to load type mappings from Excel: {e}, using default mappings")
            default_mappings = self._get_default_type_mappings()
            debug(f"Using {len(default_mappings)} default type mappings due to: {str(e)}")
            return self._get_default_type_mappings()
    
    def _get_default_function_mappings(self) -> Dict[str, str]:
        """
        Get default function mappings as fallback.
        
        Returns:
            Dict[str, str]: Default function mappings
        """
        return {
            "substr": "SUBSTRING",
            "instr": "POSITION",
            "length": "LENGTH",
            "trim": "TRIM",
            "ltrim": "LTRIM",
            "rtrim": "RTRIM",
            "upper": "UPPER",
            "lower": "LOWER",
            "replace": "REPLACE",
            "translate": "TRANSLATE",
            "lpad": "LPAD",
            "rpad": "RPAD",
            "chr": "CHR",
            "ascii": "ASCII",
            "concat": "CONCAT",
            "nvl": "COALESCE",
            "sysdate": "CURRENT_TIMESTAMP",
            "current_date": "CURRENT_DATE",
            "current_timestamp": "CURRENT_TIMESTAMP",
            "trunc": "DATE_TRUNC",
            "round": "ROUND",
            "to_date": "TO_TIMESTAMP",
            "to_char": "TO_CHAR",
            "extract": "EXTRACT",
            "abs": "ABS",
            "power": "POWER",
            "sqrt": "SQRT",
            "exp": "EXP",
            "ln": "LN",
            "log": "LOG",
            "sin": "SIN",
            "cos": "COS",
            "tan": "TAN",
            "to_number": "CAST",
            "count": "COUNT",
            "sum": "SUM",
            "avg": "AVG",
            "min": "MIN",
            "max": "MAX",
            "cast": "CAST",
            "user": "current_user",
            "sys_context": "current_setting",
            "sys_guid": "gen_random_uuid",
            "nextval": "nextval",
            "currval": "currval",
            "raise_application_error": "RAISE EXCEPTION"
        }
    
    def _get_default_type_mappings(self) -> Dict[str, str]:
        """
        Get default type mappings as fallback.
        
        Returns:
            Dict[str, str]: Default type mappings
        """
        return {
            "VARCHAR2": "VARCHAR",
            "NVARCHAR2": "VARCHAR",
            "NCHAR": "CHAR",
            "LONG": "TEXT",
            "RAWID": "VARCHAR",
            "UROWID": "VARCHAR",
            "NUMBER": "NUMERIC",
            "FLOAT": "REAL",
            "BINARY_FLOAT": "REAL",
            "BINARY_DOUBLE": "DOUBLE PRECISION",
            "PLS_INTEGER": "INTEGER",
            "SIMPLE_INTEGER": "INTEGER",
            "BINARY_INTEGER": "INTEGER",
            "POSITIVE": "INTEGER",
            "NATURAL": "INTEGER",
            "SIGNTYPE": "SMALLINT",
            "SMALLINT": "SMALLINT",
            "INTEGER": "INTEGER",
            "INT": "INTEGER",
            "DECIMAL": "DECIMAL",
            "NUMERIC": "NUMERIC",
            "REAL": "REAL",
            "DATE": "TIMESTAMP",
            "TIMESTAMP WITH TIME ZONE": "TIMESTAMP WITH TIME ZONE",
            "TIMESTAMP WITH LOCAL TIME ZONE": "TIMESTAMP",
            "INTERVAL YEAR TO MONTH": "INTERVAL",
            "INTERVAL DAY TO SECOND": "INTERVAL",
            "CLOB": "TEXT",
            "NCLOB": "TEXT",
            "BLOB": "BYTEA",
            "BFILE": "TEXT",
            "XMLTYPE": "XML",
            "RAW": "BYTEA",
            "LONG RAW": "BYTEA",
            "ROWID": "VARCHAR(18)",
            "BOOLEAN": "BOOLEAN",
            "NATURALN": "INTEGER",
            "POSITIVEN": "INTEGER",
            "SIMPLE_DOUBLE": "DOUBLE PRECISION",
            "SIMPLE_FLOAT": "REAL"
        }
        
    def to_sql(self) -> str:
        """
        Convert the analysis to formatted PostgreSQL SQL.
        
        Returns:
            str: Formatted SQL code
        """
        logger.debug("Starting SQL conversion for PostgreSQL...")
        lines: List[str] = []
        
        # Add header comment
        # lines.append("-- Generated from JSON analysis for PostgreSQL")
        # lines.append(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # lines.append("")
        
        # Render declarations
        logger.debug("Rendering declarations...")
        decl_lines = self._render_declarations(self.analysis["declarations"])
        lines.extend(decl_lines)
        # lines.append("")
        
        # Render main execution block
        logger.debug("Rendering main execution block...")
        main_lines = self._render_main_block(self.analysis["main"][0], 0)
        lines.extend(main_lines)
        
        # Add footer
        # lines.append("")
        # lines.append("-- End of generated SQL")
        
        # self.sql_content = self.sql_content.replace("\n","")
        self.sql_content = "DO $$\n" +"\n".join(lines) + "\nEND $$;"
        logger.debug(f"SQL conversion complete: {len(self.sql_content)} characters")
        return self.sql_content
        
    def _render_declarations(self, decl: Dict[str, Any]) -> List[str]:
        """
        Render variable, constant, and exception declarations for PostgreSQL.
        
        Args:
            decl (Dict[str, Any]): Declarations section
            
        Returns:
            List[str]: List of formatted declaration lines
        """
        logger.debug("=== Rendering declarations for PostgreSQL ===")
        lines: List[str] = []
        
        # PostgreSQL uses DECLARE...BEGIN...END; structure
        lines.append("DECLARE")
        
        # Variables
        variables = decl.get("variables", []) or []
        if variables:
            logger.debug(f"Rendering {len(variables)} variables")
            for var in variables:
                name = var.get("name", "")
                data_type = self._convert_data_type(var.get("data_type", ""))
                default_value = var.get("default_value")
                
                if name and data_type:
                    # PostgreSQL variable declaration syntax
                    if default_value is not None and str(default_value).upper() != "NULL":
                        lines.append(f"  {name} {data_type} := {default_value};")
                    else:
                        lines.append(f"  {name} {data_type};")
        
        # Constants - in PostgreSQL we use variables with CONSTANT keyword
        constants = decl.get("constants", []) or []
        if constants:
            logger.debug(f"Rendering {len(constants)} constants")
            for const in constants:
                name = const.get("name", "")
                data_type = self._convert_data_type(const.get("data_type", ""))
                value = const.get("value", "")
                
                if name and data_type and value is not None:
                    lines.append(f"  {name} CONSTANT {data_type} := {value};")
        
        # Exceptions - PostgreSQL handles exceptions differently
        exceptions = decl.get("exceptions", []) or []
        if exceptions:
            logger.debug(f"Rendering {len(exceptions)} exceptions")
            for exc in exceptions:
                name = exc.get("name", "")
                if name:
                    # In PostgreSQL, we define custom exceptions with this syntax
                    lines.append(f"  {name} EXCEPTION;")
        
        logger.debug("=== Declarations complete ===")
        return lines
        
    def _convert_data_type(self, oracle_type: str) -> str:
        """
        Convert Oracle data type to PostgreSQL data type using mapping rules.
        
        This function handles several data type conversion scenarios:
        1. %TYPE references (column references in Oracle)
        2. Base type conversions from the mapping dictionary
        3. Preserving size parameters for appropriate types
        4. Special handling for complex types like TIMESTAMP WITH TIME ZONE
        
        Args:
            oracle_type (str): Oracle data type (e.g., VARCHAR2(100), NUMBER(10,2), etc.)
            
        Returns:
            str: Corresponding PostgreSQL data type
        """
        debug(f"Converting data type: '{oracle_type}'")
        
        # Handle empty or None type
        if not oracle_type:
            debug("Empty data type provided, defaulting to TEXT")
            return "TEXT"
            
        # Step 1: Handle %TYPE references - PostgreSQL uses different syntax
        if "%TYPE" in oracle_type:
            # In PostgreSQL we would use variable_name%TYPE but for simplicity,
            # we'll use TEXT which is a common PostgreSQL type for these cases
            referenced_var = oracle_type.split("%")[0].strip()
            debug(f"Converting %TYPE reference '{oracle_type}' → TEXT (referenced variable: {referenced_var})")
            return "TEXT"
        
        # Step 2: Extract base type (without size parameters)
        if "(" in oracle_type:
            base_type = oracle_type.split("(")[0].strip().upper()
            size_params = oracle_type[oracle_type.find("("):]
            debug(f"Extracted base type: '{base_type}', size parameters: '{size_params}'")
        else:
            base_type = oracle_type.strip().upper()
            size_params = ""
            debug(f"Using type without size parameters: '{base_type}'")
        
        # Step 3: Convert to PostgreSQL type if mapping exists, otherwise keep as is
        if base_type in self.type_mapping:
            pg_type = self.type_mapping[base_type]
            debug(f"Found mapping: {base_type} → {pg_type}")
        else:
            pg_type = oracle_type
            debug(f"No mapping found for '{base_type}', keeping original")
        
        # Step 4: Handle size parameters
        # Types that don't use size parameters in PostgreSQL
        no_size_types = ["DATE", "TIMESTAMP", "TEXT", "BYTEA", "XML", "BOOLEAN", "INTERVAL"]
        
        if size_params and base_type not in no_size_types:
            # Preserve the size parameters for compatible types
            pg_type = pg_type + size_params
            debug(f"Preserving size parameters: '{pg_type}'")
        elif size_params:
            debug(f"Removing size parameters for type '{base_type}', final type: '{pg_type}'")
        
        # Step 5: Special handling for complex types or edge cases
        # For example, handle NUMBER with precision differently
        if base_type == "NUMBER" and "," in size_params:
            # Extract precision and scale
            try:
                precision_scale = size_params.strip("()").split(",")
                if len(precision_scale) == 2:
                    precision, scale = precision_scale
                    debug(f"NUMBER type with precision {precision} and scale {scale}")
                    # Could apply special rules based on precision/scale here
            except Exception as e:
                debug(f"Failed to parse NUMBER precision/scale: {e}")
        
        debug(f"Final converted type: '{pg_type}'")
        return pg_type
    
    def _load_exception_mappings(self) -> Dict[str, str]:
        """
        Load exception mappings from the Excel file.
        
        Returns:
            Dict[str, str]: Mapping of Oracle exceptions to PostgreSQL messages
        """
        try:
            excel_path = os.path.join(os.path.dirname(__file__), "oracle_postgresql_mappings.xlsx")
            if not os.path.exists(excel_path):
                logger.warning(f"Excel file not found at {excel_path}, using default exception mappings")
                return {}
            
            # Read the exception mappings sheet
            df = pd.read_excel(excel_path, sheet_name="exception_mappings")
            
            # Create mapping dictionary
            exception_mapping = {}
            for _, row in df.iterrows():
                oracle_exception = str(row.get('Oracle_Exception', '')).strip().upper()
                postgresql_message = str(row.get('PostgreSQL_Message', '')).strip()
                
                if oracle_exception and postgresql_message and oracle_exception != 'NAN' and postgresql_message != 'NAN':
                    exception_mapping[oracle_exception] = postgresql_message
            
            logger.debug(f"Loaded {len(exception_mapping)} exception mappings from Excel file")
            return exception_mapping
            
        except Exception as e:
            logger.warning(f"Failed to load exception mappings from Excel: {e}, using default exception mappings")
            return {}
        
    def _render_main_block(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render the main execution block which contains the actual SQL statements.
        
        Args:
            node (Dict[str, Any]): The main block node from analysis
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted SQL lines
        """
        logger.debug(f"=== Rendering main block (indent={indent_level}) ===")
        lines: List[str] = []
        
        # Add BEGIN for PostgreSQL function/procedure body
        lines.append("BEGIN")
        
        # Handle different types of main blocks
        block_type = node.get("type")
        logger.debug(f"Main block type: {block_type}")
        
        if block_type == "begin_end":
            # This is a begin_end block containing statements
            logger.debug("Processing begin_end block structure")
            statements = node.get("begin_end_statements", []) or []
            logger.debug(f"Found {len(statements)} statements in begin_end block")
            lines.extend(self._render_statement_list(statements, indent_level + 1))

            # Exception handlers
            handlers = node.get("exception_handlers", []) or []
            if handlers:
                logger.debug(f"Processing {len(handlers)} exception handlers")
                lines.append(self._indent("EXCEPTION", indent_level + 1))
                for i, h in enumerate(handlers):
                    logger.debug(f"Rendering exception handler {i+1}/{len(handlers)}: {h.get('exception_name')}")
                    lines.extend(self._render_exception_handler(h, indent_level + 2))
        else:
            # Handle as a generic statement list
            logger.debug("Processing generic statement list")
            statements = node if isinstance(node, list) else [node]
            lines.extend(self._render_statement_list(statements, indent_level + 1))

        # Add END for PostgreSQL function/procedure body
        lines.append("END;")
            
        logger.debug(f"=== Main block complete: {len(lines)} lines ===")
        return lines
        
    def _render_statement_list(self, statements: List[Dict[str, Any]], indent_level: int) -> List[str]:
        """
        Render a list of statements with proper indentation for PostgreSQL.
        
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
            
            if stmt_type in ["select_statement", "insert_statement", "update_statement", "delete_statement"]:
                sql = statement.get("sql_statement", "")
                if sql:
                    # Convert Oracle SQL to PostgreSQL SQL
                    pg_sql = self._convert_sql_statement(sql, stmt_type)
                    logger.debug(f"Rendering {stmt_type}: {pg_sql[:50]}...")
                    lines.append(self._indent(pg_sql, indent_level))
                    
            elif stmt_type == "assignment_statement":
                variable = statement.get("variable", "")
                value = statement.get("value", "")
                if variable and value is not None:
                    # PostgreSQL uses := for assignment
                    logger.debug(f"Rendering assignment: {variable} := {value}")
                    lines.append(self._indent(f"{variable} := {value};", indent_level))
                    
            elif stmt_type == "raise_statement":
                sql = statement.get("sql_statement", "")
                if sql:
                    # Convert RAISE to PostgreSQL syntax
                    pg_sql = self._convert_raise_statement(sql)
                    logger.debug(f"Rendering RAISE statement: {pg_sql[:50]}...")
                    lines.append(self._indent(pg_sql, indent_level))
                    
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
                    # Convert to PostgreSQL syntax if needed
                    pg_stmt = self._convert_unknown_statement(stmt_text)
                    logger.debug(f"Rendering unknown statement: {pg_stmt[:50]}...")
                    lines.append(self._indent(pg_stmt, indent_level))
                    
            elif stmt_type == "function_calling":
                # Handle function calling statements
                logger.debug("Rendering function calling statement")
                lines.extend(self._render_function_call(statement, indent_level))
                    
            else:
                # Fallback: try to render any SQL content
                sql = statement.get("sql_statement", "") or statement.get("sql", "")
                if sql:
                    # Convert to PostgreSQL syntax
                    pg_sql = self._convert_sql_statement(sql, "unknown")
                    logger.debug(f"Fallback rendering SQL: {pg_sql[:50]}...")
                    lines.append(self._indent(pg_sql, indent_level))
                else:
                    logger.warning(f"Unknown statement type '{stmt_type}' with no SQL content: {statement}")
                    
        logger.debug(f"=== Statement list complete: {len(lines)} lines ===")
        return lines
        
    def _render_exception_handler(self, handler: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render an exception handler for PostgreSQL.
        
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
        
        # PostgreSQL exception handling syntax is similar to Oracle
        lines.append(self._indent(f"WHEN {exception_name} THEN", indent_level))
        lines.extend(self._render_statement_list(exception_statements, indent_level + 1))
        
        return lines
        
    def _render_if_else(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render an IF-ELSE structure for PostgreSQL.
        
        Args:
            node (Dict[str, Any]): IF-ELSE node data
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted IF-ELSE lines
        """
        logger.debug(f"=== Rendering IF-ELSE structure (indent={indent_level}) ===")
        lines: List[str] = []
        
        condition = self._convert_condition(node.get("condition", ""))
        then_statements = node.get("then_statements", []) or []
        else_if_clauses = node.get("else_if", []) or []
        else_statements = node.get("else_statements", []) or []
        
        # Main IF condition - PostgreSQL syntax is similar to Oracle
        lines.append(self._indent(f"IF {condition} THEN", indent_level))
        
        # THEN statements
        lines.extend(self._render_statement_list(then_statements, indent_level + 1))
        
        # ELSIF clauses - In PostgreSQL it's ELSIF (same as Oracle)
        for else_if in else_if_clauses:
            else_if_condition = self._convert_condition(else_if.get("condition", ""))
            else_if_statements = else_if.get("then_statements", []) or []
            
            lines.append(self._indent(f"ELSIF {else_if_condition} THEN", indent_level))
            lines.extend(self._render_statement_list(else_if_statements, indent_level + 1))
        
        # ELSE clause
        if else_statements:
            lines.append(self._indent("ELSE", indent_level))
            lines.extend(self._render_statement_list(else_statements, indent_level + 1))
        
        # END IF
        lines.append(self._indent("END IF;", indent_level))
        
        logger.debug("=== IF-ELSE structure complete ===")
        return lines
        
    def _render_case_when(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render a CASE-WHEN structure for PostgreSQL.
        
        Args:
            node (Dict[str, Any]): CASE-WHEN node data
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted CASE-WHEN lines
        """
        logger.debug(f"=== Rendering CASE-WHEN structure (indent={indent_level}) ===")
        lines: List[str] = []
        
        case_expr = node.get("case_expression")
        when_clauses = node.get("when_clauses", []) or []
        else_statements = node.get("else_statements", []) or []
        searched_case = not case_expr or str(case_expr).strip() == ""
        
        if searched_case:
            # Searched CASE statement
            lines.append(self._indent("CASE", indent_level))
            
            # Process WHEN clauses
            for clause in when_clauses:
                when_val = self._convert_condition(clause.get("when_value", ""))
                then_statements = clause.get("then_statements", []) or []
                
                lines.append(self._indent(f"WHEN {when_val} THEN", indent_level + 1))
                lines.extend(self._render_statement_list(then_statements, indent_level + 2))
                
            # Handle ELSE clause
            if else_statements:
                lines.append(self._indent("ELSE", indent_level + 1))
                lines.extend(self._render_statement_list(else_statements, indent_level + 2))
                
            lines.append(self._indent("END CASE;", indent_level))
        else:
            # Simple CASE statement with expression
            lines.append(self._indent(f"CASE {case_expr}", indent_level))
            
            # Process WHEN clauses
            for clause in when_clauses:
                when_val = clause.get("when_value", "")
                then_statements = clause.get("then_statements", []) or []
                
                lines.append(self._indent(f"WHEN {when_val} THEN", indent_level + 1))
                lines.extend(self._render_statement_list(then_statements, indent_level + 2))
                
            # Handle ELSE clause
            if else_statements:
                lines.append(self._indent("ELSE", indent_level + 1))
                lines.extend(self._render_statement_list(else_statements, indent_level + 2))
                
            lines.append(self._indent("END CASE;", indent_level))
            
        logger.debug("=== CASE-WHEN structure complete ===")
        return lines
        
    def _render_for_loop(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render a FOR loop structure for PostgreSQL.
        
        Args:
            node (Dict[str, Any]): FOR loop node data
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted FOR loop lines
        """
        logger.debug(f"=== Rendering FOR loop structure (indent={indent_level}) ===")
        lines: List[str] = []
        
        loop_var = node.get("loop_variable", "i")
        cursor_query = node.get("cursor_query", "SELECT 1")
        
        # In PostgreSQL, FOR loops over query results have similar syntax
        cursor_query = cursor_query.strip()
        if cursor_query.startswith("(") and cursor_query.endswith(")"):
            cursor_query = cursor_query[1:-1].strip()
        
        # Convert Oracle query syntax to PostgreSQL
        pg_cursor_query = self._convert_sql_statement(cursor_query, "select_statement")
        
        # PostgreSQL FOR loop syntax
        lines.append(self._indent(f"FOR {loop_var} IN ({pg_cursor_query}) LOOP", indent_level))
        
        # Render loop statements
        loop_statements = node.get("loop_statements", []) or []
        lines.extend(self._render_statement_list(loop_statements, indent_level + 1))
        
        lines.append(self._indent("END LOOP;", indent_level))
        
        logger.debug("=== FOR loop structure complete ===")
        return lines
        
    def _render_function_call(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        """
        Render a function call for PostgreSQL.
        
        Args:
            node (Dict[str, Any]): Function call node data
            indent_level (int): Current indentation level
            
        Returns:
            List[str]: List of formatted function call lines
        """
        logger.debug(f"Rendering function call: {node.get('function_name')}")
        lines: List[str] = []
        
        func_name = node.get("function_name", "").lower()
        params = node.get("parameter", {})
        
        # Convert the function name to PostgreSQL equivalent if available
        pg_func = self.func_mapping.get(func_name, func_name)
        
        # Special handling for raise_application_error in Oracle
        # In PostgreSQL, we use RAISE EXCEPTION
        if func_name == "raise_application_error":
            error_code = params.get("handler_code", "-20000")
            error_msg = params.get("handler_string", "''")
            
            # PostgreSQL doesn't use numeric error codes in the same way
            # We include the code in the message for reference
            lines.append(self._indent(f"RAISE_APPLICATION_ERROR({error_code}, {error_msg});", indent_level))
        else:
            # Generic function call
            # Convert to PostgreSQL PERFORM syntax for procedures that don't return values
            lines.append(self._indent(f"PERFORM {pg_func}();", indent_level))
        
        return lines
        
    def _convert_sql_statement(self, sql: str, stmt_type: str) -> str:
        """
        Convert Oracle SQL statement to PostgreSQL syntax.
        
        Args:
            sql (str): Oracle SQL statement
            stmt_type (str): Statement type
            
        Returns:
            str: PostgreSQL SQL statement
        """
        # This is a simplified conversion - a comprehensive converter would be more complex
        
        # Basic conversions
        pg_sql = sql
        
        # DUAL table is not needed in PostgreSQL
        pg_sql = re.sub(r'\bFROM\s+DUAL\b', '', pg_sql, flags=re.IGNORECASE)
        
        # Apply function mappings from Excel file
        for oracle_func, postgresql_func in self.func_mapping.items():
            # Handle function calls with parentheses
            pg_sql = re.sub(rf'\b{oracle_func}\s*\(', f'{postgresql_func}(', pg_sql, flags=re.IGNORECASE)
            # Handle standalone function names
            pg_sql = re.sub(rf'\b{oracle_func}\b', postgresql_func, pg_sql, flags=re.IGNORECASE)
        
        # Oracle's NVL2 -> PostgreSQL's CASE WHEN (not in function mappings)
        pg_sql = re.sub(r'\bNVL2\s*\(', 'CASE WHEN ', pg_sql, flags=re.IGNORECASE)
        
        # Oracle's DECODE -> PostgreSQL's CASE
        pg_sql = re.sub(r'\bDECODE\s*\(', 'CASE WHEN ', pg_sql, flags=re.IGNORECASE)
        
        # Oracle's CONNECT_BY_ROOT -> PostgreSQL doesn't have direct equivalent
        pg_sql = re.sub(r'\bCONNECT_BY_ROOT\b', '/* CONNECT_BY_ROOT - needs manual conversion */', pg_sql, flags=re.IGNORECASE)
        
        # Oracle's CONNECT BY hierarchy -> PostgreSQL recursive CTE
        pg_sql = re.sub(r'\bCONNECT\s+BY\b', '/* CONNECT BY - replace with recursive CTE */', pg_sql, flags=re.IGNORECASE)
        
        # Oracle's EMPTY_CLOB() -> PostgreSQL NULL (no direct equivalent)
        pg_sql = re.sub(r'\bEMPTY_CLOB\s*\(\)', 'NULL', pg_sql, flags=re.IGNORECASE)
        pg_sql = re.sub(r'\bEMPTY_BLOB\s*\(\)', 'NULL', pg_sql, flags=re.IGNORECASE)
        
        # Oracle's REGEXP_LIKE -> PostgreSQL's ~ operator
        pg_sql = re.sub(r'\bREGEXP_LIKE\s*\((.+?),\s*(.+?)\)', r'\1 ~ \2', pg_sql, flags=re.IGNORECASE)
        
        # Oracle's LISTAGG -> PostgreSQL's STRING_AGG
        pg_sql = re.sub(r'\bLISTAGG\s*\(', 'STRING_AGG(', pg_sql, flags=re.IGNORECASE)
        pg_sql = re.sub(r'\bWM_CONCAT\s*\(', 'STRING_AGG(', pg_sql, flags=re.IGNORECASE)
        
        # Ensure statement ends with semicolon if it doesn't already
        if not pg_sql.strip().endswith(';'):
            pg_sql += ';'
            
        return pg_sql
        
    def _convert_raise_statement(self, sql: str) -> str:
        """
        Convert Oracle RAISE statement to PostgreSQL syntax.
        
        Args:
            sql (str): Oracle RAISE statement
            
        Returns:
            str: PostgreSQL RAISE statement
        """
        # Extract exception name from RAISE statement
        match = re.match(r'RAISE\s+([A-Za-z0-9_]+)\s*;?', sql)
        if match:
            exception_name = match.group(1)
            
            # Get specific message from loaded exception mappings or use exception name as message
            message = self.exception_mapping.get(exception_name.upper(), exception_name)
            return f"RAISE EXCEPTION '{message}';"
        
        return sql
        
    def _convert_unknown_statement(self, stmt: str) -> str:
        """
        Convert unknown Oracle statement to PostgreSQL syntax.
        
        Args:
            stmt (str): Oracle statement
            
        Returns:
            str: PostgreSQL statement
        """
        # This is a simplified conversion - a comprehensive converter would be more complex
        pg_stmt = stmt
        
        # Add PostgreSQL-specific conversions here
        
        # Ensure statement ends with semicolon if it doesn't already
        if not pg_stmt.strip().endswith(';'):
            pg_stmt += ';'
            
        return pg_stmt
        
    def _convert_condition(self, condition: str) -> str:
        """
        Convert Oracle condition to PostgreSQL syntax.
        
        Args:
            condition (str): Oracle condition
            
        Returns:
            str: PostgreSQL condition
        """
        if not condition:
            return condition
            
        pg_condition = condition
        
        # Apply function mappings from Excel file
        for oracle_func, postgresql_func in self.func_mapping.items():
            # Handle function calls with parentheses
            pg_condition = re.sub(rf'\b{oracle_func}\s*\(', f'{postgresql_func}(', pg_condition, flags=re.IGNORECASE)
            # Handle standalone function names
            pg_condition = re.sub(rf'\b{oracle_func}\b', postgresql_func, pg_condition, flags=re.IGNORECASE)
        
        return pg_condition
        
    def _indent(self, text: str, level: int) -> str:
        """
        Add indentation to a text line.
        
        Args:
            text (str): The text to indent
            level (int): Indentation level
            
        Returns:
            str: Indented text
        """
        return f"{self.indent_unit * max(level, 0)}{text}"
        
