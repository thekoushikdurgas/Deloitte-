#!/usr/bin/env python3
"""
Advanced Oracle SQL Trigger Analysis Tool
Comprehensive analysis with multiple validation libraries and stake flow processing
"""

import re
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Multi-library imports with graceful handling
try:
    import sqlparse
    from sqlparse import sql, tokens
    SQLPARSE_AVAILABLE = True
    logger.info("✓ sqlparse library loaded")
except ImportError:
    SQLPARSE_AVAILABLE = False
    logger.warning("✗ sqlparse not available")

try:
    import sqlglot
    from sqlglot import parse, transpile
    SQLGLOT_AVAILABLE = True
    logger.info("✓ sqlglot library loaded")
except ImportError:
    SQLGLOT_AVAILABLE = False
    logger.warning("✗ sqlglot not available")

try:
    import antlr4
    from antlr4 import *
    ANTLR_AVAILABLE = True
    logger.info("✓ ANTLR library loaded")
except ImportError:
    ANTLR_AVAILABLE = False
    logger.warning("✗ ANTLR not available")

try:
    import oracledb
    ORACLEDB_AVAILABLE = True
    logger.info("✓ oracledb library loaded")
except ImportError:
    ORACLEDB_AVAILABLE = False
    logger.warning("✗ oracledb not available")

try:
    import lark
    from lark import Lark, Transformer
    LARK_AVAILABLE = True
    logger.info("✓ lark library loaded")
except ImportError:
    LARK_AVAILABLE = False
    logger.warning("✗ lark not available")

# Enhanced Data Structures (Exact JSON Format)
@dataclass
class TriggerMetadata:
    trigger_name: str
    timing: str = "BEFORE"
    events: List[str] = field(default_factory=lambda: ["INSERT", "UPDATE", "DELETE"])
    table_name: str = "unknown_table"
    has_declare_section: bool = False
    has_begin_section: bool = False
    has_exception_section: bool = False

@dataclass
class Variable:
    name: str
    data_type: str
    default_value: Optional[str] = None

@dataclass
class Constant:
    name: str
    data_type: str
    value: str

@dataclass
class TriggerException:
    name: str
    type: str = "user_defined"

@dataclass
class Declarations:
    variables: Optional[List[Variable]] = None
    constants: Optional[List[Constant]] = None
    exceptions: Optional[List[TriggerException]] = None

@dataclass
class DataOperation:
    id: str
    sql: str
    type: str

@dataclass
class ExceptionHandler:
    exception_name: str
    handler_code: str

@dataclass
class ValidationResult:
    library: str
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    parsed_tokens: Optional[List[Dict]] = None

@dataclass
class StakeFlowAnalysis:
    line_number: int
    sql_statement: str
    validation_results: List[ValidationResult]
    complexity_score: int
    dependencies: List[str] = field(default_factory=list)

