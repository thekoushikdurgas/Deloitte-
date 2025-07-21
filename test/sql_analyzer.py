#!/usr/bin/env python3
"""
SQL Analyzer for Oracle to PostgreSQL Trigger Converter

This module analyzes Oracle SQL triggers and creates a structured JSON representation
to better understand the code structure before converting to PostgreSQL format.
It extracts trigger metadata, declarations, data operations, and exception handlers.
"""

import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class SQLAnalyzer:
    """
    Analyzes Oracle SQL triggers and creates structured JSON representation
    
    This class provides detailed analysis of Oracle trigger code, extracting:
    - Trigger metadata (name, timing, events, table)
    - Variable and constant declarations
    - Exception definitions
    - Data operation statements (SELECT, INSERT, UPDATE, DELETE)
    - Exception handlers
    """
    
    def __init__(self):
        """Initialize the SQL analyzer"""
        self.sql_patterns = self._build_sql_patterns()
    
    def _build_sql_patterns(self) -> Dict[str, str]:
        """
        Build regex patterns for extracting SQL elements
        
        Returns:
            Dictionary of pattern names and their regex patterns
        """
        return {
            # Variable declarations
            'variable_declaration': r'(\w+)\s+((?:varchar2|number|date|pls_integer|simple_integer|binary_integer)\s*(?:\([^)]+\))?)\s*(?::=\s*([^;]+))?',
            
            # Exception declarations
            'exception_declaration': r'(\w+)\s+exception',
            
            # Constant declarations
            'constant_declaration': r'(\w+)\s+constant\s+([^:]+):=\s*([^;]+)',
            
            # SQL statements
            'select_statement': r'select\s+.*?(?=;|\s+(?:into|from)\s)',
            'insert_statement': r'insert\s+into\s+[\w.]+\s*\([^)]+\)\s*values\s*\([^)]+\)',
            'update_statement': r'update\s+[\w.]+\s+set\s+[^;]+',
            'delete_statement': r'delete\s+from\s+[\w.]+\s*(?:where\s+[^;]+)?',
            
            # Function calls
            'function_call': r'(\w+(?:\.\w+)*)\s*\([^)]*\)',
            
            # Exception handlers
            'exception_handler': r'when\s+(\w+)\s+then\s+(.*?)(?=when|\s*end\s*;)',
            
            # Raise statements
            'raise_statement': r'raise(?:\s+(\w+))?(?:\s*;)?',
            'raise_application_error': r'raise_application_error\s*\(\s*(-?\d+)\s*,\s*[\'"]([^\'"]*)[\'"][^)]*\)'
        }
    
    def analyze_trigger(self, sql_content: str, trigger_name: str = None) -> Dict[str, Any]:
        """
        Analyze Oracle trigger and create structured JSON representation
        
        Args:
            sql_content: The Oracle trigger SQL content
            trigger_name: Optional trigger name (extracted from filename if not provided)
            
        Returns:
            Structured dictionary representation of the trigger
        """
        # Clean and normalize the SQL content
        cleaned_sql = self._clean_sql_content(sql_content)
        
        # Extract different sections
        structure = {
            "trigger_metadata": self._extract_trigger_metadata(cleaned_sql, trigger_name),
            "declarations": self._extract_declarations(cleaned_sql),
            "data_operations": self._extract_data_operations(cleaned_sql),
            "exception_handlers": self._extract_exception_handlers(cleaned_sql),
            "control_flow": self._extract_control_flow(cleaned_sql),
            "statistics": self._calculate_statistics(cleaned_sql)
        }
        
        return structure
    
    def _clean_sql_content(self, content: str) -> str:
        """
        Clean and normalize SQL content for analysis
        
        Args:
            content: Raw SQL content
            
        Returns:
            Cleaned SQL content
        """
        # Remove comments
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def _extract_trigger_metadata(self, sql_content: str, trigger_name: str = None) -> Dict[str, Any]:
        """
        Extract trigger metadata (name, timing, events, table)
        
        Args:
            sql_content: Cleaned SQL content
            trigger_name: Optional trigger name
            
        Returns:
            Dictionary containing trigger metadata
        """
        metadata = {
            "trigger_name": trigger_name or "unknown_trigger",
            "timing": "UNKNOWN",
            "events": [],
            "table_name": "unknown_table",
            "has_declare_section": "declare" in sql_content.lower(),
            "has_begin_section": "begin" in sql_content.lower(),
            "has_exception_section": "exception" in sql_content.lower()
        }
        
        # Try to detect trigger events from conditional statements
        if re.search(r'if\s+inserting', sql_content, re.IGNORECASE):
            metadata["events"].append("INSERT")
        if re.search(r'if\s+updating', sql_content, re.IGNORECASE):
            metadata["events"].append("UPDATE")
        if re.search(r'if\s+deleting', sql_content, re.IGNORECASE):
            metadata["events"].append("DELETE")
        
        # If no specific events found, assume all
        if not metadata["events"]:
            metadata["events"] = ["INSERT", "UPDATE", "DELETE"]
        
        return metadata
    
    def _extract_declarations(self, sql_content: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract variable, constant, and exception declarations
        
        Args:
            sql_content: Cleaned SQL content
            
        Returns:
            Dictionary containing declarations
        """
        declarations = {
            "variables": [],
            "constants": [],
            "exceptions": []
        }
        
        # Find DECLARE section
        declare_match = re.search(r'declare\s+(.*?)\s+begin', sql_content, re.IGNORECASE | re.DOTALL)
        if not declare_match:
            return declarations
        
        declare_section = declare_match.group(1)
        
        # Extract variables
        variable_matches = re.finditer(self.sql_patterns['variable_declaration'], declare_section, re.IGNORECASE)
        for match in variable_matches:
            variable = {
                "name": match.group(1),
                "data_type": match.group(2).strip(),
                "default_value": match.group(3).strip() if match.group(3) else None
            }
            declarations["variables"].append(variable)
        
        # Extract constants
        constant_matches = re.finditer(self.sql_patterns['constant_declaration'], declare_section, re.IGNORECASE)
        for match in constant_matches:
            constant = {
                "name": match.group(1),
                "data_type": match.group(2).strip(),
                "value": match.group(3).strip()
            }
            declarations["constants"].append(constant)
        
        # Extract exceptions
        exception_matches = re.finditer(self.sql_patterns['exception_declaration'], declare_section, re.IGNORECASE)
        for match in exception_matches:
            exception = {
                "name": match.group(1),
                "type": "user_defined"
            }
            declarations["exceptions"].append(exception)
        
        return declarations
    
    def _extract_data_operations(self, sql_content: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract data operation statements (SELECT, INSERT, UPDATE, DELETE)
        
        Args:
            sql_content: Cleaned SQL content
            
        Returns:
            Dictionary containing data operations
        """
        operations = {
            "select_statements": [],
            "insert_statements": [],
            "update_statements": [],
            "delete_statements": [],
            "function_calls": []
        }
        
        # Extract SELECT statements
        select_matches = re.finditer(r'select\s+.*?(?=;|\s+from\s+|\s+into\s+)', sql_content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(select_matches):
            statement = {
                "id": f"select_{i+1}",
                "sql": match.group(0).strip(),
                "line_approx": sql_content[:match.start()].count('\n') + 1
            }
            operations["select_statements"].append(statement)
        
        # Extract INSERT statements
        insert_matches = re.finditer(r'insert\s+into\s+[^;]+', sql_content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(insert_matches):
            statement = {
                "id": f"insert_{i+1}",
                "sql": match.group(0).strip(),
                "line_approx": sql_content[:match.start()].count('\n') + 1
            }
            operations["insert_statements"].append(statement)
        
        # Extract UPDATE statements
        update_matches = re.finditer(r'update\s+[^;]+', sql_content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(update_matches):
            statement = {
                "id": f"update_{i+1}",
                "sql": match.group(0).strip(),
                "line_approx": sql_content[:match.start()].count('\n') + 1
            }
            operations["update_statements"].append(statement)
        
        # Extract DELETE statements
        delete_matches = re.finditer(r'delete\s+from\s+[^;]+', sql_content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(delete_matches):
            statement = {
                "id": f"delete_{i+1}",
                "sql": match.group(0).strip(),
                "line_approx": sql_content[:match.start()].count('\n') + 1
            }
            operations["delete_statements"].append(statement)
        
        # Extract function calls
        function_matches = re.finditer(self.sql_patterns['function_call'], sql_content, re.IGNORECASE)
        for i, match in enumerate(function_matches):
            func_call = {
                "id": f"function_{i+1}",
                "function_name": match.group(1),
                "full_call": match.group(0).strip(),
                "line_approx": sql_content[:match.start()].count('\n') + 1
            }
            operations["function_calls"].append(func_call)
        
        return operations
    
    def _extract_exception_handlers(self, sql_content: str) -> List[Dict[str, Any]]:
        """
        Extract exception handlers
        
        Args:
            sql_content: Cleaned SQL content
            
        Returns:
            List of exception handlers
        """
        handlers = []
        
        # Find EXCEPTION section
        exception_match = re.search(r'exception\s+(.*?)$', sql_content, re.IGNORECASE | re.DOTALL)
        if not exception_match:
            return handlers
        
        exception_section = exception_match.group(1)
        
        # Extract WHEN handlers
        handler_matches = re.finditer(r'when\s+(\w+)\s+then\s+(.*?)(?=when|\s*end\s*;|$)', exception_section, re.IGNORECASE | re.DOTALL)
        for match in handler_matches:
            handler = {
                "exception_name": match.group(1),
                "handler_code": match.group(2).strip()
            }
            handlers.append(handler)
        
        # Extract raise_application_error calls
        raise_matches = re.finditer(self.sql_patterns['raise_application_error'], exception_section, re.IGNORECASE)
        for match in raise_matches:
            error_info = {
                "type": "raise_application_error",
                "error_code": match.group(1),
                "error_message": match.group(2)
            }
            # Add to the last handler if exists
            if handlers:
                if "error_details" not in handlers[-1]:
                    handlers[-1]["error_details"] = []
                handlers[-1]["error_details"].append(error_info)
        
        return handlers
    
    def _extract_control_flow(self, sql_content: str) -> Dict[str, Any]:
        """
        Extract control flow elements (IF, CASE, LOOP statements)
        
        Args:
            sql_content: Cleaned SQL content
            
        Returns:
            Dictionary containing control flow analysis
        """
        control_flow = {
            "if_statements": [],
            "case_statements": [],
            "loop_statements": [],
            "nested_blocks": 0
        }
        
        # Count IF statements
        if_matches = re.finditer(r'if\s+[^;]+?then', sql_content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(if_matches):
            if_stmt = {
                "id": f"if_{i+1}",
                "condition": match.group(0).strip(),
                "line_approx": sql_content[:match.start()].count('\n') + 1
            }
            control_flow["if_statements"].append(if_stmt)
        
        # Count CASE statements
        case_matches = re.finditer(r'case\s+.*?end\s+case', sql_content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(case_matches):
            case_stmt = {
                "id": f"case_{i+1}",
                "statement": match.group(0).strip(),
                "line_approx": sql_content[:match.start()].count('\n') + 1
            }
            control_flow["case_statements"].append(case_stmt)
        
        # Count FOR loops
        loop_matches = re.finditer(r'for\s+\w+\s+in\s+.*?loop', sql_content, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(loop_matches):
            loop_stmt = {
                "id": f"loop_{i+1}",
                "type": "for_loop",
                "statement": match.group(0).strip(),
                "line_approx": sql_content[:match.start()].count('\n') + 1
            }
            control_flow["loop_statements"].append(loop_stmt)
        
        # Estimate nesting level by counting BEGIN/END pairs
        begin_count = len(re.findall(r'\bbegin\b', sql_content, re.IGNORECASE))
        end_count = len(re.findall(r'\bend\b', sql_content, re.IGNORECASE))
        control_flow["nested_blocks"] = min(begin_count, end_count)
        
        return control_flow
    
    def _calculate_statistics(self, sql_content: str) -> Dict[str, Any]:
        """
        Calculate various statistics about the SQL code
        
        Args:
            sql_content: Cleaned SQL content
            
        Returns:
            Dictionary containing code statistics
        """
        lines = sql_content.split('\n')
        
        return {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "total_characters": len(sql_content),
            "total_words": len(sql_content.split()),
            "complexity_score": self._calculate_complexity_score(sql_content)
        }
    
    def _calculate_complexity_score(self, sql_content: str) -> int:
        """
        Calculate a simple complexity score based on various factors
        
        Args:
            sql_content: Cleaned SQL content
            
        Returns:
            Complexity score (higher = more complex)
        """
        score = 0
        
        # Count various elements that add complexity
        score += len(re.findall(r'\bif\b', sql_content, re.IGNORECASE)) * 2
        score += len(re.findall(r'\bcase\b', sql_content, re.IGNORECASE)) * 3
        score += len(re.findall(r'\bloop\b', sql_content, re.IGNORECASE)) * 3
        score += len(re.findall(r'\bselect\b', sql_content, re.IGNORECASE)) * 1
        score += len(re.findall(r'\binsert\b', sql_content, re.IGNORECASE)) * 2
        score += len(re.findall(r'\bupdate\b', sql_content, re.IGNORECASE)) * 2
        score += len(re.findall(r'\bdelete\b', sql_content, re.IGNORECASE)) * 2
        score += len(re.findall(r'\bexception\b', sql_content, re.IGNORECASE)) * 1
        
        return score
    
    def save_analysis(self, analysis: Dict[str, Any], output_file: str) -> None:
        """
        Save the analysis to a JSON file
        
        Args:
            analysis: The analysis dictionary
            output_file: Path to output JSON file
        """
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with pretty formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=4, ensure_ascii=False)
    
    def analyze_file(self, input_file: str, output_file: str = None) -> Dict[str, Any]:
        """
        Analyze a SQL file and optionally save the result
        
        Args:
            input_file: Path to input SQL file
            output_file: Optional path to output JSON file
            
        Returns:
            Analysis dictionary
        """
        # Read the SQL file
        with open(input_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Extract trigger name from filename
        trigger_name = Path(input_file).stem
        
        # Perform analysis
        analysis = self.analyze_trigger(sql_content, trigger_name)
        
        # Save if output file specified
        if output_file:
            self.save_analysis(analysis, output_file)
        
        return analysis 