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
        # Data type mappings - Oracle to PostgreSQL
        self.data_type_mappings = {
            # Character data types
            r'\bvarchar2\b': 'varchar',
            r'\bnvarchar2\b': 'varchar',
            r'\bnchar\b': 'char',
            r'\blong\b': 'text',
            r'\brawid\b': 'varchar',
            r'\burowid\b': 'varchar',
            
            # Numeric data types
            r'\bnumber\b': 'numeric',
            r'\bfloat\b': 'real',
            r'\bbinary_float\b': 'real',
            r'\bbinary_double\b': 'double precision',
            r'\bpls_integer\b': 'integer',
            r'\bsimple_integer\b': 'integer',
            r'\bbinary_integer\b': 'integer',
            r'\bpositive\b': 'integer',
            r'\bnatural\b': 'integer',
            r'\bsigntype\b': 'smallint',
            r'\bsmallint\b': 'smallint',
            r'\binteger\b': 'integer', 
            r'\bint\b': 'integer',
            r'\bdecimal\b': 'decimal',
            r'\bnumeric\b': 'numeric',
            r'\breal\b': 'real',
            
            # Date and time data types
            r'\bdate\b': 'timestamp',
            r'\btimestamp\s+with\s+time\s+zone\b': 'timestamp with time zone',
            r'\btimestamp\s+with\s+local\s+time\s+zone\b': 'timestamp',
            r'\binterval\s+year\s+to\s+month\b': 'interval',
            r'\binterval\s+day\s+to\s+second\b': 'interval',
            
            # Large object data types
            r'\bclob\b': 'text',
            r'\bnclob\b': 'text',
            r'\bblob\b': 'bytea',
            r'\bbfile\b': 'text',
            
            # Boolean and JSON (Oracle 12c+) - no conversion needed
            
            # XML data types  
            r'\bxmltype\b': 'xml',
            
            # Spatial data types
            r'\bsdo_geometry\b': 'geometry',
            
            # Collection data types (convert to arrays or JSON)
            r'\bvarray\b': 'text[]',
            r'\bnested\s+table\b': 'text[]',
            
            # Raw data types
            r'\braw\b': 'bytea',
            r'\blong\s+raw\b': 'bytea',
            
            # Rowid data types
            r'\browid\b': 'varchar(18)',
            
            # Oracle-specific numeric subtypes
            r'\bnaturaln\b': 'integer',
            r'\bpositiven\b': 'integer',
            r'\bsimple_double\b': 'double precision',
            r'\bsimple_float\b': 'real',
        }
        
        # Function mappings - Oracle to PostgreSQL
        self.function_mappings = {
            # String/Character functions
            r'\bsubstr\b': 'SUBSTRING',
            r'\binstr\b': 'POSITION',
            r'\blength\b': 'LENGTH',
            r'\btrim\b': 'TRIM',
            r'\bltrim\b': 'LTRIM',
            r'\brtrim\b': 'RTRIM',
            r'\bupper\b': 'UPPER',
            r'\blower\b': 'LOWER',
            r'\binitcap\b': 'INITCAP',
            r'\breplace\b': 'REPLACE',
            r'\btranslate\b': 'TRANSLATE',
            r'\blpad\b': 'LPAD',
            r'\brpad\b': 'RPAD',
            r'\bchr\b': 'CHR',
            r'\bascii\b': 'ASCII',
            r'\bconcat\b': 'CONCAT',
            r'\breverse\b': 'REVERSE',
            r'\bsoundex\b': 'SOUNDEX',
            
            # Null handling functions
            r'\bnvl\b': 'COALESCE',
            r'\bnvl2\b': 'CASE WHEN',  # Needs special handling
            r'\bnullif\b': 'NULLIF',
            r'\bdecode\b': 'CASE',  # Needs special handling
            
            # Date/Time functions
            r'\bsysdate\b': 'CURRENT_TIMESTAMP',
            r'\bcurrent_date\b': 'CURRENT_DATE',
            r'\bcurrent_timestamp\b': 'CURRENT_TIMESTAMP',
            r'\btrunc\b': 'DATE_TRUNC',  # For dates - context dependent
            r'\bround\b': 'DATE_TRUNC',  # For dates - context dependent
            r'\bto_date\b': 'TO_TIMESTAMP',
            r'\bto_char\b': 'TO_CHAR',
            r'\bextract\b': 'EXTRACT',
            r'\badd_months\b': 'ADD_MONTHS',  # Custom function needed
            r'\bmonths_between\b': 'MONTHS_BETWEEN',  # Custom function needed
            r'\bnext_day\b': 'NEXT_DAY',  # Custom function needed
            r'\blast_day\b': 'LAST_DAY',  # Custom function needed
            r'\bdateadd\b': 'DATE_ADD',
            r'\bdatediff\b': 'DATE_DIFF',
            
            # Numeric functions
            r'\babs\b': 'ABS',
            r'\bceil\b': 'CEIL',
            r'\bfloor\b': 'FLOOR',
            r'\bmod\b': 'MOD',
            r'\bpower\b': 'POWER',
            r'\bsqrt\b': 'SQRT',
            r'\bexp\b': 'EXP',
            r'\bln\b': 'LN',
            r'\blog\b': 'LOG',
            r'\bsin\b': 'SIN',
            r'\bcos\b': 'COS',
            r'\btan\b': 'TAN',
            r'\basin\b': 'ASIN',
            r'\bacos\b': 'ACOS',
            r'\batan\b': 'ATAN',
            r'\batan2\b': 'ATAN2',
            r'\bsinh\b': 'SINH',
            r'\bcosh\b': 'COSH',
            r'\btanh\b': 'TANH',
            r'\bsign\b': 'SIGN',
            r'\bto_number\b': 'CAST',
            
            # Aggregate functions
            r'\bcount\b': 'COUNT',
            r'\bsum\b': 'SUM',
            r'\bavg\b': 'AVG',
            r'\bmin\b': 'MIN',
            r'\bmax\b': 'MAX',
            r'\bstddev\b': 'STDDEV',
            r'\bvariance\b': 'VARIANCE',
            r'\bmedian\b': 'PERCENTILE_CONT(0.5)',
            r'\blistagg\b': 'STRING_AGG',
            r'\bwm_concat\b': 'STRING_AGG',
            
            # Analytical functions
            r'\brow_number\b': 'ROW_NUMBER',
            r'\brank\b': 'RANK',
            r'\bdense_rank\b': 'DENSE_RANK',
            r'\bfirst_value\b': 'FIRST_VALUE',
            r'\blast_value\b': 'LAST_VALUE',
            r'\blead\b': 'LEAD',
            r'\blag\b': 'LAG',
            r'\bntile\b': 'NTILE',
            r'\bpercent_rank\b': 'PERCENT_RANK',
            r'\bcume_dist\b': 'CUME_DIST',
            
            # Conversion functions
            r'\bcast\b': 'CAST',
            r'\bconvert\b': 'CAST',
            r'\bhextoraw\b': 'DECODE',
            r'\brawtohex\b': 'ENCODE',
            
            # System functions
            r'\buser\b': 'current_user',
            r'\buid\b': 'current_user',
            r'\buserenv\b': 'current_setting',
            r'\bsys_context\b': 'current_setting',
            r'\bsys_guid\b': 'gen_random_uuid',
            r'\bsessiontimezone\b': 'current_setting(\'timezone\')',
            r'\bdbtimezone\b': 'current_setting(\'timezone\')',
            
            # Sequence functions (Oracle specific)
            r'\bnextval\b': 'nextval',
            r'\bcurrval\b': 'currval',
            
            # Large Object functions
            r'\bempty_clob\b': 'NULL',
            r'\bempty_blob\b': 'NULL',
            r'\bdbms_lob\.getlength\b': 'LENGTH',
            r'\bdbms_lob\.substr\b': 'SUBSTRING',
            
            # Utility functions
            r'\bvsize\b': 'LENGTH',
            r'\bdump\b': 'ENCODE',
            r'\bgreatest\b': 'GREATEST',
            r'\bleast\b': 'LEAST',
            
            # Regular expression functions (Oracle 10g+)
            r'\bregexp_like\b': '~',  # Needs conversion
            r'\bregexp_replace\b': 'REGEXP_REPLACE',
            r'\bregexp_substr\b': 'SUBSTRING',
            r'\bregexp_instr\b': 'POSITION',
            r'\bregexp_count\b': 'REGEXP_COUNT',
            
            # Hierarchical functions
            r'\bconnect_by_root\b': '',  # Requires CTE conversion
            r'\bsys_connect_by_path\b': '',  # Requires CTE conversion
            r'\blevel\b': '',  # Requires CTE conversion
            
            # XML functions
            r'\bxmltype\b': 'XMLPARSE',
            r'\bextractvalue\b': 'XPATH',
            r'\bxmlserialize\b': 'XMLSERIALIZE',
            r'\bxmlquery\b': 'XPATH',
            
            # JSON functions (Oracle 12c+)
            r'\bjson_value\b': 'JSON_EXTRACT_PATH_TEXT',
            r'\bjson_query\b': 'JSON_EXTRACT_PATH',
            r'\bjson_table\b': 'JSON_TO_RECORDSET',
            r'\bis_json\b': 'JSON_VALID',
            
            # Error handling
            r'\bsqlcode\b': 'SQLSTATE',
            r'\bsqlerrm\b': 'SQLERRM',
        }
        
        # Exception mappings - Oracle to PostgreSQL with comprehensive coverage
        self.exception_mappings = {
            # Trigger1.sql exceptions (Themes management)
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
            'in_prep_not_portf_proj': 'MDM_V_THEMES_IOF: In-prep theme must be portfolio project',
            'in_prep_not_closed': 'MDM_V_THEMES_IOF: In-prep status validation failed',
            'invalid_molecule_id': 'This is not a valid Molecule ID',
            'sec_mol_list_not_empty': 'MDM_V_THEMES_IOF: Secondary molecule list not empty',
            'admin_update_only': 'MDM_V_THEMES_IOF: Admin access required for this operation',
            'portf_proj_mol_cre_err': 'MDM_V_THEMES_IOF: Portfolio project molecule creation error',
            'debugging': 'Debug in Themes IOF standard',
            
            # Trigger2.sql exceptions (Theme molecule mapping)
            'err_map_exists': 'MDM_THEME_MOLECULE_MAP_IOF: Mapping already exists',
            'err_molec_id_missing': 'MDM_THEME_MOLECULE_MAP_IOF: Molecule ID is missing',
            'err_no_portf_molecule_left': 'MDM_THEME_MOLECULE_MAP_IOF: No portfolio molecule left',
            'err_upd_inv_map': 'MDM_THEME_MOLECULE_MAP_IOF: Invalid mapping update',
            'err_ins_inv_map': 'MDM_THEME_MOLECULE_MAP_IOF: Invalid mapping insert',
            'err_inv_mol_sequence': 'MDM_THEME_MOLECULE_MAP_IOF: Invalid molecule sequence',
            'update_upd': 'MDM_THEME_MOLECULE_MAP_IOF: Update error',
            
            # Trigger3.sql exceptions (Company addresses)
            'err_upd': 'The address cannot be updated because the Address type is different',
            'err_ins': 'An address already exists for this Company and Address type. To modify the existing address, please use the Update button',
            'err_ctry_chg': 'The company country modified but not the Valid From Date. Please update also the Valid From Date',
            'err_not_allowed_to_invalidate': 'It is not allowed to invalidate/delete this type of address',
            'test_err': 'Test error with debug information',
            'err_ins_legal_addr': 'The legal address cannot be inserted for this type of company',
            
            # Standard Oracle exceptions that might appear
            'no_data_found': 'No data found',
            'too_many_rows': 'Too many rows returned',
            'dup_val_on_index': 'Duplicate value on index',
            'value_error': 'Numeric or value error',
            'invalid_number': 'Invalid number',
            'zero_divide': 'Division by zero',
            'invalid_cursor': 'Invalid cursor',
            'cursor_already_open': 'Cursor already open',
            'not_logged_on': 'Not logged on',
            'login_denied': 'Login denied',
            'program_error': 'Program error',
            'storage_error': 'Storage error',
            'timeout_on_resource': 'Timeout on resource',
            'invalid_rowid': 'Invalid ROWID',
            'rowtype_mismatch': 'Row type mismatch',
            'self_is_null': 'Self is null',
            'subscript_outside_limit': 'Subscript outside limit',
            'subscript_beyond_count': 'Subscript beyond count',
            'access_into_null': 'Access into null',
            'collection_is_null': 'Collection is null',
            'others': 'Unknown error occurred'
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
        sql = re.sub(r'select\s+nvl\(txo_security\.get_userid,\s*user\)\s+into\s+v_userid\s+from\s+dual', 'v_userid:=:ins_user', sql, flags=re.IGNORECASE)
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

    def format_postgresql_sql(self, sql: str) -> str:
        """Format PostgreSQL SQL for better readability"""
        # First normalize whitespace and remove existing \n characters
        sql = re.sub(r'\\n', ' ', sql)  # Remove literal \n characters
        sql = re.sub(r'\s+', ' ', sql)  # Normalize whitespace
        sql = sql.strip()
        
        # Fix assignment operators before other formatting
        sql = re.sub(r'\s*:\s*=\s*', ':=', sql)
        
        # Fix specific formatting issues from parsing
        sql = re.sub(r'\bTHEN\s+CASE\b', 'CASE', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bTHEN\s+SELECT\b', 'SELECT', sql, flags=re.IGNORECASE)  
        sql = re.sub(r'\bTHEN\s+UPDATE\b', 'UPDATE', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bTHEN\s+INSERT\b', 'INSERT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bTHEN\s+DELETE\b', 'DELETE', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bTHEN\s+IF\b', 'IF', sql, flags=re.IGNORECASE)
        
        # Fix split END IF statements
        sql = re.sub(r'\bEND\s+IF\b', 'END IF', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bEND\s+CASE\b', 'END CASE', sql, flags=re.IGNORECASE)
        
        # Fix string escaping issues  
        sql = re.sub(r"\\'\\''", "''", sql)
        sql = re.sub(r"\\\\'", "'", sql)
        sql = re.sub(r"\\'\\", "''", sql)  # Additional pattern
        
        # Remove redundant THEN keywords at start of blocks
        sql = re.sub(r'^\s*THEN\s+', '', sql, flags=re.IGNORECASE | re.MULTILINE)
        sql = re.sub(r'\bBEGIN\s+THEN\s+', 'BEGIN ', sql, flags=re.IGNORECASE)
        
        # Fix missing THEN keywords in IF statements
        sql = re.sub(r'\bIF\s+([^;]+?)\s+SELECT\b', r'IF \1 THEN SELECT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bIF\s+([^;]+?)\s+UPDATE\b', r'IF \1 THEN UPDATE', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bIF\s+([^;]+?)\s+INSERT\b', r'IF \1 THEN INSERT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bIF\s+([^;]+?)\s+DELETE\b', r'IF \1 THEN DELETE', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bIF\s+([^;]+?)\s+CASE\b', r'IF \1 THEN CASE', sql, flags=re.IGNORECASE)
        
        # Fix missing THEN in WHEN clauses
        sql = re.sub(r'\bWHEN\s+([^;]+?)\s+UPDATE\b', r'WHEN \1 THEN UPDATE', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bWHEN\s+([^;]+?)\s+INSERT\b', r'WHEN \1 THEN INSERT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bWHEN\s+([^;]+?)\s+IF\b', r'WHEN \1 THEN IF', sql, flags=re.IGNORECASE)
        
        # Add proper line breaks for major SQL keywords
        keywords_with_breaks = [
            'BEGIN', 'END', 'IF', 'THEN', 'ELSE', 'ELSIF', 'END IF', 
            'CASE', 'WHEN', 'END CASE', 'SELECT', 'INSERT', 'UPDATE', 
            'DELETE', 'FROM', 'WHERE', 'AND', 'OR', 'EXCEPTION',
            'RAISE EXCEPTION', 'CALL', 'PERFORM'
        ]
        
        for keyword in keywords_with_breaks:
            # Add line break before keyword (with word boundaries)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            sql = re.sub(pattern, '\n' + keyword, sql, flags=re.IGNORECASE)
        
        # Special handling for specific patterns
        sql = re.sub(r';\s*IF', ';\nIF', sql, flags=re.IGNORECASE)
        sql = re.sub(r';\s*SELECT', ';\nSELECT', sql, flags=re.IGNORECASE)
        sql = re.sub(r';\s*UPDATE', ';\nUPDATE', sql, flags=re.IGNORECASE)
        sql = re.sub(r';\s*INSERT', ';\nINSERT', sql, flags=re.IGNORECASE)
        sql = re.sub(r';\s*CALL', ';\nCALL', sql, flags=re.IGNORECASE)
        
        # Clean up multiple line breaks
        sql = re.sub(r'\n\s*\n+', '\n', sql)
        sql = re.sub(r'^\n+', '', sql)
        
        # Add proper spacing around operators and keywords
        sql = re.sub(r'(?<!:)\s*=\s*', ' = ', sql)  # Don't match := assignment operators
        sql = re.sub(r'\s*<>\s*', ' <> ', sql)
        sql = re.sub(r'\s*,\s*', ', ', sql)
        
        return sql.strip()

    def convert_nvl_to_coalesce(self, sql: str) -> str:
        """Convert Oracle NVL to PostgreSQL COALESCE more accurately"""
        # Convert NVL(field, value) to COALESCE(field, value)
        pattern = r'\bNVL\s*\(\s*([^,]+),\s*([^)]+)\)'
        replacement = r'COALESCE(\1, \2)'
        sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        return sql

    def convert_cast_operations(self, sql: str) -> str:
        """Convert Oracle CAST operations to PostgreSQL format more accurately"""
        # Convert molecule_id comparisons to proper CAST with NULLIF pattern
        sql = re.sub(r'molecule_id\s*=\s*:new_molecule_id', 
                    'molecule_id = CAST(NULLIF(CAST(:new_molecule_id AS TEXT),\'\') AS NUMERIC)', 
                    sql, flags=re.IGNORECASE)
        
        # Convert variable references
        sql = re.sub(r':new\.(\w+)', r':new_\1', sql)
        sql = re.sub(r':old\.(\w+)', r':old_\1', sql)
        
        # Handle general CAST operations for numeric fields
        sql = re.sub(r'CAST\(:new_molecule_id\s+AS\s+TEXT\)', 'CAST(:new_molecule_id AS TEXT)', sql, flags=re.IGNORECASE)
        sql = re.sub(r'CAST\(:old_molecule_id\s+AS\s+TEXT\)', 'CAST(:old_molecule_id AS TEXT)', sql, flags=re.IGNORECASE)
        
        # Add proper NULLIF patterns for other numeric fields
        sql = re.sub(r':new_(\w*id)\b(?!\s*AS)', r'CAST(NULLIF(CAST(:new_\1 AS TEXT),\'\') AS NUMERIC)', sql)
        
        return sql

    def convert_oracle_specifics(self, sql: str) -> str:
        """Convert Oracle-specific constructs to PostgreSQL"""
        # Convert SYSDATE to CURRENT_TIMESTAMP
        sql = re.sub(r'\bSYSDATE\b', 'CURRENT_TIMESTAMP', sql, flags=re.IGNORECASE)
        
        # Convert Oracle package calls to PostgreSQL schema$function format
        sql = re.sub(r'(\w+)\.(\w+)\s*\(', r'\1$\2(', sql)
        
        # Convert exception handling
        sql = re.sub(r'RAISE\s+(\w+);', r"RAISE EXCEPTION 'MDM_THEME_MOLECULE_MAP_IOF: \1';", sql, flags=re.IGNORECASE)
        
        # Convert BEGIN...EXCEPTION...END blocks to simpler format
        sql = re.sub(r'BEGIN\s+(.*?)\s+EXCEPTION\s+WHEN\s+OTHERS\s+THEN\s+(.*?)\s+END;', 
                    r'BEGIN \1 EXCEPTION WHEN OTHERS THEN \2 END;', sql, flags=re.DOTALL | re.IGNORECASE)
        
        return sql

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
            
            # Extract individual variable declarations - improved pattern matching
            lines = var_section.split('\n')
            current_var = ""
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('--'):
                    continue
                    
                # Handle multi-line variable declarations
                current_var += " " + line
                
                if line.endswith(';'):
                    # Complete variable declaration
                    var_decl = current_var.strip()
                    if 'exception' not in var_decl.lower():
                        # Convert Oracle types to PostgreSQL
                        pg_var = self.convert_data_types(var_decl)
                        # Fix specific type conversions
                        pg_var = re.sub(r'PLS_INTEGER', 'INTEGER', pg_var, flags=re.IGNORECASE)
                        pg_var = re.sub(r'SIMPLE_INTEGER', 'INTEGER', pg_var, flags=re.IGNORECASE)
                        pg_var = re.sub(r'BOOLEAN\s*:=\s*FALSE', 'BOOLEAN:=FALSE', pg_var, flags=re.IGNORECASE)
                        
                        # Fix assignment operators in variable declarations 
                        pg_var = re.sub(r'\s*:\s*=\s*', ':=', pg_var)
                        
                        # Handle %TYPE properly - convert to appropriate PostgreSQL types
                        if '%type' in pg_var.lower():
                            pg_var = self._convert_type_references(pg_var)
                        
                        # Handle RECORD types for cursor variables
                        if 'i1 ' in pg_var and 'RECORD' not in pg_var:
                            pg_var = re.sub(r'i1\s+[^;]+;', 'i1 RECORD;', pg_var)
                        
                        # Clean up any double conversions
                        pg_var = re.sub(r'(\w+)\s+(\w+\.\w+)varchar\(30\)', r'\1 \2%type', pg_var, flags=re.IGNORECASE)
                        
                        variables.append(pg_var)
                    current_var = ""
        
        return ' '.join(variables)

    def _convert_type_references(self, var_declaration: str) -> str:
        """Convert Oracle %TYPE references to PostgreSQL equivalents"""
        
        # Common table.column%TYPE mappings to PostgreSQL types
        type_mappings = {
            'theme_no': 'VARCHAR(10)',
            'molecule_id': 'VARCHAR(10)', 
            'rg_no': 'VARCHAR(20)',
            'trademark_no': 'NUMERIC',
            'molecule_type_id': 'INTEGER',
            'pharmacological_type_id': 'INTEGER',
            'comparator_ind': 'VARCHAR(1)',
            'theme_desc_proposal': 'VARCHAR(500)',
            'manual_short_desc': 'VARCHAR(30)'
        }
        
        # Extract variable name and type reference
        type_pattern = r'(\w+)\s+(?:(\w+)\.)?(\w+)\.(\w+)%type'
        match = re.search(type_pattern, var_declaration, re.IGNORECASE)
        
        if match:
            var_name = match.group(1)
            schema = match.group(2) or 'gmd'
            table = match.group(3)
            column = match.group(4)
            
            # Try to map to a known PostgreSQL type
            mapped_type = type_mappings.get(column.lower())
            if mapped_type:
                return f'{var_name} {mapped_type};'
            else:
                # Keep the %TYPE reference but ensure proper schema prefix
                return f'{var_name} {schema}.{table}.{column}%type;'
        
        return var_declaration

    def convert_postgresql_specific(self, sql: str) -> str:
        """Convert to PostgreSQL-specific constructs"""
        # Convert certain SELECT statements to PERFORM for existence checks
        sql = re.sub(r'SELECT\s+COUNT\(\*\)\s+INTO\s+(\w+)\s+FROM\s+([^;]+);', 
                    r'SELECT COUNT(*) INTO \1 FROM \2;', 
                    sql, flags=re.IGNORECASE)
        
        # Convert Oracle dual table references
        sql = re.sub(r'FROM\s+dual\b', '', sql, flags=re.IGNORECASE)
        
        # Convert Oracle date functions
        sql = re.sub(r'TO_DATE\(([^,]+),\s*([^)]+)\)', r'TO_DATE(\1, \2)', sql, flags=re.IGNORECASE)
        
        # Improve schema references - add proper prefixes for common tables
        # Be more careful to avoid duplication
        schema_mappings = {
            r'\b(?<!\.)(v_theme_molecules)(?!\w)': 'gmd.v_theme_molecules_mrhub',
            r'\b(?<!\.)(theme_molecule_map)(?!\w)': 'gmd.theme_molecule_map', 
            r'\b(?<!\.)(themes)(?!\w)(?!\s*\.)': 'gmd.themes',
            r'\b(?<!\.)(v_themes)(?!\w)': 'gmd.v_themes',
            r'\b(?<!\.)(mdm_v_theme_status)(?!\w)': 'mdmappl.mdm_v_theme_status',
            r'\b(?<!\.)(mdm_v_disease_biology_areas)(?!\w)': 'mdmappl.mdm_v_disease_biology_areas',
            r'\b(?<!\.)(mdm_v_theme_molecule_map_mtn)(?!\w)': 'mdmappl.mdm_v_theme_molecule_map_mtn',
            r'\b(?<!\.)(mdm_v_new_medicine_proposals_mtn)(?!\w)': 'mdmappl.mdm_v_new_medicine_proposals_mtn',
            r'\b(?<!\.)(new_medicine_proposals)(?!\w)': 'predmd.new_medicine_proposals'
        }
        
        for pattern, replacement in schema_mappings.items():
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        
        # Convert count() to COUNT(*)
        sql = re.sub(r'\bcount\(\)\b', 'COUNT(*)', sql, flags=re.IGNORECASE)
        
        # Add proper column defaults for INSERT statements
        sql = self._add_audit_columns(sql)
        
        return sql

    def _add_audit_columns(self, sql: str) -> str:
        """Add audit columns (ins_user, ins_date, upd_user, upd_date) to INSERT/UPDATE statements"""
        
        # Add audit columns to INSERT statements if not present
        insert_pattern = r'INSERT\s+INTO\s+(\w+\.\w+)\s*\(\s*([^)]+)\s*\)\s*VALUES\s*\(\s*([^)]+)\s*\)'
        
        def add_audit_to_insert(match):
            table = match.group(1)
            columns = match.group(2).strip()
            values = match.group(3).strip()
            
            # Check if audit columns are already present
            if 'ins_user' not in columns.lower():
                columns += ', ins_user, ins_date'
                values += ', :ins_user, :ins_date'
            
            return f'INSERT INTO {table} ( {columns} ) VALUES ( {values} )'
        
        sql = re.sub(insert_pattern, add_audit_to_insert, sql, flags=re.IGNORECASE | re.DOTALL)
        
        # Add audit columns to UPDATE statements if not present
        update_pattern = r'UPDATE\s+(\w+\.\w+)\s+SET\s+([^W]+?)(?=\s+WHERE|\s*;|\s*$)'
        
        def add_audit_to_update(match):
            table = match.group(1)
            set_clause = match.group(2).strip()
            
            # Check if audit columns are already present
            if 'upd_user' not in set_clause.lower():
                if not set_clause.endswith(','):
                    set_clause += ','
                set_clause += ' upd_user = :upd_user, upd_date = :upd_date'
            
            return f'UPDATE {table} SET {set_clause}'
        
        sql = re.sub(update_pattern, add_audit_to_update, sql, flags=re.IGNORECASE | re.DOTALL)
        
        return sql

    def extract_sections(self, sql_content: str) -> Dict[str, str]:
        """Extract INSERT, UPDATE, DELETE sections from Oracle trigger"""
        sections = {
            'on_insert': '',
            'on_update': '',
            'on_delete': ''
        }
        
        # Clean up content for better parsing
        content = self.clean_sql_content(sql_content)
        
        # Use a simpler but more robust parsing approach
        self._parse_oracle_trigger(content, sections)
        
        return sections

    def _parse_oracle_trigger(self, content: str, sections: Dict[str, str]):
        """Parse Oracle trigger using a line-by-line approach to handle complex nested structures"""
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        if_stack = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            line_upper = line.upper()
            
            # Skip empty lines and comments
            if not line or line.startswith('--'):
                i += 1
                continue
            
            # Check for main conditional blocks
            if self._is_delete_start(line_upper):
                current_section = 'on_delete'
                current_content = []
                if_stack = ['DELETE']
                
            elif self._is_insert_start(line_upper):
                current_section = 'on_insert'
                current_content = []
                if_stack = ['INSERT']
                
            elif self._is_update_start(line_upper):
                current_section = 'on_update'
                current_content = []
                if_stack = ['UPDATE']
                
            elif self._is_insert_or_update_start(line_upper):
                # Special handling for shared IF INSERTING OR UPDATING block
                shared_content = self._extract_shared_block_manual(lines, i)
                self._parse_shared_insert_update_block(shared_content, sections)
                # Skip to after this block
                i = self._find_block_end(lines, i, 'IF', 'END IF') + 1
                continue
                
            elif current_section:
                # Add content to current section
                if line_upper.startswith('IF '):
                    if_stack.append('IF')
                elif line_upper.startswith('END IF') or line == 'END;':
                    if if_stack:
                        if_stack.pop()
                        if not if_stack:  # End of main block
                            sections[current_section] = '\n'.join(current_content)
                            current_section = None
                            current_content = []
                            i += 1
                            continue
                
                current_content.append(line)
            
            i += 1
        
        # Handle any remaining content
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)

    def _is_delete_start(self, line: str) -> bool:
        """Check if line starts a DELETE block"""
        return (line.startswith('IF DELETING') or 
                line.startswith('IF (DELETING)') or
                line.startswith('ELSIF (DELETING)') or
                line.startswith('ELSIF DELETING'))

    def _is_insert_start(self, line: str) -> bool:
        """Check if line starts an INSERT block"""
        return (line.startswith('IF (INSERTING)') or
                line.startswith('IF INSERTING') or
                line.startswith('ELSIF (INSERTING)') or
                line.startswith('ELSIF INSERTING')) and 'OR' not in line

    def _is_update_start(self, line: str) -> bool:
        """Check if line starts an UPDATE block"""
        return (line.startswith('IF (UPDATING)') or
                line.startswith('IF UPDATING') or
                line.startswith('ELSIF (UPDATING)') or
                line.startswith('ELSIF UPDATING')) and 'OR' not in line

    def _is_insert_or_update_start(self, line: str) -> bool:
        """Check if line starts an INSERT OR UPDATE shared block"""
        return ('INSERTING OR UPDATING' in line or 
                'UPDATING OR INSERTING' in line) and line.startswith('IF')

    def _extract_shared_block_manual(self, lines: List[str], start_idx: int) -> str:
        """Manually extract the complete shared IF INSERTING OR UPDATING block"""
        end_idx = self._find_block_end(lines, start_idx, 'IF', 'END IF')
        block_lines = lines[start_idx+1:end_idx]  # Skip the IF line itself
        return '\n'.join(line.strip() for line in block_lines if line.strip())

    def _find_block_end(self, lines: List[str], start_idx: int, start_keyword: str, end_keyword: str) -> int:
        """Find the matching end of a block by counting nested IF/END IF pairs"""
        nesting_level = 1
        i = start_idx + 1
        
        while i < len(lines) and nesting_level > 0:
            line = lines[i].strip().upper()
            
            if line.startswith(start_keyword + ' '):
                nesting_level += 1
            elif line.startswith(end_keyword) or line == 'END;':
                nesting_level -= 1
                
            i += 1
        
        return i - 1  # Return index of the END IF line

    def _parse_shared_insert_update_block(self, shared_content: str, sections: Dict[str, str]):
        """Parse the shared IF INSERTING OR UPDATING block to extract operation-specific logic"""
        
        lines = shared_content.split('\n')
        shared_logic = []
        insert_logic = []
        update_logic = []
        
        current_section = 'shared'
        nesting_level = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            line_upper = line.upper()
            
            if not line:
                i += 1
                continue
                
            # Check for nested IF INSERTING
            if line_upper.startswith('IF INSERTING') and 'OR' not in line_upper:
                current_section = 'insert'
                # Find the end of this nested block
                end_idx = self._find_nested_block_end(lines, i)
                insert_logic.extend(lines[i+1:end_idx])
                i = end_idx + 1
                current_section = 'shared'
                continue
                
            # Check for nested IF UPDATING  
            elif line_upper.startswith('IF UPDATING') and 'OR' not in line_upper:
                current_section = 'update'
                # Find the end of this nested block
                end_idx = self._find_nested_block_end(lines, i)
                update_logic.extend(lines[i+1:end_idx])
                i = end_idx + 1
                current_section = 'shared'
                continue
            
            # Add to shared logic if not in a nested block
            if current_section == 'shared':
                shared_logic.append(line)
            
            i += 1
        
        # Combine shared + specific logic
        shared_text = '\n'.join(shared_logic)
        insert_text = '\n'.join(insert_logic)
        update_text = '\n'.join(update_logic)
        
        # Combine with any existing logic and add shared parts
        if shared_text or insert_text:
            combined_insert = []
            if sections['on_insert']:
                combined_insert.append(sections['on_insert'])
            if shared_text:
                combined_insert.append(shared_text)
            if insert_text:
                combined_insert.append(insert_text)
            sections['on_insert'] = '\n'.join(combined_insert)
        
        if shared_text or update_text:
            combined_update = []
            if sections['on_update']:
                combined_update.append(sections['on_update'])
            if shared_text:
                combined_update.append(shared_text)
            if update_text:
                combined_update.append(update_text)
            sections['on_update'] = '\n'.join(combined_update)

    def _find_nested_block_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a nested IF block within shared content"""
        nesting_level = 1
        i = start_idx + 1
        
        while i < len(lines) and nesting_level > 0:
            line = lines[i].strip().upper()
            
            if line.startswith('IF '):
                nesting_level += 1
            elif line.startswith('END IF'):
                nesting_level -= 1
                
            i += 1
        
        return i - 1

    def convert_oracle_to_postgresql(self, oracle_sql: str, variables: str) -> str:
        """Main conversion method"""
        sql = oracle_sql
        
        # Apply all conversions in the correct order
        sql = self.clean_sql_content(sql)
        sql = self.convert_data_types(sql)
        sql = self.convert_nvl_to_coalesce(sql)
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
        sql = self.convert_oracle_specifics(sql)
        sql = self.convert_postgresql_specific(sql)
        
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
            
            # Extract sections (now includes common code handling)
            sections = self.extract_sections(oracle_content)
            
            # Convert each section
            json_structure = {}
            
            for operation, sql_content in sections.items():
                if sql_content.strip():
                    converted_sql = self.convert_oracle_to_postgresql(sql_content, variables)
                    
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