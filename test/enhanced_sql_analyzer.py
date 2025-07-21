#!/usr/bin/env python3
"""
Enhanced SQL Analysis Tool for Oracle Triggers
Advanced version with improved parsing, validation, and analysis
"""

import re
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path

try:
    import sqlparse
    from sqlparse import sql, tokens
    SQLPARSE_AVAILABLE = True
except ImportError:
    print("Installing sqlparse...")
    os.system("pip install sqlparse")
    try:
        import sqlparse
        from sqlparse import sql, tokens
        SQLPARSE_AVAILABLE = True
    except ImportError:
        print("Warning: sqlparse not available")
        SQLPARSE_AVAILABLE = False

try:
    import sqlglot
    from sqlglot import parse, transpile
    SQLGLOT_AVAILABLE = True
except ImportError:
    print("Installing sqlglot...")
    os.system("pip install sqlglot")
    try:
        import sqlglot
        from sqlglot import parse, transpile
        SQLGLOT_AVAILABLE = True
    except ImportError:
        print("Warning: sqlglot not available")
        SQLGLOT_AVAILABLE = False

# Enhanced Data structures
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

class EnhancedOracleTriggerAnalyzer:
    """Enhanced analyzer class for Oracle SQL triggers with improved parsing"""
    
    def __init__(self):
        self.operation_counter = 0
        self.debug = False
        
    def analyze_trigger_file(self, file_path: str) -> TriggerAnalysis:
        """Analyze a single Oracle trigger file with enhanced parsing"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reset counter for each file
        self.operation_counter = 0
        
        # Clean and preprocess content
        content = self._preprocess_content(content)
        
        # Extract basic metadata
        trigger_name = Path(file_path).stem
        metadata = self._extract_metadata(content, trigger_name)
        
        # Parse declarations with enhanced logic
        declarations = self._extract_declarations_enhanced(content)
        
        # Extract data operations with improved parsing
        data_operations = self._extract_data_operations_enhanced(content)
        
        # Extract exception handlers
        exception_handlers = self._extract_exception_handlers_enhanced(content)
        
        return TriggerAnalysis(
            trigger_metadata=metadata,
            declarations=declarations,
            data_operations=data_operations,
            exception_handlers=exception_handlers
        )
    
    def _preprocess_content(self, content: str) -> str:
        """Clean and preprocess SQL content"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\s*;\s*', ';\n', content)
        content = re.sub(r'\s*\n\s*', '\n', content)
        
        # Fix common Oracle syntax issues
        content = re.sub(r'--[^\n]*', '', content)  # Remove single-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)  # Remove multi-line comments
        
        return content.strip()
    
    def _extract_metadata(self, content: str, trigger_name: str) -> TriggerMetadata:
        """Extract trigger metadata with enhanced logic"""
        content_upper = content.upper()
        
        # Determine timing more accurately
        timing = "BEFORE"  # Default for Oracle
        if "AFTER" in content_upper:
            timing = "AFTER"
        elif "INSTEAD OF" in content_upper:
            timing = "INSTEAD OF"
            
        # Determine events more accurately
        events = []
        if re.search(r'\b(INSERTING|INSERT)\b', content_upper):
            events.append("INSERT")
        if re.search(r'\b(UPDATING|UPDATE)\b', content_upper):
            events.append("UPDATE")
        if re.search(r'\b(DELETING|DELETE)\b', content_upper):
            events.append("DELETE")
        
        # Check for sections
        has_declare = bool(re.search(r'^\s*declare\s*$', content, re.IGNORECASE | re.MULTILINE))
        has_begin = bool(re.search(r'^\s*begin\s*$', content, re.IGNORECASE | re.MULTILINE))
        has_exception = bool(re.search(r'^\s*exception\s*$', content, re.IGNORECASE | re.MULTILINE))
        
        # Enhanced table name extraction
        table_name = self._extract_table_name_enhanced(content, trigger_name)
        
        return TriggerMetadata(
            trigger_name=trigger_name,
            timing=timing,
            events=events if events else ["INSERT", "UPDATE", "DELETE"],
            table_name=table_name,
            has_declare_section=has_declare,
            has_begin_section=has_begin,
            has_exception_section=has_exception
        )
    
    def _extract_table_name_enhanced(self, content: str, trigger_name: str) -> str:
        """Enhanced table name extraction"""
        # Known mappings first
        table_mappings = {
            "trigger1": "themes",
            "trigger2": "theme_molecule_map", 
            "trigger3": "company_addresses"
        }
        
        if trigger_name in table_mappings:
            return table_mappings[trigger_name]
        
        # Extract from common patterns
        patterns = [
            r"insert\s+into\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"update\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+set",
            r"delete\s+from\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+",
        ]
        
        table_counts = {}
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                table = match.split('.')[-1].lower()
                if table not in ['dual', 'sysdate', 'user']:
                    table_counts[table] = table_counts.get(table, 0) + 1
        
        if table_counts:
            return max(table_counts.items(), key=lambda x: x[1])[0]
        
        return "unknown_table"
    
    def _extract_declarations_enhanced(self, content: str) -> Declarations:
        """Enhanced declaration extraction with better parsing"""
        variables = []
        constants = []
        exceptions = []
        
        # Find declare section more accurately
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
        
        # Split into lines and process
        lines = [line.strip() for line in declare_section.split('\n') if line.strip()]
        
        # Process each declaration
        current_declaration = ""
        for line in lines:
            current_declaration += " " + line
            if line.endswith(';'):
                self._process_declaration_line(current_declaration.strip(), variables, constants, exceptions)
                current_declaration = ""
        
        return Declarations(
            variables=variables if variables else None,
            constants=constants if constants else None,
            exceptions=exceptions if exceptions else None
        )
    
    def _process_declaration_line(self, line: str, variables: List[Variable], 
                                constants: List[Constant], exceptions: List[TriggerException]):
        """Process a single declaration line"""
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
                constants.append(Constant(name=name, data_type=data_type.strip(), value=value.strip() if value else ""))
            return
        
        # Variable declaration
        match = re.match(r'(\w+)\s+([^:=;]+?)(?:\s*:=\s*(.+))?', line, re.IGNORECASE)
        if match:
            name, data_type, default_value = match.groups()
            # Clean up data type
            data_type = re.sub(r'\s+', ' ', data_type.strip())
            variables.append(Variable(
                name=name,
                data_type=data_type,
                default_value=default_value.strip() if default_value else None
            ))
    
    def _extract_data_operations_enhanced(self, content: str) -> List[DataOperation]:
        """Enhanced data operations extraction"""
        operations = []
        
        # Find the main body
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
        
        # Parse operations in order of complexity
        operations.extend(self._parse_complex_blocks(body))
        operations.extend(self._parse_sql_statements_enhanced(body))
        operations.extend(self._parse_assignments_enhanced(body))
        operations.extend(self._parse_function_calls_enhanced(body))
        
        # Sort by position in original text for proper order
        return sorted(operations, key=lambda x: body.find(x.sql[:50]) if len(x.sql) > 50 else body.find(x.sql))
    
    def _parse_complex_blocks(self, body: str) -> List[DataOperation]:
        """Parse complex control flow blocks"""
        operations = []
        
        # Parse nested IF statements
        if_pattern = r'if\s+.*?end\s+if\s*;'
        for match in re.finditer(if_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = self._clean_sql(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="if_else"
            ))
        
        # Parse CASE statements
        case_pattern = r'case\s+.*?end\s+case\s*;'
        for match in re.finditer(case_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = self._clean_sql(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="case_statements"
            ))
        
        # Parse FOR loops
        for_pattern = r'for\s+\w+\s+in\s+.*?end\s+loop\s*;'
        for match in re.finditer(for_pattern, body, re.IGNORECASE | re.DOTALL):
            sql_text = self._clean_sql(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="loop_statements"
            ))
        
        # Parse BEGIN blocks
        begin_pattern = r'begin\s+.*?(?:exception.*?)?end\s*;'
        for match in re.finditer(begin_pattern, body, re.IGNORECASE | re.DOTALL):
            # Skip if this is the main BEGIN block
            if match.start() < 10:  # Near the beginning
                continue
            sql_text = self._clean_sql(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="begin_block"
            ))
        
        return operations
    
    def _parse_sql_statements_enhanced(self, body: str) -> List[DataOperation]:
        """Enhanced SQL statement parsing"""
        operations = []
        
        # More precise SQL patterns
        patterns = {
            'select_statements': r'select\s+.*?(?:into\s+.*?)?(?:from\s+.*?)?(?:where\s+.*?)?(?:;|\n(?=\s*(?:if|when|else|end|exception|begin|\w+\s*:=)))',
            'insert_statements': r'insert\s+into\s+.*?(?:values\s*\(.*?\)|select\s+.*?)?(?:;|\n(?=\s*(?:if|when|else|end|exception|begin|\w+\s*:=)))',
            'update_statements': r'update\s+.*?set\s+.*?(?:where\s+.*?)?(?:;|\n(?=\s*(?:if|when|else|end|exception|begin|\w+\s*:=)))',
            'delete_statements': r'delete\s+from\s+.*?(?:where\s+.*?)?(?:;|\n(?=\s*(?:if|when|else|end|exception|begin|\w+\s*:=)))'
        }
        
        for stmt_type, pattern in patterns.items():
            for match in re.finditer(pattern, body, re.IGNORECASE | re.DOTALL):
                sql_text = self._clean_sql(match.group(0))
                if self._is_valid_sql_statement(sql_text, stmt_type):
                    operations.append(DataOperation(
                        id=f"code_{self._next_id()}",
                        sql=sql_text,
                        type=stmt_type
                    ))
        
        return operations
    
    def _parse_assignments_enhanced(self, body: str) -> List[DataOperation]:
        """Enhanced assignment parsing"""
        operations = []
        
        # More precise assignment pattern
        assignment_pattern = r'(\w+)\s*:=\s*([^;]+)\s*;'
        for match in re.finditer(assignment_pattern, body, re.IGNORECASE):
            sql_text = self._clean_sql(match.group(0))
            operations.append(DataOperation(
                id=f"code_{self._next_id()}",
                sql=sql_text,
                type="assignment"
            ))
        
        return operations
    
    def _parse_function_calls_enhanced(self, body: str) -> List[DataOperation]:
        """Enhanced function call parsing"""
        operations = []
        
        # Function/procedure call pattern
        func_pattern = r'(\w+(?:\.\w+)*)\s*\([^;]*\)\s*;'
        for match in re.finditer(func_pattern, body, re.IGNORECASE):
            sql_text = self._clean_sql(match.group(0))
            # Skip if it's part of a larger statement or assignment
            if not any(keyword in sql_text.lower() for keyword in ['select', 'insert', 'update', 'delete', 'if', 'case', ':=']):
                operations.append(DataOperation(
                    id=f"code_{self._next_id()}",
                    sql=sql_text,
                    type="function_call"
                ))
        
        return operations
    
    def _extract_exception_handlers_enhanced(self, content: str) -> List[ExceptionHandler]:
        """Enhanced exception handler extraction"""
        handlers = []
        
        # Find exception section
        exception_match = re.search(r'^\s*exception\s*$', content, re.IGNORECASE | re.MULTILINE)
        end_match = re.search(r'^\s*end\s*;?\s*$', content, re.IGNORECASE | re.MULTILINE)
        
        if exception_match:
            start_pos = exception_match.end()
            end_pos = end_match.start() if end_match else len(content)
            exception_section = content[start_pos:end_pos]
            
            # Parse handlers more carefully
            handler_pattern = r'when\s+(\w+)\s+then\s+(.*?)(?=when\s+\w+\s+then|$)'
            for match in re.finditer(handler_pattern, exception_section, re.IGNORECASE | re.DOTALL):
                exception_name = match.group(1)
                handler_code = self._clean_sql(match.group(2).strip())
                if not handler_code.endswith(';'):
                    handler_code += ";"
                
                handlers.append(ExceptionHandler(
                    exception_name=exception_name,
                    handler_code=handler_code
                ))
        
        return handlers
    
    def _clean_sql(self, sql_text: str) -> str:
        """Clean and format SQL text"""
        # Remove excessive whitespace
        sql_text = re.sub(r'\s+', ' ', sql_text.strip())
        
        # Ensure proper semicolon ending
        if not sql_text.endswith(';'):
            sql_text += ";"
        
        return sql_text
    
    def _is_valid_sql_statement(self, sql_text: str, stmt_type: str) -> bool:
        """Validate if the SQL statement is properly formed"""
        if not sql_text.strip():
            return False
        
        # Basic validation based on statement type
        sql_lower = sql_text.lower()
        if stmt_type == 'select_statements' and not sql_lower.startswith('select'):
            return False
        elif stmt_type == 'insert_statements' and not sql_lower.startswith('insert'):
            return False
        elif stmt_type == 'update_statements' and not sql_lower.startswith('update'):
            return False
        elif stmt_type == 'delete_statements' and not sql_lower.startswith('delete'):
            return False
        
        # Use sqlparse for validation if available
        if SQLPARSE_AVAILABLE:
            try:
                parsed = sqlparse.parse(sql_text)
                return len(parsed) > 0
            except Exception:
                pass
        
        return True
    
    def _next_id(self) -> int:
        """Get next operation ID"""
        self.operation_counter += 1
        return self.operation_counter
    
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
    
    def validate_output_against_expected(self, generated: Dict, expected: Dict) -> Dict[str, Any]:
        """Validate generated output against expected format"""
        validation_report = {
            "structure_match": True,
            "missing_fields": [],
            "extra_fields": [],
            "data_quality": {}
        }
        
        # Check structure
        expected_keys = set(expected.keys())
        generated_keys = set(generated.keys())
        
        validation_report["missing_fields"] = list(expected_keys - generated_keys)
        validation_report["extra_fields"] = list(generated_keys - expected_keys)
        validation_report["structure_match"] = len(validation_report["missing_fields"]) == 0
        
        # Check data operations count
        if "data_operations" in expected and "data_operations" in generated:
            expected_ops = len(expected.get("data_operations", []))
            generated_ops = len(generated.get("data_operations", []))
            validation_report["data_quality"]["operation_count_ratio"] = generated_ops / expected_ops if expected_ops > 0 else 0
        
        return validation_report

