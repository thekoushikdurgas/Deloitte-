"""
Enhanced JSON Comparison Analyzer for Oracle to PostgreSQL Converter

This module provides deep comparison functionality for JSON files with:
- Line-by-line diff visualization
- Missing element detection
- Suggestions for PostgreSQL improvements
"""

import json
import difflib
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass


@dataclass
class ComparisonResult:
    """Result of JSON comparison analysis."""
    structure_differences: List[str]
    content_differences: List[str]
    missing_in_postgresql: List[str]
    suggestions: List[str]
    line_by_line_diff: List[Dict[str, Any]]
    compatibility_score: float


@dataclass
class LineComparison:
    """Individual line comparison result."""
    line_number: int
    postgresql_line: Optional[str]
    uploaded_line: Optional[str]
    status: str  # 'same', 'different', 'missing_postgresql', 'missing_uploaded'
    difference_type: str  # 'structure', 'content', 'format', 'logic'
    suggestion: Optional[str]


class JSONComparisonAnalyzer:
    """Enhanced JSON comparison analyzer with deep analysis capabilities."""
    
    def __init__(self):
        pass

    def compare_json_files(self, postgresql_json: dict, uploaded_json: dict) -> ComparisonResult:
        """
        Perform comprehensive comparison of two JSON files.
        
        Args:
            postgresql_json: The PostgreSQL format JSON
            uploaded_json: The uploaded/reference JSON
            
        Returns:
            ComparisonResult with detailed analysis
        """
        # Analyze structure differences
        structure_diffs = self._analyze_structure_differences(postgresql_json, uploaded_json)
        
        # Analyze content differences
        content_diffs = self._analyze_content_differences(postgresql_json, uploaded_json)
        
        # Find missing elements in PostgreSQL
        missing_elements = self._find_missing_in_postgresql(postgresql_json, uploaded_json)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(postgresql_json, uploaded_json, missing_elements)
        
        # Create line-by-line diff
        line_diff = self._create_line_by_line_diff(postgresql_json, uploaded_json)
        
        # Calculate compatibility score
        compatibility_score = self._calculate_compatibility_score(postgresql_json, uploaded_json)
        
        return ComparisonResult(
            structure_differences=structure_diffs,
            content_differences=content_diffs,
            missing_in_postgresql=missing_elements,
            suggestions=suggestions,
            line_by_line_diff=line_diff,
            compatibility_score=compatibility_score
        )

    def _analyze_structure_differences(self, postgresql_json: dict, uploaded_json: dict) -> List[str]:
        """Analyze structural differences between JSONs."""
        differences = []
        
        # Check top-level structure
        postgresql_keys = set(postgresql_json.keys())
        uploaded_keys = set(uploaded_json.keys())
        
        if postgresql_keys != uploaded_keys:
            only_in_postgresql = postgresql_keys - uploaded_keys
            only_in_uploaded = uploaded_keys - postgresql_keys
            
            if only_in_postgresql:
                differences.append(f"Keys only in PostgreSQL: {', '.join(only_in_postgresql)}")
            if only_in_uploaded:
                differences.append(f"Keys only in uploaded: {', '.join(only_in_uploaded)}")
        
        # Check structure types for each key
        for key in postgresql_keys & uploaded_keys:
            postgresql_value = postgresql_json[key]
            uploaded_value = uploaded_json[key]
            
            postgresql_type = type(postgresql_value).__name__
            uploaded_type = type(uploaded_value).__name__
            
            if postgresql_type != uploaded_type:
                differences.append(f"Key '{key}': PostgreSQL is {postgresql_type}, uploaded is {uploaded_type}")
            
            # Check if one is array and other is object
            if isinstance(postgresql_value, dict) and isinstance(uploaded_value, list):
                differences.append(f"Key '{key}': PostgreSQL uses object format, uploaded uses array format")
            elif isinstance(postgresql_value, list) and isinstance(uploaded_value, dict):
                differences.append(f"Key '{key}': PostgreSQL uses array format, uploaded uses object format")
        
        return differences

    def _analyze_content_differences(self, postgresql_json: dict, uploaded_json: dict) -> List[str]:
        """Analyze content differences in SQL and other fields."""
        differences = []
        
        for key in postgresql_json.keys():
            if key in uploaded_json:
                postgresql_content = self._extract_sql_content(postgresql_json[key])
                uploaded_content = self._extract_sql_content(uploaded_json[key])
                
                # Check for TODO placeholders in PostgreSQL
                postgresql_todos = re.findall(r'-- TODO: Map Oracle exception "[^"]*"', postgresql_content)
                if postgresql_todos:
                    differences.append(f"Key '{key}': Contains {len(postgresql_todos)} TODO placeholders for exception mapping")
                
                # Check for variable reference differences
                postgresql_vars = re.findall(r':\w+\.\w+', postgresql_content)
                uploaded_vars = re.findall(r':\w+_\w+', uploaded_content)
                
                if postgresql_vars and uploaded_vars:
                    differences.append(f"Key '{key}': Different variable reference formats (dot vs underscore)")
                
                # Check for function differences
                if 'coa_security.get_userid' in postgresql_content and 'coa_util.get_changing_user' in uploaded_content:
                    differences.append(f"Key '{key}': Different user ID functions used")
                
                if 'CURRENT_TIMESTAMP' in postgresql_content and 'SYSDATE' in uploaded_content:
                    differences.append(f"Key '{key}': Different date functions (CURRENT_TIMESTAMP vs SYSDATE)")
        
        return differences

    def _find_missing_in_postgresql(self, postgresql_json: dict, uploaded_json: dict) -> List[str]:
        """Find elements missing in PostgreSQL JSON compared to uploaded JSON."""
        missing = []
        
        for key in uploaded_json.keys():
            if key not in postgresql_json:
                missing.append(f"Missing key: '{key}'")
                continue
            
            # Check for missing SQL components
            postgresql_content = self._extract_sql_content(postgresql_json[key])
            uploaded_content = self._extract_sql_content(uploaded_json[key])
            
            # Check for missing INSERT/UPDATE fields
            postgresql_insert_fields = self._extract_insert_fields(postgresql_content)
            uploaded_insert_fields = self._extract_insert_fields(uploaded_content)
            
            missing_fields = set(uploaded_insert_fields) - set(postgresql_insert_fields)
            if missing_fields:
                missing.append(f"Key '{key}': Missing INSERT fields: {', '.join(missing_fields)}")
            
            # Check for missing UPDATE fields
            postgresql_update_fields = self._extract_update_fields(postgresql_content)
            uploaded_update_fields = self._extract_update_fields(uploaded_content)
            
            missing_update_fields = set(uploaded_update_fields) - set(postgresql_update_fields)
            if missing_update_fields:
                missing.append(f"Key '{key}': Missing UPDATE fields: {', '.join(missing_update_fields)}")
            
            # Check for proper exception messages
            if '-- TODO:' in postgresql_content and 'RAISE EXCEPTION' in uploaded_content:
                todo_count = len(re.findall(r'-- TODO:', postgresql_content))
                missing.append(f"Key '{key}': {todo_count} incomplete exception mappings")
        
        return missing

    def _generate_suggestions(self, postgresql_json: dict, uploaded_json: dict, missing_elements: List[str] = None) -> List[str]:
        """Generate suggestions to improve PostgreSQL JSON based on uploaded JSON."""
        suggestions = []
        
        # Suggest structure alignment
        for key in uploaded_json.keys():
            if key in postgresql_json:
                postgresql_value = postgresql_json[key]
                uploaded_value = uploaded_json[key]
                
                if isinstance(postgresql_value, dict) and isinstance(uploaded_value, list):
                    suggestions.append(f"Consider changing '{key}' from object to array format to match uploaded structure")
                elif isinstance(postgresql_value, list) and isinstance(uploaded_value, dict):
                    suggestions.append(f"Consider changing '{key}' from array to object format to match uploaded structure")
        
        # Suggest exception mapping completion
        for key in postgresql_json.keys():
            if key in uploaded_json:
                postgresql_content = self._extract_sql_content(postgresql_json[key])
                uploaded_content = self._extract_sql_content(uploaded_json[key])
                
                # Find TODO placeholders and suggest replacements
                todos = re.findall(r'-- TODO: Map Oracle exception "([^"]*)"', postgresql_content)
                for exception_name in todos:
                    if exception_name in self.known_oracle_exceptions:
                        suggestion = f"Replace TODO for '{exception_name}' with: '{self.known_oracle_exceptions[exception_name]}'"
                        suggestions.append(suggestion)
                
                # Suggest missing fields
                uploaded_fields = self._extract_insert_fields(uploaded_content)
                postgresql_fields = self._extract_insert_fields(postgresql_content)
                
                missing_fields = set(uploaded_fields) - set(postgresql_fields)
                if missing_fields:
                    suggestions.append(f"Add missing INSERT fields to '{key}': {', '.join(missing_fields)}")
        
        # Suggest PostgreSQL-specific improvements
        suggestions.append("Consider using PostgreSQL-specific error codes instead of generic RAISE EXCEPTION")
        suggestions.append("Ensure all variable references use consistent format (:new_ vs :new.)")
        suggestions.append("Verify that all Oracle functions have proper PostgreSQL equivalents")
        
        # Handle missing_elements parameter if provided
        if missing_elements:
            for element in missing_elements:
                suggestions.append(f"Address missing element: {element}")
        
        return suggestions

    def _create_line_by_line_diff(self, postgresql_json: dict, uploaded_json: dict) -> List[Dict[str, Any]]:
        """Create detailed line-by-line comparison with semicolon-based SQL parsing."""
        line_comparisons = []
        
        # Process each key in the JSON files
        all_keys = set(postgresql_json.keys()) | set(uploaded_json.keys())
        
        for key in sorted(all_keys):
            postgresql_content = self._extract_sql_content(postgresql_json.get(key, {}))
            uploaded_content = self._extract_sql_content(uploaded_json.get(key, {}))
            
            if not postgresql_content and not uploaded_content:
                continue
            
            # Parse SQL statements by semicolons
            postgresql_statements = self._parse_sql_by_semicolons(postgresql_content)
            uploaded_statements = self._parse_sql_by_semicolons(uploaded_content)
            
            # Add header for this key
            line_comparisons.append({
                'line_number': 0,
                'content': f"=== {key.upper()} ===",
                'status': 'header',
                'difference_type': 'none',
                'suggestion': None,
                'key': key
            })
            
            # Compare statements
            statement_comparisons = self._compare_sql_statements(
                postgresql_statements, uploaded_statements, key
            )
            line_comparisons.extend(statement_comparisons)
        
        return line_comparisons

    def _parse_sql_by_semicolons(self, sql_content: str) -> List[Dict[str, Any]]:
        """Parse SQL content into individual statements separated by semicolons."""
        if not sql_content:
            return []
        
        # Split by semicolons but preserve the semicolon
        statements = []
        current_statement = ""
        in_string = False
        string_char = None
        i = 0
        
        while i < len(sql_content):
            char = sql_content[i]
            
            # Handle string literals
            if char in ["'", '"'] and (i == 0 or sql_content[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
            
            current_statement += char
            
            # Check for semicolon (end of statement)
            if char == ';' and not in_string:
                statement_text = current_statement.strip()
                if statement_text:
                    statements.append({
                        'text': statement_text,
                        'type': self._identify_sql_statement_type(statement_text),
                        'lines': statement_text.count('\n') + 1
                    })
                current_statement = ""
            
            i += 1
        
        # Handle any remaining content without semicolon
        if current_statement.strip():
            statement_text = current_statement.strip()
            statements.append({
                'text': statement_text,
                'type': self._identify_sql_statement_type(statement_text),
                'lines': statement_text.count('\n') + 1
            })
        
        return statements

    def _identify_sql_statement_type(self, statement: str) -> str:
        """Identify the type of SQL statement."""
        statement_upper = statement.upper().strip()
        
        if statement_upper.startswith('INSERT'):
            return 'INSERT'
        elif statement_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif statement_upper.startswith('DELETE'):
            return 'DELETE'
        elif statement_upper.startswith('SELECT'):
            return 'SELECT'
        elif statement_upper.startswith('CREATE'):
            return 'CREATE'
        elif statement_upper.startswith('ALTER'):
            return 'ALTER'
        elif statement_upper.startswith('DROP'):
            return 'DROP'
        elif 'RAISE' in statement_upper or 'EXCEPTION' in statement_upper:
            return 'EXCEPTION'
        elif 'IF' in statement_upper and 'THEN' in statement_upper:
            return 'CONDITIONAL'
        elif 'BEGIN' in statement_upper or 'END' in statement_upper:
            return 'BLOCK'
        else:
            return 'OTHER'

    def _compare_sql_statements(self, postgresql_statements: List[Dict], uploaded_statements: List[Dict], key: str) -> List[Dict[str, Any]]:
        """Compare SQL statements between PostgreSQL and uploaded versions."""
        comparisons = []
        
        # Create a mapping of statement types for easier comparison
        postgresql_by_type = {}
        uploaded_by_type = {}
        
        for stmt in postgresql_statements:
            stmt_type = stmt['type']
            if stmt_type not in postgresql_by_type:
                postgresql_by_type[stmt_type] = []
            postgresql_by_type[stmt_type].append(stmt)
        
        for stmt in uploaded_statements:
            stmt_type = stmt['type']
            if stmt_type not in uploaded_by_type:
                uploaded_by_type[stmt_type] = []
            uploaded_by_type[stmt_type].append(stmt)
        
        # Compare each statement type
        all_types = set(postgresql_by_type.keys()) | set(uploaded_by_type.keys())
        
        for stmt_type in sorted(all_types):
            postgresql_stmts = postgresql_by_type.get(stmt_type, [])
            uploaded_stmts = uploaded_by_type.get(stmt_type, [])
            
            # Add statement type header
            comparisons.append({
                'line_number': 0,
                'content': f"  📋 {stmt_type} Statements",
                'status': 'subheader',
                'difference_type': 'none',
                'suggestion': None,
                'key': key,
                'statement_type': stmt_type
            })
            
            # Compare statements of the same type
            max_count = max(len(postgresql_stmts), len(uploaded_stmts))
            
            for i in range(max_count):
                postgresql_stmt = postgresql_stmts[i] if i < len(postgresql_stmts) else None
                uploaded_stmt = uploaded_stmts[i] if i < len(uploaded_stmts) else None
                
                if postgresql_stmt and uploaded_stmt:
                    # Both exist - compare content
                    if postgresql_stmt['text'] == uploaded_stmt['text']:
                        status = 'same'
                        difference_type = 'none'
                        suggestion = None
                        content = f"✅ {stmt_type} #{i+1}: Identical"
                    else:
                        status = 'different'
                        difference_type = 'content'
                        suggestion = self._generate_statement_suggestion(postgresql_stmt, uploaded_stmt, stmt_type)
                        content = f"🔄 {stmt_type} #{i+1}: Different content"
                        
                        # Add detailed diff for different statements
                        detailed_diff = self._create_statement_diff(postgresql_stmt['text'], uploaded_stmt['text'])
                        comparisons.append({
                            'line_number': i + 1,
                            'content': detailed_diff,
                            'status': 'detailed_diff',
                            'difference_type': 'content',
                            'suggestion': suggestion,
                            'key': key,
                            'statement_type': stmt_type
                        })
                
                elif postgresql_stmt and not uploaded_stmt:
                    # Only in PostgreSQL
                    status = 'missing_uploaded'
                    difference_type = 'structure'
                    suggestion = f"Consider if this {stmt_type} statement should be in the uploaded version"
                    content = f"➕ {stmt_type} #{i+1}: Only in PostgreSQL"
                    
                elif not postgresql_stmt and uploaded_stmt:
                    # Only in uploaded
                    status = 'missing_postgresql'
                    difference_type = 'structure'
                    suggestion = f"Add this {stmt_type} statement to PostgreSQL version"
                    content = f"➖ {stmt_type} #{i+1}: Missing in PostgreSQL"
                
                comparisons.append({
                    'line_number': i + 1,
                    'content': content,
                    'status': status,
                    'difference_type': difference_type,
                    'suggestion': suggestion,
                    'key': key,
                    'statement_type': stmt_type
                })
        
        return comparisons

    def _create_statement_diff(self, postgresql_text: str, uploaded_text: str) -> str:
        """Create a detailed diff between two SQL statements."""
        postgresql_lines = postgresql_text.split('\n')
        uploaded_lines = uploaded_text.split('\n')
        
        differ = difflib.unified_diff(
            postgresql_lines, uploaded_lines,
            fromfile='PostgreSQL', tofile='Uploaded',
            lineterm=''
        )
        
        diff_lines = []
        for line in differ:
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                continue
            diff_lines.append(line)
        
        return '\n'.join(diff_lines)

    def _generate_statement_suggestion(self, postgresql_stmt: Dict, uploaded_stmt: Dict, stmt_type: str) -> str:
        """Generate suggestions for statement differences."""
        suggestions = []
        
        # Check for common Oracle to PostgreSQL differences
        postgresql_text = postgresql_stmt['text']
        uploaded_text = uploaded_stmt['text']
        
        if 'SYSDATE' in uploaded_text and 'CURRENT_TIMESTAMP' in postgresql_text:
            suggestions.append("Date function conversion: SYSDATE → CURRENT_TIMESTAMP")
        
        if ':new.' in uploaded_text and ':new_' in postgresql_text:
            suggestions.append("Variable reference format: :new. → :new_")
        
        if 'coa_security.get_userid' in uploaded_text and 'coa_util.get_changing_user' in postgresql_text:
            suggestions.append("Function mapping: coa_security.get_userid → coa_util.get_changing_user")
        
        if 'TODO' in postgresql_text:
            suggestions.append("Complete TODO mapping with proper exception message")
        
        return '; '.join(suggestions) if suggestions else f"Review {stmt_type} statement for Oracle to PostgreSQL compatibility"

    def _calculate_compatibility_score(self, postgresql_json: dict, uploaded_json: dict) -> float:
        """Calculate compatibility score between 0 and 100."""
        total_score = 100.0
        
        # Structure penalty
        postgresql_keys = set(postgresql_json.keys())
        uploaded_keys = set(uploaded_json.keys())
        
        if postgresql_keys != uploaded_keys:
            key_diff = len(postgresql_keys.symmetric_difference(uploaded_keys))
            total_score -= min(30, key_diff * 10)
        
        # Content penalty
        for key in postgresql_keys & uploaded_keys:
            postgresql_content = self._extract_sql_content(postgresql_json[key])
            todo_count = len(re.findall(r'-- TODO:', postgresql_content))
            total_score -= min(25, todo_count * 5)
            
            # Missing fields penalty
            postgresql_fields = self._extract_insert_fields(postgresql_content)
            uploaded_content = self._extract_sql_content(uploaded_json.get(key, {})) if key in uploaded_json else ""
            uploaded_fields = self._extract_insert_fields(uploaded_content)
            
            missing_field_count = len(set(uploaded_fields) - set(postgresql_fields))
            total_score -= min(20, missing_field_count * 2)
        
        return max(0, total_score)

    def _extract_sql_content(self, json_value: Any) -> str:
        """Extract SQL content from JSON value."""
        if isinstance(json_value, dict):
            return json_value.get('sql', '')
        elif isinstance(json_value, list) and len(json_value) > 0:
            return json_value[0].get('sql', '') if isinstance(json_value[0], dict) else ''
        return ''

    def _extract_insert_fields(self, sql_content: str) -> List[str]:
        """Extract field names from INSERT statements."""
        insert_pattern = r'INSERT\s+INTO\s+\w+\.\w+\s*\(([^)]+)\)'
        matches = re.findall(insert_pattern, sql_content, re.IGNORECASE)
        
        fields = []
        for match in matches:
            field_list = [field.strip() for field in match.split(',')]
            fields.extend(field_list)
        
        return fields

    def _extract_update_fields(self, sql_content: str) -> List[str]:
        """Extract field names from UPDATE statements."""
        update_pattern = r'UPDATE\s+\w+\.\w+\s+SET\s+([^W]+?)WHERE'
        matches = re.findall(update_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        
        fields = []
        for match in matches:
            assignments = re.findall(r'(\w+)\s*=', match)
            fields.extend(assignments)
        
        return fields

    def format_comparison_for_streamlit(self, result: ComparisonResult) -> Dict[str, Any]:
        """Format comparison result for Streamlit display."""
        return {
            'structure_differences': result.structure_differences,
            'content_differences': result.content_differences,
            'missing_in_postgresql': result.missing_in_postgresql,
            'suggestions': result.suggestions,
            'line_by_line_diff': result.line_by_line_diff,
            'compatibility_score': result.compatibility_score,
            'status_colors': {
                'same': '🟢',
                'different': '🟡', 
                'missing_postgresql': '🔴',
                'missing_uploaded': '🟠',
                'header': '🔵',
                'subheader': '🟣',
                'detailed_diff': '🟤'
            },
            'difference_type_icons': {
                'structure': '🏗️',
                'content': '📝',
                'format': '🎨',
                'logic': '🧠',
                'none': '✅'
            },
            'status_styles': {
                'same': {'color': '#28a745', 'background': '#d4edda', 'border': '1px solid #c3e6cb'},
                'different': {'color': '#856404', 'background': '#fff3cd', 'border': '1px solid #ffeaa7'},
                'missing_postgresql': {'color': '#721c24', 'background': '#f8d7da', 'border': '1px solid #f5c6cb'},
                'missing_uploaded': {'color': '#856404', 'background': '#fff3cd', 'border': '1px solid #ffeaa7'},
                'header': {'color': '#004085', 'background': '#cce7ff', 'border': '2px solid #80bdff', 'font-weight': 'bold'},
                'subheader': {'color': '#383d41', 'background': '#e2e3e5', 'border': '1px solid #d6d8db'},
                'detailed_diff': {'color': '#495057', 'background': '#f8f9fa', 'border': '1px solid #dee2e6', 'font-family': 'monospace'}
            }
        }
