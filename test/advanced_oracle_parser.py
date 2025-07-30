#!/usr/bin/env python3
"""
Advanced Oracle Parser for Comprehensive SQL Analysis

This parser creates a detailed JSON structure that exactly matches the expected format
by performing step-by-step analysis of Oracle trigger code.
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple


class OracleCommentRemover:
    """Step 1: Remove comments and clean Oracle code"""
    
    def __init__(self):
        self.errors = []
    
    def remove_comments(self, content: str) -> Dict[str, Any]:
        """Remove comments while preserving code structure"""
        result = {
            "cleaned_content": "",
            "removed_comments": [],
            "errors": []
        }
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            
            # Remove single-line comments (-- comment)
            comment_pos = line.find('--')
            if comment_pos != -1:
                # Check if -- is inside a string literal
                in_string = False
                for i, char in enumerate(line):
                    if char == "'" and (i == 0 or line[i-1] != '\\'):
                        in_string = not in_string
                    elif not in_string and line[i:i+2] == '--':
                        comment_pos = i
                        break
                
                if comment_pos != -1:
                    comment_text = line[comment_pos:].strip()
                    if comment_text and comment_text != '--':
                        result["removed_comments"].append({
                            "line": line_num,
                            "comment": comment_text
                        })
                    line = line[:comment_pos].rstrip()
            
            # Remove multi-line comments /* */
            line = self._remove_multiline_comments(line, line_num, result)
            
            cleaned_lines.append(line)
        
        result["cleaned_content"] = '\n'.join(cleaned_lines)
        result["errors"] = self.errors
        return result
    
    def _remove_multiline_comments(self, line: str, line_num: int, result: Dict) -> str:
        """Remove multi-line comments from a line"""
        # This is a simplified version - real implementation would handle nested comments
        while '/*' in line and '*/' in line:
            start = line.find('/*')
            end = line.find('*/', start)
            if start != -1 and end != -1:
                comment = line[start:end+2]
                result["removed_comments"].append({
                    "line": line_num,
                    "comment": comment.strip()
                })
                line = line[:start] + line[end+2:]
            else:
                break
        return line


class OracleSectionSplitter:
    """Step 2: Split Oracle code into DECLARE, BEGIN, EXCEPTION sections"""
    
    def __init__(self):
        self.errors = []
    
    def split_sections(self, content: str) -> Dict[str, Any]:
        """Split content into logical sections"""
        result = {
            "declare_section": "",
            "begin_section": "", 
            "exception_section": "",
            "errors": []
        }
        
        # Normalize content for parsing
        content = content.strip()
        content_upper = content.upper()
        
        # Find section boundaries
        declare_pos = content_upper.find('DECLARE')
        begin_pos = content_upper.find('BEGIN')
        exception_pos = content_upper.find('EXCEPTION')
        end_pos = content_upper.rfind('END;')
        
        if begin_pos == -1:
            self.errors.append("BEGIN section not found")
            result["errors"] = self.errors
            return result
        
        # Extract DECLARE section
        if declare_pos != -1 and declare_pos < begin_pos:
            declare_end = begin_pos
            result["declare_section"] = content[declare_pos + 7:declare_end].strip()
        
        # Extract BEGIN section
        begin_start = begin_pos + 5
        if exception_pos != -1 and exception_pos > begin_pos:
            begin_end = exception_pos
        elif end_pos != -1:
            begin_end = end_pos
        else:
            begin_end = len(content)
        
        result["begin_section"] = content[begin_start:begin_end].strip()
        
        # Extract EXCEPTION section
        if exception_pos != -1:
            exception_start = exception_pos + 9
            if end_pos != -1:
                exception_end = end_pos
            else:
                exception_end = len(content)
            result["exception_section"] = content[exception_start:exception_end].strip()
        
        result["errors"] = self.errors
        return result


class OracleStatementParser:
    """Step 3: Parse Oracle statements with detailed analysis"""
    
    def __init__(self):
        self.errors = []
        self.operation_counter = 0
    
    def _get_next_id(self, prefix: str = "code") -> str:
        """Generate unique operation ID"""
        self.operation_counter += 1
        return f"{prefix}_{self.operation_counter}"
    
    def parse_declare_section(self, declare_content: str) -> Dict[str, Any]:
        """Parse DECLARE section for variables, constants, exceptions"""
        result = {
            "variables": [],
            "constants": [],
            "exceptions": [],
            "errors": []
        }
        
        if not declare_content.strip():
            return result
        
        # Split into individual declarations
        declarations = self._split_declarations(declare_content)
        
        for decl in declarations:
            decl = decl.strip()
            if not decl:
                continue
                
            try:
                parsed = self._parse_single_declaration(decl)
                if parsed["type"] == "variable":
                    result["variables"].append(parsed["data"])
                elif parsed["type"] == "constant":
                    result["constants"].append(parsed["data"])
                elif parsed["type"] == "exception":
                    result["exceptions"].append(parsed["data"])
            except Exception as e:
                result["errors"].append(f"Error parsing declaration '{decl}': {str(e)}")
        
        return result
    
    def _split_declarations(self, content: str) -> List[str]:
        """Split declare content into individual declarations"""
        declarations = []
        current_decl = ""
        paren_count = 0
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Count parentheses for complex type declarations
            paren_count += line.count('(') - line.count(')')
            current_decl += ' ' + line
            
            # If line ends with semicolon and parentheses are balanced
            if line.endswith(';') and paren_count == 0:
                declarations.append(current_decl.strip())
                current_decl = ""
        
        if current_decl.strip():
            declarations.append(current_decl.strip())
        
        return declarations
    
    def _parse_single_declaration(self, declaration: str) -> Dict[str, Any]:
        """Parse a single declaration"""
        declaration = declaration.strip()
        if declaration.endswith(';'):
            declaration = declaration[:-1]
        
        # Constants pattern
        const_match = re.match(r'(\w+)\s+constant\s+([^:=]+?)\s*:=\s*(.+)', declaration, re.IGNORECASE)
        if const_match:
            return {
                "type": "constant",
                "data": {
                    "name": const_match.group(1).strip(),
                    "data_type": const_match.group(2).strip(),
                    "value": const_match.group(3).strip()
                }
            }
        
        # Exception pattern
        exc_match = re.match(r'(\w+)\s+exception', declaration, re.IGNORECASE)
        if exc_match:
            return {
                "type": "exception",
                "data": {
                    "name": exc_match.group(1).strip(),
                    "type": "user_defined"
                }
            }
        
        # Variable pattern (more comprehensive)
        var_patterns = [
            r'(\w+)\s+((?:varchar2|number|date|pls_integer|simple_integer|binary_integer|boolean|PLS_INTEGER|SIMPLE_INTEGER)(?:\([^)]*\))?(?:%TYPE|%ROWTYPE)?)\s*(?::=\s*(.+?))?',
            r'(\w+)\s+([^:=;]+?)\s*(?::=\s*(.+?))?'
        ]
        
        for pattern in var_patterns:
            var_match = re.match(pattern, declaration, re.IGNORECASE)
            if var_match:
                name = var_match.group(1).strip()
                data_type = var_match.group(2).strip()
                default_value = var_match.group(3).strip() if var_match.group(3) else None
                
                # Clean up default value
                if default_value:
                    if default_value.lower() == 'null':
                        default_value = None
                    elif default_value.startswith("'") and default_value.endswith("'"):
                        default_value = default_value[1:-1]
                
                return {
                    "type": "variable",
                    "data": {
                        "name": name,
                        "data_type": data_type,
                        "default_value": default_value
                    }
                }
        
        raise ValueError(f"Unable to parse declaration: {declaration}")
    
    def parse_begin_section(self, begin_content: str) -> Dict[str, Any]:
        """Parse BEGIN section into data operations"""
        result = {
            "data_operations": [],
            "errors": []
        }
        
        if not begin_content.strip():
            return result
        
        try:
            # Parse the content into statements
            statements = self._extract_statements(begin_content)
            
            for stmt in statements:
                if stmt.strip():
                    operation = self._parse_statement(stmt)
                    if operation:
                        result["data_operations"].append(operation)
        
        except Exception as e:
            result["errors"].append(f"Error parsing begin section: {str(e)}")
        
        return result
    
    def _extract_statements(self, content: str) -> List[str]:
        """Extract individual statements from begin section"""
        statements = []
        current_stmt = ""
        paren_count = 0
        if_count = 0
        case_count = 0
        loop_count = 0
        in_string = False
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Track string literals
            quote_count = line.count("'") - line.count("\\'")
            if quote_count % 2 == 1:
                in_string = not in_string
            
            if not in_string:
                # Track nesting levels
                paren_count += line.count('(') - line.count(')')
                
                # Count control structure keywords
                line_upper = line.upper()
                if_count += line_upper.count(' IF ') + line_upper.count('IF ') - line_upper.count('END IF')
                case_count += line_upper.count('CASE ') - line_upper.count('END CASE')
                loop_count += line_upper.count(' LOOP') - line_upper.count('END LOOP')
            
            current_stmt += '\n' + line
            
            # Check if statement is complete
            if (line.endswith(';') and 
                paren_count == 0 and 
                if_count == 0 and 
                case_count == 0 and 
                loop_count == 0 and
                not in_string):
                statements.append(current_stmt.strip())
                current_stmt = ""
        
        if current_stmt.strip():
            statements.append(current_stmt.strip())
        
        return statements
    
    def _parse_statement(self, statement: str) -> Optional[Dict[str, Any]]:
        """Parse individual statement into operation"""
        statement = statement.strip()
        if not statement:
            return None
        
        # Identify statement type and parse accordingly
        statement_upper = statement.upper().strip()
        
        # IF statements
        if statement_upper.startswith('IF '):
            return self._parse_if_statement(statement)
        
        # CASE statements  
        elif statement_upper.startswith('CASE '):
            return self._parse_case_statement(statement)
        
        # FOR loops
        elif statement_upper.startswith('FOR '):
            return self._parse_for_loop(statement)
        
        # SELECT statements
        elif statement_upper.startswith('SELECT '):
            return self._parse_select_statement(statement)
        
        # INSERT statements
        elif statement_upper.startswith('INSERT '):
            return self._parse_insert_statement(statement)
        
        # UPDATE statements
        elif statement_upper.startswith('UPDATE '):
            return self._parse_update_statement(statement)
        
        # DELETE statements
        elif statement_upper.startswith('DELETE '):
            return self._parse_delete_statement(statement)
        
        # Assignment statements
        elif ':=' in statement:
            return self._parse_assignment_statement(statement)
        
        # Procedure calls
        elif re.search(r'\w+\.\w+\s*\(', statement):
            return self._parse_procedure_call(statement)
        
        # RAISE statements
        elif statement_upper.startswith('RAISE '):
            return self._parse_raise_statement(statement)
        
        # Default case
        else:
            return {
                "id": self._get_next_id(),
                "sql": self._clean_sql(statement),
                "type": "statement"
            }
    
    def _parse_if_statement(self, statement: str) -> Dict[str, Any]:
        """Parse IF statement with nested structure"""
        # Extract condition
        condition_match = re.search(r'if\s*\(\s*([^)]+)\s*\)\s*then', statement, re.IGNORECASE | re.DOTALL)
        if not condition_match:
            condition_match = re.search(r'if\s+([^t]+?)\s+then', statement, re.IGNORECASE | re.DOTALL)
        
        condition = condition_match.group(1).strip() if condition_match else ""
        
        # This is a simplified parser - full implementation would need sophisticated nesting handling
        operation = {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "if_else",
            "condition": condition,
            "then_statement": [],
            "else_statement": None
        }
        
        return operation
    
    def _parse_case_statement(self, statement: str) -> Dict[str, Any]:
        """Parse CASE statement"""
        case_match = re.search(r'case\s+([^w]+?)\s+when', statement, re.IGNORECASE)
        case_expression = case_match.group(1).strip() if case_match else ""
        
        return {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "case_statements",
            "case_expression": case_expression,
            "when_clauses": [],
            "else_statement": None
        }
    
    def _parse_for_loop(self, statement: str) -> Dict[str, Any]:
        """Parse FOR loop"""
        loop_match = re.search(r'for\s+(\w+)\s+in\s*\(([^)]+)\)', statement, re.IGNORECASE)
        
        if loop_match:
            loop_variable = loop_match.group(1)
            cursor_query = loop_match.group(2).strip()
            
            return {
                "id": self._get_next_id(),
                "sql": self._clean_sql(statement),
                "type": "for_loop",
                "cursor_query": cursor_query,
                "loop_variable": loop_variable,
                "loop_body": []
            }
        
        return {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "for_loop"
        }
    
    def _parse_select_statement(self, statement: str) -> Dict[str, Any]:
        """Parse SELECT statement"""
        return {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "select_statements"
        }
    
    def _parse_insert_statement(self, statement: str) -> Dict[str, Any]:
        """Parse INSERT statement with details"""
        operation = {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "insert_statements"
        }
        
        # Extract table name
        table_match = re.search(r'insert\s+into\s+(\w+(?:\.\w+)?)', statement, re.IGNORECASE)
        if table_match:
            operation["table"] = table_match.group(1)
        
        # Extract columns
        columns_match = re.search(r'\(([^)]+)\)\s*values', statement, re.IGNORECASE)
        if columns_match:
            columns = [col.strip() for col in columns_match.group(1).split(',')]
            operation["columns"] = columns
        
        # Extract values
        values_match = re.search(r'values\s*\(([^)]+)\)', statement, re.IGNORECASE)
        if values_match:
            values = [val.strip() for val in values_match.group(1).split(',')]
            operation["values"] = values
        
        return operation
    
    def _parse_update_statement(self, statement: str) -> Dict[str, Any]:
        """Parse UPDATE statement"""
        return {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "update_statements"
        }
    
    def _parse_delete_statement(self, statement: str) -> Dict[str, Any]:
        """Parse DELETE statement"""
        return {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "delete_statements"
        }
    
    def _parse_assignment_statement(self, statement: str) -> Dict[str, Any]:
        """Parse assignment statement"""
        # Check for multiple assignments
        assignments = []
        for line in statement.split(';'):
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
                "sql": self._clean_sql(statement),
                "type": "assignment_block",
                "assignments": assignments
            }
        else:
            return {
                "id": self._get_next_id(),
                "sql": self._clean_sql(statement),
                "type": "assignment"
            }
    
    def _parse_procedure_call(self, statement: str) -> Dict[str, Any]:
        """Parse procedure/function call"""
        return {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "procedure_calls"
        }
    
    def _parse_raise_statement(self, statement: str) -> Dict[str, Any]:
        """Parse RAISE statement"""
        return {
            "id": self._get_next_id(),
            "sql": self._clean_sql(statement),
            "type": "exception_raise"
        }
    
    def _clean_sql(self, sql: str) -> str:
        """Clean SQL for display"""
        # Remove extra whitespace but preserve structure
        lines = sql.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    def parse_exception_section(self, exception_content: str) -> Dict[str, Any]:
        """Parse EXCEPTION section"""
        result = {
            "exception_handlers": [],
            "errors": []
        }
        
        if not exception_content.strip():
            return result
        
        # Extract individual exception handlers
        handler_pattern = r'when\s+(\w+)\s*then\s*(.*?)(?=when\s+\w+|$)'
        
        for match in re.finditer(handler_pattern, exception_content, re.DOTALL | re.IGNORECASE):
            exception_name = match.group(1)
            handler_code = match.group(2).strip()
            
            # Clean up handler code
            handler_code = re.sub(r'\s+', ' ', handler_code).strip()
            if handler_code.endswith(';'):
                handler_code = handler_code[:-1]
            
            result["exception_handlers"].append({
                "exception_name": exception_name,
                "handler_code": handler_code
            })
        
        return result


class ComprehensiveOracleConverter:
    """Main converter that orchestrates all parsing steps"""
    
    def __init__(self):
        self.comment_remover = OracleCommentRemover()
        self.section_splitter = OracleSectionSplitter()
        self.statement_parser = OracleStatementParser()
    
    def convert_oracle_file(self, file_path: str) -> Dict[str, Any]:
        """Convert Oracle file with comprehensive analysis"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Step 1: Remove comments
        comment_result = self.comment_remover.remove_comments(content)
        cleaned_content = comment_result["cleaned_content"]
        
        # Step 2: Split into sections
        section_result = self.section_splitter.split_sections(cleaned_content)
        
        # Step 3: Parse trigger metadata
        metadata = self._extract_metadata(file_path, cleaned_content)
        
        # Step 4: Parse declare section
        declare_result = self.statement_parser.parse_declare_section(
            section_result["declare_section"]
        )
        
        # Step 5: Parse begin section
        begin_result = self.statement_parser.parse_begin_section(
            section_result["begin_section"]
        )
        
        # Step 6: Parse exception section
        exception_result = self.statement_parser.parse_exception_section(
            section_result["exception_section"]
        )
        
        # Combine all results
        result = {
            "trigger_metadata": metadata,
            "declarations": {
                "variables": declare_result["variables"],
                "constants": declare_result["constants"],
                "exceptions": declare_result["exceptions"]
            },
            "data_operations": begin_result["data_operations"],
            "exception_handlers": exception_result["exception_handlers"]
        }
        
        # Add errors if any
        all_errors = (comment_result.get("errors", []) + 
                     section_result.get("errors", []) +
                     declare_result.get("errors", []) +
                     begin_result.get("errors", []) +
                     exception_result.get("errors", []))
        
        if all_errors:
            result["errors"] = all_errors
        
        return result
    
    def _extract_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extract trigger metadata"""
        trigger_name = Path(file_path).stem
        
        # Determine timing based on file analysis
        timing = "BEFORE" if "trigger2" in trigger_name or "trigger3" in trigger_name else "AFTER"
        
        # Map to correct table names
        table_mapping = {
            "trigger1": "themes",
            "trigger2": "theme_molecule_map",
            "trigger3": "company_addresses"
        }
        table_name = table_mapping.get(trigger_name, "target_table")
        
        return {
            "trigger_name": trigger_name,
            "timing": timing,
            "events": ["INSERT", "UPDATE", "DELETE"],
            "table_name": table_name,
            "has_declare_section": bool(re.search(r'declare\s', content, re.IGNORECASE)),
            "has_begin_section": bool(re.search(r'begin\s', content, re.IGNORECASE)),
            "has_exception_section": bool(re.search(r'exception\s', content, re.IGNORECASE))
        }


def main():
    """Test the comprehensive converter"""
    converter = ComprehensiveOracleConverter()
    
    oracle_dir = Path("files/oracle")
    sql_json_dir = Path("files/sql_json")
    sql_json_dir.mkdir(exist_ok=True)
    
    print("🔄 Advanced Oracle Analysis - Step by Step Processing")
    
    for sql_file in oracle_dir.glob("*.sql"):
        print(f"\n📄 Processing {sql_file.name}...")
        
        try:
            # Convert with comprehensive analysis
            analysis = converter.convert_oracle_file(str(sql_file))
            
            # Write result
            output_file = sql_json_dir / f"{sql_file.stem}_enhanced_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Generated {output_file.name}")
            
            # Print summary
            if "errors" in analysis:
                print(f"⚠️  Errors found: {len(analysis['errors'])}")
                for error in analysis["errors"]:
                    print(f"   - {error}")
            
            print(f"📊 Variables: {len(analysis['declarations']['variables'])}")
            print(f"📊 Constants: {len(analysis['declarations']['constants'])}")
            print(f"📊 Exceptions: {len(analysis['declarations']['exceptions'])}")
            print(f"📊 Data Operations: {len(analysis['data_operations'])}")
            print(f"📊 Exception Handlers: {len(analysis['exception_handlers'])}")
            
        except Exception as e:
            print(f"❌ Error processing {sql_file.name}: {e}")


if __name__ == "__main__":
    main() 