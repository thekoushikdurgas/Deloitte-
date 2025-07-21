#!/usr/bin/env python3
"""
Enhanced Stake Flow Oracle SQL Analyzer - Version 2

This is an improved version that better handles Oracle SQL parsing and statement extraction.
It uses a more robust approach to identify and extract SQL statements from the main body.

Key Improvements:
- Better SQL statement boundary detection
- Improved handling of complex Oracle SQL constructs
- More robust tokenization
- Enhanced statement classification
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


class ImprovedSQLExtractor:
    """Improved SQL statement extractor that handles Oracle SQL constructs better"""
    
    def __init__(self):
        self.statement_patterns = [
            # SELECT statements
            (r'select\s+.*?(?:;|\s+(?=(?:select|insert|update|delete|if|case|for|loop|begin|end|exception)\s))', 'select_statements'),
            
            # INSERT statements  
            (r'insert\s+into\s+[^;]+;?', 'insert_statements'),
            
            # UPDATE statements
            (r'update\s+[^;]+;?', 'update_statements'),
            
            # DELETE statements
            (r'delete\s+from\s+[^;]+;?', 'delete_statements'),
            
            # IF statements (complex handling)
            (r'if\s*\([^)]+\)\s*then\s+[^;]+(?:\s*end\s+if)?;?', 'if_else'),
            (r'if\s+[^;]+?\s+then\s+[^;]+?(?:\s*end\s+if)?;?', 'if_else'),
            
            # Variable assignments
            (r'\w+\s*:=\s*[^;]+;?', 'assignment_statements'),
            
            # CASE statements
            (r'case\s+.*?\s+end\s+case;?', 'case_statements'),
            
            # RAISE statements
            (r'raise\s+[^;]*;?', 'exception_statements'),
            
            # Function calls
            (r'\w+\.\w+\([^)]*\);?', 'function_calls'),
        ]
        
    def extract_statements(self, sql_content: str) -> List[SQLStatement]:
        """Extract SQL statements from content using improved pattern matching"""
        statements = []
        statement_id = 1
        
        # Clean the content
        cleaned_content = self._clean_sql_content(sql_content)
        
        # Split into logical blocks first
        blocks = self._split_into_blocks(cleaned_content)
        
        for block in blocks:
            block_statements = self._extract_from_block(block, statement_id)
            statements.extend(block_statements)
            statement_id += len(block_statements)
            
        return statements
        
    def _clean_sql_content(self, content: str) -> str:
        """Clean SQL content for processing"""
        # Remove comments
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Normalize whitespace but preserve structure
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
        
    def _split_into_blocks(self, content: str) -> List[str]:
        """Split content into logical blocks for processing"""
        # Split by major keywords that indicate new blocks
        block_keywords = r'\b(?:if|case|for|while|loop|begin|select|insert|update|delete)\b'
        
        # Simple approach: split by semicolons and major keywords
        blocks = []
        current_block = ""
        
        # Split by semicolons first
        parts = content.split(';')
        
        for part in parts:
            part = part.strip()
            if part:
                current_block += part + ';'
                
                # Check if this completes a logical block
                if self._is_complete_block(current_block):
                    blocks.append(current_block.strip())
                    current_block = ""
                    
        # Add any remaining content
        if current_block.strip():
            blocks.append(current_block.strip())
            
        return blocks
        
    def _is_complete_block(self, block: str) -> bool:
        """Check if a block is logically complete"""
        block_lower = block.lower().strip()
        
        # Complete if ends with semicolon
        if block_lower.endswith(';'):
            return True
            
        # Check for complete control structures
        if 'if' in block_lower and 'then' in block_lower and 'end if' in block_lower:
            return True
            
        if 'case' in block_lower and 'end case' in block_lower:
            return True
            
        # Check for complete SQL statements
        if any(block_lower.startswith(keyword) for keyword in ['select', 'insert', 'update', 'delete']):
            return True
            
        return False
        
    def _extract_from_block(self, block: str, start_id: int) -> List[SQLStatement]:
        """Extract statements from a single block"""
        statements = []
        
        if not block.strip():
            return statements
            
        # Try to match against patterns
        for pattern, stmt_type in self.statement_patterns:
            matches = re.finditer(pattern, block, re.IGNORECASE | re.DOTALL)
            
            for i, match in enumerate(matches):
                sql_text = match.group(0).strip()
                
                # Clean up the SQL
                sql_text = self._clean_statement(sql_text)
                
                if len(sql_text) > 5:  # Skip very short statements
                    stmt = SQLStatement(
                        id=f"code_{start_id + len(statements)}",
                        sql=sql_text,
                        type=stmt_type
                    )
                    statements.append(stmt)
                    
        # If no patterns matched, try to create a generic statement
        if not statements and len(block.strip()) > 5:
            stmt_type = self._classify_generic_statement(block)
            stmt = SQLStatement(
                id=f"code_{start_id}",
                sql=self._clean_statement(block),
                type=stmt_type
            )
            statements.append(stmt)
            
        return statements
        
    def _clean_statement(self, sql_text: str) -> str:
        """Clean up individual SQL statement"""
        # Remove extra whitespace
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
        elif 'if' in statement_lower:
            return 'if_else'
        elif 'case' in statement_lower:
            return 'case_statements'
        elif 'raise' in statement_lower:
            return 'exception_statements'
        elif ':=' in statement_lower:
            return 'assignment_statements'
        else:
            return 'other_statements'


class SimpleSectionParser:
    """Simplified section parser focused on getting the main SQL body"""
    
    def parse_sections(self, sql_content: str) -> Tuple[str, str, str]:
        """Parse Oracle SQL into three sections with improved logic"""
        
        # Find section markers using case-insensitive search
        declare_pos = self._find_keyword_position(sql_content, 'declare')
        begin_pos = self._find_keyword_position(sql_content, 'begin')
        exception_pos = self._find_keyword_position(sql_content, 'exception')
        end_pos = self._find_keyword_position(sql_content, r'end\s*;?\s*$')
        
        declare_section = ""
        main_sql_section = ""
        exception_section = ""
        
        if declare_pos is not None and begin_pos is not None:
            # Extract DECLARE section
            declare_section = sql_content[declare_pos[1]:begin_pos[0]].strip()
            
            # Extract main SQL section
            main_start = begin_pos[1]
            main_end = exception_pos[0] if exception_pos else (end_pos[0] if end_pos else len(sql_content))
            main_sql_section = sql_content[main_start:main_end].strip()
            
            # Extract EXCEPTION section
            if exception_pos:
                exception_start = exception_pos[1]
                exception_end = end_pos[0] if end_pos else len(sql_content)
                exception_section = sql_content[exception_start:exception_end].strip()
                
        elif begin_pos is not None:
            # No DECLARE section
            main_start = begin_pos[1]
            main_end = exception_pos[0] if exception_pos else (end_pos[0] if end_pos else len(sql_content))
            main_sql_section = sql_content[main_start:main_end].strip()
            
            if exception_pos:
                exception_start = exception_pos[1]
                exception_end = end_pos[0] if end_pos else len(sql_content)
                exception_section = sql_content[exception_start:exception_end].strip()
        else:
            # Fallback - treat everything as main SQL
            main_sql_section = sql_content
            
        return declare_section, main_sql_section, exception_section
        
    def _find_keyword_position(self, content: str, keyword: str) -> Optional[Tuple[int, int]]:
        """Find position of keyword, returning (start, end) positions"""
        match = re.search(r'\b' + keyword + r'\b', content, re.IGNORECASE)
        if match:
            return (match.start(), match.end())
        return None


class DeclarationParser:
    """Parses variable, constant, and exception declarations"""
    
    def parse_declarations(self, declare_section: str) -> Tuple[List[Variable], List[Constant], List[Exception]]:
        """Parse declarations from DECLARE section"""
        variables = []
        constants = []
        exceptions = []
        
        if not declare_section.strip():
            return variables, constants, exceptions
            
        # Split by semicolons and newlines
        lines = re.split(r'[;\n]', declare_section)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse exceptions (simple pattern)
            if re.search(r'\w+\s+exception', line, re.IGNORECASE):
                exception_match = re.match(r'(\w+)\s+exception', line, re.IGNORECASE)
                if exception_match:
                    exceptions.append(Exception(name=exception_match.group(1)))
                continue
                
            # Parse constants
            const_match = re.match(r'(\w+)\s+constant\s+([^:]+):=\s*(.+)', line, re.IGNORECASE)
            if const_match:
                constants.append(Constant(
                    name=const_match.group(1),
                    data_type=const_match.group(2).strip(),
                    value=const_match.group(3).strip()
                ))
                continue
                
            # Parse variables (enhanced pattern)
            var_patterns = [
                r'(\w+)\s+(varchar2\s*\([^)]+\))\s*(?::=\s*(.+))?',
                r'(\w+)\s+(pls_integer|simple_integer|PLS_INTEGER|binary_integer)\s*(?::=\s*(.+))?',
                r'(\w+)\s+(number|date)\s*(?::=\s*(.+))?',
                r'(\w+)\s+(\w+\.\w+%type)\s*(?::=\s*(.+))?',
                r'(\w+)\s+(varchar2|number|date)\s*(?::=\s*(.+))?'
            ]
            
            for pattern in var_patterns:
                var_match = re.match(pattern, line, re.IGNORECASE)
                if var_match:
                    variables.append(Variable(
                        name=var_match.group(1),
                        data_type=var_match.group(2).strip(),
                        default_value=var_match.group(3).strip() if var_match.group(3) else None
                    ))
                    break
                    
        return variables, constants, exceptions


class ExceptionParser:
    """Parses exception handlers"""
    
    def parse_exception_handlers(self, exception_section: str) -> List[ExceptionHandler]:
        """Parse exception handlers from EXCEPTION section"""
        handlers = []
        
        if not exception_section.strip():
            return handlers
            
        # Split by WHEN clauses
        when_parts = re.split(r'\bwhen\s+', exception_section, flags=re.IGNORECASE)
        
        for part in when_parts[1:]:  # Skip first empty part
            # Extract exception name and handler code
            lines = part.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                
                # Extract exception name (word before 'then')
                then_match = re.search(r'^(\w+)\s+then\s*(.*)', first_line, re.IGNORECASE)
                if then_match:
                    exception_name = then_match.group(1)
                    handler_code = then_match.group(2)
                    
                    # Add remaining lines
                    if len(lines) > 1:
                        handler_code += ' ' + ' '.join(lines[1:])
                        
                    # Clean up handler code
                    handler_code = re.sub(r'\s+', ' ', handler_code).strip()
                    if handler_code.endswith(';'):
                        handler_code = handler_code[:-1]
                        
                    handlers.append(ExceptionHandler(
                        exception_name=exception_name,
                        handler_code=handler_code
                    ))
                    
        return handlers


class EnhancedOracleAnalyzer:
    """Enhanced Oracle analyzer with improved SQL extraction"""
    
    def __init__(self):
        self.section_parser = SimpleSectionParser()
        self.declaration_parser = DeclarationParser()
        self.exception_parser = ExceptionParser()
        self.sql_extractor = ImprovedSQLExtractor()
        
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
        
        print(f"DEBUG: Main SQL section length: {len(main_sql_section)}")
        print(f"DEBUG: Main SQL preview: {main_sql_section[:200]}...")
        
        # Parse declarations
        variables, constants, exceptions = self.declaration_parser.parse_declarations(declare_section)
        
        # Parse exception handlers
        exception_handlers = self.exception_parser.parse_exception_handlers(exception_section)
        
        # Extract SQL statements from main section
        data_operations = self.sql_extractor.extract_statements(main_sql_section)
        
        print(f"DEBUG: Extracted {len(data_operations)} data operations")
        
        # Extract metadata
        metadata = TriggerMetadata(
            trigger_name=trigger_name or "unknown_trigger",
            timing="AFTER",  # Default, could be improved with better detection
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
    analyzer = EnhancedOracleAnalyzer()
    
    # Define paths
    oracle_dir = Path("files/oracle")
    output_dir = Path("files/sql_json")
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Process each SQL file
    for sql_file in oracle_dir.glob("*.sql"):
        print(f"🔄 Processing {sql_file.name} with enhanced analyzer...")
        
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
            
            print(f"✅ Generated {output_file.name}")
            print(f"   📊 Data operations: {data_ops_count}")
            print(f"   📝 Variables: {variables_count}")
            print(f"   🚨 Exceptions: {exceptions_count}")
            
        except Exception as e:
            print(f"❌ Error processing {sql_file.name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main() 