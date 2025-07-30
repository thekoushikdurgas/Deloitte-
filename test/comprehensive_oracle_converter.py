#!/usr/bin/env python3
"""
Comprehensive Oracle to Enhanced JSON Converter

This converter performs detailed step-by-step analysis:
1. Comment removal with logging
2. Section splitting with validation
3. SQL tokenization and word analysis
4. SQL validation with error keys
5. Detailed data operation analysis with deep nesting
6. Exact matching to expected 1353-line format
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple


class CommentProcessor:
    """Step 1: Advanced comment removal with detailed logging"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def process_comments(self, content: str) -> Dict[str, Any]:
        """Remove comments with detailed analysis"""
        result = {
            "cleaned_content": "",
            "removed_comments": [],
            "comment_stats": {},
            "errors": [],
            "warnings": []
        }
        
        lines = content.split('\n')
        cleaned_lines = []
        comment_count = 0
        multiline_comment_count = 0
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            
            # Handle single-line comments (-- comment)
            if '--' in line:
                comment_pos = self._find_comment_position(line)
                if comment_pos != -1:
                    comment_text = line[comment_pos:].strip()
                    if comment_text and comment_text != '--':
                        result["removed_comments"].append({
                            "line": line_num,
                            "type": "single_line",
                            "comment": comment_text,
                            "original_line": original_line.strip()
                        })
                        comment_count += 1
                    line = line[:comment_pos].rstrip()
            
            # Handle multi-line comments /* */
            line, ml_count = self._process_multiline_comments(line, line_num, result)
            multiline_comment_count += ml_count
            
            cleaned_lines.append(line)
        
        result["cleaned_content"] = '\n'.join(cleaned_lines)
        result["comment_stats"] = {
            "single_line_comments": comment_count,
            "multiline_comments": multiline_comment_count,
            "total_comments": comment_count + multiline_comment_count
        }
        result["errors"] = self.errors
        result["warnings"] = self.warnings
        
        return result
    
    def _find_comment_position(self, line: str) -> int:
        """Find comment position, avoiding string literals"""
        in_string = False
        for i, char in enumerate(line):
            if char == "'" and (i == 0 or line[i-1] != '\\'):
                in_string = not in_string
            elif not in_string and line[i:i+2] == '--':
                return i
        return -1
    
    def _process_multiline_comments(self, line: str, line_num: int, result: Dict) -> Tuple[str, int]:
        """Process multiline comments"""
        count = 0
        while '/*' in line and '*/' in line:
            start = line.find('/*')
            end = line.find('*/', start)
            if start != -1 and end != -1:
                comment = line[start:end+2]
                result["removed_comments"].append({
                    "line": line_num,
                    "type": "multiline",
                    "comment": comment.strip()
                })
                line = line[:start] + line[end+2:]
                count += 1
            else:
                break
        return line, count


