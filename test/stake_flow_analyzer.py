#!/usr/bin/env python3
"""
Stake Flow Oracle SQL Analyzer

This module implements a comprehensive Oracle SQL trigger analyzer that uses
stake flow analysis (word-by-word parsing) to properly extract data operations
and convert Oracle SQL triggers to the expected enhanced JSON format.

Key Features:
- Stake flow analysis: Parse SQL word by word with validation
- Three-section parsing: DECLARE, main SQL body, EXCEPTION
- Individual SQL statement extraction
- Statement type classification
- Exact JSON format matching expected output
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
    line_number: int = 0
    complexity: int = 1


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


class SQLValidator:
    """Validates SQL statements using simple parsing rules"""
    
    def __init__(self):
        self.sql_keywords = {
            'select', 'insert', 'update', 'delete', 'from', 'where', 'into', 
            'values', 'set', 'if', 'then', 'else', 'end', 'begin', 'declare',
            'exception', 'when', 'raise', 'case', 'loop', 'for', 'while',
            'and', 'or', 'not', 'is', 'null', 'in', 'exists', 'between',
            'like', 'order', 'by', 'group', 'having', 'union', 'join',
            'inner', 'outer', 'left', 'right', 'on', 'as', 'count', 'sum',
            'max', 'min', 'avg', 'distinct', 'all'
        }
        
        self.pl_sql_keywords = {
            'if', 'then', 'elsif', 'else', 'end', 'case', 'when', 'loop',
            'for', 'while', 'exit', 'continue', 'return', 'raise', 'begin',
            'exception', 'declare', 'constant', 'variable', 'type', 'rowtype',
            'function', 'procedure', 'package', 'trigger', 'cursor'
        }
        
    def is_valid_partial_sql(self, tokens: List[str]) -> bool:
        """Check if a partial SQL statement could be valid"""
        if not tokens:
            return True
            
        # Basic validation - check if it starts with a valid keyword
        first_token = tokens[0].lower()
        if first_token in self.sql_keywords or first_token in self.pl_sql_keywords:
            return True
            
        # Check for variable assignments
        if len(tokens) >= 3 and tokens[1] == ':=':
            return True
            
        # Check for other valid patterns
        if any(keyword in [t.lower() for t in tokens] for keyword in self.sql_keywords):
            return True
            
        return False
        
    def is_complete_statement(self, tokens: List[str]) -> bool:
        """Check if tokens form a complete SQL statement"""
        if not tokens:
            return False
            
        # Check for statement terminators
        last_token = tokens[-1].lower()
        if last_token.endswith(';'):
            return True
            
        # Check for control flow completeness
        token_str = ' '.join(tokens).lower()
        
        # Complete IF statement
        if token_str.startswith('if') and 'then' in token_str and 'end if' in token_str:
            return True
            
        # Complete SELECT INTO statement
        if 'select' in token_str and 'into' in token_str and 'from' in token_str:
            return True
            
        # Complete INSERT statement
        if token_str.startswith('insert') and 'values' in token_str:
            return True
            
        # Complete UPDATE statement
        if token_str.startswith('update') and 'set' in token_str:
            return True
            
        # Complete DELETE statement
        if token_str.startswith('delete') and 'from' in token_str:
            return True
            
        return False


class StakeFlowAnalyzer:
    """Implements stake flow analysis for Oracle SQL"""
    
    def __init__(self):
        self.validator = SQLValidator()
        self.statement_classifiers = {
            'select': 'select_statements',
            'insert': 'insert_statements', 
            'update': 'update_statements',
            'delete': 'delete_statements',
            'if': 'if_else',
            'case': 'case_statements',
            'loop': 'loop_statements',
            'for': 'loop_statements',
            'while': 'loop_statements',
            'raise': 'exception_statements',
            'declare': 'declaration_statements',
            'begin': 'block_statements',
            'end': 'other_statements'
        }
        
    def tokenize_sql(self, sql_content: str) -> List[str]:
        """Tokenize SQL content into words"""
        # Remove comments
        sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        # Split into tokens, preserving important punctuation
        tokens = re.findall(r'''
            (?:[a-zA-Z_][a-zA-Z0-9_]*\.)*[a-zA-Z_][a-zA-Z0-9_]*  |  # Identifiers with dots
            :\w+                                                  |  # Bind variables
            '[^']*'                                              |  # String literals
            \d+(?:\.\d+)?                                        |  # Numbers
            <=|>=|<>|!=|:=                                       |  # Multi-char operators
            [();,=<>+\-*/]                                       |  # Single char operators
            \S                                                      # Any other non-space
        ''', sql_content, re.VERBOSE)
        
        # Clean up tokens
        cleaned_tokens = []
        for token in tokens:
            token = token.strip()
            if token:
                cleaned_tokens.append(token)
                
        return cleaned_tokens
        
    def analyze_with_stake_flow(self, sql_content: str) -> List[SQLStatement]:
        """Analyze SQL using stake flow (word by word) approach"""
        tokens = self.tokenize_sql(sql_content)
        statements = []
        current_stake = []
        statement_id = 1
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            current_stake.append(token)
            
            # Check if current stake is valid
            if not self.validator.is_valid_partial_sql(current_stake):
                # If not valid, try to complete previous statement
                if len(current_stake) > 1:
                    # Check if previous stake was complete
                    prev_stake = current_stake[:-1]
                    if self.validator.is_complete_statement(prev_stake):
                        # Save previous statement
                        stmt = self._create_statement(prev_stake, statement_id)
                        if stmt:
                            statements.append(stmt)
                            statement_id += 1
                        
                        # Start new stake with current token
                        current_stake = [token]
                    
            # Check if current stake is complete
            elif self.validator.is_complete_statement(current_stake):
                stmt = self._create_statement(current_stake, statement_id)
                if stmt:
                    statements.append(stmt)
                    statement_id += 1
                current_stake = []
                
            i += 1
            
        # Handle remaining tokens
        if current_stake and self.validator.is_valid_partial_sql(current_stake):
            stmt = self._create_statement(current_stake, statement_id)
            if stmt:
                statements.append(stmt)
                
        return statements
        
    def _create_statement(self, tokens: List[str], statement_id: int) -> Optional[SQLStatement]:
        """Create a SQLStatement from tokens"""
        if not tokens:
            return None
            
        sql_text = ' '.join(tokens)
        
        # Clean up SQL
        sql_text = re.sub(r'\s+', ' ', sql_text).strip()
        
        # Skip very short or meaningless statements
        if len(sql_text) < 3 or sql_text.lower() in ['end', 'begin', ';']:
            return None
            
        # Classify statement type
        stmt_type = self._classify_statement(tokens[0].lower())
        
        return SQLStatement(
            id=f"code_{statement_id}",
            sql=sql_text,
            type=stmt_type,
            complexity=self._calculate_complexity(sql_text)
        )
        
    def _classify_statement(self, first_token: str) -> str:
        """Classify statement type based on first token"""
        first_token = first_token.lower()
        
        # Handle special cases
        if first_token.startswith(':'):
            return 'assignment_statements'
            
        return self.statement_classifiers.get(first_token, 'other_statements')
        
    def _calculate_complexity(self, sql_text: str) -> int:
        """Calculate statement complexity"""
        complexity = 1
        
        # Add complexity for keywords
        keywords = ['select', 'from', 'where', 'join', 'union', 'case', 'if', 'loop']
        for keyword in keywords:
            complexity += sql_text.lower().count(keyword)
            
        # Add complexity for nested structures
        complexity += sql_text.count('(')
        complexity += sql_text.count('select')
        
        return complexity


class OracleTriSectionParser:
    """Parses Oracle SQL into three main sections: DECLARE, main SQL body, EXCEPTION"""
    
    def parse_sections(self, sql_content: str) -> Tuple[str, str, str]:
        """
        Parse Oracle SQL into three sections
        
        Returns:
            Tuple of (declare_section, main_sql_section, exception_section)
        """
        # Normalize content
        content = re.sub(r'\s+', ' ', sql_content).strip()
        
        # Find section boundaries
        declare_match = re.search(r'\bdeclare\b', content, re.IGNORECASE)
        begin_match = re.search(r'\bbegin\b', content, re.IGNORECASE)
        exception_match = re.search(r'\bexception\b', content, re.IGNORECASE)
        end_match = re.search(r'\bend\s*;?\s*$', content, re.IGNORECASE)
        
        declare_section = ""
        main_sql_section = ""
        exception_section = ""
        
        if declare_match and begin_match:
            # Extract DECLARE section
            declare_start = declare_match.end()
            declare_end = begin_match.start()
            declare_section = content[declare_start:declare_end].strip()
            
            # Extract main SQL section
            main_start = begin_match.end()
            main_end = exception_match.start() if exception_match else (end_match.start() if end_match else len(content))
            main_sql_section = content[main_start:main_end].strip()
            
            # Extract EXCEPTION section if exists
            if exception_match:
                exception_start = exception_match.end()
                exception_end = end_match.start() if end_match else len(content)
                exception_section = content[exception_start:exception_end].strip()
                
        elif begin_match:
            # No DECLARE section, just main SQL
            main_start = begin_match.end()
            main_end = exception_match.start() if exception_match else (end_match.start() if end_match else len(content))
            main_sql_section = content[main_start:main_end].strip()
            
            if exception_match:
                exception_start = exception_match.end()
                exception_end = end_match.start() if end_match else len(content)
                exception_section = content[exception_start:exception_end].strip()
        else:
            # Fallback - treat entire content as main SQL
            main_sql_section = content
            
        return declare_section, main_sql_section, exception_section


class DeclarationParser:
    """Parses variable, constant, and exception declarations"""
    
    def parse_declarations(self, declare_section: str) -> Tuple[List[Variable], List[Constant], List[Exception]]:
        """Parse declarations from DECLARE section"""
        variables = []
        constants = []
        exceptions = []
        
        if not declare_section:
            return variables, constants, exceptions
            
        # Split by semicolons but be careful of strings
        declarations = self._split_declarations(declare_section)
        
        for decl in declarations:
            decl = decl.strip()
            if not decl:
                continue
                
            # Parse exceptions
            exception_match = re.match(r'(\w+)\s+exception', decl, re.IGNORECASE)
            if exception_match:
                exceptions.append(Exception(name=exception_match.group(1)))
                continue
                
            # Parse constants
            constant_match = re.match(r'(\w+)\s+constant\s+([^:]+):=\s*([^;]+)', decl, re.IGNORECASE)
            if constant_match:
                constants.append(Constant(
                    name=constant_match.group(1),
                    data_type=constant_match.group(2).strip(),
                    value=constant_match.group(3).strip()
                ))
                continue
                
            # Parse variables
            var_match = re.match(r'(\w+)\s+((?:varchar2|number|date|pls_integer|simple_integer|binary_integer|PLS_INTEGER)\s*(?:\([^)]+\))?|\w+\.\w+%type)\s*(?::=\s*([^;]+))?', decl, re.IGNORECASE)
            if var_match:
                variables.append(Variable(
                    name=var_match.group(1),
                    data_type=var_match.group(2).strip(),
                    default_value=var_match.group(3).strip() if var_match.group(3) else None
                ))
                continue
                
        return variables, constants, exceptions
        
    def _split_declarations(self, declare_section: str) -> List[str]:
        """Split declarations by semicolon, handling string literals"""
        declarations = []
        current_decl = ""
        in_string = False
        
        i = 0
        while i < len(declare_section):
            char = declare_section[i]
            
            if char == "'" and (i == 0 or declare_section[i-1] != '\\'):
                in_string = not in_string
            elif char == ';' and not in_string:
                if current_decl.strip():
                    declarations.append(current_decl.strip())
                current_decl = ""
                i += 1
                continue
                
            current_decl += char
            i += 1
            
        if current_decl.strip():
            declarations.append(current_decl.strip())
            
        return declarations


class ExceptionParser:
    """Parses exception handlers"""
    
    def parse_exception_handlers(self, exception_section: str) -> List[ExceptionHandler]:
        """Parse exception handlers from EXCEPTION section"""
        handlers = []
        
        if not exception_section:
            return handlers
            
        # Split into individual WHEN clauses
        when_matches = re.finditer(r'when\s+(\w+)\s+then\s+(.*?)(?=when\s+\w+\s+then|\s*$)', exception_section, re.IGNORECASE | re.DOTALL)
        
        for match in when_matches:
            exception_name = match.group(1)
            handler_code = match.group(2).strip()
            
            # Clean up handler code
            handler_code = re.sub(r'\s+', ' ', handler_code).strip()
            if handler_code.endswith(';'):
                handler_code = handler_code[:-1]
                
            handlers.append(ExceptionHandler(
                exception_name=exception_name,
                handler_code=handler_code
            ))
            
        return handlers


class ComprehensiveOracleAnalyzer:
    """Main analyzer class that orchestrates all parsing components"""
    
    def __init__(self):
        self.section_parser = OracleTriSectionParser()
        self.declaration_parser = DeclarationParser()
        self.exception_parser = ExceptionParser()
        self.stake_analyzer = StakeFlowAnalyzer()
        
    def analyze_trigger_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Oracle trigger file and return enhanced JSON structure"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        trigger_name = Path(file_path).stem
        return self.analyze_trigger(content, trigger_name)
        
    def analyze_trigger(self, sql_content: str, trigger_name: str = None) -> Dict[str, Any]:
        """Analyze Oracle trigger content and return enhanced JSON structure"""
        
        # Step 1: Parse into three sections
        declare_section, main_sql_section, exception_section = self.section_parser.parse_sections(sql_content)
        
        # Step 2: Parse declarations
        variables, constants, exceptions = self.declaration_parser.parse_declarations(declare_section)
        
        # Step 3: Parse exception handlers
        exception_handlers = self.exception_parser.parse_exception_handlers(exception_section)
        
        # Step 4: Analyze main SQL with stake flow
        data_operations = self.stake_analyzer.analyze_with_stake_flow(main_sql_section)
        
        # Step 5: Extract trigger metadata
        metadata = self._extract_trigger_metadata(sql_content, trigger_name)
        
        # Step 6: Build final JSON structure
        result = {
            "trigger_metadata": asdict(metadata),
            "declarations": {
                "variables": [asdict(v) for v in variables],
                "constants": [asdict(c) for c in constants],
                "exceptions": [asdict(e) for e in exceptions]
            },
            "data_operations": [asdict(op) for op in data_operations],
            "exception_handlers": [asdict(eh) for eh in exception_handlers]
        }
        
        return result
        
    def _extract_trigger_metadata(self, sql_content: str, trigger_name: str = None) -> TriggerMetadata:
        """Extract trigger metadata"""
        metadata = TriggerMetadata(
            trigger_name=trigger_name or "unknown_trigger",
            has_declare_section="declare" in sql_content.lower(),
            has_begin_section="begin" in sql_content.lower(),
            has_exception_section="exception" in sql_content.lower()
        )
        
        # Detect trigger events
        events = []
        if re.search(r'if\s*\(\s*inserting\s*\)', sql_content, re.IGNORECASE):
            events.append("INSERT")
        if re.search(r'if\s*\(\s*updating\s*\)', sql_content, re.IGNORECASE):
            events.append("UPDATE")
        if re.search(r'if\s*\(\s*deleting\s*\)', sql_content, re.IGNORECASE):
            events.append("DELETE")
            
        if events:
            metadata.events = events
            
        # Try to detect timing
        if "before" in sql_content.lower():
            metadata.timing = "BEFORE"
        elif "after" in sql_content.lower():
            metadata.timing = "AFTER"
        elif "instead of" in sql_content.lower():
            metadata.timing = "INSTEAD OF"
            
        return metadata
        
    def save_analysis(self, analysis_data: Dict[str, Any], output_file: str):
        """Save analysis data to JSON file"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)


def main():
    """Main function to process Oracle trigger files"""
    analyzer = ComprehensiveOracleAnalyzer()
    
    # Define paths
    oracle_dir = Path("files/oracle")
    output_dir = Path("files/sql_json")
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Process each SQL file
    for sql_file in oracle_dir.glob("*.sql"):
        print(f"🔄 Processing {sql_file.name} with stake flow analysis...")
        
        try:
            # Analyze the trigger
            analysis = analyzer.analyze_trigger_file(str(sql_file))
            
            # Save to output file
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