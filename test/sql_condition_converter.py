#!/usr/bin/env python3
"""
SQL Condition Converter: Oracle to PostgreSQL
Extracts and converts SQL conditions from Oracle trigger conversion logs
"""

import re
import json
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLConditionConverter:
    """Converts Oracle SQL conditions to PostgreSQL format"""
    
    def __init__(self):
        self.conversion_mappings = {
            # Function mappings
            'NVL': 'COALESCE',
            'SUBSTR': 'SUBSTRING',
            'SYSDATE': 'CURRENT_DATE',
            'TRUNC': 'DATE_TRUNC',
            
            # Operator mappings
            '<>': '!=',
            
            # Trigger operation mappings
            'INSERTING': "TG_OP = 'INSERT'",
            'UPDATING': "TG_OP = 'UPDATE'",
            'DELETING': "TG_OP = 'DELETE'",
        }
        
        # Regex patterns for different condition types
        self.patterns = {
            'nvl_function': r'NVL\(([^,]+),([^)]+)\)',
            'substr_function': r'SUBSTR\(([^,]+),([^,]+),([^)]+)\)',
            'column_reference': r':(NEW|OLD)\.(\w+)',
            'trigger_operation': r'\b(INSERTING|UPDATING|DELETING)\b',
            'inequality_operator': r'<>',
        }
    
    def identify_condition_type(self, condition: str) -> str:
        """Identify the type of SQL condition"""
        condition = condition.strip()
        
        # Check for specific patterns
        if 'NVL(' in condition:
            return 'nvl_function'
        elif 'SUBSTR(' in condition:
            return 'substr_function'
        elif 'TRUNC(' in condition or 'TO_DATE(' in condition:
            return 'date_function'
        elif 'LENGTH(' in condition:
            return 'length_function'
        elif 'UPPER(' in condition:
            return 'upper_function'
        elif condition in ['INSERTING', 'UPDATING', 'DELETING']:
            return 'trigger_operation'
        elif 'INSERTING OR UPDATING' in condition:
            return 'trigger_combination'
        elif ' IN (' in condition:
            return 'in_condition'
        elif ' NOT IN (' in condition:
            return 'not_in_condition'
        elif ' BETWEEN ' in condition:
            return 'between_condition'
        elif 'IS NULL' in condition:
            return 'null_check'
        elif 'IS NOT NULL' in condition:
            return 'not_null_check'
        elif '<>' in condition:
            return 'inequality'
        elif ' AND ' in condition or ' OR ' in condition:
            return 'boolean_logic'
        elif '=' in condition:
            return 'equality'
        elif '>' in condition or '<' in condition:
            return 'range'
        else:
            return 'unknown'
    
    def extract_components(self, condition: str) -> Dict:
        """Extract components from SQL condition"""
        components = {
            'columns': [],
            'functions': [],
            'literals': [],
            'operators': [],
            'variables': [],
            'trigger_ops': []
        }
        
        # Extract column references
        column_matches = re.findall(r':(NEW|OLD)\.(\w+)', condition)
        components['columns'] = [f"{ref[0]}.{ref[1]}" for ref in column_matches]
        
        # Extract functions
        function_matches = re.findall(r'(\w+)\([^)]*\)', condition)
        components['functions'] = function_matches
        
        # Extract operators
        operator_matches = re.findall(r'(=|<>|>|<|>=|<=|AND|OR|IN|NOT IN|BETWEEN|IS NULL|IS NOT NULL)', condition, re.IGNORECASE)
        components['operators'] = operator_matches
        
        # Extract trigger operations
        trigger_matches = re.findall(r'\b(INSERTING|UPDATING|DELETING)\b', condition)
        components['trigger_ops'] = trigger_matches
        
        # Extract variables (V_ prefixed)
        variable_matches = re.findall(r'\bV_\w+\b', condition)
        components['variables'] = variable_matches
        
        return components
    
    def convert_nvl_function(self, condition: str) -> str:
        """Convert NVL function to COALESCE"""
        pattern = r'NVL\(([^,]+),([^)]+)\)'
        replacement = r'COALESCE(\1,\2)'
        return re.sub(pattern, replacement, condition)
    
    def convert_substr_function(self, condition: str) -> str:
        """Convert SUBSTR function to SUBSTRING"""
        pattern = r'SUBSTR\(([^,]+),([^,]+),([^)]+)\)'
        replacement = r'SUBSTRING(\1 FROM \2 FOR \3)'
        return re.sub(pattern, replacement, condition)
    
    def convert_trigger_operations(self, condition: str) -> str:
        """Convert trigger operations to TG_OP format"""
        # Handle combinations first
        if 'INSERTING OR UPDATING' in condition:
            condition = condition.replace('INSERTING OR UPDATING', "TG_OP IN ('INSERT', 'UPDATE')")
        
        # Handle individual operations
        for op, replacement in [
            ('INSERTING', "TG_OP = 'INSERT'"),
            ('UPDATING', "TG_OP = 'UPDATE'"),
            ('DELETING', "TG_OP = 'DELETE'")
        ]:
            condition = condition.replace(op, replacement)
        
        return condition
    
    def convert_date_functions(self, condition: str) -> str:
        """Convert Oracle date functions to PostgreSQL"""
        # Convert SYSDATE to CURRENT_DATE
        condition = condition.replace('SYSDATE', 'CURRENT_DATE')
        
        # Convert TRUNC to DATE_TRUNC (simplified)
        if 'TRUNC(' in condition and 'TO_DATE' in condition:
            # This is a complex case that might need manual review
            condition = condition.replace('TRUNC(', 'DATE_TRUNC(')
        
        return condition
    
    def convert_operators(self, condition: str) -> str:
        """Convert Oracle operators to PostgreSQL"""
        # Convert inequality operator
        condition = condition.replace('<>', '!=')
        
        return condition
    
    def convert_column_references(self, condition: str) -> str:
        """Convert Oracle column references to PostgreSQL"""
        # Remove the colon prefix from NEW/OLD references
        condition = re.sub(r':(NEW|OLD)\.', r'\1.', condition)
        return condition
    
    def convert_condition(self, condition: str) -> str:
        """Main conversion function"""
        original_condition = condition.strip()
        converted_condition = original_condition
        
        # Identify condition type
        condition_type = self.identify_condition_type(original_condition)
        
        # Apply conversions based on type
        if condition_type == 'nvl_function':
            converted_condition = self.convert_nvl_function(converted_condition)
        elif condition_type == 'substr_function':
            converted_condition = self.convert_substr_function(converted_condition)
        elif condition_type in ['trigger_operation', 'trigger_combination']:
            converted_condition = self.convert_trigger_operations(converted_condition)
        elif condition_type == 'date_function':
            converted_condition = self.convert_date_functions(converted_condition)
        elif condition_type == 'inequality':
            converted_condition = self.convert_operators(converted_condition)
        
        # Apply universal conversions
        converted_condition = self.convert_column_references(converted_condition)
        
        return converted_condition
    
    def validate_conversion(self, original: str, converted: str) -> bool:
        """Validate that the conversion is correct"""
        # Basic validation checks
        if 'NVL(' in converted:
            logger.warning(f"NVL function not converted: {converted}")
            return False
        
        if '<>' in converted:
            logger.warning(f"Inequality operator not converted: {converted}")
            return False
        
        if any(op in converted for op in ['INSERTING', 'UPDATING', 'DELETING']):
            logger.warning(f"Trigger operation not converted: {converted}")
            return False
        
        return True