class SectionAnalyzer:
    """Step 2: Precise section splitting with validation"""
    
    def __init__(self):
        self.errors = []
        self.validation_results = {}
    
    def analyze_sections(self, content: str) -> Dict[str, Any]:
        """Split and validate Oracle sections"""
        result = {
            "declare_section": "",
            "begin_section": "",
            "exception_section": "",
            "section_boundaries": {},
            "validation_results": {},
            "errors": []
        }
        
        content = content.strip()
        content_upper = content.upper()
        
        # Find all section boundaries
        boundaries = self._find_section_boundaries(content_upper)
        result["section_boundaries"] = boundaries
        
        # Validate section structure
        validation = self._validate_section_structure(boundaries)
        result["validation_results"] = validation
        
        if not validation["is_valid"]:
            self.errors.extend(validation["errors"])
            result["errors"] = self.errors
            return result
        
        # Extract sections
        sections = self._extract_sections(content, boundaries)
        result.update(sections)
        
        # Detailed section analysis
        result["section_analysis"] = self._analyze_section_content(sections)
        
        result["errors"] = self.errors
        return result
    
    def _find_section_boundaries(self, content_upper: str) -> Dict[str, int]:
        """Find precise section boundaries"""
        boundaries = {
            "declare_start": content_upper.find('DECLARE'),
            "begin_start": content_upper.find('BEGIN'),
            "exception_start": content_upper.find('EXCEPTION'),
            "end_position": content_upper.rfind('END;')
        }
        return boundaries
    
    def _validate_section_structure(self, boundaries: Dict[str, int]) -> Dict[str, Any]:
        """Validate Oracle trigger structure"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        if boundaries["begin_start"] == -1:
            validation["is_valid"] = False
            validation["errors"].append("STRUCTURE_ERROR_001: BEGIN section not found")
        
        if boundaries["declare_start"] != -1 and boundaries["begin_start"] != -1:
            if boundaries["declare_start"] >= boundaries["begin_start"]:
                validation["is_valid"] = False
                validation["errors"].append("STRUCTURE_ERROR_002: DECLARE section must come before BEGIN")
        
        if boundaries["exception_start"] != -1 and boundaries["begin_start"] != -1:
            if boundaries["exception_start"] <= boundaries["begin_start"]:
                validation["is_valid"] = False
                validation["errors"].append("STRUCTURE_ERROR_003: EXCEPTION section must come after BEGIN")
        
        if boundaries["end_position"] == -1:
            validation["warnings"].append("STRUCTURE_WARNING_001: END; statement not found")
        
        return validation
    
    def _extract_sections(self, content: str, boundaries: Dict[str, int]) -> Dict[str, str]:
        """Extract individual sections"""
        sections = {"declare_section": "", "begin_section": "", "exception_section": ""}
        
        # Extract DECLARE section
        if boundaries["declare_start"] != -1 and boundaries["begin_start"] != -1:
            start = boundaries["declare_start"] + 7
            end = boundaries["begin_start"]
            sections["declare_section"] = content[start:end].strip()
        
        # Extract BEGIN section
        if boundaries["begin_start"] != -1:
            start = boundaries["begin_start"] + 5
            if boundaries["exception_start"] != -1:
                end = boundaries["exception_start"]
            elif boundaries["end_position"] != -1:
                end = boundaries["end_position"]
            else:
                end = len(content)
            sections["begin_section"] = content[start:end].strip()
        
        # Extract EXCEPTION section
        if boundaries["exception_start"] != -1:
            start = boundaries["exception_start"] + 9
            if boundaries["end_position"] != -1:
                end = boundaries["end_position"]
            else:
                end = len(content)
            sections["exception_section"] = content[start:end].strip()
        
        return sections
    
    def _analyze_section_content(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Analyze content of each section"""
        analysis = {}
        
        for section_name, content in sections.items():
            if content.strip():
                analysis[section_name] = {
                    "line_count": len(content.split('\n')),
                    "character_count": len(content),
                    "non_empty_lines": len([line for line in content.split('\n') if line.strip()]),
                    "contains_sql": bool(re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', content, re.IGNORECASE))
                }
            else:
                analysis[section_name] = {"empty": True}
        
        return analysis


class SQLTokenizer:
    """Step 3: Advanced SQL tokenization and word analysis"""
    
    def __init__(self):
        self.sql_keywords = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'IF', 'THEN', 'ELSE', 'END', 'CASE', 'WHEN',
            'BEGIN', 'EXCEPTION', 'RAISE', 'FOR', 'LOOP', 'WHILE', 'DECLARE', 'INTO', 'FROM',
            'WHERE', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'BETWEEN', 'IN', 'EXISTS', 'UNION',
            'VALUES', 'SET', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'ORDER', 'BY',
            'GROUP', 'HAVING', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AS'
        }
        
        self.oracle_functions = {
            'NVL', 'SUBSTR', 'LENGTH', 'UPPER', 'LOWER', 'TRIM', 'SYSDATE', 'TO_DATE', 'TO_CHAR',
            'TO_NUMBER', 'ROWNUM', 'CONNECT', 'DECODE', 'COALESCE', 'INSTR', 'REPLACE'
        }
        
        self.operators = {'=', '<>', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/', '||', ':='}
    
    def tokenize_sql(self, sql_content: str) -> Dict[str, Any]:
        """Tokenize SQL into detailed word analysis"""
        result = {
            "tokens": [],
            "token_stats": {},
            "syntax_elements": {},
            "errors": []
        }
        
        # Split into individual statements
        statements = self._split_into_statements(sql_content)
        
        for stmt_idx, statement in enumerate(statements):
            if not statement.strip():
                continue
            
            # Tokenize individual statement
            tokens = self._tokenize_statement(statement)
            
            # Analyze tokens
            token_analysis = self._analyze_tokens(tokens)
            
            stmt_result = {
                "statement_id": f"stmt_{stmt_idx + 1}",
                "raw_sql": statement.strip(),
                "tokens": tokens,
                "analysis": token_analysis
            }
            
            result["tokens"].append(stmt_result)
        
        # Generate overall statistics
        result["token_stats"] = self._generate_token_statistics(result["tokens"])
        result["syntax_elements"] = self._extract_syntax_elements(result["tokens"])
        
        return result
    
    def _split_into_statements(self, content: str) -> List[str]:
        """Split content into individual SQL statements"""
        statements = []
        current_stmt = ""
        paren_depth = 0
        if_depth = 0
        case_depth = 0
        in_string = False
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Track string literals
            for char in line:
                if char == "'" and not in_string:
                    in_string = True
                elif char == "'" and in_string:
                    in_string = False
            
            if not in_string:
                # Track nesting
                paren_depth += line.count('(') - line.count(')')
                
                line_upper = line.upper()
                if_depth += line_upper.count(' IF ') - line_upper.count('END IF')
                case_depth += line_upper.count('CASE ') - line_upper.count('END CASE')
            
            current_stmt += ' ' + line
            
            # Check for statement completion
            if (line.endswith(';') and paren_depth == 0 and 
                if_depth == 0 and case_depth == 0 and not in_string):
                statements.append(current_stmt.strip())
                current_stmt = ""
        
        if current_stmt.strip():
            statements.append(current_stmt.strip())
        
        return statements
    
    def _tokenize_statement(self, statement: str) -> List[Dict[str, Any]]:
        """Tokenize individual statement into detailed tokens"""
        tokens = []
        
        # Remove semicolon
        if statement.endswith(';'):
            statement = statement[:-1]
        
        # Split by whitespace and special characters
        words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*|'[^']*'|[0-9]+(?:\.[0-9]+)?|[<>=!:]+|[(),.;]|.", statement)
        
        for pos, word in enumerate(words):
            if not word.strip():
                continue
            
            token = {
                "position": pos,
                "text": word.strip(),
                "type": self._classify_token(word.strip()),
                "is_keyword": word.strip().upper() in self.sql_keywords,
                "is_function": word.strip().upper() in self.oracle_functions,
                "is_operator": word.strip() in self.operators
            }
            
            tokens.append(token)
        
        return tokens
    
    def _classify_token(self, token: str) -> str:
        """Classify token type"""
        token_upper = token.upper()
        
        if token_upper in self.sql_keywords:
            return "keyword"
        elif token_upper in self.oracle_functions:
            return "function"
        elif token in self.operators:
            return "operator"
        elif token.startswith("'") and token.endswith("'"):
            return "string_literal"
        elif re.match(r'^\d+(\.\d+)?$', token):
            return "numeric_literal"
        elif token.startswith(':'):
            return "bind_variable"
        elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token):
            return "identifier"
        elif token in '()[]{}':
            return "parenthesis"
        elif token in ',.;':
            return "punctuation"
        else:
            return "unknown"
    
    def _analyze_tokens(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze token patterns and structure"""
        analysis = {
            "token_count": len(tokens),
            "keyword_count": sum(1 for t in tokens if t["is_keyword"]),
            "function_count": sum(1 for t in tokens if t["is_function"]),
            "operator_count": sum(1 for t in tokens if t["is_operator"]),
            "identifier_count": sum(1 for t in tokens if t["type"] == "identifier"),
            "complexity_score": 0
        }
        
        # Calculate complexity score
        complexity = 0
        complexity += analysis["keyword_count"] * 2
        complexity += analysis["function_count"] * 3
        complexity += sum(1 for t in tokens if t["type"] == "parenthesis")
        analysis["complexity_score"] = complexity
        
        return analysis
    
    def _generate_token_statistics(self, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate overall token statistics"""
        stats = {
            "total_statements": len(statements),
            "total_tokens": sum(len(stmt["tokens"]) for stmt in statements),
            "avg_tokens_per_statement": 0,
            "most_complex_statement": None,
            "keyword_frequency": {},
            "function_frequency": {}
        }
        
        if statements:
            stats["avg_tokens_per_statement"] = stats["total_tokens"] / len(statements)
            
            # Find most complex statement
            max_complexity = 0
            for stmt in statements:
                if stmt["analysis"]["complexity_score"] > max_complexity:
                    max_complexity = stmt["analysis"]["complexity_score"]
                    stats["most_complex_statement"] = stmt["statement_id"]
        
        return stats
    
    def _extract_syntax_elements(self, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract SQL syntax elements"""
        elements = {
            "has_if_statements": False,
            "has_case_statements": False,
            "has_loops": False,
            "has_exceptions": False,
            "has_select": False,
            "has_insert": False,
            "has_update": False,
            "has_delete": False
        }
        
        for stmt in statements:
            sql_upper = stmt["raw_sql"].upper()
            if 'IF ' in sql_upper:
                elements["has_if_statements"] = True
            if 'CASE ' in sql_upper:
                elements["has_case_statements"] = True
            if 'LOOP' in sql_upper:
                elements["has_loops"] = True
            if 'EXCEPTION' in sql_upper or 'RAISE' in sql_upper:
                elements["has_exceptions"] = True
            if 'SELECT' in sql_upper:
                elements["has_select"] = True
            if 'INSERT' in sql_upper:
                elements["has_insert"] = True
            if 'UPDATE' in sql_upper:
                elements["has_update"] = True
            if 'DELETE' in sql_upper:
                elements["has_delete"] = True
        
        return elements


class SQLValidator:
    """Step 4: Comprehensive SQL validation with error keys"""
    
    def __init__(self):
        self.error_codes = {
            "SYNTAX_001": "Missing semicolon",
            "SYNTAX_002": "Unmatched parentheses",
            "SYNTAX_003": "Invalid keyword sequence",
            "SYNTAX_004": "Missing END statement",
            "SYNTAX_005": "Invalid identifier",
            "LOGIC_001": "Unreachable code detected",
            "LOGIC_002": "Undefined variable reference",
            "LOGIC_003": "Type mismatch",
            "STRUCTURE_001": "Improper nesting",
            "STRUCTURE_002": "Missing THEN clause",
            "STRUCTURE_003": "Invalid CASE structure"
        }
    
    def validate_sql(self, tokenized_sql: Dict[str, Any], sections: Dict[str, str]) -> Dict[str, Any]:
        """Comprehensive SQL validation"""
        result = {
            "is_valid": True,
            "syntax_errors": [],
            "logic_errors": [],
            "structure_errors": [],
            "warnings": [],
            "validation_summary": {}
        }
        
        # Syntax validation
        syntax_results = self._validate_syntax(tokenized_sql)
        result["syntax_errors"] = syntax_results
        
        # Logic validation
        logic_results = self._validate_logic(tokenized_sql, sections)
        result["logic_errors"] = logic_results
        
        # Structure validation
        structure_results = self._validate_structure(tokenized_sql)
        result["structure_errors"] = structure_results
        
        # Overall validation status
        total_errors = len(syntax_results) + len(logic_results) + len(structure_results)
        result["is_valid"] = total_errors == 0
        
        result["validation_summary"] = {
            "total_errors": total_errors,
            "syntax_error_count": len(syntax_results),
            "logic_error_count": len(logic_results),
            "structure_error_count": len(structure_results)
        }
        
        return result
    
    def _validate_syntax(self, tokenized_sql: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate SQL syntax"""
        errors = []
        
        for stmt in tokenized_sql["tokens"]:
            tokens = stmt["tokens"]
            
            # Check parentheses matching
            paren_count = 0
            for token in tokens:
                if token["text"] == '(':
                    paren_count += 1
                elif token["text"] == ')':
                    paren_count -= 1
                
                if paren_count < 0:
                    errors.append({
                        "error_code": "SYNTAX_002",
                        "message": self.error_codes["SYNTAX_002"],
                        "statement_id": stmt["statement_id"],
                        "position": token["position"]
                    })
            
            if paren_count != 0:
                errors.append({
                    "error_code": "SYNTAX_002",
                    "message": self.error_codes["SYNTAX_002"],
                    "statement_id": stmt["statement_id"],
                    "position": -1
                })
        
        return errors
    
    def _validate_logic(self, tokenized_sql: Dict[str, Any], sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Validate SQL logic"""
        errors = []
        
        # Check for undefined variables (simplified check)
        declared_vars = self._extract_declared_variables(sections.get("declare_section", ""))
        
        for stmt in tokenized_sql["tokens"]:
            for token in stmt["tokens"]:
                if token["type"] == "identifier" and token["text"].startswith('v_'):
                    if token["text"] not in declared_vars:
                        errors.append({
                            "error_code": "LOGIC_002",
                            "message": f"Undefined variable: {token['text']}",
                            "statement_id": stmt["statement_id"],
                            "position": token["position"]
                        })
        
        return errors
    
    def _validate_structure(self, tokenized_sql: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate SQL structure"""
        errors = []
        
        for stmt in tokenized_sql["tokens"]:
            tokens = stmt["tokens"]
            
            # Check IF-THEN-END structure
            if_count = 0
            then_count = 0
            end_count = 0
            
            for token in tokens:
                if token["text"].upper() == "IF":
                    if_count += 1
                elif token["text"].upper() == "THEN":
                    then_count += 1
                elif token["text"].upper() == "END":
                    end_count += 1
            
            if if_count > 0 and then_count == 0:
                errors.append({
                    "error_code": "STRUCTURE_002",
                    "message": self.error_codes["STRUCTURE_002"],
                    "statement_id": stmt["statement_id"],
                    "position": -1
                })
        
        return errors
    
    def _extract_declared_variables(self, declare_section: str) -> set:
        """Extract declared variable names"""
        variables = set()
        
        if not declare_section.strip():
            return variables
        
        # Simple variable extraction
        for line in declare_section.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                # Match variable declarations
                match = re.match(r'(\w+)\s+', line)
                if match:
                    variables.add(match.group(1))
        
        return variables


def main():
    """Test the comprehensive converter"""
    print("🎯 Comprehensive Oracle Converter - Step by Step Analysis")
    print("=" * 80)
    
    # Test with trigger1
    oracle_file = "files/oracle/trigger1.sql"
    
    with open(oracle_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n📄 Processing {oracle_file}...")
    
    # Step 1: Comment Processing
    print("\n🔧 Step 1: Comment Processing...")
    comment_processor = CommentProcessor()
    comment_result = comment_processor.process_comments(content)
    print(f"   ✓ Removed {comment_result['comment_stats']['total_comments']} comments")
    
    # Step 2: Section Analysis
    print("\n🔧 Step 2: Section Analysis...")
    section_analyzer = SectionAnalyzer()
    section_result = section_analyzer.analyze_sections(comment_result["cleaned_content"])
    print(f"   ✓ Sections analyzed: {len([k for k, v in section_result['section_analysis'].items() if not v.get('empty', False)])}")
    
    # Step 3: SQL Tokenization
    print("\n🔧 Step 3: SQL Tokenization...")
    tokenizer = SQLTokenizer()
    token_result = tokenizer.tokenize_sql(section_result["begin_section"])
    print(f"   ✓ Tokenized {token_result['token_stats']['total_statements']} statements")
    print(f"   ✓ Total tokens: {token_result['token_stats']['total_tokens']}")
    
    # Step 4: SQL Validation
    print("\n🔧 Step 4: SQL Validation...")
    validator = SQLValidator()
    validation_result = validator.validate_sql(token_result, section_result)
    print(f"   ✓ Validation status: {'VALID' if validation_result['is_valid'] else 'INVALID'}")
    if not validation_result['is_valid']:
        print(f"   ⚠️ Total errors: {validation_result['validation_summary']['total_errors']}")
    
    # Save intermediate results
    results = {
        "comment_processing": comment_result,
        "section_analysis": section_result,
        "tokenization": token_result,
        "validation": validation_result
    }
    
    output_file = "files/sql_json/comprehensive_analysis_step_by_step.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Comprehensive analysis complete!")
    print(f"📊 Results saved to: {output_file}")


if __name__ == "__main__":
    main() 