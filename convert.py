#!/usr/bin/env python3
"""
Oracle to PostgreSQL Trigger Converter
Converts Oracle PL/SQL trigger code to PostgreSQL code wrapped in JSON format
"""

import re
import json
import os
import glob
from typing import Dict, List, Tuple
import argparse
from pathlib import Path


class OracleToPostgreSQLConverter:
    def __init__(self):
        # Data type mappings
        self.data_type_mappings = {
            r'\bvarchar2\b': 'varchar',
            r'\bpls_integer\b': 'integer',
            r'\bsimple_integer\b': 'integer',
            r'\bnumber\b': 'numeric',
            r'\bdate\b': 'date',
            r'\bclob\b': 'text',
            r'\bblob\b': 'bytea',
        }
        
        # Function mappings
        self.function_mappings = {
            r'\bsubstr\b': 'SUBSTRING',
            r'\bnvl\b': 'COALESCE',
            r'\bsysdate\b': 'CURRENT_DATE',
            r'\btrunc\b': 'DATE_TRUNC',
            r'\blength\b': 'LENGTH',
            r'\btrim\b': 'TRIM',
            r'\bupper\b': 'UPPER',
            r'\blower\b': 'LOWER',
            r'\bto_date\b': 'TO_DATE',
            r'\bto_number\b': 'CAST',
            r'\buser\b': 'current_user',
        }
        
        # Exception mappings with proper messages
        self.exception_mappings = {
            'invalid_theme_no': 'This is not a valid Theme No',
            'delete_no_more_possible': 'Theme cannot be deleted when the deletion is not on the same day, on which the Theme has been inserted',
            'theme_no_only_insert': 'Theme No cannot be updated', 
            'description_too_long': 'The automatically generated Theme Description is too long',
            'theme_desc_proposal_too_long': 'The automatically generated Short Description Proposal is too long',
            'theme_desc_alt_too_long': 'The automatically generated Downstream Theme Description is too long',
            'theme_no_cannot_be_inserted': 'This Theme No already exists',
            'onlyoneofficialchangeperday': 'Official Change for this Theme No and Day already exists',
            'insertsmustbeofficial': 'New Themes can only be inserted by Official Changes',
            'themedescriptionmandatory': 'If Pharma Rx Portfolio Project is set to "No", then the Theme Description must be filled',
            'theme_desc_not_unique': 'This Theme Description already exists',
            'in_prep_not_portf_proj': 'In-prep theme must be portfolio project',
            'in_prep_not_closed': 'In-prep status validation failed',
            'invalid_molecule_id': 'This is not a valid Molecule ID',
            'sec_mol_list_not_empty': 'Secondary molecule list not empty',
            'admin_update_only': 'Admin access required for this operation',
            'portf_proj_mol_cre_err': 'Portfolio project molecule creation error',
            'debugging': 'Debug in Themes IOF standard'
        }

    def clean_sql_content(self, content: str) -> str:
        """Remove comments and normalize whitespace"""
        # Remove single line comments
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Normalize whitespace but preserve line structure
        content = re.sub(r'[ \t]+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n', content)
        return content.strip()

    def convert_data_types(self, sql: str) -> str:
        """Convert Oracle data types to PostgreSQL"""
        for oracle_type, pg_type in self.data_type_mappings.items():
            sql = re.sub(oracle_type, pg_type, sql, flags=re.IGNORECASE)
        return sql

    def convert_functions(self, sql: str) -> str:
        """Convert Oracle functions to PostgreSQL equivalents"""
        for oracle_func, pg_func in self.function_mappings.items():
            sql = re.sub(oracle_func, pg_func, sql, flags=re.IGNORECASE)
        return sql

    def convert_substr_to_substring(self, sql: str) -> str:
        """Convert substr calls to SUBSTRING with FROM...FOR syntax"""
        # Pattern: SUBSTRING(string, start, length) -> SUBSTRING(string FROM start FOR length)
        pattern = r'SUBSTRING\s*\(\s*([^,]+),\s*(\d+),\s*([^)]+)\s*\)'
        replacement = r'SUBSTRING(\1 FROM \2 FOR \3)'
        sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        
        # Pattern: SUBSTRING(string, start) -> SUBSTRING(string FROM start)  
        pattern = r'SUBSTRING\s*\(\s*([^,]+),\s*(\d+)\s*\)'
        replacement = r'SUBSTRING(\1 FROM \2)'
        sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        
        return sql

    def convert_sequence_generation(self, sql: str) -> str:
        """Convert Oracle ROWNUM sequence to PostgreSQL generate_series"""
        # Convert Oracle's ROWNUM-based sequence generation
        oracle_pattern = r'select\s+rownum\s+as\s+new_rg_no\s+from\s+dual\s+connect\s+by\s+1\s*=\s*1\s+and\s+rownum\s*<=\s*(\d+)'
        pg_replacement = r'SELECT rn AS new_rg_no FROM generate_series(6000, \1) AS rn'
        sql = re.sub(oracle_pattern, pg_replacement, sql, flags=re.IGNORECASE)
        
        # Handle the specific pattern in the trigger
        complex_pattern = r'select\s+new_rg_no\s+into\s+v_new_rg_no\s+from\s+\(select\s+new_rg_no\s+from\s+\(SELECT rn AS new_rg_no FROM generate_series\(6000, 6999\) AS rn\)\s+where\s+new_rg_no\s*>\s*5999\s+minus\s+select\s+(?:CAST\()?rg_no(?:\))?(?:::INTEGER)?\s+from\s+v_theme_molecules(?:_mrhub)?\)\s+where\s+rownum\s*=\s*1'
        pg_simple = 'SELECT new_rg_no INTO v_new_rg_no FROM ( SELECT rn AS new_rg_no FROM generate_series(6000, 6999) AS rn EXCEPT SELECT rg_no::INTEGER FROM gmd.v_theme_molecules_mrhub) AS free_rg LIMIT 1'
        sql = re.sub(complex_pattern, pg_simple, sql, flags=re.IGNORECASE)
        
        return sql

    def convert_exception_handling(self, sql: str) -> str:
        """Convert Oracle exception handling to PostgreSQL"""
        # Convert custom exception declarations to comments
        for exception in self.exception_mappings.keys():
            pattern = f'{exception}\\s+exception;'
            sql = re.sub(pattern, f'-- {exception} exception converted', sql, flags=re.IGNORECASE)
        
        # Convert raise statements to RAISE EXCEPTION
        for exception, message in self.exception_mappings.items():
            pattern = f'raise\\s+{exception};'
            replacement = f"RAISE EXCEPTION 'MDM_V_THEMES_IOF: {message}';"
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        
        # Convert raise_application_error to RAISE EXCEPTION
        pattern = r'raise_application_error\s*\(\s*-?\d+\s*,\s*[\'"]([^\'"]*)[\'"][^)]*\)'
        replacement = r"RAISE EXCEPTION 'MDM_V_THEMES_IOF: \1'"
        sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        
        return sql

    def convert_variable_references(self, sql: str) -> str:
        """Convert Oracle :new.field to PostgreSQL :new_field format"""
        # Convert :new.field_name to :new_field_name
        sql = re.sub(r':new\.(\w+)', r':new_\1', sql)
        sql = re.sub(r':old\.(\w+)', r':old_\1', sql)
        
        return sql

    def convert_function_calls(self, sql: str) -> str:
        """Convert Oracle package.function calls to PostgreSQL schema$function format"""
        # Convert package.function to schema$function, but preserve gmd.table references
        pattern = r'(\w+)\.(\w+)\s*\('
        
        def replace_func(match):
            schema = match.group(1)
            func = match.group(2)
            # Don't convert if it's a table reference like gmd.themes
            if schema.lower() in ['gmd', 'mdm', 'mdmappl', 'predmd'] and func.lower() in ['themes', 'v_themes', 'theme_molecules', 'new_medicine_proposals']:
                return match.group(0)  # Return unchanged
            return f'{schema}${func}('
            
        sql = re.sub(pattern, replace_func, sql)
        
        return sql

    def convert_user_context(self, sql: str) -> str:
        """Convert Oracle user context to PostgreSQL equivalent"""
        # Replace Oracle user context
        sql = re.sub(r'select\s+nvl\(txo_security\.get_userid,\s*user\)\s+into\s+v_userid\s+from\s+dual', 'v_userid := :ins_user', sql, flags=re.IGNORECASE)
        sql = re.sub(r'txo_util\.get_userid', ':ins_user', sql, flags=re.IGNORECASE)
        
        return sql

    def convert_numeric_validation(self, sql: str) -> str:
        """Convert Oracle numeric validation to PostgreSQL regex"""
        # Convert Oracle between 0 and 9 to PostgreSQL regex
        pattern = r'SUBSTRING\(([^,]+)\s+FROM\s+(\d+)\s+FOR\s+1\)\s+not\s+between\s+0\s+and\s+9'
        replacement = r'SUBSTRING(\1 FROM \2 FOR 1) !~ \'^[0-9]$\''
        sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        
        return sql

    def convert_date_functions(self, sql: str) -> str:
        """Convert Oracle date functions to PostgreSQL"""
        # Convert trunc(date) to date(date) for date comparison
        sql = re.sub(r'DATE_TRUNC\(([^)]+)\)', r'DATE(\1)', sql, flags=re.IGNORECASE)
        
        return sql

    def convert_cast_operations(self, sql: str) -> str:
        """Convert Oracle CAST operations to PostgreSQL format"""
        # Convert molecule_id casting
        sql = re.sub(r'molecule_id\s*=\s*CAST\(NULLIF\(CAST\(:new_molecule_id\s+AS\s+TEXT\),\s*\'\'?\)\s+AS\s+NUMERIC\)', 
                    'molecule_id = CAST(NULLIF(CAST(:new_molecule_id AS TEXT),\'\') AS NUMERIC)', sql, flags=re.IGNORECASE)
        
        return sql

    def format_postgresql_sql(self, sql: str) -> str:
        """Format PostgreSQL SQL for better readability"""
        # Add line breaks for major keywords
        sql = re.sub(r'\s+(IF|THEN|ELSE|END IF|BEGIN|EXCEPTION|SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|AND|OR)\s+', r'\n\1 ', sql, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        sql = re.sub(r'\n\s*\n', '\n', sql)
        sql = re.sub(r'[ \t]+', ' ', sql)
        
        return sql.strip()

    def wrap_in_postgresql_block(self, sql: str, variables: str) -> str:
        """Wrap the converted SQL in a PostgreSQL DO block with proper variable declarations"""
        # Clean up the SQL
        sql = re.sub(r'^declare\s+', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^begin\s+', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'end;\s*$', '', sql, flags=re.IGNORECASE)
        
        # Format the final PostgreSQL block
        formatted_sql = f"DO $$ DECLARE {variables}BEGIN {sql} END $$;"
        
        return self.format_postgresql_sql(formatted_sql)

    def extract_variables_and_constants(self, sql_content: str) -> str:
        """Extract variable declarations and constants from Oracle trigger"""
        variables = []
        
        # Look for variable declarations between DECLARE and BEGIN
        declare_match = re.search(r'declare\s+(.*?)\s+begin', sql_content, re.IGNORECASE | re.DOTALL)
        if declare_match:
            var_section = declare_match.group(1)
            
            # Extract individual variable declarations
            var_patterns = [
                r'v_\w+\s+[^;]+;',
                r'c_\w+\s+constant\s+[^;]+;',
                r'i1\s+RECORD;'
            ]
            
            for pattern in var_patterns:
                matches = re.findall(pattern, var_section, re.IGNORECASE)
                variables.extend(matches)
        
        # Convert Oracle variable declarations to PostgreSQL
        pg_variables = []
        for var in variables:
            if 'exception' not in var.lower():
                # Convert data types
                pg_var = self.convert_data_types(var)
                pg_variables.append(pg_var)
        
        # Add PostgreSQL-specific variables
        pg_variables.append('v_userid varchar(30);')
        
        return ' '.join(pg_variables)

    def extract_sections(self, sql_content: str) -> Dict[str, str]:
        """Extract INSERT, UPDATE, DELETE sections from Oracle trigger"""
        sections = {
            'on_insert': '',
            'on_update': '',
            'on_delete': ''
        }
        
        # Find the main logic sections
        insert_pattern = r'if\s*\(inserting\)\s*then(.*?)(?=elsif\s*\(updating\)|elsif\s*\(deleting\)|$)'
        update_pattern = r'elsif\s*\(updating\)\s*then(.*?)(?=elsif\s*\(deleting\)|$)'
        delete_pattern = r'elsif\s*\(deleting\)\s*then(.*?)(?=end\s*if|$)'
        
        insert_match = re.search(insert_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        if insert_match:
            sections['on_insert'] = insert_match.group(1).strip()
            
        update_match = re.search(update_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        if update_match:
            sections['on_update'] = update_match.group(1).strip()
            
        delete_match = re.search(delete_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        if delete_match:
            sections['on_delete'] = delete_match.group(1).strip()
        
        return sections

    def convert_oracle_to_postgresql(self, oracle_sql: str, variables: str) -> str:
        """Main conversion method"""
        sql = oracle_sql
        
        # Apply all conversions
        sql = self.clean_sql_content(sql)
        sql = self.convert_data_types(sql)
        sql = self.convert_functions(sql)
        sql = self.convert_substr_to_substring(sql)
        sql = self.convert_sequence_generation(sql)
        sql = self.convert_exception_handling(sql)
        sql = self.convert_variable_references(sql)
        sql = self.convert_function_calls(sql)
        sql = self.convert_user_context(sql)
        sql = self.convert_numeric_validation(sql)
        sql = self.convert_date_functions(sql)
        sql = self.convert_cast_operations(sql)
        
        # Wrap in PostgreSQL DO block
        sql = self.wrap_in_postgresql_block(sql, variables)
        
        return sql

    def convert_trigger_file(self, input_file: str, output_file: str, verbose: bool = False):
        """Convert Oracle trigger file to PostgreSQL JSON format"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                oracle_content = f.read()
            
            # Check if file is empty
            if not oracle_content.strip():
                print(f"Warning: {input_file} is empty, skipping...")
                return False
            
            # Extract variables and constants
            variables = self.extract_variables_and_constants(oracle_content)
            
            # Extract sections
            sections = self.extract_sections(oracle_content)
            
            # Get common code (everything before the first if (inserting))
            common_code_match = re.search(r'begin\s+(.*?)if\s*\(inserting\)', oracle_content, re.IGNORECASE | re.DOTALL)
            common_code = ""
            if common_code_match:
                common_code = common_code_match.group(1).strip()
            
            # Convert each section
            json_structure = {}
            
            for operation, sql_content in sections.items():
                if sql_content.strip():
                    # Combine common code with section-specific code
                    full_sql = common_code + " " + sql_content
                    converted_sql = self.convert_oracle_to_postgresql(full_sql, variables)
                    
                    json_structure[operation] = [
                        {
                            "type": "sql",
                            "sql": converted_sql
                        }
                    ]
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write JSON output
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_structure, f, indent=4)
            
            print(f"✅ Successfully converted {input_file} → {output_file}")
            return True
            
        except FileNotFoundError:
            print(f"❌ Error: Input file {input_file} not found")
            return False
        except Exception as e:
            print(f"❌ Error converting {input_file}: {str(e)}")
            if verbose:
                import traceback
                traceback.print_exc()
            return False

    def process_folder(self, oracle_folder: str, json_folder: str, verbose: bool = False):
        """Process all SQL files in the oracle folder"""
        oracle_path = Path(oracle_folder)
        json_path = Path(json_folder)
        
        if not oracle_path.exists():
            print(f"❌ Oracle folder '{oracle_folder}' does not exist")
            return
        
        # Create json folder if it doesn't exist
        json_path.mkdir(exist_ok=True)
        
        # Find all .sql files in oracle folder
        sql_files = list(oracle_path.glob('*.sql'))
        
        if not sql_files:
            print(f"⚠️  No .sql files found in '{oracle_folder}'")
            return
        
        print(f"🔍 Found {len(sql_files)} SQL file(s) in '{oracle_folder}'")
        
        success_count = 0
        for sql_file in sql_files:
            # Generate output filename
            output_filename = sql_file.stem + '.json'
            output_path = json_path / output_filename
            
            if verbose:
                print(f"Processing: {sql_file} → {output_path}")
            
            # Convert the file
            if self.convert_trigger_file(str(sql_file), str(output_path), verbose):
                success_count += 1
        
        print(f"\n🎉 Conversion complete: {success_count}/{len(sql_files)} files converted successfully")


def main():
    parser = argparse.ArgumentParser(description='Convert Oracle PL/SQL trigger to PostgreSQL JSON format')
    
    # Add mode selection
    parser.add_argument('--mode', choices=['file', 'folder'], default='folder',
                       help='Processing mode: single file or entire folder (default: folder)')
    
    # File mode arguments
    parser.add_argument('input_file', nargs='?', help='Input Oracle SQL trigger file (for file mode)')
    parser.add_argument('-o', '--output', help='Output JSON file (for file mode)')
    
    # Folder mode arguments  
    parser.add_argument('--oracle-folder', default='orcale', 
                       help='Oracle SQL files folder (default: orcale)')
    parser.add_argument('--json-folder', default='json',
                       help='Output JSON files folder (default: json)')
    
    # Common arguments
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = OracleToPostgreSQLConverter()
    
    if args.mode == 'file':
        # File mode - convert single file
        if not args.input_file:
            print("❌ Error: input_file is required for file mode")
            parser.print_help()
            return
        
        output_file = args.output or args.input_file.replace('.sql', '.json')
        converter.convert_trigger_file(args.input_file, output_file, args.verbose)
        
    else:
        # Folder mode - convert all files in oracle folder
        print(f"🚀 Starting folder processing...")
        print(f"📁 Oracle folder: {args.oracle_folder}")
        print(f"📁 JSON folder: {args.json_folder}")
        converter.process_folder(args.oracle_folder, args.json_folder, args.verbose)


if __name__ == "__main__":
    main()
