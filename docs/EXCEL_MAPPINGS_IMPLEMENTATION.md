# Excel Mappings Implementation

## Overview

The `FORMATPostsqlTriggerAnalyzer.py` has been updated to load function, type, and exception mappings from the `utilities/oracle_postgresql_mappings.xlsx` file instead of using hardcoded mappings.

## Changes Made

### 1. Added Excel Reading Dependencies

- Added `pandas>=1.5.0` and `openpyxl>=3.0.0` to `requirements.txt`
- Imported `pandas` in `FORMATPostsqlTriggerAnalyzer.py`

### 2. Updated FORMATPostsqlTriggerAnalyzer Class

#### New Methods Added:

- `_load_function_mappings()`: Loads function mappings from Excel sheet "function_mappings"
- `_load_type_mappings()`: Loads type mappings from Excel sheet "data_type_mappings"  
- `_load_exception_mappings()`: Loads exception mappings from Excel sheet "exception_mappings"
- `_get_default_function_mappings()`: Provides fallback function mappings
- `_get_default_type_mappings()`: Provides fallback type mappings

#### Updated Methods:

- `_convert_data_type()`: Now uses `self.type_mapping` instead of hardcoded dictionary
- `_render_function_call()`: Now uses `self.func_mapping` instead of hardcoded dictionary
- `_convert_sql_statement()`: Now applies function mappings dynamically from Excel
- `_convert_condition()`: Now applies function mappings dynamically from Excel
- `_convert_raise_statement()`: Now uses `self.exception_mapping` instead of hardcoded dictionary

### 3. Excel File Structure

The Excel file `utilities/oracle_postgresql_mappings.xlsx` contains three sheets:

#### function_mappings
- Columns: `Oracle_Function`, `PostgreSQL_Function`
- Contains 111 function mappings

#### data_type_mappings  
- Columns: `Oracle_Type`, `PostgreSQL_Type`
- Contains 42 type mappings

#### exception_mappings
- Columns: `Oracle_Exception`, `PostgreSQL_Message`
- Contains 52 exception mappings

## Benefits

1. **Maintainability**: Mappings can be updated in Excel without code changes
2. **Flexibility**: Easy to add new mappings or modify existing ones
3. **Consistency**: All mappings are centralized in one Excel file
4. **Fallback Support**: Default mappings are used if Excel file is not available
5. **Error Handling**: Graceful fallback with warning messages if Excel reading fails

## Usage

The mappings are automatically loaded when a `FORMATPostsqlTriggerAnalyzer` instance is created:

```python
analyzer = FORMATPostsqlTriggerAnalyzer(json_data)
# Mappings are automatically loaded from Excel file
```

## Error Handling

- If Excel file is not found, default mappings are used with a warning
- If Excel reading fails, default mappings are used with a warning
- If specific sheets or columns are missing, appropriate fallbacks are used

## Testing

The implementation was tested with:
- Excel file reading functionality
- Mapping loading verification
- Data type conversion examples
- Function mapping examples

All tests passed successfully, confirming that:
- 111 function mappings were loaded
- 42 type mappings were loaded  
- 52 exception mappings were loaded
