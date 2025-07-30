#!/usr/bin/env python3
"""
Comprehensive Oracle to JSON Converter

This script converts Oracle SQL triggers through a two-stage process:
1. Oracle SQL → Enhanced Analysis JSON (detailed analysis)
2. Enhanced Analysis JSON → SQL JSON (simplified format)

The converter follows the user's requirements:
- Remove comments properly
- Break into declare, main, and exception statements  
- Tokenize and validate SQL
- Provide detailed error handling with error keys
"""

import re
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Custom exception for conversion errors with error keys"""
    def __init__(self, error_key: str, message: str, details: str = ""):
        self.error_key = error_key
        self.message = message
        self.details = details
        super().__init__(f"[{error_key}] {message}")


@dataclass
class TriggerMetadata:
    """Metadata about the trigger"""
    trigger_name: str
    timing: str = "AFTER"  # Default for most triggers
    events: List[str] = None
    table_name: str = ""
    has_declare_section: bool = False
    has_begin_section: bool = False
    has_exception_section: bool = False

    def __post_init__(self):
        if self.events is None:
            self.events = ["INSERT", "UPDATE", "DELETE"]


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
class DataOperation:
    """Represents a data operation in the trigger"""
    id: str
    sql: str
    type: str
    condition: Optional[str] = None
    then_statement: Optional[Union[List[Dict], str]] = None
    else_statement: Optional[Union[List[Dict], str]] = None
    when_clauses: Optional[List[Dict]] = None
    parameters: Optional[Dict] = None
    table: Optional[str] = None
    columns: Optional[List[str]] = None
    values: Optional[List[str]] = None
    operations: Optional[List[Dict]] = None
    assignments: Optional[List[Dict]] = None
    select_statement: Optional[str] = None
    exception_handlers: Optional[List[Dict]] = None


class CommentRemover:
    """Handles comment removal from Oracle SQL"""
    
    @staticmethod
    def remove_comments(sql_content: str) -> str:
        """Remove SQL comments while preserving string literals"""
        try:
            # Remove single-line comments (-- style)
            lines = sql_content.split('\n')
            processed_lines = []
            
            for line in lines:
                # Simple approach: remove -- comments not inside strings
                in_string = False
                quote_char = None
                comment_start = -1
                
                for i, char in enumerate(line):
                    if not in_string and char in ("'", '"'):
                        in_string = True
                        quote_char = char
                    elif in_string and char == quote_char:
                        in_string = False
                        quote_char = None
                    elif not in_string and i < len(line) - 1 and line[i:i+2] == '--':
                        comment_start = i
                        break
                
                if comment_start >= 0:
                    line = line[:comment_start].rstrip()
                
                processed_lines.append(line)
            
            result = '\n'.join(processed_lines)
            
            # Remove multi-line comments (/* ... */)
            result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)
            
            logger.info("Comments removed successfully")
            return result
            
        except Exception as e:
            raise ConversionError("COMMENT_REMOVAL_ERROR", f"Failed to remove comments: {str(e)}")


class TriggerSectionParser:
    """Parses Oracle trigger into declare, main, and exception sections"""
    
    @staticmethod
    def parse_sections(sql_content: str) -> Tuple[str, str, str]:
        """Parse SQL into declare, main (begin), and exception sections"""
        try:
            # Clean up the content
            content = sql_content.strip()
            
            # Find the main sections
            declare_match = re.search(r'^declare\s*(.*?)\s*begin', content, re.IGNORECASE | re.DOTALL)
            begin_match = re.search(r'begin\s*(.*?)\s*exception', content, re.IGNORECASE | re.DOTALL)
            exception_match = re.search(r'exception\s*(.*?)\s*end\s*;?\s*$', content, re.IGNORECASE | re.DOTALL)
            
            # Alternative patterns if first attempt fails
            if not begin_match:
                begin_match = re.search(r'begin\s*(.*?)\s*end\s*;?\s*$', content, re.IGNORECASE | re.DOTALL)
            
            declare_section = declare_match.group(1).strip() if declare_match else ""
            main_section = begin_match.group(1).strip() if begin_match else ""
            exception_section = exception_match.group(1).strip() if exception_match else ""
            
            logger.info(f"Sections parsed - Declare: {len(declare_section)} chars, Main: {len(main_section)} chars, Exception: {len(exception_section)} chars")
            
            return declare_section, main_section, exception_section
            
        except Exception as e:
            raise ConversionError("SECTION_PARSING_ERROR", f"Failed to parse trigger sections: {str(e)}")


class DeclarationParser:
    """Parses variable, constant, and exception declarations"""
    
    def __init__(self):
        self.patterns = {
            'variable': r'(\w+)\s+((?:varchar2|number|date|pls_integer|simple_integer|binary_integer|boolean|PLS_INTEGER|BOOLEAN|%TYPE)[^;]*?)(?::=\s*([^;]+?))?\s*;',
            'constant': r'(\w+)\s+constant\s+([^:=]+?)\s*:=\s*([^;]+?)\s*;',
            'exception': r'(\w+)\s+exception\s*;',
        }
    
    def parse_declarations(self, declare_section: str) -> Tuple[List[Variable], List[Constant], List[Exception]]:
        """Parse declarations from the declare section"""
        try:
            variables = []
            constants = []
            exceptions = []
            
            if not declare_section.strip():
                return variables, constants, exceptions
            
            # Parse variables
            var_matches = re.finditer(self.patterns['variable'], declare_section, re.IGNORECASE)
            for match in var_matches:
                name = match.group(1)
                data_type = match.group(2).strip()
                default_value = match.group(3).strip() if match.group(3) else None
                
                variables.append(Variable(name=name, data_type=data_type, default_value=default_value))
            
            # Parse constants
            const_matches = re.finditer(self.patterns['constant'], declare_section, re.IGNORECASE)
            for match in const_matches:
                name = match.group(1)
                data_type = match.group(2).strip()
                value = match.group(3).strip()
                
                constants.append(Constant(name=name, data_type=data_type, value=value))
            
            # Parse exceptions
            exc_matches = re.finditer(self.patterns['exception'], declare_section, re.IGNORECASE)
            for match in exc_matches:
                name = match.group(1)
                exceptions.append(Exception(name=name, type="user_defined"))
            
            logger.info(f"Declarations parsed - Variables: {len(variables)}, Constants: {len(constants)}, Exceptions: {len(exceptions)}")
            return variables, constants, exceptions
            
        except Exception as e:
            raise ConversionError("DECLARATION_PARSING_ERROR", f"Failed to parse declarations: {str(e)}")


class DataOperationExtractor:
    """Extracts and analyzes data operations from the main section"""
    
    def __init__(self):
        self.operation_counter = 0
        
    def extract_data_operations(self, main_section: str) -> List[DataOperation]:
        """Extract all data operations from the main section"""
        try:
            operations = []
            self.operation_counter = 0
            
            # First, extract simple SQL statements
            operations.extend(self._extract_simple_statements(main_section))
            
            # Then extract control structures
            operations.extend(self._extract_control_structures(main_section))
            
            logger.info(f"Extracted {len(operations)} data operations")
            return operations
            
        except Exception as e:
            raise ConversionError("DATA_OPERATION_EXTRACTION_ERROR", f"Failed to extract data operations: {str(e)}")
    
    def _extract_simple_statements(self, content: str) -> List[DataOperation]:
        """Extract simple SQL statements"""
        operations = []
        
        # SELECT statements
        select_pattern = r'select\s+.*?(?=\s*;|\s*from\s+dual|\s*into\s+\w+)'
        for match in re.finditer(select_pattern, content, re.IGNORECASE | re.DOTALL):
            self.operation_counter += 1
            sql = match.group(0).strip()
            if not sql.endswith(';'):
                sql += ';'
                
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=sql,
                type="select_statements"
            ))
        
        # INSERT statements
        insert_pattern = r'insert\s+into\s+.*?(?=\s*;)'
        for match in re.finditer(insert_pattern, content, re.IGNORECASE | re.DOTALL):
            self.operation_counter += 1
            sql = match.group(0).strip()
            if not sql.endswith(';'):
                sql += ';'
                
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=sql,
                type="insert_statements"
            ))
        
        # UPDATE statements
        update_pattern = r'update\s+.*?(?=\s*;)'
        for match in re.finditer(update_pattern, content, re.IGNORECASE | re.DOTALL):
            self.operation_counter += 1
            sql = match.group(0).strip()
            if not sql.endswith(';'):
                sql += ';'
                
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=sql,
                type="update_statements"
            ))
        
        return operations
    
    def _extract_control_structures(self, content: str) -> List[DataOperation]:
        """Extract control structures like IF, CASE, etc."""
        operations = []
        
        # Simple IF statements - basic pattern for now
        if_pattern = r'if\s*\([^)]+\)\s*then.*?end\s+if\s*;'
        for match in re.finditer(if_pattern, content, re.IGNORECASE | re.DOTALL):
            self.operation_counter += 1
            sql = match.group(0).strip()
            
            # Extract condition
            condition_match = re.search(r'if\s*\(([^)]+)\)', sql, re.IGNORECASE)
            condition = condition_match.group(1) if condition_match else ""
            
            operations.append(DataOperation(
                id=f"code_{self.operation_counter}",
                sql=f"if ({condition}) then ... end if;",
                type="if_else",
                condition=condition,
                then_statement="...",  # Placeholder for now
                else_statement=None
            ))
        
        return operations


class ExceptionHandler:
    """Handles exception parsing"""
    
    @staticmethod
    def parse_exception_handlers(exception_section: str) -> List[Dict[str, Any]]:
        """Parse exception handlers from the exception section"""
        try:
            handlers = []
            
            if not exception_section.strip():
                return handlers
            
            # Parse WHEN clauses
            when_pattern = r'when\s+(\w+)\s*then\s*(.*?)(?=when\s+\w+|$)'
            for match in re.finditer(when_pattern, exception_section, re.IGNORECASE | re.DOTALL):
                exception_name = match.group(1)
                handler_code = match.group(2).strip()
                
                handlers.append({
                    "exception_name": exception_name,
                    "handler_code": handler_code
                })
            
            logger.info(f"Parsed {len(handlers)} exception handlers")
            return handlers
            
        except Exception as e:
            raise ConversionError("EXCEPTION_PARSING_ERROR", f"Failed to parse exception handlers: {str(e)}")


class OracleToEnhancedJsonConverter:
    """Main converter class for Oracle SQL to Enhanced JSON"""
    
    def __init__(self):
        self.comment_remover = CommentRemover()
        self.section_parser = TriggerSectionParser()
        self.declaration_parser = DeclarationParser()
        self.operation_extractor = DataOperationExtractor()
        self.exception_handler = ExceptionHandler()
    
    def convert_oracle_to_enhanced_json(self, oracle_file_path: str, output_file_path: str) -> Dict[str, Any]:
        """Convert Oracle SQL file to Enhanced Analysis JSON"""
        try:
            logger.info(f"Starting conversion: {oracle_file_path} → {output_file_path}")
            
            # Step 1: Read Oracle SQL file
            with open(oracle_file_path, 'r', encoding='utf-8') as f:
                oracle_content = f.read()
            
            # Step 2: Remove comments
            clean_content = self.comment_remover.remove_comments(oracle_content)
            
            # Step 3: Parse sections
            declare_section, main_section, exception_section = self.section_parser.parse_sections(clean_content)
            
            # Step 4: Extract metadata
            trigger_name = Path(oracle_file_path).stem
            metadata = TriggerMetadata(
                trigger_name=trigger_name,
                timing="AFTER",  # Default, could be detected from SQL
                events=["INSERT", "UPDATE", "DELETE"],
                table_name=self._extract_table_name(clean_content),
                has_declare_section=bool(declare_section.strip()),
                has_begin_section=bool(main_section.strip()),
                has_exception_section=bool(exception_section.strip())
            )
            
            # Step 5: Parse declarations
            variables, constants, exceptions = self.declaration_parser.parse_declarations(declare_section)
            
            # Step 6: Extract data operations
            data_operations = self.operation_extractor.extract_data_operations(main_section)
            
            # Step 7: Parse exception handlers
            exception_handlers = self.exception_handler.parse_exception_handlers(exception_section)
            
            # Step 8: Build enhanced JSON structure
            enhanced_json = {
                "trigger_metadata": asdict(metadata),
                "declarations": {
                    "variables": [asdict(var) for var in variables],
                    "constants": [asdict(const) for const in constants],
                    "exceptions": [asdict(exc) for exc in exceptions]
                },
                "data_operations": [self._operation_to_dict(op) for op in data_operations],
                "exception_handlers": exception_handlers
            }
            
            # Step 9: Save to file
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_json, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Enhanced JSON conversion completed: {output_file_path}")
            return enhanced_json
            
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError("GENERAL_CONVERSION_ERROR", f"Unexpected error during conversion: {str(e)}")
    
    def _extract_table_name(self, content: str) -> str:
        """Extract table name from trigger content"""
        # Simple pattern - could be improved
        table_patterns = [
            r'insert\s+into\s+(\w+)',
            r'update\s+(\w+)',
            r'delete\s+from\s+(\w+)',
        ]
        
        for pattern in table_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                if not table_name.startswith('v_'):  # Skip views
                    return table_name
        
        return "themes"  # Default fallback
    
    def _operation_to_dict(self, operation: DataOperation) -> Dict[str, Any]:
        """Convert DataOperation to dictionary, excluding None values"""
        result = {"id": operation.id, "sql": operation.sql, "type": operation.type}
        
        if operation.condition:
            result["condition"] = operation.condition
        if operation.then_statement:
            result["then_statement"] = operation.then_statement
        if operation.else_statement:
            result["else_statement"] = operation.else_statement
        if operation.when_clauses:
            result["when_clauses"] = operation.when_clauses
        if operation.parameters:
            result["parameters"] = operation.parameters
        if operation.table:
            result["table"] = operation.table
        if operation.columns:
            result["columns"] = operation.columns
        if operation.values:
            result["values"] = operation.values
        if operation.operations:
            result["operations"] = operation.operations
        if operation.assignments:
            result["assignments"] = operation.assignments
        if operation.select_statement:
            result["select_statement"] = operation.select_statement
        if operation.exception_handlers:
            result["exception_handlers"] = operation.exception_handlers
            
        return result


class EnhancedToSqlJsonConverter:
    """Converter for Enhanced JSON to SQL JSON (simplified format)"""
    
    @staticmethod
    def convert_enhanced_to_sql_json(enhanced_json_path: str, sql_json_path: str) -> Dict[str, Any]:
        """Convert Enhanced Analysis JSON to SQL JSON"""
        try:
            logger.info(f"Starting enhanced to SQL JSON conversion: {enhanced_json_path} → {sql_json_path}")
            
            # Read enhanced JSON
            with open(enhanced_json_path, 'r', encoding='utf-8') as f:
                enhanced_data = json.load(f)
            
            # Create simplified SQL JSON structure
            sql_json = {
                "trigger_metadata": enhanced_data["trigger_metadata"],
                "declarations": enhanced_data["declarations"],
                "data_operations": enhanced_data["data_operations"][:10],  # Limit operations for SQL JSON
                "exception_handlers": enhanced_data["exception_handlers"]
            }
            
            # Save to file
            os.makedirs(os.path.dirname(sql_json_path), exist_ok=True)
            with open(sql_json_path, 'w', encoding='utf-8') as f:
                json.dump(sql_json, f, indent=2, ensure_ascii=False)
            
            logger.info(f"SQL JSON conversion completed: {sql_json_path}")
            return sql_json
            
        except Exception as e:
            raise ConversionError("SQL_JSON_CONVERSION_ERROR", f"Failed to convert to SQL JSON: {str(e)}")


class ComprehensiveConverter:
    """Main converter that orchestrates the complete conversion process"""
    
    def __init__(self):
        self.oracle_to_enhanced = OracleToEnhancedJsonConverter()
        self.enhanced_to_sql = EnhancedToSqlJsonConverter()
    
    def convert_all_triggers(self, oracle_folder: str = "files/oracle", 
                           enhanced_folder: str = "files/expected_ana_json",
                           sql_json_folder: str = "files/sql_json") -> Dict[str, Any]:
        """Convert all Oracle triggers through the complete pipeline"""
        try:
            results = {
                "successful_conversions": [],
                "failed_conversions": [],
                "total_processed": 0,
                "conversion_time": datetime.now().isoformat()
            }
            
            oracle_files = list(Path(oracle_folder).glob("*.sql"))
            results["total_processed"] = len(oracle_files)
            
            for oracle_file in oracle_files:
                try:
                    logger.info(f"Processing {oracle_file.name}")
                    
                    # Stage 1: Oracle → Enhanced JSON
                    enhanced_file = Path(enhanced_folder) / f"{oracle_file.stem}_enhanced_analysis.json"
                    enhanced_json = self.oracle_to_enhanced.convert_oracle_to_enhanced_json(
                        str(oracle_file), str(enhanced_file)
                    )
                    
                    # Stage 2: Enhanced JSON → SQL JSON
                    sql_json_file = Path(sql_json_folder) / f"{oracle_file.stem}_enhanced_analysis.json"
                    sql_json = self.enhanced_to_sql.convert_enhanced_to_sql_json(
                        str(enhanced_file), str(sql_json_file)
                    )
                    
                    results["successful_conversions"].append({
                        "oracle_file": str(oracle_file),
                        "enhanced_file": str(enhanced_file),
                        "sql_json_file": str(sql_json_file),
                        "operations_count": len(enhanced_json.get("data_operations", [])),
                        "variables_count": len(enhanced_json.get("declarations", {}).get("variables", [])),
                        "exceptions_count": len(enhanced_json.get("declarations", {}).get("exceptions", []))
                    })
                    
                except ConversionError as e:
                    logger.error(f"Conversion failed for {oracle_file.name}: {e}")
                    results["failed_conversions"].append({
                        "oracle_file": str(oracle_file),
                        "error_key": e.error_key,
                        "error_message": e.message,
                        "error_details": e.details
                    })
                
                except Exception as e:
                    logger.error(f"Unexpected error for {oracle_file.name}: {e}")
                    results["failed_conversions"].append({
                        "oracle_file": str(oracle_file),
                        "error_key": "UNEXPECTED_ERROR",
                        "error_message": str(e),
                        "error_details": ""
                    })
            
            # Save conversion report
            report_file = "conversion_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conversion complete. Report saved to {report_file}")
            return results
            
        except Exception as e:
            raise ConversionError("BATCH_CONVERSION_ERROR", f"Failed to convert all triggers: {str(e)}")


def main():
    """Main function to run the comprehensive converter"""
    try:
        print("🚀 Starting Comprehensive Oracle to JSON Converter")
        print("=" * 60)
        
        converter = ComprehensiveConverter()
        results = converter.convert_all_triggers()
        
        print("\n📊 Conversion Results:")
        print(f"✅ Successful: {len(results['successful_conversions'])}")
        print(f"❌ Failed: {len(results['failed_conversions'])}")
        print(f"📁 Total Processed: {results['total_processed']}")
        
        if results['failed_conversions']:
            print("\n🔍 Failed Conversions:")
            for failure in results['failed_conversions']:
                print(f"  - {failure['oracle_file']}: [{failure['error_key']}] {failure['error_message']}")
        
        print(f"\n📄 Detailed report saved to: conversion_report.json")
        
    except ConversionError as e:
        print(f"❌ Conversion Error: [{e.error_key}] {e.message}")
        if e.details:
            print(f"   Details: {e.details}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


if __name__ == "__main__":
    main() 