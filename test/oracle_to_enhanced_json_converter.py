#!/usr/bin/env python3
"""
Oracle to Enhanced JSON Converter

This script converts Oracle SQL triggers to enhanced analysis JSON format.
It analyzes the trigger structure deeply and creates a comprehensive JSON 
representation with trigger metadata, declarations, data operations, and exception handlers.
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass


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


class OracleEnhancedAnalyzer:
    """
    Comprehensive Oracle trigger analyzer that creates detailed JSON structure
    """
    
    def __init__(self):
        """Initialize the analyzer with regex patterns"""
        self.operation_counter = 0
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, str]:
        """Initialize regex patterns for parsing"""
        return {
            # Variable declarations
            'variable': r'(\w+)\s+((?:varchar2|number|date|pls_integer|simple_integer|binary_integer|boolean|PLS_INTEGER|BOOLEAN)[^;]*?)(?::=\s*([^;]+?))?\s*;',
            
            # Constant declarations  
            'constant': r'(\w+)\s+constant\s+([^:]+?)\s*:=\s*([^;]+?)\s*;',
            
            # Exception declarations
            'exception': r'(\w+)\s+exception\s*;',
            
            # SQL statements
            'select': r'select\s+.*?(?=\s*;|\s*$)',
            'insert': r'insert\s+into\s+.*?(?=\s*;|\s*$)',
            'update': r'update\s+.*?(?=\s*;|\s*$)',
            'delete': r'delete\s+from\s+.*?(?=\s*;|\s*$)',
            
            # Control structures
            'if_statement': r'if\s*\([^)]+\)\s*then',
            'case_statement': r'case\s+.*?\s+when',
            'for_loop': r'for\s+\w+\s+in\s*\(',
            
            # Procedure calls
            'procedure_call': r'(\w+(?:\.\w+)*)\s*\(',
            
            # Assignments
            'assignment': r'(\w+)\s*:=\s*([^;]+)',
            
            # Exception handlers
            'exception_handler': r'when\s+(\w+)\s*then\s*(.*?)(?=when\s+\w+|$)',
        }
    
    def _get_next_id(self, prefix: str = "code") -> str:
        """Generate unique operation ID"""
        self.operation_counter += 1
        return f"{prefix}_{self.operation_counter}"
    
    def extract_trigger_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract trigger metadata from Oracle trigger content"""
        # Determine trigger name from filename
        trigger_name = Path(filename).stem
        
        # Determine timing (BEFORE/AFTER) - default to AFTER for most business logic triggers
        timing = "AFTER"
        if re.search(r'before\s+(?:insert|update|delete)', content, re.IGNORECASE):
            timing = "BEFORE"
        
        # Events are typically INSERT, UPDATE, DELETE for triggers
        events = ["INSERT", "UPDATE", "DELETE"]
        
        # Extract table name from trigger context or default to generic name
        table_match = re.search(r'(?:on|into|from)\s+(\w+(?:\.\w+)?)', content, re.IGNORECASE)
        table_name = table_match.group(1) if table_match else "target_table"
        
        # Check for declare, begin, and exception sections
        has_declare = bool(re.search(r'declare\s', content, re.IGNORECASE))
        has_begin = bool(re.search(r'begin\s', content, re.IGNORECASE))
        has_exception = bool(re.search(r'exception\s', content, re.IGNORECASE))
        
        return {
            "trigger_name": trigger_name,
            "timing": timing,
            "events": events,
            "table_name": table_name,
            "has_declare_section": has_declare,
            "has_begin_section": has_begin,
            "has_exception_section": has_exception
        }
    
    def extract_declarations(self, content: str) -> Dict[str, Any]:
        """Extract variable, constant, and exception declarations"""
        variables = []
        constants = []
        exceptions = []
        
        # Find the declare section
        declare_match = re.search(r'declare\s+(.*?)begin', content, re.DOTALL | re.IGNORECASE)
        if not declare_match:
            return {"variables": variables, "constants": constants, "exceptions": exceptions}
        
        declare_content = declare_match.group(1)
        
        # Extract variables
        var_matches = re.finditer(self.patterns['variable'], declare_content, re.IGNORECASE | re.MULTILINE)
        for match in var_matches:
            name = match.group(1).strip()
            data_type = match.group(2).strip()
            default_value = match.group(3).strip() if match.group(3) else None
            variables.append({
                "name": name,
                "data_type": data_type,
                "default_value": default_value
            })
        
        # Extract constants
        const_matches = re.finditer(self.patterns['constant'], declare_content, re.IGNORECASE | re.MULTILINE)
        for match in const_matches:
            name = match.group(1).strip()
            data_type = match.group(2).strip()
            value = match.group(3).strip()
            constants.append({
                "name": name,
                "data_type": data_type,
                "value": value
            })
        
        # Extract exceptions
        exc_matches = re.finditer(self.patterns['exception'], declare_content, re.IGNORECASE | re.MULTILINE)
        for match in exc_matches:
            name = match.group(1).strip()
            exceptions.append({
                "name": name,
                "type": "user_defined"
            })
        
        return {"variables": variables, "constants": constants, "exceptions": exceptions}
    
    def _analyze_control_structure(self, content: str) -> Dict[str, Any]:
        """Analyze control structures like IF-ELSE, CASE, FOR loops"""
        content = content.strip()
        
        # IF-ELSE statement
        if re.match(r'if\s*\(', content, re.IGNORECASE):
            return self._analyze_if_statement(content)
        
        # CASE statement
        elif re.match(r'case\s+', content, re.IGNORECASE):
            return self._analyze_case_statement(content)
        
        # FOR loop
        elif re.match(r'for\s+\w+\s+in', content, re.IGNORECASE):
            return self._analyze_for_loop(content)
        
        # Assignment
        elif ':=' in content and not content.strip().startswith('select'):
            return self._analyze_assignment(content)
        
        # SQL statements
        elif re.match(r'select\s+', content, re.IGNORECASE):
            return {"id": self._get_next_id(), "sql": content, "type": "select_statements"}
        elif re.match(r'insert\s+', content, re.IGNORECASE):
            return {"id": self._get_next_id(), "sql": content, "type": "insert_statements"}
        elif re.match(r'update\s+', content, re.IGNORECASE):
            return {"id": self._get_next_id(), "sql": content, "type": "update_statements"}
        elif re.match(r'delete\s+', content, re.IGNORECASE):
            return {"id": self._get_next_id(), "sql": content, "type": "delete_statements"}
        
        # Procedure call
        elif re.search(r'\w+\.\w+\s*\(', content):
            return {"id": self._get_next_id(), "sql": content, "type": "procedure_calls"}
        
        # Exception raise
        elif re.match(r'raise\s+', content, re.IGNORECASE):
            return {"id": self._get_next_id(), "sql": content, "type": "exception_raise"}
        
        # Default case
        return {"id": self._get_next_id(), "sql": content, "type": "statement"}
    
    def _analyze_if_statement(self, content: str) -> Dict[str, Any]:
        """Analyze IF-ELSE statement structure"""
        # Extract condition
        condition_match = re.search(r'if\s*\(\s*([^)]+)\s*\)\s*then', content, re.IGNORECASE | re.DOTALL)
        condition = condition_match.group(1).strip() if condition_match else ""
        
        # Extract then and else parts (simplified for now)
        then_part = ""
        else_part = None
        
        # This would need more sophisticated parsing for nested structures
        then_match = re.search(r'then\s+(.*?)(?:else|end\s+if)', content, re.IGNORECASE | re.DOTALL)
        if then_match:
            then_part = then_match.group(1).strip()
        
        else_match = re.search(r'else\s+(.*?)end\s+if', content, re.IGNORECASE | re.DOTALL)
        if else_match:
            else_part = else_match.group(1).strip()
        
        operation = {
            "id": self._get_next_id(),
            "sql": content,
            "type": "if_else",
            "condition": condition,
            "then_statement": [self._analyze_control_structure(then_part)] if then_part else None,
            "else_statement": [self._analyze_control_structure(else_part)] if else_part else None
        }
        
        return operation
    
    def _analyze_case_statement(self, content: str) -> Dict[str, Any]:
        """Analyze CASE statement structure"""
        # Extract case expression
        case_match = re.search(r'case\s+([^w]+?)\s+when', content, re.IGNORECASE)
        case_expression = case_match.group(1).strip() if case_match else ""
        
        # Extract WHEN clauses (simplified)
        when_clauses = []
        when_matches = re.finditer(r'when\s+([^t]+?)\s+then\s+([^w]+?)(?=when|else|end)', content, re.IGNORECASE | re.DOTALL)
        
        for match in when_matches:
            when_value = match.group(1).strip()
            then_statement = match.group(2).strip()
            when_clauses.append({
                "when_value": when_value,
                "then_statement": [self._analyze_control_structure(then_statement)]
            })
        
        # Extract else clause
        else_match = re.search(r'else\s+([^e]+?)end\s+case', content, re.IGNORECASE | re.DOTALL)
        else_statement = else_match.group(1).strip() if else_match else None
        
        return {
            "id": self._get_next_id(),
            "sql": content,
            "type": "case_statements",
            "case_expression": case_expression,
            "when_clauses": when_clauses,
            "else_statement": else_statement
        }
    
    def _analyze_for_loop(self, content: str) -> Dict[str, Any]:
        """Analyze FOR loop structure"""
        # Extract loop variable and cursor query
        loop_match = re.search(r'for\s+(\w+)\s+in\s*\(([^)]+)\)\s+loop\s+(.*?)end\s+loop', content, re.IGNORECASE | re.DOTALL)
        
        if loop_match:
            loop_variable = loop_match.group(1)
            cursor_query = loop_match.group(2).strip()
            loop_body = loop_match.group(3).strip()
            
            return {
                "id": self._get_next_id(),
                "sql": content,
                "type": "for_loop",
                "cursor_query": cursor_query,
                "loop_variable": loop_variable,
                "loop_body": [self._analyze_control_structure(loop_body)]
            }
        
        return {"id": self._get_next_id(), "sql": content, "type": "for_loop"}
    
    def _analyze_assignment(self, content: str) -> Dict[str, Any]:
        """Analyze assignment statements"""
        # Check for multiple assignments
        assignments = []
        for line in content.split(';'):
            line = line.strip()
            if ':=' in line:
                parts = line.split(':=', 1)
                if len(parts) == 2:
                    variable = parts[0].strip()
                    expression = parts[1].strip()
                    assignments.append({
                        "variable": variable,
                        "expression": expression
                    })
        
        if len(assignments) > 1:
            return {
                "id": self._get_next_id(),
                "sql": content,
                "type": "assignment_block",
                "assignments": assignments
            }
        else:
            return {
                "id": self._get_next_id(),
                "sql": content,
                "type": "assignment"
            }
    
    def extract_data_operations(self, content: str) -> List[Dict[str, Any]]:
        """Extract and analyze data operations from trigger body"""
        operations = []
        
        # Find the main body between BEGIN and EXCEPTION (or END)
        begin_match = re.search(r'begin\s+(.*?)(?:exception|end\s*;)', content, re.DOTALL | re.IGNORECASE)
        if not begin_match:
            return operations
        
        body_content = begin_match.group(1)
        
        # Split into logical blocks (simplified approach)
        # This would need more sophisticated parsing for real-world scenarios
        statements = self._split_statements(body_content)
        
        for stmt in statements:
            if stmt.strip():
                operation = self._analyze_control_structure(stmt)
                operations.append(operation)
        
        return operations
    
    def _split_statements(self, content: str) -> List[str]:
        """Split content into individual statements (simplified)"""
        # This is a simplified approach - real parsing would need to handle nesting properly
        statements = []
        current_stmt = ""
        paren_count = 0
        in_string = False
        
        i = 0
        while i < len(content):
            char = content[i]
            
            if char == "'" and (i == 0 or content[i-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                elif char == ';' and paren_count == 0:
                    statements.append(current_stmt.strip())
                    current_stmt = ""
                    i += 1
                    continue
            
            current_stmt += char
            i += 1
        
        if current_stmt.strip():
            statements.append(current_stmt.strip())
        
        return statements
    
    def extract_exception_handlers(self, content: str) -> List[Dict[str, Any]]:
        """Extract exception handler blocks"""
        handlers = []
        
        # Find exception section
        exception_match = re.search(r'exception\s+(.*?)end\s*;', content, re.DOTALL | re.IGNORECASE)
        if not exception_match:
            return handlers
        
        exception_content = exception_match.group(1)
        
        # Extract individual exception handlers
        handler_matches = re.finditer(r'when\s+(\w+)\s*then\s*(.*?)(?=when\s+\w+|$)', exception_content, re.DOTALL | re.IGNORECASE)
        
        for match in handler_matches:
            exception_name = match.group(1)
            handler_code = match.group(2).strip()
            handlers.append({
                "exception_name": exception_name,
                "handler_code": handler_code
            })
        
        return handlers
    
    def analyze_trigger_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a complete Oracle trigger file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reset counter for each file
        self.operation_counter = 0
        
        # Extract all components
        metadata = self.extract_trigger_metadata(content, file_path)
        declarations = self.extract_declarations(content)
        data_operations = self.extract_data_operations(content)
        exception_handlers = self.extract_exception_handlers(content)
        
        # Build the complete analysis structure
        analysis = {
            "trigger_metadata": metadata,
            "declarations": declarations,
            "data_operations": data_operations,
            "exception_handlers": exception_handlers
        }
        
        return analysis


class OracleToEnhancedJSONConverter:
    """
    Main converter class that processes Oracle triggers to enhanced JSON format
    """
    
    def __init__(self):
        """Initialize the converter"""
        self.analyzer = OracleEnhancedAnalyzer()
    
    def convert_file(self, input_file: str, output_file: str, verbose: bool = False) -> bool:
        """Convert a single Oracle trigger file to enhanced JSON"""
        try:
            if verbose:
                print(f"🔄 Analyzing {input_file}...")
            
            # Analyze the trigger file
            analysis = self.analyzer.analyze_trigger_file(input_file)
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Write the analysis to JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            if verbose:
                print(f"✅ Converted to {output_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error converting {input_file}: {e}")
            return False
    
    def convert_directory(self, oracle_dir: str, json_dir: str, verbose: bool = False) -> None:
        """Convert all Oracle trigger files in a directory"""
        oracle_path = Path(oracle_dir)
        json_path = Path(json_dir)
        
        if not oracle_path.exists():
            print(f"❌ Oracle directory not found: {oracle_dir}")
            return
        
        # Create output directory
        json_path.mkdir(parents=True, exist_ok=True)
        
        # Process all .sql files
        sql_files = list(oracle_path.glob("*.sql"))
        
        if not sql_files:
            print(f"❌ No .sql files found in {oracle_dir}")
            return
        
        print(f"🔄 Converting {len(sql_files)} files from {oracle_dir} to {json_dir}")
        
        success_count = 0
        for sql_file in sql_files:
            output_file = json_path / f"{sql_file.stem}_enhanced_analysis.json"
            if self.convert_file(str(sql_file), str(output_file), verbose):
                success_count += 1
        
        print(f"✅ Successfully converted {success_count}/{len(sql_files)} files")


def main():
    """Main function to run the converter"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Oracle triggers to enhanced JSON analysis format")
    parser.add_argument('--oracle-dir', default='files/oracle', help='Directory containing Oracle SQL files')
    parser.add_argument('--json-dir', default='files/sql_json', help='Output directory for JSON files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--file', help='Convert a single file instead of directory')
    parser.add_argument('--output', '-o', help='Output file for single file conversion')
    
    args = parser.parse_args()
    
    converter = OracleToEnhancedJSONConverter()
    
    if args.file:
        # Single file conversion
        output_file = args.output or f"{Path(args.file).stem}_enhanced_analysis.json"
        converter.convert_file(args.file, output_file, args.verbose)
    else:
        # Directory conversion
        converter.convert_directory(args.oracle_dir, args.json_dir, args.verbose)


if __name__ == "__main__":
    main() 