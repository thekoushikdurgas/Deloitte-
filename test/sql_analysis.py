#!/usr/bin/env python3
"""
SQL Analysis Tool for Oracle Triggers
Converts Oracle SQL trigger files to enhanced JSON analysis format
"""

import re
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import sqlparse
    # from sqlparse import sql, tokens
except ImportError:
    print("Installing sqlparse...")
    os.system("pip install sqlparse")
    import sqlparse
    # from sqlparse import sql, tokens

try:
    import sqlglot
    # from sqlglot import parse, transpile
except ImportError:
    print("Installing sqlglot...")
    os.system("pip install sqlglot")
    import sqlglot
    # from sqlglot import parse, transpile

# Data structures
@dataclass
class TriggerMetadata:
    trigger_name: str
    timing: str = "BEFORE"
    events: Optional[List[str]] = None
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
class TriggerAnalysis:
    trigger_metadata: TriggerMetadata
    declarations: Declarations
    data_operations: List[DataOperation]
    exception_handlers: List[ExceptionHandler]

class OracleTriggerAnalyzer:
    """Main analyzer class for Oracle SQL triggers"""
    
    def __init__(self):
        self.operation_counter = 0
        
    def analyze_trigger_file(self, file_path: str) -> TriggerAnalysis:
        """Analyze a single Oracle trigger file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reset counter for each file
        self.operation_counter = 0
        
        # Extract basic metadata
        trigger_name = Path(file_path).stem
        metadata = self._extract_metadata(content, trigger_name)
        
        # Parse declarations
        declarations = self._extract_declarations(content)
        
        # Extract data operations
        data_operations = self._extract_data_operations(content)
        
        # Extract exception handlers
        exception_handlers = self._extract_exception_handlers(content)
        
        return TriggerAnalysis(
            trigger_metadata=metadata,
            declarations=declarations,
            data_operations=data_operations,
            exception_handlers=exception_handlers
        )
    
    def _extract_metadata(self, content: str, trigger_name: str) -> TriggerMetadata:
        """Extract trigger metadata from content"""
        content_upper = content.upper()
        
        # Determine timing (default to BEFORE for Oracle triggers)
        timing = "BEFORE"
        if "AFTER" in content_upper:
            timing = "AFTER"
        elif "INSTEAD OF" in content_upper:
            timing = "INSTEAD OF"
            
        # Determine events
        events = []
        if "INSERT" in content_upper:
            events.append("INSERT")
        if "UPDATE" in content_upper:
            events.append("UPDATE")
        if "DELETE" in content_upper:
            events.append("DELETE")
        
        # Check for sections
        has_declare = "DECLARE" in content_upper or content.strip().startswith("declare")
        has_begin = "BEGIN" in content_upper
        has_exception = "EXCEPTION" in content_upper
        
        # Try to extract table name from context or filename
        table_name = self._extract_table_name(content, trigger_name)
        
        return TriggerMetadata(
            trigger_name=trigger_name,
            timing=timing,
            events=events if events else ["INSERT", "UPDATE", "DELETE"],
            table_name=table_name,
            has_declare_section=has_declare,
            has_begin_section=has_begin,
            has_exception_section=has_exception
        )
    
    def _extract_table_name(self, content: str, trigger_name: str) -> str:
        """Extract table name from trigger content or infer from context"""
        # Try to find table name patterns in the content
        table_patterns = [
            r"(?:FROM|INTO|UPDATE|DELETE\s+FROM)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)",
            r":(?:new|old)\.([a-zA-Z_][a-zA-Z0-9_]*)",
        ]
        
        # Common table names based on trigger analysis
        table_mappings = {
            "trigger1": "themes",
            "trigger2": "theme_molecule_map", 
            "trigger3": "company_addresses"
        }
        
        if trigger_name in table_mappings:
            return table_mappings[trigger_name]
            
        # Try to extract from SQL patterns
        for pattern in table_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Return the most common table name
                table_counts = {}
                for match in matches:
                    table = match.split('.')[-1]  # Get table name without schema
                    table_counts[table] = table_counts.get(table, 0) + 1
                if table_counts:
                    return max(table_counts.items(), key=lambda x: x[1])[0]
        
        return "unknown_table"
    
    def _extract_declarations(self, content: str) -> Declarations:
        """Extract variable, constant, and exception declarations"""
        variables = []
        constants = []
        exceptions = []
        
        # Find the DECLARE section or start of the trigger
        declare_match = re.search(r'(?:^|\n)\s*declare\s*$', content, re.IGNORECASE | re.MULTILINE)
        begin_match = re.search(r'(?:^|\n)\s*begin\s*$', content, re.IGNORECASE | re.MULTILINE)
        
        if declare_match and begin_match:
            declare_section = content[declare_match.end():begin_match.start()]
        elif content.strip().lower().startswith('declare'):
            # If it starts with declare, get everything until begin
            if begin_match:
                declare_section = content[:begin_match.start()]
            else:
                declare_section = content
        else:
            declare_section = ""
        
        # Extract exceptions
        exception_pattern = r'(\w+)\s+exception\s*;'
        for match in re.finditer(exception_pattern, declare_section, re.IGNORECASE):
            exceptions.append(TriggerException(name=match.group(1), type="user_defined"))
        
        # Extract variables
        var_pattern = r'(\w+)\s+([^;:=]+?)(?:\s*:=\s*([^;]+))?\s*;'
        for match in re.finditer(var_pattern, declare_section, re.IGNORECASE):
            name = match.group(1)
            data_type = match.group(2).strip()
            default_value = match.group(3).strip() if match.group(3) else None
            
            # Skip exceptions
            if 'exception' in data_type.lower():
                continue
                
            # Check if it's a constant
            if 'constant' in data_type.lower():
                # Extract the actual type and value
                const_match = re.match(r'(.+?)\s+constant\s+(.+)', data_type, re.IGNORECASE)
                if const_match:
                    actual_type = const_match.group(1).strip()
                    value = default_value if default_value else const_match.group(2).strip()
                    constants.append(Constant(name=name, data_type=actual_type, value=value))
                else:
                    constants.append(Constant(name=name, data_type=data_type, value=default_value or ""))
            else:
                variables.append(Variable(name=name, data_type=data_type, default_value=default_value))
        
        return Declarations(
            variables=variables if variables else None,
            constants=constants if constants else None,
            exceptions=exceptions if exceptions else None
        )
    
    def _extract_data_operations(self, content: str) -> List[DataOperation]:
        """Extract and categorize data operations from the trigger"""
        operations = []
        
        # Find the main body (between BEGIN and EXCEPTION/END)
        begin_match = re.search(r'(?:^|\n)\s*begin\s*$', content, re.IGNORECASE | re.MULTILINE)
        exception_match = re.search(r'(?:^|\n)\s*exception\s*$', content, re.IGNORECASE | re.MULTILINE)
        end_match = re.search(r'(?:^|\n)\s*end\s*;?\s*$', content, re.IGNORECASE | re.MULTILINE)
        
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
            # If no BEGIN found, analyze the whole content
            body = content
        
        # Parse the body into logical blocks
        operations.extend(self._parse_sql_statements(body))
        operations.extend(self._parse_control_flow(body))
        operations.extend(self._parse_assignments(body))
        operations.extend(self._parse_function_calls(body))
        
        return operations
    
    def _parse_sql_statements(self, body: str) -> List[DataOperation]:
        """Parse SELECT, INSERT, UPDATE, DELETE statements"""
        operations = []
        
        # SQL statement patterns
        patterns = {
            'select_statements': r'select\s+.*?(?:;|\n\s*(?:if|when|else|end|exception|begin))',
            'insert_statements': r'insert\s+into\s+.*?(?:;|\n\s*(?:if|when|else|end|exception|begin))',
            'update_statements': r'update\s+.*?(?:;|\n\s*(?:if|when|else|end|exception|begin))',
            'delete_statements': r'delete\s+from\s+.*?(?:;|\n\s*(?:if|when|else|end|exception|begin))'
        }
        
        for stmt_type, pattern in patterns.items():
            for match in re.finditer(pattern, body, re.IGNORECASE | re.DOTALL):
                sql_text = match.group(0).strip()
                # Clean up the SQL
                sql_text = re.sub(r'\s+', ' ', sql_text)
                if sql_text.endswith(';'):
                    sql_text = sql_text[:-1]
                
                operations.append(DataOperation(
                    id=f"code_{self._next_id()}",
                    sql=sql_text + ";",
                    type=stmt_type
                ))
        
        return operations
    
    def _parse_control_flow(self, body: str) -> List[DataOperation]:
        """Parse control flow statements (IF, CASE, LOOP)"""
        operations = []
        
        # Parse IF statements
        if_pattern = r'if\s+.*?end\s+if\s*;'
        for match in re.finditer(if_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = match.group(0).strip()
            sql_text = re.sub(r'\s+', ' ', sql_text)
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="if_else"
            ))
        
        # Parse CASE statements
        case_pattern = r'case\s+.*?end\s+case\s*;'
        for match in re.finditer(case_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = match.group(0).strip()
            sql_text = re.sub(r'\s+', ' ', sql_text)
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="case_statements"
            ))
        
        # Parse LOOP statements
        loop_pattern = r'(?:for\s+\w+\s+in\s+.*?|while\s+.*?|loop)\s+.*?end\s+loop\s*;'
        for match in re.finditer(loop_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = match.group(0).strip()
            sql_text = re.sub(r'\s+', ' ', sql_text)
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="loop_statements"
            ))
        
        # Parse BEGIN blocks
        begin_pattern = r'begin\s+.*?(?:exception.*?)?end\s*;'
        for match in re.finditer(begin_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = match.group(0).strip()
            sql_text = re.sub(r'\s+', ' ', sql_text)
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="begin_block"
            ))
        
        return operations
    
    def _parse_assignments(self, body: str) -> List[DataOperation]:
        """Parse variable assignments"""
        operations = []
        
        # Assignment pattern
        assignment_pattern = r'(\w+)\s*:=\s*([^;]+)\s*;'
        for match in re.finditer(assignment_pattern, body, re.IGNORECASE):
            sql_text = match.group(0).strip()
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="assignment"
            ))
        
        return operations
    
    def _parse_function_calls(self, body: str) -> List[DataOperation]:
        """Parse function calls that are not part of other statements"""
        operations = []
        
        # Function call pattern (procedure calls)
        func_pattern = r'(\w+(?:\.\w+)*)\s*\([^;]*\)\s*;'
        for match in re.finditer(func_pattern, body, re.IGNORECASE):
            sql_text = match.group(0).strip()
            # Skip if it's part of a larger SQL statement
            if not any(keyword in sql_text.lower() for keyword in ['select', 'insert', 'update', 'delete', 'if', 'case']):
                operations.append(DataOperation(
                    id=f"code_{self._next_id()}",
                    sql=sql_text,
                    type="function_call"
                ))
        
        return operations
    
    def _extract_exception_handlers(self, content: str) -> List[ExceptionHandler]:
        """Extract exception handlers from the trigger"""
        handlers = []
        
        # Find the EXCEPTION section
        exception_match = re.search(r'(?:^|\n)\s*exception\s*$', content, re.IGNORECASE | re.MULTILINE)
        end_match = re.search(r'(?:^|\n)\s*end\s*;?\s*$', content, re.IGNORECASE | re.MULTILINE)
        
        if exception_match:
            start_pos = exception_match.end()
            end_pos = end_match.start() if end_match else len(content)
            exception_section = content[start_pos:end_pos]
            
            # Parse exception handlers
            handler_pattern = r'when\s+(\w+)\s+then\s+(.*?)(?=when\s+\w+\s+then|$)'
            for match in re.finditer(handler_pattern, exception_section, re.IGNORECASE | re.DOTALL):
                exception_name = match.group(1)
                handler_code = match.group(2).strip()
                # Clean up the handler code
                handler_code = re.sub(r'\s+', ' ', handler_code)
                if not handler_code.endswith(';'):
                    handler_code += ";"
                
                handlers.append(ExceptionHandler(
                    exception_name=exception_name,
                    handler_code=handler_code
                ))
        
        return handlers
    
    def _next_id(self) -> int:
        """Get next operation ID"""
        self.operation_counter += 1
        return self.operation_counter
    
    def validate_sql(self, sql_text: str) -> bool:
        """Validate SQL using sqlparse"""
        try:
            parsed = sqlparse.parse(sql_text)
            return len(parsed) > 0 and not any(token.ttype is tokens.Error for token in parsed[0].flatten())
        except Exception:
            return False
    
    def convert_to_json(self, analysis: TriggerAnalysis) -> Dict[str, Any]:
        """Convert analysis to JSON format matching expected output"""
        result = {
            "trigger_metadata": asdict(analysis.trigger_metadata),
            "declarations": {},
            "data_operations": [asdict(op) for op in analysis.data_operations],
            "exception_handlers": [asdict(eh) for eh in analysis.exception_handlers]
        }
        
        # Handle declarations
        if analysis.declarations.variables:
            result["declarations"]["variables"] = [asdict(v) for v in analysis.declarations.variables]
        if analysis.declarations.constants:
            result["declarations"]["constants"] = [asdict(c) for c in analysis.declarations.constants]
        if analysis.declarations.exceptions:
            result["declarations"]["exceptions"] = [asdict(e) for e in analysis.declarations.exceptions]
        
        return result

def main():
    """Main function to process all trigger files"""
    analyzer = OracleTriggerAnalyzer()
    
    # Input and output directories
    input_dir = Path("files/oracle")
    output_dir = Path("files/sql_json")
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Process each trigger file
    for sql_file in input_dir.glob("*.sql"):
        print(f"Processing {sql_file.name}...")
        
        try:
            # Analyze the trigger
            analysis = analyzer.analyze_trigger_file(str(sql_file))
            
            # Convert to JSON
            json_data = analyzer.convert_to_json(analysis)
            
            # Write to output file
            output_file = output_dir / f"{sql_file.stem}_enhanced_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Generated {output_file.name}")
            
        except Exception as e:
            print(f"✗ Error processing {sql_file.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
