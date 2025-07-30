#!/usr/bin/env python3
"""
Enhanced Oracle to JSON Converter V2

Improvements over V1:
1. Better section parsing for different trigger structures
2. More sophisticated data operation extraction
3. Better handling of nested control structures
4. Improved pattern matching for complex SQL statements
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


class ImprovedCommentRemover:
    """Enhanced comment removal with better string literal handling"""
    
    @staticmethod
    def remove_comments(sql_content: str) -> str:
        """Remove SQL comments while preserving string literals"""
        try:
            result = []
            lines = sql_content.split('\n')
            
            for line in lines:
                cleaned_line = ImprovedCommentRemover._clean_line(line)
                result.append(cleaned_line)
            
            content = '\n'.join(result)
            
            # Remove multi-line comments more carefully
            content = ImprovedCommentRemover._remove_multiline_comments(content)
            
            logger.info("Comments removed successfully")
            return content
            
        except Exception as e:
            raise ConversionError("COMMENT_REMOVAL_ERROR", f"Failed to remove comments: {str(e)}")
    
    @staticmethod
    def _clean_line(line: str) -> str:
        """Clean a single line, removing -- comments not in strings"""
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
                    # Check for escaped quotes
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
        """Remove /* ... */ comments"""
        # Simple approach for now - could be improved to handle nested comments
        return re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)


class ImprovedTriggerSectionParser:
    """Enhanced section parser that handles different trigger structures"""
    
    @staticmethod
    def parse_sections(sql_content: str) -> Tuple[str, str, str]:
        """Parse SQL into declare, main (begin), and exception sections"""
        try:
            content = sql_content.strip()
            
            # Handle different trigger structures
            if content.upper().startswith('DECLARE'):
                return ImprovedTriggerSectionParser._parse_declare_begin_structure(content)
            else:
                return ImprovedTriggerSectionParser._parse_simple_structure(content)
                
        except Exception as e:
            raise ConversionError("SECTION_PARSING_ERROR", f"Failed to parse trigger sections: {str(e)}")
    
    @staticmethod
    def _parse_declare_begin_structure(content: str) -> Tuple[str, str, str]:
        """Parse DECLARE ... BEGIN ... EXCEPTION ... END structure"""
        
        # Find DECLARE section
        declare_match = re.search(r'^DECLARE\s+(.*?)\s+BEGIN', content, re.IGNORECASE | re.DOTALL)
        declare_section = declare_match.group(1).strip() if declare_match else ""
        
        # Find main section (between BEGIN and EXCEPTION or END)
        begin_pattern = r'BEGIN\s+(.*?)\s+(?:EXCEPTION|END\s*;?\s*$)'
        begin_match = re.search(begin_pattern, content, re.IGNORECASE | re.DOTALL)
        main_section = begin_match.group(1).strip() if begin_match else ""
        
        # Find exception section
        exception_pattern = r'EXCEPTION\s+(.*?)\s+END\s*;?\s*$'
        exception_match = re.search(exception_pattern, content, re.IGNORECASE | re.DOTALL)
        exception_section = exception_match.group(1).strip() if exception_match else ""
        
        # If main section is still too small, try alternative approach
        if len(main_section) < 100:  # Threshold for "too small"
            # Maybe there's no EXCEPTION section
            begin_pattern_alt = r'BEGIN\s+(.*?)\s+END\s*;?\s*$'
            begin_match_alt = re.search(begin_pattern_alt, content, re.IGNORECASE | re.DOTALL)
            if begin_match_alt and len(begin_match_alt.group(1)) > len(main_section):
                main_section = begin_match_alt.group(1).strip()
                exception_section = ""  # No exception section
        
        logger.info(f"DECLARE structure - Declare: {len(declare_section)} chars, Main: {len(main_section)} chars, Exception: {len(exception_section)} chars")
        return declare_section, main_section, exception_section
    
    @staticmethod
    def _parse_simple_structure(content: str) -> Tuple[str, str, str]:
        """Parse structure without DECLARE keyword"""
        
        # Try to find variable declarations at the start
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
                
            if re.match(r'^\s*(IF|SELECT|INSERT|UPDATE|DELETE|BEGIN)\s+', line, re.IGNORECASE):
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
        
        logger.info(f"Simple structure - Declare: {len(declare_section)} chars, Main: {len(main_section)} chars, Exception: {len(exception_section)} chars")
        return declare_section, main_section, exception_section


class ImprovedDeclarationParser:
    """Enhanced declaration parser with better pattern matching"""
    
    def __init__(self):
        self.patterns = {
            'variable': r'(\w+)\s+((?:varchar2|number|date|pls_integer|simple_integer|binary_integer|boolean|PLS_INTEGER|BOOLEAN|%TYPE)[^;]*?)(?::=\s*([^;]+?))?\s*;',
            'constant': r'(\w+)\s+constant\s+([^:=]+?)\s*:=\s*([^;]+?)\s*;',
            'exception': r'(\w+)\s+exception\s*;',
            # Enhanced patterns
            'typed_variable': r'(\w+)\s+([^.]+\.[^%]+%TYPE)(?:\s*:=\s*([^;]+?))?\s*;',
            'simple_var': r'(\w+)\s+(varchar2\(\d+\)|PLS_INTEGER|BOOLEAN)(?:\s*:=\s*([^;]+?))?\s*;',
        }
    
    def parse_declarations(self, declare_section: str) -> Tuple[List[Variable], List[Constant], List[Exception]]:
        """Parse declarations with improved pattern matching"""
        try:
            variables = []
            constants = []
            exceptions = []
            
            if not declare_section.strip():
                return variables, constants, exceptions
            
            # Parse all variable types
            for pattern_name, pattern in self.patterns.items():
                if pattern_name.endswith('variable') or pattern_name.endswith('var'):
                    matches = re.finditer(pattern, declare_section, re.IGNORECASE)
                    for match in matches:
                        name = match.group(1)
                        data_type = match.group(2).strip()
                        default_value = match.group(3).strip() if match.group(3) else None
                        
                        # Avoid duplicates
                        if not any(var.name == name for var in variables):
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
            
            logger.info(f"Enhanced parsing - Variables: {len(variables)}, Constants: {len(constants)}, Exceptions: {len(exceptions)}")
            return variables, constants, exceptions
            
        except Exception as e:
            raise ConversionError("DECLARATION_PARSING_ERROR", f"Failed to parse declarations: {str(e)}")


class AdvancedDataOperationExtractor:
    """Advanced data operation extractor with nested structure support"""
    
    def __init__(self):
        self.operation_counter = 0
        
    def extract_data_operations(self, main_section: str) -> List[DataOperation]:
        """Extract all data operations with nested structure support"""
        try:
            operations = []
            self.operation_counter = 0
            
            # Extract different types of operations
            operations.extend(self._extract_sql_statements(main_section))
            operations.extend(self._extract_assignments(main_section))
            operations.extend(self._extract_control_structures(main_section))
            operations.extend(self._extract_procedure_calls(main_section))
            
            logger.info(f"Advanced extraction - {len(operations)} operations found")
            return operations
            
        except Exception as e:
            raise ConversionError("DATA_OPERATION_EXTRACTION_ERROR", f"Failed to extract data operations: {str(e)}")
    
    def _extract_sql_statements(self, content: str) -> List[DataOperation]:
        """Extract SQL statements (SELECT, INSERT, UPDATE, DELETE)"""
        operations = []
        
        # Improved patterns for SQL statements
        sql_patterns = {
            'select': r'(?:^|\s)(SELECT\s+.*?)(?=\s*;|\s*$|\s*(?:IF|END|EXCEPTION|INSERT|UPDATE|DELETE))',
            'insert': r'(?:^|\s)(INSERT\s+INTO\s+.*?)(?=\s*;|\s*$|\s*(?:IF|END|EXCEPTION|SELECT|UPDATE|DELETE))',
            'update': r'(?:^|\s)(UPDATE\s+.*?)(?=\s*;|\s*$|\s*(?:IF|END|EXCEPTION|SELECT|INSERT|DELETE))',
            'delete': r'(?:^|\s)(DELETE\s+FROM\s+.*?)(?=\s*;|\s*$|\s*(?:IF|END|EXCEPTION|SELECT|INSERT|UPDATE))',
        }
        
        for sql_type, pattern in sql_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
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
    
    def _extract_assignments(self, content: str) -> List[DataOperation]:
        """Extract variable assignments"""
        operations = []
        
        assignment_pattern = r'(\w+)\s*:=\s*([^;]+);'
        matches = re.finditer(assignment_pattern, content, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            self.operation_counter += 1
            variable = match.group(1)
            expression = match.group(2).strip()
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=f"{variable} := {expression};",
                type="assignment"
            ))
        
        return operations
    
    def _extract_control_structures(self, content: str) -> List[DataOperation]:
        """Extract control structures (IF, CASE, LOOP, etc.)"""
        operations = []
        
        # IF statements with better nesting support
        if_pattern = r'IF\s*\(([^)]+)\)\s*THEN(.*?)(?:ELSE(.*?))?END\s+IF\s*;'
        matches = re.finditer(if_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            self.operation_counter += 1
            condition = match.group(1).strip()
            then_block = match.group(2).strip() if match.group(2) else ""
            else_block = match.group(3).strip() if match.group(3) else None
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=f"if ({condition}) then ... end if;",
                type="if_else",
                condition=condition,
                then_statement=then_block if then_block else "...",
                else_statement=else_block
            ))
        
        # CASE statements
        case_pattern = r'CASE\s+(.*?)\s+END\s*;'
        matches = re.finditer(case_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            self.operation_counter += 1
            case_body = match.group(1).strip()
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=f"case {case_body[:50]}... end;",
                type="case_statement"
            ))
        
        return operations
    
    def _extract_procedure_calls(self, content: str) -> List[DataOperation]:
        """Extract procedure/function calls"""
        operations = []
        
        # Pattern for procedure calls
        proc_pattern = r'(\w+(?:\.\w+)*)\s*\([^)]*\)\s*;'
        matches = re.finditer(proc_pattern, content, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            # Skip common SQL keywords
            proc_name = match.group(1).lower()
            if proc_name not in ['select', 'insert', 'update', 'delete', 'if', 'case', 'when', 'then', 'else']:
                self.operation_counter += 1
                sql = match.group(0).strip()
                
                operations.append(DataOperation(
                    id=f"code_{self.operation_counter}",
                    sql=sql,
                    type="procedure_call"
                ))
        
        return operations


class EnhancedOracleToJsonConverter:
    """Enhanced Oracle to JSON converter with improved parsing"""
    
    def __init__(self):
        self.comment_remover = ImprovedCommentRemover()
        self.section_parser = ImprovedTriggerSectionParser()
        self.declaration_parser = ImprovedDeclarationParser()
        self.operation_extractor = AdvancedDataOperationExtractor()
    
    def convert_oracle_to_enhanced_json(self, oracle_file_path: str, output_file_path: str) -> Dict[str, Any]:
        """Convert Oracle SQL file to Enhanced Analysis JSON"""
        try:
            logger.info(f"Enhanced conversion: {oracle_file_path} → {output_file_path}")
            
            # Step 1: Read Oracle SQL file
            with open(oracle_file_path, 'r', encoding='utf-8') as f:
                oracle_content = f.read()
            
            # Step 2: Remove comments
            clean_content = self.comment_remover.remove_comments(oracle_content)
            
            # Step 3: Parse sections with improved parser
            declare_section, main_section, exception_section = self.section_parser.parse_sections(clean_content)
            
            # Step 4: Extract metadata
            trigger_name = Path(oracle_file_path).stem
            metadata = TriggerMetadata(
                trigger_name=trigger_name,
                timing=self._detect_timing(clean_content),
                events=["INSERT", "UPDATE", "DELETE"],
                table_name=self._extract_table_name(clean_content),
                has_declare_section=bool(declare_section.strip()),
                has_begin_section=bool(main_section.strip()),
                has_exception_section=bool(exception_section.strip())
            )
            
            # Step 5: Parse declarations with improved parser
            variables, constants, exceptions = self.declaration_parser.parse_declarations(declare_section)
            
            # Step 6: Extract data operations with advanced extractor
            data_operations = self.operation_extractor.extract_data_operations(main_section)
            
            # Step 7: Parse exception handlers
            exception_handlers = self._parse_exception_handlers(exception_section)
            
            # Step 8: Build enhanced JSON structure
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
            
            logger.info(f"Enhanced JSON completed: {len(data_operations)} operations, {len(variables)} variables")
            return enhanced_json
            
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError("GENERAL_CONVERSION_ERROR", f"Unexpected error: {str(e)}")
    
    def _detect_timing(self, content: str) -> str:
        """Detect trigger timing (BEFORE/AFTER)"""
        if re.search(r'BEFORE\s+(?:INSERT|UPDATE|DELETE)', content, re.IGNORECASE):
            return "BEFORE"
        return "AFTER"  # Default
    
    def _extract_table_name(self, content: str) -> str:
        """Extract table name from trigger content"""
        table_patterns = [
            r'INSERT\s+INTO\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)',
        ]
        
        for pattern in table_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                if not table_name.startswith('v_'):  # Skip views
                    return table_name
        
        return "unknown_table"
    
    def _parse_exception_handlers(self, exception_section: str) -> List[Dict[str, Any]]:
        """Parse exception handlers"""
        handlers = []
        
        if not exception_section.strip():
            return handlers
        
        when_pattern = r'WHEN\s+(\w+)\s*THEN\s*(.*?)(?=WHEN\s+\w+|$)'
        for match in re.finditer(when_pattern, exception_section, re.IGNORECASE | re.DOTALL):
            exception_name = match.group(1)
            handler_code = match.group(2).strip()
            
            handlers.append({
                "exception_name": exception_name,
                "handler_code": handler_code
            })
        
        return handlers
    
    def _operation_to_dict(self, operation: DataOperation) -> Dict[str, Any]:
        """Convert DataOperation to dictionary"""
        result = {"id": operation.id, "sql": operation.sql, "type": operation.type}
        
        for attr in ['condition', 'then_statement', 'else_statement', 'when_clauses', 
                     'parameters', 'table', 'columns', 'values', 'operations', 
                     'assignments', 'select_statement', 'exception_handlers']:
            value = getattr(operation, attr)
            if value:
                result[attr] = value
                
        return result


def main():
    """Test the enhanced converter"""
    try:
        print("🚀 Testing Enhanced Oracle to JSON Converter V2")
        print("=" * 60)
        
        converter = EnhancedOracleToJsonConverter()
        
        # Test with each trigger file
        oracle_files = ["files/oracle/trigger1.sql", "files/oracle/trigger2.sql", "files/oracle/trigger3.sql"]
        
        for oracle_file in oracle_files:
            if Path(oracle_file).exists():
                output_file = f"files/enhanced_test/{Path(oracle_file).stem}_enhanced_v2.json"
                
                try:
                    result = converter.convert_oracle_to_enhanced_json(oracle_file, output_file)
                    
                    operations_count = len(result.get("data_operations", []))
                    variables_count = len(result.get("declarations", {}).get("variables", []))
                    
                    print(f"✅ {Path(oracle_file).name}: {operations_count} operations, {variables_count} variables")
                    
                except ConversionError as e:
                    print(f"❌ {Path(oracle_file).name}: [{e.error_key}] {e.message}")
            else:
                print(f"⚠️  File not found: {oracle_file}")
        
        print("\n✅ Enhanced converter testing completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main() 