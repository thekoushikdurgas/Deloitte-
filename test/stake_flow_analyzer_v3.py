#!/usr/bin/env python3
"""
Final Stake Flow Oracle SQL Analyzer - Version 3

This version fixes the section parsing logic to properly extract the main SQL body
and implements comprehensive SQL statement extraction with proper classification.

Key Fixes:
- Correct EXCEPTION section detection (line start, not declaration)
- Robust main SQL body extraction
- Improved SQL statement parsing
- Better handling of Oracle SQL constructs
"""

import re
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class SQLStatement:
    """Represents an individual SQL statement"""
    id: str
    sql: str
    type: str


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
class ExceptionHandler:
    """Represents an exception handler"""
    exception_name: str
    handler_code: str


@dataclass
class TriggerMetadata:
    """Represents trigger metadata"""
    trigger_name: str
    timing: str = "BEFORE"
    events: List[str] = None
    table_name: str = "unknown_table"
    has_declare_section: bool = False
    has_begin_section: bool = False
    has_exception_section: bool = False

    def __post_init__(self):
        if self.events is None:
            self.events = ["INSERT", "UPDATE", "DELETE"]


class CorrectSectionParser:
    """Corrected section parser that properly identifies Oracle SQL sections"""
    
    def parse_sections(self, sql_content: str) -> Tuple[str, str, str]:
        """Parse Oracle SQL into three sections with correct logic"""
        
        # Find DECLARE section (at start of content)
        declare_match = re.search(r'^\s*declare\b', sql_content, re.IGNORECASE | re.MULTILINE)
        
        # Find BEGIN section
        begin_match = re.search(r'\bbegin\b', sql_content, re.IGNORECASE)
        
        # Find EXCEPTION section (must be at start of line, after BEGIN)
        exception_match = None
        if begin_match:
            # Look for EXCEPTION only after BEGIN section
            content_after_begin = sql_content[begin_match.end():]
            exception_in_main = re.search(r'^\s*exception\b', content_after_begin, re.IGNORECASE | re.MULTILINE)
            if exception_in_main:
                # Adjust position to be relative to original content
                exception_match = type('Match', (), {
                    'start': lambda: begin_match.end() + exception_in_main.start(),
                    'end': lambda: begin_match.end() + exception_in_main.end()
                })()
        
        # Find END section (at end of content)
        end_match = re.search(r'\bend\s*;?\s*$', sql_content, re.IGNORECASE)
        
        declare_section = ""
        main_sql_section = ""
        exception_section = ""
        
        if declare_match and begin_match:
            # Extract DECLARE section
            declare_section = sql_content[declare_match.end():begin_match.start()].strip()
            
            # Extract main SQL section
            main_start = begin_match.end()
            main_end = exception_match.start() if exception_match else (end_match.start() if end_match else len(sql_content))
            main_sql_section = sql_content[main_start:main_end].strip()
            
            # Extract EXCEPTION section
            if exception_match:
                exception_start = exception_match.end()
                exception_end = end_match.start() if end_match else len(sql_content)
                exception_section = sql_content[exception_start:exception_end].strip()
                
        elif begin_match:
            # No DECLARE section
            main_start = begin_match.end()
            main_end = exception_match.start() if exception_match else (end_match.start() if end_match else len(sql_content))
            main_sql_section = sql_content[main_start:main_end].strip()
            
            if exception_match:
                exception_start = exception_match.end()
                exception_end = end_match.start() if end_match else len(sql_content)
                exception_section = sql_content[exception_start:exception_end].strip()
        else:
            # Fallback - treat everything as main SQL
            main_sql_section = sql_content
            
        return declare_section, main_sql_section, exception_section