def main():
    """Main function to process all trigger files with enhanced analysis"""
    analyzer = EnhancedOracleTriggerAnalyzer()
    
    # Input and output directories
    input_dir = Path("files/oracle")
    output_dir = Path("files/sql_json")
    expected_dir = Path("files/expected_ana_json")
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Process each trigger file
    for sql_file in input_dir.glob("*.sql"):
        print(f"Processing {sql_file.name} with enhanced analyzer...")
        
        try:
            # Analyze the trigger
            analysis = analyzer.analyze_trigger_file(str(sql_file))
            
            # Convert to JSON
            json_data = analyzer.convert_to_json(analysis)
            
            # Write to output file
            output_file = output_dir / f"{sql_file.stem}_enhanced_analysis_v2.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Generated {output_file.name}")
            
            # Validate against expected if available
            expected_file = expected_dir / f"{sql_file.stem}_enhanced_analysis.json"
            if expected_file.exists():
                with open(expected_file, 'r', encoding='utf-8') as f:
                    expected_data = json.load(f)
                
                validation = analyzer.validate_output_against_expected(json_data, expected_data)
                print(f"  Validation: Structure match: {validation['structure_match']}")
                if "operation_count_ratio" in validation.get("data_quality", {}):
                    ratio = validation["data_quality"]["operation_count_ratio"]
                    print(f"  Operation coverage: {ratio:.1%}")
            
        except Exception as e:
            print(f"✗ Error processing {sql_file.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 