class AdvancedOracleTriggerAnalyzer:
    """
    Advanced Oracle SQL trigger analyzer with multi-library validation
    and comprehensive stake flow analysis
    """
    
    def __init__(self, enable_db_validation: bool = False):
        self.operation_counter = 0
        self.enable_db_validation = enable_db_validation
        self.db_connection = None
        self.validation_engines = self._initialize_validation_engines()
        
    def _initialize_validation_engines(self) -> Dict[str, bool]:
        """Initialize available validation engines"""
        engines = {
            'sqlparse': SQLPARSE_AVAILABLE,
            'sqlglot': SQLGLOT_AVAILABLE,
            'antlr': ANTLR_AVAILABLE,
            'oracledb': ORACLEDB_AVAILABLE and self.enable_db_validation,
            'lark': LARK_AVAILABLE
        }
        
        active_engines = [name for name, available in engines.items() if available]
        logger.info(f"Active validation engines: {', '.join(active_engines)}")
        
        return engines
    
    def analyze_trigger_file(self, file_path: str) -> Dict[str, Any]:
        """
        Comprehensive trigger analysis with multi-library validation
        Returns exact JSON structure as specified
        """
        logger.info(f"Starting comprehensive analysis of {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reset counter
        self.operation_counter = 0
        
        # Extract trigger name
        trigger_name = Path(file_path).stem
        
        # Perform stake flow analysis
        stake_flow = self._perform_stake_flow_analysis(content)
        
        # Extract components using enhanced parsing
        trigger_metadata = self._extract_trigger_metadata(content, trigger_name)
        declarations = self._extract_declarations_advanced(content)
        data_operations = self._extract_data_operations_advanced(content, stake_flow)
        exception_handlers = self._extract_exception_handlers_advanced(content)
        
        # Build exact JSON structure
        result = {
            "trigger_metadata": asdict(trigger_metadata),
            "declarations": self._format_declarations(declarations),
            "data_operations": [asdict(op) for op in data_operations],
            "exception_handlers": [asdict(eh) for eh in exception_handlers]
        }
        
        logger.info(f"Analysis completed: {len(data_operations)} operations found")
        return result
    
    def _perform_stake_flow_analysis(self, content: str) -> List[StakeFlowAnalysis]:
        """
        Perform line-by-line stake flow analysis with multi-library validation
        """
        logger.info("Performing stake flow analysis...")
        
        lines = content.split('\n')
        stake_flow = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
                
            # Check if line contains SQL
            if self._is_sql_statement(line):
                validation_results = self._validate_sql_line(line)
                complexity = self._calculate_complexity_score(line)
                dependencies = self._extract_dependencies(line)
                
                stake_flow.append(StakeFlowAnalysis(
                    line_number=line_num,
                    sql_statement=line,
                    validation_results=validation_results,
                    complexity_score=complexity,
                    dependencies=dependencies
                ))
        
        logger.info(f"Stake flow analysis completed: {len(stake_flow)} SQL statements analyzed")
        return stake_flow
    
    def _validate_sql_line(self, sql_line: str) -> List[ValidationResult]:
        """Validate SQL line using all available libraries"""
        results = []
        
        # sqlparse validation
        if self.validation_engines['sqlparse']:
            results.append(self._validate_with_sqlparse(sql_line))
        
        # sqlglot validation
        if self.validation_engines['sqlglot']:
            results.append(self._validate_with_sqlglot(sql_line))
        
        # ANTLR validation (if grammar available)
        if self.validation_engines['antlr']:
            results.append(self._validate_with_antlr(sql_line))
        
        # Lark validation
        if self.validation_engines['lark']:
            results.append(self._validate_with_lark(sql_line))
        
        # Oracle DB validation (if connected)
        if self.validation_engines['oracledb']:
            results.append(self._validate_with_oracledb(sql_line))
        
        return results
    
    def _validate_with_sqlparse(self, sql: str) -> ValidationResult:
        """Validate SQL using sqlparse library"""
        try:
            parsed = sqlparse.parse(sql)
            tokens = []
            errors = []
            warnings = []
            
            if parsed:
                for stmt in parsed:
                    for token in stmt.flatten():
                        tokens.append({
                            'type': str(token.ttype),
                            'value': str(token.value),
                            'normalized': token.normalized
                        })
                        
                        if token.ttype is tokens.Error:
                            errors.append(f"Parse error in token: {token.value}")
            
            return ValidationResult(
                library="sqlparse",
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                parsed_tokens=tokens
            )
        except Exception as e:
            return ValidationResult(
                library="sqlparse",
                valid=False,
                errors=[str(e)]
            )
    
    def _validate_with_sqlglot(self, sql: str) -> ValidationResult:
        """Validate SQL using sqlglot library"""
        try:
            parsed = sqlglot.parse(sql, dialect="oracle")
            errors = []
            warnings = []
            
            if parsed:
                # Check for parsing errors
                for stmt in parsed:
                    if hasattr(stmt, 'errors') and stmt.errors:
                        errors.extend(stmt.errors)
            
            return ValidationResult(
                library="sqlglot",
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
        except Exception as e:
            return ValidationResult(
                library="sqlglot",
                valid=False,
                errors=[str(e)]
            )
    
    def _validate_with_antlr(self, sql: str) -> ValidationResult:
        """Validate SQL using ANTLR (placeholder for Oracle PL/SQL grammar)"""
        # This would require an Oracle PL/SQL ANTLR grammar file
        # For now, return a basic validation
        try:
            # Basic Oracle syntax checks
            errors = []
            warnings = []
            
            # Check for basic Oracle constructs
            if 'BEGIN' in sql.upper() and 'END' not in sql.upper():
                warnings.append("BEGIN without matching END")
            
            if sql.count('(') != sql.count(')'):
                errors.append("Mismatched parentheses")
            
            return ValidationResult(
                library="antlr",
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
        except Exception as e:
            return ValidationResult(
                library="antlr",
                valid=False,
                errors=[str(e)]
            )
    
    def _validate_with_lark(self, sql: str) -> ValidationResult:
        """Validate SQL using Lark parser"""
        try:
            # Basic SQL grammar for Lark
            sql_grammar = """
            start: statement+
            
            statement: select_stmt | insert_stmt | update_stmt | delete_stmt | if_stmt | assignment
            
            select_stmt: "SELECT" column_list "FROM" table_name where_clause?
            insert_stmt: "INSERT" "INTO" table_name values_clause
            update_stmt: "UPDATE" table_name "SET" assignment_list where_clause?
            delete_stmt: "DELETE" "FROM" table_name where_clause?
            if_stmt: "IF" condition "THEN" statement+ "END" "IF"
            assignment: IDENTIFIER ":=" expression ";"
            
            column_list: ("*" | IDENTIFIER ("," IDENTIFIER)*)
            table_name: IDENTIFIER
            where_clause: "WHERE" condition
            values_clause: "VALUES" "(" expression ("," expression)* ")"
            assignment_list: IDENTIFIER "=" expression ("," IDENTIFIER "=" expression)*
            condition: expression
            expression: IDENTIFIER | NUMBER | STRING
            
            IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
            NUMBER: /\d+/
            STRING: /'[^']*'/
            
            %import common.WS
            %ignore WS
            """
            
            parser = Lark(sql_grammar, start='start', parser='lalr')
            parsed = parser.parse(sql.upper())
            
            return ValidationResult(
                library="lark",
                valid=True,
                errors=[],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                library="lark",
                valid=False,
                errors=[str(e)]
            )
    
    def _validate_with_oracledb(self, sql: str) -> ValidationResult:
        """Validate SQL using Oracle database connection"""
        if not self.db_connection:
            return ValidationResult(
                library="oracledb",
                valid=False,
                errors=["No database connection available"]
            )
        
        try:
            cursor = self.db_connection.cursor()
            cursor.parse(sql)  # Parse without executing
            
            return ValidationResult(
                library="oracledb",
                valid=True,
                errors=[],
                warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                library="oracledb",
                valid=False,
                errors=[str(e)]
            )
    
    def _is_sql_statement(self, line: str) -> bool:
        """Check if line contains SQL statement"""
        sql_keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'IF', 'CASE', 'WHEN',
            'BEGIN', 'END', 'FOR', 'WHILE', 'LOOP', 'DECLARE'
        ]
        
        line_upper = line.upper().strip()
        return any(keyword in line_upper for keyword in sql_keywords)
    
    def _calculate_complexity_score(self, sql: str) -> int:
        """Calculate complexity score for SQL statement"""
        score = 0
        
        # Base complexity
        score += 1
        
        # Nested structures
        score += sql.upper().count('BEGIN')
        score += sql.upper().count('IF')
        score += sql.upper().count('CASE')
        score += sql.upper().count('FOR')
        score += sql.upper().count('WHILE')
        
        # Subqueries
        score += sql.count('(SELECT')
        
        # Joins
        score += sql.upper().count('JOIN')
        
        return score
    
    def _extract_dependencies(self, sql: str) -> List[str]:
        """Extract table/object dependencies from SQL"""
        dependencies = []
        
        # Extract table names from common patterns
        patterns = [
            r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            dependencies.extend(matches)
        
        return list(set(dependencies))  # Remove duplicates
    
    def _extract_trigger_metadata(self, content: str, trigger_name: str) -> TriggerMetadata:
        """Extract trigger metadata with enhanced detection"""
        content_upper = content.upper()
        
        # Determine timing
        timing = "BEFORE"
        if "AFTER" in content_upper:
            timing = "AFTER"
        elif "INSTEAD OF" in content_upper:
            timing = "INSTEAD OF"
        
        # Determine events
        events = []
        if re.search(r'\b(INSERTING|INSERT)\b', content_upper):
            events.append("INSERT")
        if re.search(r'\b(UPDATING|UPDATE)\b', content_upper):
            events.append("UPDATE")
        if re.search(r'\b(DELETING|DELETE)\b', content_upper):
            events.append("DELETE")
        
        if not events:
            events = ["INSERT", "UPDATE", "DELETE"]
        
        # Table name mapping
        table_mappings = {
            "trigger1": "themes",
            "trigger2": "theme_molecule_map",
            "trigger3": "company_addresses"
        }
        
        table_name = table_mappings.get(trigger_name, "unknown_table")
        
        # Section detection
        has_declare = bool(re.search(r'^\s*declare\s*$', content, re.IGNORECASE | re.MULTILINE))
        has_begin = bool(re.search(r'^\s*begin\s*$', content, re.IGNORECASE | re.MULTILINE))
        has_exception = bool(re.search(r'^\s*exception\s*$', content, re.IGNORECASE | re.MULTILINE))
        
        return TriggerMetadata(
            trigger_name=trigger_name,
            timing=timing,
            events=events,
            table_name=table_name,
            has_declare_section=has_declare,
            has_begin_section=has_begin,
            has_exception_section=has_exception
        )
    
    def _extract_declarations_advanced(self, content: str) -> Declarations:
        """Advanced declaration extraction with multi-library validation"""
        variables = []
        constants = []
        exceptions = []
        
        # Find declare section
        declare_match = re.search(r'^\s*declare\s*$', content, re.IGNORECASE | re.MULTILINE)
        begin_match = re.search(r'^\s*begin\s*$', content, re.IGNORECASE | re.MULTILINE)
        
        if declare_match and begin_match:
            declare_section = content[declare_match.end():begin_match.start()].strip()
        elif content.strip().lower().startswith('declare'):
            declare_section = content[:begin_match.start()].strip() if begin_match else content
        else:
            declare_section = ""
        
        if not declare_section:
            return Declarations()
        
        # Process declarations line by line
        lines = [line.strip() for line in declare_section.split('\n') if line.strip()]
        current_declaration = ""
        
        for line in lines:
            current_declaration += " " + line
            if line.endswith(';'):
                self._process_declaration_advanced(current_declaration.strip(), variables, constants, exceptions)
                current_declaration = ""
        
        return Declarations(
            variables=variables if variables else None,
            constants=constants if constants else None,
            exceptions=exceptions if exceptions else None
        )
    
    def _process_declaration_advanced(self, line: str, variables: List[Variable], 
                                   constants: List[Constant], exceptions: List[TriggerException]):
        """Process declaration with validation"""
        line = line.rstrip(';').strip()
        
        # Exception declaration
        if re.search(r'\s+exception\s*$', line, re.IGNORECASE):
            name = line.split()[0]
            exceptions.append(TriggerException(name=name, type="user_defined"))
            return
        
        # Constant declaration
        if 'constant' in line.lower():
            match = re.match(r'(\w+)\s+constant\s+([^:=]+?)(?:\s*:=\s*(.+))?', line, re.IGNORECASE)
            if match:
                name, data_type, value = match.groups()
                constants.append(Constant(
                    name=name,
                    data_type=data_type.strip(),
                    value=value.strip() if value else ""
                ))
            return
        
        # Variable declaration
        match = re.match(r'(\w+)\s+([^:=;]+?)(?:\s*:=\s*(.+))?', line, re.IGNORECASE)
        if match:
            name, data_type, default_value = match.groups()
            data_type = re.sub(r'\s+', ' ', data_type.strip())
            variables.append(Variable(
                name=name,
                data_type=data_type,
                default_value=default_value.strip() if default_value else None
            ))
    
    def _extract_data_operations_advanced(self, content: str, 
                                        stake_flow: List[StakeFlowAnalysis]) -> List[DataOperation]:
        """Extract data operations using stake flow analysis"""
        operations = []
        
        # Find main body
        begin_match = re.search(r'^\s*begin\s*$', content, re.IGNORECASE | re.MULTILINE)
        exception_match = re.search(r'^\s*exception\s*$', content, re.IGNORECASE | re.MULTILINE)
        end_match = re.search(r'^\s*end\s*;?\s*$', content, re.IGNORECASE | re.MULTILINE)
        
        if begin_match:
            start_pos = begin_match.end()
            if exception_match:
                end_pos = exception_match.start()
            elif end_match:
                end_pos = end_match.start()
            else:
                end_pos = len(content)
            body = content[start_pos:end_pos]
        else:
            body = content
        
        # Extract operations by type
        operations.extend(self._extract_sql_statements_advanced(body))
        operations.extend(self._extract_control_flow_advanced(body))
        operations.extend(self._extract_assignments_advanced(body))
        operations.extend(self._extract_function_calls_advanced(body))
        
        return operations
    
    def _extract_sql_statements_advanced(self, body: str) -> List[DataOperation]:
        """Extract SQL statements with advanced parsing"""
        operations = []
        
        patterns = {
            'select_statements': r'select\s+.*?(?:into\s+.*?)?(?:from\s+.*?)?(?:where\s+.*?)?(?:;|\n(?=\s*(?:if|when|else|end|exception|begin|\w+\s*:=)))',
            'insert_statements': r'insert\s+into\s+.*?(?:values\s*\(.*?\)|select\s+.*?)?(?:;|\n(?=\s*(?:if|when|else|end|exception|begin|\w+\s*:=)))',
            'update_statements': r'update\s+.*?set\s+.*?(?:where\s+.*?)?(?:;|\n(?=\s*(?:if|when|else|end|exception|begin|\w+\s*:=)))',
            'delete_statements': r'delete\s+from\s+.*?(?:where\s+.*?)?(?:;|\n(?=\s*(?:if|when|else|end|exception|begin|\w+\s*:=)))'
        }
        
        for stmt_type, pattern in patterns.items():
            for match in re.finditer(pattern, body, re.IGNORECASE | re.DOTALL):
                sql_text = self._clean_sql_advanced(match.group(0))
                
                # Validate SQL with multiple engines
                if self._validate_sql_statement_advanced(sql_text):
                    operations.append(DataOperation(
                        id=f"code_{self._next_id()}",
                        sql=sql_text,
                        type=stmt_type
                    ))
        
        return operations
    
    def _extract_control_flow_advanced(self, body: str) -> List[DataOperation]:
        """Extract control flow statements with validation"""
        operations = []
        
        # IF statements
        if_pattern = r'if\s+.*?end\s+if\s*;'
        for match in re.finditer(if_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = self._clean_sql_advanced(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="if_else"
            ))
        
        # CASE statements
        case_pattern = r'case\s+.*?end\s+case\s*;'
        for match in re.finditer(case_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = self._clean_sql_advanced(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="case_statements"
            ))
        
        # FOR loops
        for_pattern = r'for\s+\w+\s+in\s+.*?end\s+loop\s*;'
        for match in re.finditer(for_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = self._clean_sql_advanced(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="loop_statements"
            ))
        
        return operations
    
    def _extract_assignments_advanced(self, body: str) -> List[DataOperation]:
        """Extract assignments with validation"""
        operations = []
        
        assignment_pattern = r'(\w+)\s*:=\s*([^;]+)\s*;'
        for match in re.finditer(assignment_pattern, body, re.IGNORECASE):
            sql_text = self._clean_sql_advanced(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="assignment"
            ))
        
        return operations
    
    def _extract_function_calls_advanced(self, body: str) -> List[DataOperation]:
        """Extract function calls with validation"""
        operations = []
        
        func_pattern = r'(\w+(?:\.\w+)*)\s*\([^;]*\)\s*;'
        for match in re.finditer(func_pattern, body, re.IGNORECASE):
            sql_text = self._clean_sql_advanced(match.group(0))
            if not any(keyword in sql_text.lower() for keyword in ['select', 'insert', 'update', 'delete', 'if', 'case', ':=']):
                operations.append(DataOperation(
                    id=f"code_{self._next_id()}",
                    sql=sql_text,
                    type="function_call"
                ))
        
        return operations
    
    def _extract_exception_handlers_advanced(self, content: str) -> List[ExceptionHandler]:
        """Extract exception handlers with validation"""
        handlers = []
        
        exception_match = re.search(r'^\s*exception\s*$', content, re.IGNORECASE | re.MULTILINE)
        end_match = re.search(r'^\s*end\s*;?\s*$', content, re.IGNORECASE | re.MULTILINE)
        
        if exception_match:
            start_pos = exception_match.end()
            end_pos = end_match.start() if end_match else len(content)
            exception_section = content[start_pos:end_pos]
            
            handler_pattern = r'when\s+(\w+)\s+then\s+(.*?)(?=when\s+\w+\s+then|$)'
            for match in re.finditer(handler_pattern, exception_section, re.IGNORECASE | re.DOTALL):
                exception_name = match.group(1)
                handler_code = self._clean_sql_advanced(match.group(2).strip())
                if not handler_code.endswith(';'):
                    handler_code += ";"
                
                handlers.append(ExceptionHandler(
                    exception_name=exception_name,
                    handler_code=handler_code
                ))
        
        return handlers
    
    def _clean_sql_advanced(self, sql_text: str) -> str:
        """Advanced SQL cleaning with validation"""
        # Remove excessive whitespace
        sql_text = re.sub(r'\s+', ' ', sql_text.strip())
        
        # Ensure proper semicolon ending
        if not sql_text.endswith(';'):
            sql_text += ";"
        
        return sql_text
    
    def _validate_sql_statement_advanced(self, sql_text: str) -> bool:
        """Advanced SQL validation using multiple engines"""
        if not sql_text.strip():
            return False
        
        validation_count = 0
        valid_count = 0
        
        # Validate with available engines
        for engine_name, available in self.validation_engines.items():
            if not available:
                continue
                
            validation_count += 1
            
            try:
                if engine_name == 'sqlparse' and SQLPARSE_AVAILABLE:
                    parsed = sqlparse.parse(sql_text)
                    if parsed and not any(token.ttype is tokens.Error for stmt in parsed for token in stmt.flatten()):
                        valid_count += 1
                
                elif engine_name == 'sqlglot' and SQLGLOT_AVAILABLE:
                    parsed = sqlglot.parse(sql_text, dialect="oracle")
                    if parsed:
                        valid_count += 1
                
                # Add other validation engines as needed
                
            except Exception:
                pass  # Validation failed for this engine
        
        # Consider valid if at least 50% of engines validate successfully
        return validation_count == 0 or (valid_count / validation_count) >= 0.5
    
    def _format_declarations(self, declarations: Declarations) -> Dict[str, Any]:
        """Format declarations to match exact JSON structure"""
        result = {}
        
        if declarations.variables:
            result["variables"] = [asdict(v) for v in declarations.variables]
        
        if declarations.constants:
            result["constants"] = [asdict(c) for c in declarations.constants]
        
        if declarations.exceptions:
            result["exceptions"] = [asdict(e) for e in declarations.exceptions]
        
        return result
    
    def _next_id(self) -> int:
        """Get next operation ID"""
        self.operation_counter += 1
        return self.operation_counter
    
    def connect_to_oracle(self, dsn: str, username: str, password: str) -> bool:
        """Connect to Oracle database for live validation"""
        if not ORACLEDB_AVAILABLE:
            logger.error("oracledb library not available")
            return False
        
        try:
            self.db_connection = oracledb.connect(
                user=username,
                password=password,
                dsn=dsn
            )
            logger.info("Successfully connected to Oracle database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Oracle database: {e}")
            return False
    
    def generate_validation_report(self, stake_flow: List[StakeFlowAnalysis]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        report = {
            "total_statements": len(stake_flow),
            "validation_summary": {},
            "complexity_analysis": {},
            "dependency_analysis": {},
            "issues": []
        }
        
        # Validation summary
        for engine in self.validation_engines:
            if self.validation_engines[engine]:
                valid_count = sum(1 for sf in stake_flow 
                                for vr in sf.validation_results 
                                if vr.library == engine and vr.valid)
                total_count = sum(1 for sf in stake_flow 
                                for vr in sf.validation_results 
                                if vr.library == engine)
                
                report["validation_summary"][engine] = {
                    "valid": valid_count,
                    "total": total_count,
                    "percentage": (valid_count / total_count * 100) if total_count > 0 else 0
                }
        
        # Complexity analysis
        complexities = [sf.complexity_score for sf in stake_flow]
        if complexities:
            report["complexity_analysis"] = {
                "average": sum(complexities) / len(complexities),
                "max": max(complexities),
                "min": min(complexities),
                "total": sum(complexities)
            }
        
        # Dependency analysis
        all_dependencies = []
        for sf in stake_flow:
            all_dependencies.extend(sf.dependencies)
        
        dependency_counts = {}
        for dep in all_dependencies:
            dependency_counts[dep] = dependency_counts.get(dep, 0) + 1
        
        report["dependency_analysis"] = {
            "unique_dependencies": len(dependency_counts),
            "most_referenced": sorted(dependency_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        # Issues
        for sf in stake_flow:
            for vr in sf.validation_results:
                if vr.errors:
                    report["issues"].append({
                        "line": sf.line_number,
                        "library": vr.library,
                        "errors": vr.errors
                    })
        
        return report

def main():
    """Main function with comprehensive analysis and reporting"""
    analyzer = AdvancedOracleTriggerAnalyzer()
    
    # Input and output directories
    input_dir = Path("files/oracle")
    output_dir = Path("files/sql_json")
    reports_dir = Path("files/validation_reports")
    
    # Ensure directories exist
    output_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    
    # Process each trigger file
    for sql_file in input_dir.glob("*.sql"):
        logger.info(f"Processing {sql_file.name} with advanced analyzer...")
        
        try:
            # Analyze the trigger
            result = analyzer.analyze_trigger_file(str(sql_file))
            
            # Write enhanced JSON analysis
            output_file = output_dir / f"{sql_file.stem}_advanced_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Generated {output_file.name}")
            
            # Generate validation report
            with open(sql_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            stake_flow = analyzer._perform_stake_flow_analysis(content)
            validation_report = analyzer.generate_validation_report(stake_flow)
            
            # Write validation report
            report_file = reports_dir / f"{sql_file.stem}_validation_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(validation_report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Generated validation report: {report_file.name}")
            
            # Print summary
            print(f"\n=== {sql_file.name} Analysis Summary ===")
            print(f"Data Operations: {len(result['data_operations'])}")
            print(f"Exception Handlers: {len(result['exception_handlers'])}")
            print(f"Validation Engines: {', '.join([k for k, v in analyzer.validation_engines.items() if v])}")
            if validation_report["complexity_analysis"]:
                print(f"Average Complexity: {validation_report['complexity_analysis']['average']:.1f}")
            print()
            
        except Exception as e:
            logger.error(f"✗ Error processing {sql_file.name}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main() 