class LogProcessor:
    """Processes log files to extract SQL conditions"""
    
    def __init__(self, converter: SQLConditionConverter):
        self.converter = converter
    
    def extract_conditions_from_log(self, log_file_path: str) -> List[str]:
        """Extract SQL conditions from log file"""
        conditions = []
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    # Look for lines containing SQL conditions
                    if 'DEBUG' in line and 'test.py:36' in line:
                        # Extract the condition part after the last dash
                        parts = line.split(' - ')
                        if len(parts) >= 4:
                            condition = parts[-1].strip()
                            if condition and not condition.startswith('2025-'):
                                conditions.append(condition)
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
        
        return conditions
    
    def process_conditions(self, conditions: List[str]) -> List[Dict]:
        """Process and convert conditions"""
        results = []
        
        for i, condition in enumerate(conditions):
            try:
                # Skip empty conditions
                if not condition.strip():
                    continue
                
                # Convert the condition
                converted = self.converter.convert_condition(condition)
                
                # Validate conversion
                is_valid = self.converter.validate_conversion(condition, converted)
                
                # Extract components for analysis
                components = self.converter.extract_components(condition)
                condition_type = self.converter.identify_condition_type(condition)
                
                result = {
                    'index': i,
                    'original': condition,
                    'converted': converted,
                    'type': condition_type,
                    'components': components,
                    'valid': is_valid,
                    'status': 'success' if is_valid else 'warning'
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing condition {i}: {e}")
                results.append({
                    'index': i,
                    'original': condition,
                    'converted': None,
                    'type': 'error',
                    'components': {},
                    'valid': False,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def generate_report(self, results: List[Dict], output_file: str = None) -> str:
        """Generate a conversion report"""
        report_lines = []
        report_lines.append("# SQL Condition Conversion Report")
        report_lines.append("")
        
        # Summary statistics
        total = len(results)
        successful = sum(1 for r in results if r['status'] == 'success')
        warnings = sum(1 for r in results if r['status'] == 'warning')
        errors = sum(1 for r in results if r['status'] == 'error')
        
        report_lines.append(f"## Summary")
        report_lines.append(f"- Total conditions: {total}")
        report_lines.append(f"- Successful conversions: {successful}")
        report_lines.append(f"- Warnings: {warnings}")
        report_lines.append(f"- Errors: {errors}")
        report_lines.append("")
        
        # Type breakdown
        type_counts = {}
        for result in results:
            condition_type = result['type']
            type_counts[condition_type] = type_counts.get(condition_type, 0) + 1
        
        report_lines.append("## Condition Types")
        for condition_type, count in sorted(type_counts.items()):
            report_lines.append(f"- {condition_type}: {count}")
        report_lines.append("")
        
        # Detailed conversions
        report_lines.append("## Detailed Conversions")
        report_lines.append("")
        
        for result in results:
            report_lines.append(f"### Condition {result['index']}")
            report_lines.append(f"**Type:** {result['type']}")
            report_lines.append(f"**Original:** `{result['original']}`")
            
            if result['converted']:
                report_lines.append(f"**Converted:** `{result['converted']}`")
            
            if result['components']:
                report_lines.append(f"**Components:**")
                for key, value in result['components'].items():
                    if value:
                        report_lines.append(f"  - {key}: {value}")
            
            if result['status'] != 'success':
                report_lines.append(f"**Status:** {result['status']}")
                if 'error' in result:
                    report_lines.append(f"**Error:** {result['error']}")
            
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        # Save to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"Report saved to {output_file}")
            except Exception as e:
                logger.error(f"Error saving report: {e}")
        
        return report

def main():
    """Main function to process log file and generate conversion report"""
    
    # Initialize converter and processor
    converter = SQLConditionConverter()
    processor = LogProcessor(converter)
    
    # Process the log file
    log_file = "output/oracle_conversion_20250813_045217.log"
    
    if not Path(log_file).exists():
        logger.error(f"Log file not found: {log_file}")
        return
    
    logger.info(f"Processing log file: {log_file}")
    
    # Extract conditions
    conditions = processor.extract_conditions_from_log(log_file)
    logger.info(f"Extracted {len(conditions)} conditions")
    
    # Process and convert conditions
    results = processor.process_conditions(conditions)
    
    # Generate report
    report = processor.generate_report(results, "docs/sql_condition_conversion_report.md")
    
    # Print summary
    successful = sum(1 for r in results if r['status'] == 'success')
    warnings = sum(1 for r in results if r['status'] == 'warning')
    errors = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\nConversion Summary:")
    print(f"Total conditions: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Warnings: {warnings}")
    print(f"Errors: {errors}")
    
    # Show some examples
    print(f"\nExample conversions:")
    for i, result in enumerate(results[:5]):
        if result['converted']:
            print(f"{i+1}. {result['original']} → {result['converted']}")

if __name__ == "__main__":
    main()
