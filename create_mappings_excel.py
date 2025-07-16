
#!/usr/bin/env python3
"""
Script to create Excel file with Oracle to PostgreSQL mappings
"""

import pandas as pd
import re

def create_mappings_excel():
    """Create Excel file with three sheets: data_type_mappings, function_mappings, exception_mappings"""
    
    # Data type mappings - Oracle to PostgreSQL
    data_type_mappings = {
        'Oracle_Type': [
            'varchar2', 'nvarchar2', 'nchar', 'long', 'rawid', 'urowid',
            'number', 'float', 'binary_float', 'binary_double', 'pls_integer', 
            'simple_integer', 'binary_integer', 'positive', 'natural', 'signtype',
            'smallint', 'integer', 'int', 'decimal', 'numeric', 'real',
            'date', 'timestamp with time zone', 'timestamp with local time zone',
            'interval year to month', 'interval day to second',
            'clob', 'nclob', 'blob', 'bfile', 'xmltype', 'sdo_geometry',
            'varray', 'nested table', 'raw', 'long raw', 'rowid',
            'naturaln', 'positiven', 'simple_double', 'simple_float'
        ],
        'PostgreSQL_Type': [
            'varchar', 'varchar', 'char', 'text', 'varchar', 'varchar',
            'numeric', 'real', 'real', 'double precision', 'integer',
            'integer', 'integer', 'integer', 'integer', 'smallint',
            'smallint', 'integer', 'integer', 'decimal', 'numeric', 'real',
            'date', 'timestamp with time zone', 'timestamp',
            'interval', 'interval',
            'text', 'text', 'bytea', 'text', 'xml', 'geometry',
            'text[]', 'text[]', 'bytea', 'bytea', 'varchar(18)',
            'integer', 'integer', 'double precision', 'real'
        ]
    }
    
    # Function mappings - Oracle to PostgreSQL
    function_mappings = {
        'Oracle_Function': [
            'substr', 'instr', 'length', 'trim', 'ltrim', 'rtrim', 'upper', 'lower',
            'initcap', 'replace', 'translate', 'lpad', 'rpad', 'chr', 'ascii',
            'concat', 'reverse', 'soundex', 'nvl', 'nvl2', 'nullif', 'decode',
            'sysdate', 'current_date', 'current_timestamp', 'trunc', 'round',
            'to_date', 'to_char', 'extract', 'add_months', 'months_between',
            'next_day', 'last_day', 'dateadd', 'datediff', 'abs', 'ceil',
            'floor', 'mod', 'power', 'sqrt', 'exp', 'ln', 'log', 'sin', 'cos',
            'tan', 'asin', 'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh',
            'sign', 'to_number', 'count', 'sum', 'avg', 'min', 'max', 'stddev',
            'variance', 'median', 'listagg', 'wm_concat', 'row_number', 'rank',
            'dense_rank', 'first_value', 'last_value', 'lead', 'lag', 'ntile',
            'percent_rank', 'cume_dist', 'cast', 'convert', 'hextoraw', 'rawtohex',
            'user', 'uid', 'userenv', 'sys_context', 'sys_guid', 'sessiontimezone',
            'dbtimezone', 'nextval', 'currval', 'empty_clob', 'empty_blob',
            'dbms_lob.getlength', 'dbms_lob.substr', 'vsize', 'dump', 'greatest',
            'least', 'regexp_like', 'regexp_replace', 'regexp_substr', 'regexp_instr',
            'regexp_count', 'connect_by_root', 'sys_connect_by_path', 'level',
            'xmltype', 'extractvalue', 'xmlserialize', 'xmlquery', 'json_value',
            'json_query', 'json_table', 'is_json', 'sqlcode', 'sqlerrm'
        ],
        'PostgreSQL_Function': [
            'SUBSTRING', 'POSITION', 'LENGTH', 'TRIM', 'LTRIM', 'RTRIM', 'UPPER', 'LOWER',
            'INITCAP', 'REPLACE', 'TRANSLATE', 'LPAD', 'RPAD', 'CHR', 'ASCII',
            'CONCAT', 'REVERSE', 'SOUNDEX', 'COALESCE', 'CASE WHEN', 'NULLIF', 'CASE',
            'CURRENT_TIMESTAMP', 'CURRENT_DATE', 'CURRENT_TIMESTAMP', 'DATE_TRUNC', 'DATE_TRUNC',
            'TO_TIMESTAMP', 'TO_CHAR', 'EXTRACT', 'ADD_MONTHS', 'MONTHS_BETWEEN',
            'NEXT_DAY', 'LAST_DAY', 'DATE_ADD', 'DATE_DIFF', 'ABS', 'CEIL',
            'FLOOR', 'MOD', 'POWER', 'SQRT', 'EXP', 'LN', 'LOG', 'SIN', 'COS',
            'TAN', 'ASIN', 'ACOS', 'ATAN', 'ATAN2', 'SINH', 'COSH', 'TANH',
            'SIGN', 'CAST', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'STDDEV',
            'VARIANCE', 'PERCENTILE_CONT(0.5)', 'STRING_AGG', 'STRING_AGG', 'ROW_NUMBER', 'RANK',
            'DENSE_RANK', 'FIRST_VALUE', 'LAST_VALUE', 'LEAD', 'LAG', 'NTILE',
            'PERCENT_RANK', 'CUME_DIST', 'CAST', 'CAST', 'DECODE', 'ENCODE',
            'current_user', 'current_user', 'current_setting', 'current_setting', 'gen_random_uuid', 'current_setting(\'timezone\')',
            'current_setting(\'timezone\')', 'nextval', 'currval', 'NULL', 'NULL',
            'LENGTH', 'SUBSTRING', 'LENGTH', 'ENCODE', 'GREATEST',
            'LEAST', '~', 'REGEXP_REPLACE', 'SUBSTRING', 'POSITION',
            'REGEXP_COUNT', '', '', '',
            'XMLPARSE', 'XPATH', 'XMLSERIALIZE', 'XPATH', 'JSON_EXTRACT_PATH_TEXT',
            'JSON_EXTRACT_PATH', 'JSON_TO_RECORDSET', 'JSON_VALID', 'SQLSTATE', 'SQLERRM'
        ]
    }
    
    # Exception mappings - Oracle exceptions to PostgreSQL messages
    exception_mappings = {
        'Oracle_Exception': [
            'invalid_theme_no', 'delete_no_more_possible', 'theme_no_only_insert',
            'description_too_long', 'theme_desc_proposal_too_long', 'theme_desc_alt_too_long',
            'theme_no_cannot_be_inserted', 'onlyoneofficialchangeperday', 'insertsmustbeofficial',
            'themedescriptionmandatory', 'theme_desc_not_unique', 'in_prep_not_portf_proj',
            'in_prep_not_closed', 'invalid_molecule_id', 'sec_mol_list_not_empty',
            'admin_update_only', 'portf_proj_mol_cre_err', 'debugging',
            'err_map_exists', 'err_molec_id_missing', 'err_no_portf_molecule_left',
            'err_upd_inv_map', 'err_ins_inv_map', 'err_inv_mol_sequence', 'update_upd',
            'err_upd', 'err_ins', 'err_ctry_chg', 'err_not_allowed_to_invalidate',
            'test_err', 'err_ins_legal_addr', 'no_data_found', 'too_many_rows',
            'dup_val_on_index', 'value_error', 'invalid_number', 'zero_divide',
            'invalid_cursor', 'cursor_already_open', 'not_logged_on', 'login_denied',
            'program_error', 'storage_error', 'timeout_on_resource', 'invalid_rowid',
            'rowtype_mismatch', 'self_is_null', 'subscript_outside_limit', 'subscript_beyond_count',
            'access_into_null', 'collection_is_null', 'others'
        ],
        'PostgreSQL_Message': [
            'This is not a valid Theme No',
            'Theme cannot be deleted when the deletion is not on the same day, on which the Theme has been inserted',
            'Theme No cannot be updated',
            'The automatically generated Theme Description is too long',
            'The automatically generated Short Description Proposal is too long',
            'The automatically generated Downstream Theme Description is too long',
            'This Theme No already exists',
            'Official Change for this Theme No and Day already exists',
            'New Themes can only be inserted by Official Changes',
            'If Pharma Rx Portfolio Project is set to "No", then the Theme Description must be filled',
            'This Theme Description already exists',
            'MDM_V_THEMES_IOF: In-prep theme must be portfolio project',
            'MDM_V_THEMES_IOF: In-prep status validation failed',
            'This is not a valid Molecule ID',
            'MDM_V_THEMES_IOF: Secondary molecule list not empty',
            'MDM_V_THEMES_IOF: Admin access required for this operation',
            'MDM_V_THEMES_IOF: Portfolio project molecule creation error',
            'Debug in Themes IOF standard',
            'MDM_THEME_MOLECULE_MAP_IOF: Mapping already exists',
            'MDM_THEME_MOLECULE_MAP_IOF: Molecule ID is missing',
            'MDM_THEME_MOLECULE_MAP_IOF: No portfolio molecule left',
            'MDM_THEME_MOLECULE_MAP_IOF: Invalid mapping update',
            'MDM_THEME_MOLECULE_MAP_IOF: Invalid mapping insert',
            'MDM_THEME_MOLECULE_MAP_IOF: Invalid molecule sequence',
            'MDM_THEME_MOLECULE_MAP_IOF: Update error',
            'The address cannot be updated because the Address type is different',
            'An address already exists for this Company and Address type. To modify the existing address, please use the Update button',
            'The company country modified but not the Valid From Date. Please update also the Valid From Date',
            'It is not allowed to invalidate/delete this type of address',
            'Test error with debug information',
            'The legal address cannot be inserted for this type of company',
            'No data found',
            'Too many rows returned',
            'Duplicate value on index',
            'Numeric or value error',
            'Invalid number',
            'Division by zero',
            'Invalid cursor',
            'Cursor already open',
            'Not logged on',
            'Login denied',
            'Program error',
            'Storage error',
            'Timeout on resource',
            'Invalid ROWID',
            'Row type mismatch',
            'Self is null',
            'Subscript outside limit',
            'Subscript beyond count',
            'Access into null',
            'Collection is null',
            'Unknown error occurred'
        ]
    }
    
    # Create DataFrames
    df_data_types = pd.DataFrame(data_type_mappings)
    df_functions = pd.DataFrame(function_mappings)
    df_exceptions = pd.DataFrame(exception_mappings)
    
    # Create Excel file with multiple sheets
    excel_filename = 'oracle_postgresql_mappings.xlsx'
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df_data_types.to_excel(writer, sheet_name='data_type_mappings', index=False)
        df_functions.to_excel(writer, sheet_name='function_mappings', index=False)
        df_exceptions.to_excel(writer, sheet_name='exception_mappings', index=False)
    
    print(f"✅ Created Excel file: {excel_filename}")
    print(f"📊 Data Type Mappings: {len(df_data_types)} rows")
    print(f"🔧 Function Mappings: {len(df_functions)} rows")
    print(f"⚠️  Exception Mappings: {len(df_exceptions)} rows")
    
    return excel_filename

if __name__ == "__main__":
    create_mappings_excel()
