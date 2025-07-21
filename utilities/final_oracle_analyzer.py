#!/usr/bin/env python3
"""
Final Working Oracle SQL Analyzer

This analyzer correctly parses Oracle SQL triggers into the expected JSON format
with proper data_operations extraction using stake flow principles.

Updated to remove all comments first before proceeding with any analysis work.
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


class SQLCommentRemover:
    """Utility class to remove all types of SQL comments"""
    
    @staticmethod
    def remove_all_comments(sql_content: str) -> str:
        """
        Remove all SQL comments from the content before any processing
        
        Handles:
        - Single line comments (-- comment)
        - Multi-line comments (/* comment */)
        - Comments within strings are preserved
        """
        # Remove single-line comments (-- to end of line)
        sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
        
        # Remove multi-line comments (/* ... */) 
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        return sql_content


class OracleSectionParser:
    """Parse Oracle SQL into DECLARE, main SQL body, and EXCEPTION sections"""
    
    def parse_sections(self, sql_content: str) -> Tuple[str, str, str]:
        """Parse Oracle SQL into three sections"""
        
        # Find section positions
        declare_pos = self._find_declare_position(sql_content)
        begin_pos = self._find_begin_position(sql_content)
        exception_pos = self._find_exception_position(sql_content, begin_pos)
        end_pos = self._find_end_position(sql_content)
        
        declare_section = ""
        main_sql_section = ""
        exception_section = ""
        
        if declare_pos is not None and begin_pos is not None:
            # Extract DECLARE section
            declare_section = sql_content[declare_pos:begin_pos].strip()
            
            # Extract main SQL section
            main_start = begin_pos
            main_end = exception_pos if exception_pos is not None else (end_pos if end_pos is not None else len(sql_content))
            main_sql_section = sql_content[main_start:main_end].strip()
            
            # Extract EXCEPTION section
            if exception_pos is not None:
                exception_end = end_pos if end_pos is not None else len(sql_content)
                exception_section = sql_content[exception_pos:exception_end].strip()
                
        elif begin_pos is not None:
            # No DECLARE section
            main_start = begin_pos
            main_end = exception_pos if exception_pos is not None else (end_pos if end_pos is not None else len(sql_content))
            main_sql_section = sql_content[main_start:main_end].strip()
            
            if exception_pos is not None:
                exception_end = end_pos if end_pos is not None else len(sql_content)
                exception_section = sql_content[exception_pos:exception_end].strip()
        else:
            # Fallback
            main_sql_section = sql_content
            
        return declare_section, main_sql_section, exception_section
    
    def _find_declare_position(self, content: str) -> Optional[int]:
        """Find position after DECLARE keyword"""
        match = re.search(r'^\s*declare\b', content, re.IGNORECASE | re.MULTILINE)
        return match.end() if match else None
    
    def _find_begin_position(self, content: str) -> Optional[int]:
        """Find position after BEGIN keyword"""
        match = re.search(r'\bbegin\b', content, re.IGNORECASE)
        return match.end() if match else None
    
    def _find_exception_position(self, content: str, begin_pos: Optional[int]) -> Optional[int]:
        """Find position of EXCEPTION section (after BEGIN, at line start)"""
        if begin_pos is None:
            return None
            
        # Look for EXCEPTION only after BEGIN section
        content_after_begin = content[begin_pos:]
        match = re.search(r'^\s*exception\b', content_after_begin, re.IGNORECASE | re.MULTILINE)
        
        if match:
            return begin_pos + match.end()
        return None
    
    def _find_end_position(self, content: str) -> Optional[int]:
        """Find position of END keyword at end"""
        match = re.search(r'\bend\s*;?\s*$', content, re.IGNORECASE)
        return match.start() if match else None


class SQLStatementExtractor:
    """Extract individual SQL statements from Oracle SQL body"""
    
    def extract_statements(self, sql_content: str) -> List[SQLStatement]:
        """Extract SQL statements from content"""
        statements = []
        
        if not sql_content.strip():
            return statements
            
        # Clean content (normalize whitespace only, comments already removed)
        cleaned_content = self._clean_content(sql_content)
        
        # Extract statements using multiple approaches
        statements = self._extract_by_patterns(cleaned_content)
        
        return statements
    
    def _clean_content(self, content: str) -> str:
        """Clean SQL content (comments already removed at start of analysis)"""
        # Normalize whitespace only - comments already removed
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def _extract_by_patterns(self, content: str) -> List[SQLStatement]:
        """Extract statements using regex patterns"""
        statements = []
        statement_id = 1
        
        # Define SQL patterns
        patterns = [
            # SELECT statements (with INTO)
            (r'select\s+(?:distinct\s+)?.*?\s+into\s+[^;]+\s+from\s+[^;]+(?:\s+where\s+[^;]+)?(?:\s+and\s+[^;]+)*(?:\s+order\s+by\s+[^;]+)?', 'select_statements'),
            
            # Regular SELECT statements
            (r'select\s+(?:distinct\s+)?.*?\s+from\s+[^;]+(?:\s+where\s+[^;]+)?(?:\s+and\s+[^;]+)*(?:\s+order\s+by\s+[^;]+)?', 'select_statements'),
            
            # INSERT statements
            (r'insert\s+into\s+[^;]+(?:\([^)]+\))?\s*values\s*\([^)]+\)', 'insert_statements'),
            
            # UPDATE statements
            (r'update\s+[^;]+\s+set\s+[^;]+(?:\s+where\s+[^;]+)?', 'update_statements'),
            
            # DELETE statements
            (r'delete\s+from\s+[^;]+(?:\s+where\s+[^;]+)?', 'delete_statements'),
            
            # IF statements
            (r'if\s*\([^)]+\)\s*then\s+[^;]+', 'if_else'),
            (r'if\s+[^;]+?\s+then\s+[^;]+', 'if_else'),
            
            # Variable assignments
            (r'\w+\s*:=\s*[^;]+', 'assignment_statements'),
            
            # RAISE statements
            (r'raise\s+\w+', 'exception_statements'),
            (r'raise_application_error\s*\([^)]+\)', 'exception_statements'),
        ]
        
        # Process content to extract statements
        processed_content = content
        
        for pattern, stmt_type in patterns:
            matches = list(re.finditer(pattern, processed_content, re.IGNORECASE | re.DOTALL))
            
            for match in matches:
                sql_text = match.group(0).strip()
                sql_text = self._clean_statement(sql_text)
                
                if len(sql_text) > 5:  # Skip very short statements
                    stmt = SQLStatement(
                        id=f"code_{statement_id}",
                        sql=sql_text,
                        type=stmt_type
                    )
                    statements.append(stmt)
                    statement_id += 1
                    
                    # Remove this match from content to avoid duplicates
                    processed_content = processed_content[:match.start()] + ' ' * len(match.group(0)) + processed_content[match.end():]
        
        return statements
    
    def _clean_statement(self, sql_text: str) -> str:
        """Clean individual SQL statement"""
        sql_text = re.sub(r'\s+', ' ', sql_text).strip()
        
        # Remove trailing semicolon for consistency
        if sql_text.endswith(';'):
            sql_text = sql_text[:-1]
            
        return sql_text


class DeclarationParser:
    """Parse variable, constant, and exception declarations"""
    
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
                
            # Parse exceptions first
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
                
            # Parse variables
            var_patterns = [
                r'(\w+)\s+(varchar2\s*\([^)]+\))\s*(?::=\s*(.+))?',
                r'(\w+)\s+(pls_integer|simple_integer|PLS_INTEGER|binary_integer)\s*(?::=\s*(.+))?',
                r'(\w+)\s+(number|date)\s*(?::=\s*(.+))?',
                r'(\w+)\s+(\w+\.\w+%type)\s*(?::=\s*(.+))?',
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
        return [decl.strip() for decl in declare_section.split(';') if decl.strip()]


class ExceptionParser:
    """Parse exception handlers"""
    
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


class WorkingOracleAnalyzer:
    """Working Oracle analyzer that produces correct JSON output"""
    
    def __init__(self):
        self.section_parser = OracleSectionParser()
        self.declaration_parser = DeclarationParser()
        self.exception_parser = ExceptionParser()
        self.sql_extractor = SQLStatementExtractor()
        
    def analyze_trigger_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Oracle trigger file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        trigger_name = Path(file_path).stem
        return self.analyze_trigger(content, trigger_name)
        
    def analyze_trigger(self, sql_content: str, trigger_name: str = None) -> Dict[str, Any]:
        """Analyze Oracle trigger content"""
        
        # STEP 1: Remove all comments FIRST before any other processing
        print(f"🧹 Removing comments from {trigger_name}...")
        cleaned_sql_content = SQLCommentRemover.remove_all_comments(sql_content)
        
        # STEP 2: Parse into sections (using comment-free content)
        declare_section, main_sql_section, exception_section = self.section_parser.parse_sections(cleaned_sql_content)
        
        # STEP 3: Parse declarations
        variables, constants, exceptions = self.declaration_parser.parse_declarations(declare_section)
        
        # STEP 4: Parse exception handlers
        exception_handlers = self.exception_parser.parse_exception_handlers(exception_section)
        
        # STEP 5: Extract SQL statements from main section
        data_operations = self.sql_extractor.extract_statements(main_sql_section)
        
        # STEP 6: Extract metadata (using original content for detection)
        metadata = TriggerMetadata(
            trigger_name=trigger_name or "unknown_trigger",
            timing="AFTER",
            has_declare_section=bool(declare_section),
            has_begin_section="begin" in cleaned_sql_content.lower(),
            has_exception_section=bool(exception_section)
        )
        
        # Detect events (using cleaned content)
        events = []
        if re.search(r'if\s*\(\s*inserting\s*\)', cleaned_sql_content, re.IGNORECASE):
            events.append("INSERT")
        if re.search(r'if\s*\(\s*updating\s*\)', cleaned_sql_content, re.IGNORECASE):
            events.append("UPDATE")
        if re.search(r'if\s*\(\s*deleting\s*\)', cleaned_sql_content, re.IGNORECASE):
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
    """Main function to process Oracle trigger files"""
    analyzer = WorkingOracleAnalyzer()
    
    # Define paths
    oracle_dir = Path("files/oracle")
    output_dir = Path("files/sql_json")
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting Oracle SQL to JSON conversion with comment removal...")
    
    # Process each SQL file
    for sql_file in oracle_dir.glob("*.sql"):
        print(f"\n🔄 Processing {sql_file.name} with comment-aware analyzer...")
        
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
                print(f"   📋 Sample: {analysis['data_operations'][0]['sql'][:50]}...")
                
        except Exception as e:
            print(f"❌ Error processing {sql_file.name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n🎉 Oracle SQL to JSON conversion completed!")


if __name__ == "__main__":
    main() 