class ComprehensiveSQLExtractor:
    """Comprehensive SQL statement extractor using multiple approaches"""
    
    def __init__(self):
        # Enhanced patterns that handle Oracle SQL better
        self.sql_patterns = [
            # SELECT statements (various forms)
            (r'select\s+(?:distinct\s+)?.*?\s+from\s+[^;]+(?:\s+where\s+[^;]+)?(?:\s+order\s+by\s+[^;]+)?;?', 'select_statements'),
            (r'select\s+.*?\s+into\s+[^;]+\s+from\s+[^;]+(?:\s+where\s+[^;]+)?;?', 'select_statements'),
            
            # INSERT statements
            (r'insert\s+into\s+[^;]+;?', 'insert_statements'),
            
            # UPDATE statements
            (r'update\s+[^;]+\s+set\s+[^;]+(?:\s+where\s+[^;]+)?;?', 'update_statements'),
            
            # DELETE statements
            (r'delete\s+from\s+[^;]+(?:\s+where\s+[^;]+)?;?', 'delete_statements'),
            
            # IF statements (various forms)
            (r'if\s*\([^)]+\)\s*then\s+[^;]+(?:\s*end\s+if)?;?', 'if_else'),
            (r'if\s+[^;]+?\s+then\s+[^;]+?(?:\s*end\s+if)?;?', 'if_else'),
            (r'if\s+[^;]+', 'if_else'),  # Simple IF without THEN
            
            # Variable assignments
            (r'\w+\s*:=\s*[^;]+;?', 'assignment_statements'),
            
            # CASE statements
            (r'case\s+[^;]+\s+end\s+case;?', 'case_statements'),
            
            # RAISE statements
            (r'raise\s+\w+;?', 'exception_statements'),
            (r'raise_application_error\s*\([^)]+\);?', 'exception_statements'),
            
            # Function/procedure calls
            (r'\w+\.\w+\([^)]*\);?', 'function_calls'),
            
            # Simple statements
            (r'\w+;', 'other_statements'),
        ]
        
    def extract_statements(self, sql_content: str) -> List[SQLStatement]:
        """Extract SQL statements using comprehensive approach"""
        statements = []
        
        if not sql_content.strip():
            return statements
            
        # Clean content first
        cleaned_content = self._clean_sql_content(sql_content)
        
        # Split by semicolons as primary approach
        statement_blocks = self._split_by_semicolons(cleaned_content)
        
        statement_id = 1
        for block in statement_blocks:
            block = block.strip()
            if len(block) > 3:  # Skip very short blocks
                # Try to extract statements from this block
                block_statements = self._extract_from_block(block, statement_id)
                statements.extend(block_statements)
                statement_id += len(block_statements)
                
        return statements
        
    def _clean_sql_content(self, content: str) -> str:
        """Clean SQL content for processing"""
        # Remove comments
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
        
    def _split_by_semicolons(self, content: str) -> List[str]:
        """Split content by semicolons, handling strings and nested structures"""
        blocks = []
        current_block = ""
        in_string = False
        paren_depth = 0
        
        i = 0
        while i < len(content):
            char = content[i]
            
            if char == "'" and (i == 0 or content[i-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ';' and paren_depth == 0:
                    # End of statement
                    if current_block.strip():
                        blocks.append(current_block.strip())
                    current_block = ""
                    i += 1
                    continue
                    
            current_block += char
            i += 1
            
        # Add remaining content
        if current_block.strip():
            blocks.append(current_block.strip())
            
        return blocks
        
    def _extract_from_block(self, block: str, start_id: int) -> List[SQLStatement]:
        """Extract statements from a single block"""
        statements = []
        
        # Try pattern matching first
        for pattern, stmt_type in self.sql_patterns:
            match = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
            if match:
                sql_text = match.group(0).strip()
                sql_text = self._clean_statement(sql_text)
                
                if len(sql_text) > 3:
                    stmt = SQLStatement(
                        id=f"code_{start_id}",
                        sql=sql_text,
                        type=stmt_type
                    )
                    statements.append(stmt)
                    return statements  # Return first match
                    
        # If no patterns matched, classify generically
        if not statements:
            stmt_type = self._classify_generic_statement(block)
            sql_text = self._clean_statement(block)
            
            if len(sql_text) > 3:
                stmt = SQLStatement(
                    id=f"code_{start_id}",
                    sql=sql_text,
                    type=stmt_type
                )
                statements.append(stmt)
                
        return statements
        
    def _clean_statement(self, sql_text: str) -> str:
        """Clean up individual SQL statement"""
        sql_text = re.sub(r'\s+', ' ', sql_text).strip()
        
        # Remove trailing semicolon for consistency
        if sql_text.endswith(';'):
            sql_text = sql_text[:-1]
            
        return sql_text
        
    def _classify_generic_statement(self, statement: str) -> str:
        """Classify a statement that didn't match specific patterns"""
        statement_lower = statement.lower().strip()
        
        if 'select' in statement_lower:
            return 'select_statements'
        elif 'insert' in statement_lower:
            return 'insert_statements'
        elif 'update' in statement_lower:
            return 'update_statements'
        elif 'delete' in statement_lower:
            return 'delete_statements'
        elif statement_lower.startswith('if'):
            return 'if_else'
        elif 'case' in statement_lower:
            return 'case_statements'
        elif 'raise' in statement_lower:
            return 'exception_statements'
        elif ':=' in statement_lower:
            return 'assignment_statements'
        elif statement_lower.startswith(('end', 'then', 'else')):
            return 'other_statements'
        else:
            return 'other_statements'


class DeclarationParser:
    """Enhanced declaration parser"""
    
    def parse_declarations(self, declare_section: str) -> Tuple[List[Variable], List[Constant], List[Exception]]:
        """Parse declarations from DECLARE section"""
        variables = []
        constants = []
        exceptions = []
        
        if not declare_section.strip():
            return variables, constants, exceptions
            
        # Split by semicolons
        declarations = self._split_declarations(declare_section)
        
        for decl in declarations:
            decl = decl.strip()
            if not decl:
                continue
                
            # Parse exceptions
            if 'exception' in decl.lower() and not (':=' in decl or 'constant' in decl.lower()):
                exception_match = re.match(r'(\w+)\s+exception', decl, re.IGNORECASE)
                if exception_match:
                    exceptions.append(Exception(name=exception_match.group(1)))
                continue
                
            # Parse constants
            const_match = re.match(r'(\w+)\s+constant\s+([^:]+):=\s*(.+)', decl, re.IGNORECASE)
            if const_match:
                constants.append(Constant(
                    name=const_match.group(1),
                    data_type=const_match.group(2).strip(),
                    value=const_match.group(3).strip()
                ))
                continue
                
            # Parse variables - multiple patterns
            var_patterns = [
                r'(\w+)\s+(varchar2\s*\([^)]+\))\s*(?::=\s*(.+))?',
                r'(\w+)\s+(pls_integer|simple_integer|PLS_INTEGER|binary_integer)\s*(?::=\s*(.+))?',
                r'(\w+)\s+(number|date)\s*(?::=\s*(.+))?',
                r'(\w+)\s+(\w+\.\w+%type)\s*(?::=\s*(.+))?',
                r'(\w+)\s+(varchar2|number|date)\s*(?::=\s*(.+))?'
            ]
            
            for pattern in var_patterns:
                var_match = re.match(pattern, decl, re.IGNORECASE)
                if var_match:
                    variables.append(Variable(
                        name=var_match.group(1),
                        data_type=var_match.group(2).strip(),
                        default_value=var_match.group(3).strip() if var_match.group(3) else None
                    ))
                    break
                    
        return variables, constants, exceptions
        
    def _split_declarations(self, declare_section: str) -> List[str]:
        """Split declarations by semicolon"""
        declarations = []
        current_decl = ""
        in_string = False
        
        for char in declare_section:
            if char == "'" and current_decl and current_decl[-1] != '\\':
                in_string = not in_string
            elif char == ';' and not in_string:
                if current_decl.strip():
                    declarations.append(current_decl.strip())
                current_decl = ""
                continue
                
            current_decl += char
            
        if current_decl.strip():
            declarations.append(current_decl.strip())
            
        return declarations


class ExceptionParser:
    """Exception handler parser"""
    
    def parse_exception_handlers(self, exception_section: str) -> List[ExceptionHandler]:
        """Parse exception handlers from EXCEPTION section"""
        handlers = []
        
        if not exception_section.strip():
            return handlers
            
        # Split by WHEN clauses
        when_parts = re.split(r'\bwhen\s+', exception_section, flags=re.IGNORECASE)
        
        for part in when_parts[1:]:  # Skip first empty part
            # Extract exception name and handler code
            then_match = re.search(r'^(\w+)\s+then\s+(.*?)(?=\bwhen\s+|\s*$)', part, re.IGNORECASE | re.DOTALL)
            if then_match:
                exception_name = then_match.group(1)
                handler_code = then_match.group(2).strip()
                
                # Clean up handler code
                handler_code = re.sub(r'\s+', ' ', handler_code).strip()
                if handler_code.endswith(';'):
                    handler_code = handler_code[:-1]
                    
                handlers.append(ExceptionHandler(
                    exception_name=exception_name,
                    handler_code=handler_code
                ))
                
        return handlers


class FinalOracleAnalyzer:
    """Final Oracle analyzer with all fixes applied"""
    
    def __init__(self):
        self.section_parser = CorrectSectionParser()
        self.declaration_parser = DeclarationParser()
        self.exception_parser = ExceptionParser()
        self.sql_extractor = ComprehensiveSQLExtractor()
        
    def analyze_trigger_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Oracle trigger file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        trigger_name = Path(file_path).stem
        return self.analyze_trigger(content, trigger_name)
        
    def analyze_trigger(self, sql_content: str, trigger_name: str = None) -> Dict[str, Any]:
        """Analyze Oracle trigger content"""
        
        # Parse into sections
        declare_section, main_sql_section, exception_section = self.section_parser.parse_sections(sql_content)
        
        # Parse declarations
        variables, constants, exceptions = self.declaration_parser.parse_declarations(declare_section)
        
        # Parse exception handlers
        exception_handlers = self.exception_parser.parse_exception_handlers(exception_section)
        
        # Extract SQL statements from main section
        data_operations = self.sql_extractor.extract_statements(main_sql_section)
        
        # Extract metadata
        metadata = TriggerMetadata(
            trigger_name=trigger_name or "unknown_trigger",
            timing="AFTER",  # Could detect this better
            has_declare_section=bool(declare_section),
            has_begin_section="begin" in sql_content.lower(),
            has_exception_section=bool(exception_section)
        )
        
        # Detect events
        events = []
        if re.search(r'if\s*\(\s*inserting\s*\)', sql_content, re.IGNORECASE):
            events.append("INSERT")
        if re.search(r'if\s*\(\s*updating\s*\)', sql_content, re.IGNORECASE):
            events.append("UPDATE")
        if re.search(r'if\s*\(\s*deleting\s*\)', sql_content, re.IGNORECASE):
            events.append("DELETE")
        if events:
            metadata.events = events
            
        return {
            "trigger_metadata": asdict(metadata),
            "declarations": {
                "variables": [asdict(v) for v in variables],
                "constants": [asdict(c) for c in constants],
                "exceptions": [asdict(e) for e in exceptions]
            },
            "data_operations": [asdict(op) for op in data_operations],
            "exception_handlers": [asdict(eh) for eh in exception_handlers]
        }
        
    def save_analysis(self, analysis_data: Dict[str, Any], output_file: str):
        """Save analysis to JSON file"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)


def main():
    """Main function"""
    analyzer = FinalOracleAnalyzer()
    
    # Define paths
    oracle_dir = Path("files/oracle")
    output_dir = Path("files/sql_json")
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Process each SQL file
    for sql_file in oracle_dir.glob("*.sql"):
        print(f"🔄 Processing {sql_file.name} with final analyzer...")
        
        try:
            # Analyze the trigger
            analysis = analyzer.analyze_trigger_file(str(sql_file))
            
            # Save to output file (overwrite existing)
            output_file = output_dir / f"{sql_file.stem}.json"
            analyzer.save_analysis(analysis, str(output_file))
            
            # Display summary
            data_ops_count = len(analysis.get('data_operations', []))
            variables_count = len(analysis.get('declarations', {}).get('variables', []))
            exceptions_count = len(analysis.get('declarations', {}).get('exceptions', []))
            handlers_count = len(analysis.get('exception_handlers', []))
            
            print(f"✅ Generated {output_file.name}")
            print(f"   📊 Data operations: {data_ops_count}")
            print(f"   📝 Variables: {variables_count}")
            print(f"   🚨 Exceptions: {exceptions_count}")
            print(f"   🛠️ Exception handlers: {handlers_count}")
            
            # Show first few data operations as preview
            if data_ops_count > 0:
                print(f"   📋 First data operation: {analysis['data_operations'][0]['type']}")
                
        except Exception as e:
            print(f"❌ Error processing {sql_file.name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main() 