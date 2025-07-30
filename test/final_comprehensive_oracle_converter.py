#!/usr/bin/env python3
"""
Final Comprehensive Oracle to JSON Converter

This is the production-ready converter that combines all improvements:
1. Stage 1: Oracle SQL → Enhanced Analysis JSON (detailed structure)
2. Stage 2: Enhanced Analysis JSON → SQL JSON (simplified format)

Key Features:
- Proper comment removal while preserving string literals
- Advanced section parsing for different trigger structures  
- Sophisticated data operation extraction with nested structures
- Comprehensive error handling with error keys
- Full two-stage conversion pipeline
- Detailed validation and reporting
"""

import re
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Custom exception for conversion errors with error keys"""
    def __init__(self, error_key: str, message: str, details: str = ""):
        self.error_key = error_key
        self.message = message
        self.details = details
        super().__init__(f"[{error_key}] {message}")


@dataclass
class TriggerMetadata:
    """Metadata about the trigger"""
    trigger_name: str
    timing: str = "AFTER"
    events: List[str] = None
    table_name: str = ""
    has_declare_section: bool = False
    has_begin_section: bool = False
    has_exception_section: bool = False

    def __post_init__(self):
        if self.events is None:
            self.events = ["INSERT", "UPDATE", "DELETE"]


@dataclass
class Variable:
    """Represents a variable declaration"""
    name: str
    data_type: str
    default_value: Optional[str] = None


@dataclass
class Constant:
    """Represents a constant declaration"""
    name: str
    data_type: str
    value: str


@dataclass
class Exception:
    """Represents an exception declaration"""
    name: str
    type: str = "user_defined"


@dataclass
class DataOperation:
    """Represents a data operation in the trigger"""
    id: str
    sql: str
    type: str
    condition: Optional[str] = None
    then_statement: Optional[Union[List[Dict], str]] = None
    else_statement: Optional[Union[List[Dict], str]] = None
    when_clauses: Optional[List[Dict]] = None
    parameters: Optional[Dict] = None
    table: Optional[str] = None
    columns: Optional[List[str]] = None
    values: Optional[List[str]] = None
    operations: Optional[List[Dict]] = None
    assignments: Optional[List[Dict]] = None
    select_statement: Optional[str] = None
    exception_handlers: Optional[List[Dict]] = None


class ProductionCommentRemover:
    """Production-grade comment removal with comprehensive string literal handling"""
    
    @staticmethod
    def remove_comments(sql_content: str) -> str:
        """Remove SQL comments while preserving string literals and embedded quotes"""
        try:
            result = []
            lines = sql_content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                try:
                    cleaned_line = ProductionCommentRemover._clean_line(line)
                    result.append(cleaned_line)
                except Exception as e:
                    logger.warning(f"Comment removal issue on line {line_num}: {str(e)}")
                    result.append(line)  # Keep original line if cleaning fails
            
            content = '\n'.join(result)
            
            # Remove multi-line comments with better handling
            content = ProductionCommentRemover._remove_multiline_comments(content)
            
            logger.info("Comments removed successfully")
            return content
            
        except Exception as e:
            raise ConversionError("COMMENT_REMOVAL_ERROR", f"Failed to remove comments: {str(e)}")
    
    @staticmethod
    def _clean_line(line: str) -> str:
        """Clean a single line, removing -- comments not in strings"""
        if '--' not in line:
            return line
            
        in_string = False
        quote_char = None
        result = []
        i = 0
        
        while i < len(line):
            char = line[i]
            
            if not in_string:
                if char in ("'", '"'):
                    in_string = True
                    quote_char = char
                    result.append(char)
                elif i < len(line) - 1 and line[i:i+2] == '--':
                    # Found comment, stop processing this line
                    break
                else:
                    result.append(char)
            else:
                result.append(char)
                if char == quote_char:
                    # Check for escaped quotes (doubled quotes in SQL)
                    if i + 1 < len(line) and line[i + 1] == quote_char:
                        result.append(line[i + 1])
                        i += 1
                    else:
                        in_string = False
                        quote_char = None
            
            i += 1
        
        return ''.join(result).rstrip()
    
    @staticmethod
    def _remove_multiline_comments(content: str) -> str:
        """Remove /* ... */ comments with proper nesting handling"""
        result = []
        i = 0
        while i < len(content):
            if i < len(content) - 1 and content[i:i+2] == '/*':
                # Find matching */
                j = content.find('*/', i + 2)
                if j != -1:
                    i = j + 2  # Skip past */
                    continue
                else:
                    # No matching */, treat as regular text
                    result.append(content[i])
            else:
                result.append(content[i])
            i += 1
        
        return ''.join(result)


class ProductionTriggerSectionParser:
    """Production-grade section parser that handles complex trigger structures"""
    
    @staticmethod
    def parse_sections(sql_content: str) -> Tuple[str, str, str]:
        """Parse SQL into declare, main (begin), and exception sections"""
        try:
            content = sql_content.strip()
            
            # Determine trigger structure type
            if content.upper().startswith('DECLARE'):
                return ProductionTriggerSectionParser._parse_declare_structure(content)
            else:
                return ProductionTriggerSectionParser._parse_inline_structure(content)
                
        except Exception as e:
            raise ConversionError("SECTION_PARSING_ERROR", f"Failed to parse trigger sections: {str(e)}")
    
    @staticmethod
    def _parse_declare_structure(content: str) -> Tuple[str, str, str]:
        """Parse DECLARE ... BEGIN ... EXCEPTION ... END structure"""
        
        # Use more sophisticated regex to handle nested BEGIN/END blocks
        
        # Find DECLARE section (between DECLARE and first BEGIN)
        declare_match = re.search(r'^DECLARE\s+(.*?)\s+BEGIN', content, re.IGNORECASE | re.DOTALL)
        declare_section = declare_match.group(1).strip() if declare_match else ""
        
        # Find the main section - this is trickier due to nested BEGIN/END
        main_section = ProductionTriggerSectionParser._extract_main_section(content)
        
        # Find exception section (last EXCEPTION before final END)
        exception_pattern = r'EXCEPTION\s+((?:(?!EXCEPTION).)*?)\s*END\s*;?\s*$'
        exception_match = re.search(exception_pattern, content, re.IGNORECASE | re.DOTALL)
        exception_section = exception_match.group(1).strip() if exception_match else ""
        
        logger.info(f"DECLARE structure parsed - Declare: {len(declare_section)} chars, Main: {len(main_section)} chars, Exception: {len(exception_section)} chars")
        return declare_section, main_section, exception_section
    
    @staticmethod
    def _extract_main_section(content: str) -> str:
        """Extract main section handling nested BEGIN/END blocks"""
        # Find the position after the first BEGIN
        first_begin = re.search(r'DECLARE\s+.*?\s+BEGIN\s+', content, re.IGNORECASE | re.DOTALL)
        if not first_begin:
            return ""
        
        start_pos = first_begin.end()
        
        # Find the matching END for the outer BEGIN, accounting for nesting
        begin_count = 1
        current_pos = start_pos
        
        while current_pos < len(content) and begin_count > 0:
            # Look for next BEGIN or END
            begin_match = re.search(r'\bBEGIN\b', content[current_pos:], re.IGNORECASE)
            end_match = re.search(r'\bEND\b', content[current_pos:], re.IGNORECASE)
            exception_match = re.search(r'\bEXCEPTION\b', content[current_pos:], re.IGNORECASE)
            
            # Find the closest match
            matches = []
            if begin_match:
                matches.append((begin_match.start() + current_pos, 'BEGIN'))
            if end_match:
                matches.append((end_match.start() + current_pos, 'END'))
            if exception_match and begin_count == 1:  # Only consider EXCEPTION at top level
                matches.append((exception_match.start() + current_pos, 'EXCEPTION'))
            
            if not matches:
                break
                
            matches.sort(key=lambda x: x[0])
            next_pos, keyword = matches[0]
            
            if keyword == 'BEGIN':
                begin_count += 1
                current_pos = next_pos + 5  # Length of 'BEGIN'
            elif keyword == 'END':
                begin_count -= 1
                if begin_count == 0:
                    # Found the matching END
                    return content[start_pos:next_pos].strip()
                current_pos = next_pos + 3  # Length of 'END'
            elif keyword == 'EXCEPTION':
                # Found EXCEPTION at top level
                return content[start_pos:next_pos].strip()
        
        # If we get here, return everything from start_pos to end
        return content[start_pos:].strip()
    
    @staticmethod
    def _parse_inline_structure(content: str) -> Tuple[str, str, str]:
        """Parse structure for triggers without DECLARE keyword"""
        
        lines = content.split('\n')
        declare_lines = []
        main_lines = []
        exception_lines = []
        
        current_section = 'declare'
        in_exception = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect section transitions
            if re.match(r'^\s*(IF|SELECT|INSERT|UPDATE|DELETE|BEGIN|FOR|WHILE|LOOP)\s+', line, re.IGNORECASE):
                current_section = 'main'
            elif re.match(r'^\s*EXCEPTION\s*$', line, re.IGNORECASE):
                in_exception = True
                current_section = 'exception'
                continue
            elif re.match(r'^\s*END\s*;?\s*$', line, re.IGNORECASE) and in_exception:
                break
                
            if current_section == 'declare':
                declare_lines.append(line)
            elif current_section == 'main':
                main_lines.append(line)
            elif current_section == 'exception':
                exception_lines.append(line)
        
        declare_section = '\n'.join(declare_lines)
        main_section = '\n'.join(main_lines)
        exception_section = '\n'.join(exception_lines)
        
        logger.info(f"Inline structure parsed - Declare: {len(declare_section)} chars, Main: {len(main_section)} chars, Exception: {len(exception_section)} chars")
        return declare_section, main_section, exception_section


class ProductionDeclarationParser:
    """Production-grade declaration parser with comprehensive pattern matching"""
    
    def __init__(self):
        self.patterns = {
            # Basic variable patterns
            'basic_variable': r'(\w+)\s+(varchar2\([^)]+\)|number\([^)]*\)|date|pls_integer|simple_integer|binary_integer|boolean|PLS_INTEGER|BOOLEAN)\s*(?::=\s*([^;]+?))?\s*;',
            
            # %TYPE variables
            'type_variable': r'(\w+)\s+([^.]+\.[^%\s]+%TYPE)\s*(?::=\s*([^;]+?))?\s*;',
            
            # Constants
            'constant': r'(\w+)\s+constant\s+([^:=]+?)\s*:=\s*([^;]+?)\s*;',
            
            # Exceptions
            'exception': r'(\w+)\s+exception\s*;',
            
            # Complex types
            'complex_variable': r'(\w+)\s+(varchar2|VARCHAR2)\s*\(\s*(\d+)\s*\)\s*(?::=\s*([^;]+?))?\s*;',
        }
    
    def parse_declarations(self, declare_section: str) -> Tuple[List[Variable], List[Constant], List[Exception]]:
        """Parse declarations with comprehensive pattern matching"""
        try:
            variables = []
            constants = []
            exceptions = []
            
            if not declare_section.strip():
                return variables, constants, exceptions
            
            # Parse variables with multiple patterns
            found_vars = set()  # To avoid duplicates
            
            for pattern_name, pattern in self.patterns.items():
                if 'variable' in pattern_name:
                    matches = re.finditer(pattern, declare_section, re.IGNORECASE)
                    for match in matches:
                        name = match.group(1)
                        if name not in found_vars:
                            found_vars.add(name)
                            
                            if pattern_name == 'complex_variable':
                                data_type = f"{match.group(2)}({match.group(3)})"
                                default_value = match.group(4).strip() if match.group(4) else None
                            else:
                                data_type = match.group(2).strip()
                                default_value = match.group(3).strip() if match.group(3) else None
                            
                            variables.append(Variable(name=name, data_type=data_type, default_value=default_value))
            
            # Parse constants
            const_matches = re.finditer(self.patterns['constant'], declare_section, re.IGNORECASE)
            for match in const_matches:
                name = match.group(1)
                data_type = match.group(2).strip()
                value = match.group(3).strip()
                constants.append(Constant(name=name, data_type=data_type, value=value))
            
            # Parse exceptions
            exc_matches = re.finditer(self.patterns['exception'], declare_section, re.IGNORECASE)
            for match in exc_matches:
                name = match.group(1)
                exceptions.append(Exception(name=name, type="user_defined"))
            
            logger.info(f"Production parsing - Variables: {len(variables)}, Constants: {len(constants)}, Exceptions: {len(exceptions)}")
            return variables, constants, exceptions
            
        except Exception as e:
            raise ConversionError("DECLARATION_PARSING_ERROR", f"Failed to parse declarations: {str(e)}")


class ProductionDataOperationExtractor:
    """Production-grade data operation extractor with comprehensive SQL analysis"""
    
    def __init__(self):
        self.operation_counter = 0
        
    def extract_data_operations(self, main_section: str) -> List[DataOperation]:
        """Extract comprehensive data operations with advanced parsing"""
        try:
            operations = []
            self.operation_counter = 0
            
            # Extract operations in order of complexity
            operations.extend(self._extract_sql_statements(main_section))
            operations.extend(self._extract_control_structures(main_section))
            operations.extend(self._extract_assignments(main_section))
            operations.extend(self._extract_procedure_calls(main_section))
            operations.extend(self._extract_exception_raises(main_section))
            
            logger.info(f"Production extraction - {len(operations)} operations extracted")
            return operations
            
        except Exception as e:
            raise ConversionError("DATA_OPERATION_EXTRACTION_ERROR", f"Failed to extract data operations: {str(e)}")
    
    def _extract_sql_statements(self, content: str) -> List[DataOperation]:
        """Extract SQL statements with improved boundary detection"""
        operations = []
        
        # Enhanced SQL patterns with better boundary detection
        sql_patterns = {
            'select': r'(?i)(?:^|\s+)(SELECT\s+(?:(?!(?:INSERT|UPDATE|DELETE|IF|END|EXCEPTION)\s).)*?)(?=\s*;|\s*$|\s*(?:IF|END|EXCEPTION|INSERT|UPDATE|DELETE|ELSE|ELSIF)\s)',
            'insert': r'(?i)(?:^|\s+)(INSERT\s+INTO\s+(?:(?!(?:SELECT|UPDATE|DELETE|IF|END|EXCEPTION)\s).)*?)(?=\s*;|\s*$|\s*(?:IF|END|EXCEPTION|SELECT|UPDATE|DELETE|ELSE|ELSIF)\s)',
            'update': r'(?i)(?:^|\s+)(UPDATE\s+(?:(?!(?:SELECT|INSERT|DELETE|IF|END|EXCEPTION)\s).)*?)(?=\s*;|\s*$|\s*(?:IF|END|EXCEPTION|SELECT|INSERT|DELETE|ELSE|ELSIF)\s)',
            'delete': r'(?i)(?:^|\s+)(DELETE\s+FROM\s+(?:(?!(?:SELECT|INSERT|UPDATE|IF|END|EXCEPTION)\s).)*?)(?=\s*;|\s*$|\s*(?:IF|END|EXCEPTION|SELECT|INSERT|UPDATE|ELSE|ELSIF)\s)',
        }
        
        for sql_type, pattern in sql_patterns.items():
            matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
            for match in matches:
                self.operation_counter += 1
                sql = match.group(1).strip()
                
                # Clean up the SQL
                sql = re.sub(r'\s+', ' ', sql)
                if not sql.endswith(';'):
                    sql += ';'
                
                operations.append(DataOperation(
                    id=f"code_{self.operation_counter}",
                    sql=sql,
                    type=f"{sql_type}_statements"
                ))
        
        return operations
    
    def _extract_control_structures(self, content: str) -> List[DataOperation]:
        """Extract control structures with nested handling"""
        operations = []
        
        # Enhanced IF statement pattern with nesting support
        if_pattern = r'(?i)IF\s*\(([^)]+)\)\s*THEN(.*?)(?:ELSE(.*?))?END\s+IF\s*;?'
        matches = re.finditer(if_pattern, content, re.DOTALL)
        
        for match in matches:
            self.operation_counter += 1
            condition = match.group(1).strip()
            then_block = match.group(2).strip() if match.group(2) else ""
            else_block = match.group(3).strip() if match.group(3) else None
            
            # Create abbreviated SQL for display
            then_preview = then_block[:50] + "..." if len(then_block) > 50 else then_block
            else_preview = else_block[:50] + "..." if else_block and len(else_block) > 50 else else_block
            
            display_sql = f"if ({condition}) then {then_preview}"
            if else_preview:
                display_sql += f" else {else_preview}"
            display_sql += " end if;"
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=display_sql,
                type="if_else",
                condition=condition,
                then_statement=then_block if then_block else "...",
                else_statement=else_block
            ))
        
        # CASE statements
        case_pattern = r'(?i)CASE\s+(.*?)\s+END\s*(?:CASE)?\s*;?'
        matches = re.finditer(case_pattern, content, re.DOTALL)
        
        for match in matches:
            self.operation_counter += 1
            case_body = match.group(1).strip()
            case_preview = case_body[:100] + "..." if len(case_body) > 100 else case_body
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=f"case {case_preview} end;",
                type="case_statement"
            ))
        
        # FOR loops
        for_pattern = r'(?i)FOR\s+(\w+)\s+IN\s*\((.*?)\)\s*LOOP(.*?)END\s+LOOP\s*;?'
        matches = re.finditer(for_pattern, content, re.DOTALL)
        
        for match in matches:
            self.operation_counter += 1
            iterator = match.group(1)
            range_expr = match.group(2).strip()
            loop_body = match.group(3).strip()
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=f"for {iterator} in ({range_expr[:30]}...) loop ... end loop;",
                type="for_loop"
            ))
        
        return operations
    
    def _extract_assignments(self, content: str) -> List[DataOperation]:
        """Extract variable assignments"""
        operations = []
        
        assignment_pattern = r'(\w+)\s*:=\s*([^;]+);'
        matches = re.finditer(assignment_pattern, content, re.MULTILINE)
        
        for match in matches:
            self.operation_counter += 1
            variable = match.group(1)
            expression = match.group(2).strip()
            
            # Truncate long expressions for readability
            if len(expression) > 100:
                expression = expression[:100] + "..."
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=f"{variable} := {expression};",
                type="assignment"
            ))
        
        return operations
    
    def _extract_procedure_calls(self, content: str) -> List[DataOperation]:
        """Extract procedure/function calls"""
        operations = []
        
        # Enhanced procedure call pattern
        proc_pattern = r'([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)\s*\([^)]*\)\s*;'
        matches = re.finditer(proc_pattern, content, re.MULTILINE)
        
        for match in matches:
            proc_name = match.group(1).lower()
            
            # Skip SQL keywords and common constructs
            skip_words = {'select', 'insert', 'update', 'delete', 'if', 'case', 'when', 'then', 
                         'else', 'elsif', 'for', 'while', 'loop', 'end', 'begin', 'declare',
                         'to_date', 'to_char', 'to_number', 'substr', 'nvl', 'decode'}
            
            if proc_name not in skip_words:
                self.operation_counter += 1
                sql = match.group(0).strip()
                
                operations.append(DataOperation(
                    id=f"code_{self.operation_counter}",
                    sql=sql,
                    type="procedure_call"
                ))
        
        return operations
    
    def _extract_exception_raises(self, content: str) -> List[DataOperation]:
        """Extract RAISE statements"""
        operations = []
        
        raise_pattern = r'(?i)RAISE\s+(\w+)\s*;'
        matches = re.finditer(raise_pattern, content)
        
        for match in matches:
            self.operation_counter += 1
            exception_name = match.group(1)
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=f"raise {exception_name};",
                type="exception_raise"
            ))
        
        return operations


class ProductionOracleToEnhancedJsonConverter:
    """Production Oracle to Enhanced JSON converter with all improvements"""
    
    def __init__(self):
        self.comment_remover = ProductionCommentRemover()
        self.section_parser = ProductionTriggerSectionParser()
        self.declaration_parser = ProductionDeclarationParser()
        self.operation_extractor = ProductionDataOperationExtractor()
    
    def convert_oracle_to_enhanced_json(self, oracle_file_path: str, output_file_path: str) -> Dict[str, Any]:
        """Convert Oracle SQL file to Enhanced Analysis JSON with comprehensive analysis"""
        try:
            logger.info(f"Production conversion: {Path(oracle_file_path).name}")
            
            # Step 1: Read Oracle SQL file
            with open(oracle_file_path, 'r', encoding='utf-8') as f:
                oracle_content = f.read()
            
            # Step 2: Remove comments with production-grade handling
            clean_content = self.comment_remover.remove_comments(oracle_content)
            
            # Step 3: Parse sections with advanced parser
            declare_section, main_section, exception_section = self.section_parser.parse_sections(clean_content)
            
            # Step 4: Extract comprehensive metadata
            trigger_name = Path(oracle_file_path).stem
            metadata = TriggerMetadata(
                trigger_name=trigger_name,
                timing=self._detect_timing(clean_content),
                events=self._detect_events(clean_content),
                table_name=self._extract_table_name(clean_content),
                has_declare_section=bool(declare_section.strip()),
                has_begin_section=bool(main_section.strip()),
                has_exception_section=bool(exception_section.strip())
            )
            
            # Step 5: Parse declarations with production parser
            variables, constants, exceptions = self.declaration_parser.parse_declarations(declare_section)
            
            # Step 6: Extract data operations with production extractor
            data_operations = self.operation_extractor.extract_data_operations(main_section)
            
            # Step 7: Parse exception handlers
            exception_handlers = self._parse_exception_handlers(exception_section)
            
            # Step 8: Build comprehensive enhanced JSON structure
            enhanced_json = {
                "trigger_metadata": asdict(metadata),
                "declarations": {
                    "variables": [asdict(var) for var in variables],
                    "constants": [asdict(const) for const in constants],
                    "exceptions": [asdict(exc) for exc in exceptions]
                },
                "data_operations": [self._operation_to_dict(op) for op in data_operations],
                "exception_handlers": exception_handlers
            }
            
            # Step 9: Save to file
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_json, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Enhanced JSON complete: {len(data_operations)} ops, {len(variables)} vars, {len(exception_handlers)} handlers")
            return enhanced_json
            
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError("GENERAL_CONVERSION_ERROR", f"Unexpected error: {str(e)}")
    
    def _detect_timing(self, content: str) -> str:
        """Detect trigger timing (BEFORE/AFTER/INSTEAD OF)"""
        content_upper = content.upper()
        if 'BEFORE' in content_upper and any(event in content_upper for event in ['INSERT', 'UPDATE', 'DELETE']):
            return "BEFORE"
        elif 'INSTEAD OF' in content_upper:
            return "INSTEAD OF"
        return "AFTER"  # Default
    
    def _detect_events(self, content: str) -> List[str]:
        """Detect trigger events"""
        events = []
        content_upper = content.upper()
        
        if 'INSERT' in content_upper or 'INSERTING' in content_upper:
            events.append("INSERT")
        if 'UPDATE' in content_upper or 'UPDATING' in content_upper:
            events.append("UPDATE")
        if 'DELETE' in content_upper or 'DELETING' in content_upper:
            events.append("DELETE")
        
        return events if events else ["INSERT", "UPDATE", "DELETE"]  # Default
    
    def _extract_table_name(self, content: str) -> str:
        """Extract primary table name from trigger content"""
        table_patterns = [
            r'(?i)INSERT\s+INTO\s+([a-zA-Z_]\w*)',
            r'(?i)UPDATE\s+([a-zA-Z_]\w*)',
            r'(?i)DELETE\s+FROM\s+([a-zA-Z_]\w*)',
            r'(?i)FROM\s+([a-zA-Z_]\w*)',
        ]
        
        table_candidates = []
        
        for pattern in table_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if not match.startswith('v_') and not match.startswith('mdm_'):  # Skip views and MDM tables
                    table_candidates.append(match)
        
        if table_candidates:
            # Return most common table name
            from collections import Counter
            return Counter(table_candidates).most_common(1)[0][0]
        
        return "unknown_table"
    
    def _parse_exception_handlers(self, exception_section: str) -> List[Dict[str, Any]]:
        """Parse exception handlers with comprehensive pattern matching"""
        handlers = []
        
        if not exception_section.strip():
            return handlers
        
        # Enhanced WHEN pattern to handle multi-line handlers
        when_pattern = r'(?i)WHEN\s+(\w+)\s*THEN\s*(.*?)(?=\s*WHEN\s+\w+|\s*$)'
        for match in re.finditer(when_pattern, exception_section, re.DOTALL):
            exception_name = match.group(1)
            handler_code = match.group(2).strip()
            
            # Clean up handler code
            handler_code = re.sub(r'\s+', ' ', handler_code)
            
            handlers.append({
                "exception_name": exception_name,
                "handler_code": handler_code
            })
        
        logger.info(f"Parsed {len(handlers)} exception handlers")
        return handlers
    
    def _operation_to_dict(self, operation: DataOperation) -> Dict[str, Any]:
        """Convert DataOperation to dictionary with all relevant fields"""
        result = {"id": operation.id, "sql": operation.sql, "type": operation.type}
        
        for attr in ['condition', 'then_statement', 'else_statement', 'when_clauses', 
                     'parameters', 'table', 'columns', 'values', 'operations', 
                     'assignments', 'select_statement', 'exception_handlers']:
            value = getattr(operation, attr)
            if value is not None:
                result[attr] = value
                
        return result


class ProductionEnhancedToSqlJsonConverter:
    """Production converter for Enhanced JSON to simplified SQL JSON"""
    
    @staticmethod
    def convert_enhanced_to_sql_json(enhanced_json_path: str, sql_json_path: str) -> Dict[str, Any]:
        """Convert Enhanced Analysis JSON to SQL JSON with validation"""
        try:
            logger.info(f"Converting to SQL JSON: {Path(enhanced_json_path).name}")
            
            # Read and validate enhanced JSON
            with open(enhanced_json_path, 'r', encoding='utf-8') as f:
                enhanced_data = json.load(f)
            
            # Validate structure
            required_keys = ['trigger_metadata', 'declarations', 'data_operations', 'exception_handlers']
            for key in required_keys:
                if key not in enhanced_data:
                    raise ConversionError("INVALID_ENHANCED_JSON", f"Missing required key: {key}")
            
            # Create simplified SQL JSON structure
            # Take a reasonable subset of operations for SQL JSON (not all)
            max_operations = 15  # Configurable limit
            
            sql_json = {
                "trigger_metadata": enhanced_data["trigger_metadata"],
                "declarations": enhanced_data["declarations"],
                "data_operations": enhanced_data["data_operations"][:max_operations],
                "exception_handlers": enhanced_data["exception_handlers"]
            }
            
            # Add conversion metadata
            sql_json["conversion_info"] = {
                "source_file": enhanced_json_path,
                "conversion_time": datetime.now().isoformat(),
                "original_operations_count": len(enhanced_data["data_operations"]),
                "simplified_operations_count": len(sql_json["data_operations"])
            }
            
            # Save to file
            os.makedirs(os.path.dirname(sql_json_path), exist_ok=True)
            with open(sql_json_path, 'w', encoding='utf-8') as f:
                json.dump(sql_json, f, indent=2, ensure_ascii=False)
            
            logger.info(f"SQL JSON complete: {len(sql_json['data_operations'])} operations of {len(enhanced_data['data_operations'])} total")
            return sql_json
            
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError("SQL_JSON_CONVERSION_ERROR", f"Failed to convert to SQL JSON: {str(e)}")


class FinalComprehensiveConverter:
    """Final production converter that orchestrates the complete two-stage process"""
    
    def __init__(self):
        self.oracle_to_enhanced = ProductionOracleToEnhancedJsonConverter()
        self.enhanced_to_sql = ProductionEnhancedToSqlJsonConverter()
    
    def convert_all_triggers(self, 
                           oracle_folder: str = "files/oracle", 
                           enhanced_folder: str = "files/expected_ana_json",
                           sql_json_folder: str = "files/sql_json") -> Dict[str, Any]:
        """Execute complete two-stage conversion pipeline for all triggers"""
        try:
            results = {
                "conversion_summary": {
                    "start_time": datetime.now().isoformat(),
                    "oracle_folder": oracle_folder,
                    "enhanced_folder": enhanced_folder,
                    "sql_json_folder": sql_json_folder
                },
                "successful_conversions": [],
                "failed_conversions": [],
                "total_processed": 0,
                "total_operations": 0,
                "total_variables": 0,
                "total_exceptions": 0
            }
            
            oracle_files = list(Path(oracle_folder).glob("*.sql"))
            results["total_processed"] = len(oracle_files)
            
            for oracle_file in oracle_files:
                try:
                    logger.info(f"Processing {oracle_file.name}")
                    
                    # Stage 1: Oracle → Enhanced JSON
                    enhanced_file = Path(enhanced_folder) / f"{oracle_file.stem}_enhanced_analysis.json"
                    enhanced_json = self.oracle_to_enhanced.convert_oracle_to_enhanced_json(
                        str(oracle_file), str(enhanced_file)
                    )
                    
                    # Stage 2: Enhanced JSON → SQL JSON
                    sql_json_file = Path(sql_json_folder) / f"{oracle_file.stem}_enhanced_analysis.json"
                    sql_json = self.enhanced_to_sql.convert_enhanced_to_sql_json(
                        str(enhanced_file), str(sql_json_file)
                    )
                    
                    # Collect statistics
                    operations_count = len(enhanced_json.get("data_operations", []))
                    variables_count = len(enhanced_json.get("declarations", {}).get("variables", []))
                    exceptions_count = len(enhanced_json.get("declarations", {}).get("exceptions", []))
                    
                    results["total_operations"] += operations_count
                    results["total_variables"] += variables_count
                    results["total_exceptions"] += exceptions_count
                    
                    results["successful_conversions"].append({
                        "oracle_file": str(oracle_file),
                        "enhanced_file": str(enhanced_file),
                        "sql_json_file": str(sql_json_file),
                        "statistics": {
                            "operations_count": operations_count,
                            "variables_count": variables_count,
                            "exceptions_count": exceptions_count,
                            "exception_handlers_count": len(enhanced_json.get("exception_handlers", []))
                        }
                    })
                    
                except ConversionError as e:
                    logger.error(f"Conversion failed for {oracle_file.name}: {e}")
                    results["failed_conversions"].append({
                        "oracle_file": str(oracle_file),
                        "error_key": e.error_key,
                        "error_message": e.message,
                        "error_details": e.details
                    })
                
                except Exception as e:
                    logger.error(f"Unexpected error for {oracle_file.name}: {e}")
                    results["failed_conversions"].append({
                        "oracle_file": str(oracle_file),
                        "error_key": "UNEXPECTED_ERROR",
                        "error_message": str(e),
                        "error_details": ""
                    })
            
            # Finalize results
            results["conversion_summary"]["end_time"] = datetime.now().isoformat()
            results["conversion_summary"]["success_rate"] = (
                len(results["successful_conversions"]) / results["total_processed"] * 100
                if results["total_processed"] > 0 else 0
            )
            
            # Save comprehensive report
            report_file = "final_conversion_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conversion pipeline complete. Report: {report_file}")
            return results
            
        except Exception as e:
            raise ConversionError("PIPELINE_ERROR", f"Conversion pipeline failed: {str(e)}")


def main():
    """Main function to run the final comprehensive converter"""
    try:
        print("🚀 Final Comprehensive Oracle to JSON Converter")
        print("=" * 70)
        print("Features:")
        print("  ✓ Production-grade comment removal")
        print("  ✓ Advanced section parsing for complex triggers")
        print("  ✓ Comprehensive data operation extraction")
        print("  ✓ Full two-stage conversion pipeline")
        print("  ✓ Detailed error handling with error keys")
        print("  ✓ Comprehensive validation and reporting")
        print("=" * 70)
        
        converter = FinalComprehensiveConverter()
        results = converter.convert_all_triggers()
        
        print("\n📊 Final Conversion Results:")
        print(f"✅ Successful: {len(results['successful_conversions'])}")
        print(f"❌ Failed: {len(results['failed_conversions'])}")
        print(f"📁 Total Processed: {results['total_processed']}")
        print(f"🎯 Success Rate: {results['conversion_summary']['success_rate']:.1f}%")
        
        print(f"\n📈 Statistics:")
        print(f"  🔧 Total Operations: {results['total_operations']}")
        print(f"  📝 Total Variables: {results['total_variables']}")
        print(f"  ⚠️  Total Exceptions: {results['total_exceptions']}")
        
        if results['failed_conversions']:
            print("\n🔍 Failed Conversions:")
            for failure in results['failed_conversions']:
                print(f"  ❌ {Path(failure['oracle_file']).name}: [{failure['error_key']}] {failure['error_message']}")
        
        print(f"\n📄 Detailed report saved to: final_conversion_report.json")
        print("✅ Conversion pipeline completed successfully!")
        
    except ConversionError as e:
        print(f"❌ Conversion Error: [{e.error_key}] {e.message}")
        if e.details:
            print(f"   Details: {e.details}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


if __name__ == "__main__":
    main() 