# Oracle SQL Trigger Analysis Tools

## Overview

This project provides comprehensive tools to convert Oracle SQL trigger files into enhanced JSON analysis format. The tools parse Oracle triggers and extract detailed information about their structure, declarations, data operations, and exception handling.

## Architecture

### Core Components

1. **`utilities/sql_analysis.py`** - Main SQL analysis tool
2. **`utilities/enhanced_sql_analyzer.py`** - Enhanced version with improved parsing
3. **`requirements.txt`** - Dependencies for SQL parsing libraries

### Key Features

- **Trigger Metadata Extraction**: Timing, events, table names, sections
- **Declaration Parsing**: Variables, constants, and exceptions
- **Data Operations Analysis**: SQL statements, control flow, assignments
- **Exception Handler Extraction**: Comprehensive error handling analysis
- **SQL Validation**: Integration with sqlparse and sqlglot
- **Enhanced JSON Output**: Structured format matching expected specifications

## Input/Output Structure

### Input Files
- **Source**: `files/oracle/*.sql` - Oracle trigger SQL files
- **Expected**: `files/expected_ana_json/*_enhanced_analysis.json` - Reference outputs

### Output Files
- **Generated**: `files/sql_json/*_enhanced_analysis.json` - Basic analysis
- **Enhanced**: `files/sql_json/*_enhanced_analysis_v2.json` - Improved analysis

## JSON Output Format

The enhanced JSON format includes:

```json
{
  "trigger_metadata": {
    "trigger_name": "trigger1",
    "timing": "BEFORE|AFTER|INSTEAD OF",
    "events": ["INSERT", "UPDATE", "DELETE"],
    "table_name": "themes",
    "has_declare_section": true,
    "has_begin_section": true,
    "has_exception_section": true
  },
  "declarations": {
    "variables": [
      {
        "name": "v_counter",
        "data_type": "pls_integer",
        "default_value": null
      }
    ],
    "constants": [
      {
        "name": "c_molecule_type_id",
        "data_type": "v_molecule_types.molecule_type_id%type",
        "value": "99"
      }
    ],
    "exceptions": [
      {
        "name": "invalid_theme_no",
        "type": "user_defined"
      }
    ]
  },
  "data_operations": [
    {
      "id": "code_1",
      "sql": "select nvl(txo_security.get_userid, user) into v_userid from dual;",
      "type": "select_statements"
    }
  ],
  "exception_handlers": [
    {
      "exception_name": "admin_update_only",
      "handler_code": "raise_application_error(-20115, 'MDM_V_THEMES_IOF');"
    }
  ]
}
```

### Data Operation Types

- **`select_statements`** - SELECT queries
- **`insert_statements`** - INSERT operations
- **`update_statements`** - UPDATE operations  
- **`delete_statements`** - DELETE operations
- **`if_else`** - IF-THEN-ELSE blocks
- **`case_statements`** - CASE blocks
- **`loop_statements`** - FOR/WHILE loops
- **`assignment`** - Variable assignments
- **`function_call`** - Procedure/function calls
- **`begin_block`** - BEGIN-END blocks

## Installation & Usage

### Prerequisites

```bash
pip install -r requirements.txt
```

Required libraries:
- `sqlparse>=0.4.4` - SQL parsing and validation
- `sqlglot>=19.0.0` - Advanced SQL processing

### Running the Analysis

#### Basic Analyzer
```bash
python utilities/sql_analysis.py
```

#### Enhanced Analyzer (Recommended)
```bash
python utilities/enhanced_sql_analyzer.py
```

### Output

The tools will:
1. Process all `.sql` files in `files/oracle/`
2. Generate enhanced JSON analysis files
3. Validate against expected outputs (if available)
4. Display progress and validation results

Example output:
```
Processing trigger1.sql with enhanced analyzer...
✓ Generated trigger1_enhanced_analysis_v2.json
Processing trigger2.sql with enhanced analyzer...
  Operation coverage: 142.9%
Processing trigger3.sql with enhanced analyzer...
✓ Generated trigger3_enhanced_analysis_v2.json
  Validation: Structure match: True
  Operation coverage: 100.0%
```

## Key Improvements Over Original Format

### 1. Unified Data Operations
- **Before**: Separate arrays for each SQL operation type
- **After**: Single `data_operations` array with typed entries

### 2. Enhanced Structure
- **Before**: Fragmented SQL snippets
- **After**: Complete logical blocks with proper categorization

### 3. Better Metadata
- **Before**: Basic trigger information
- **After**: Comprehensive metadata including table names and section detection

### 4. Improved Parsing
- **Before**: Simple regex patterns
- **After**: Context-aware parsing with SQL validation

## Advanced Features

### SQL Validation
The enhanced analyzer includes SQL validation using:
- **sqlparse** for basic syntax validation
- **sqlglot** for advanced SQL processing
- Custom Oracle-specific validation rules

### Error Handling
Comprehensive error handling with:
- Graceful degradation when libraries unavailable
- Detailed error reporting for debugging
- Fallback parsing strategies

### Performance Optimization
- Efficient regex patterns for large files
- Memory-conscious processing
- Parallel processing capabilities

## Validation & Quality Metrics

The enhanced analyzer provides validation metrics:

- **Structure Match**: JSON structure compatibility
- **Operation Coverage**: Percentage of operations captured vs expected
- **Data Quality**: Various quality indicators

Example validation output:
```json
{
  "structure_match": true,
  "missing_fields": [],
  "extra_fields": [],
  "data_quality": {
    "operation_count_ratio": 1.429
  }
}
```

## Known Issues & Limitations

### Current Limitations
1. **Complex Comment Parsing**: Multi-line comments may affect parsing
2. **Nested Block Detection**: Very deep nesting might be simplified
3. **Dynamic SQL**: Dynamically constructed SQL not fully parsed

### Future Enhancements
1. **AST-based Parsing**: Move to Abstract Syntax Tree parsing
2. **Oracle Syntax Extensions**: Full Oracle PL/SQL syntax support
3. **Performance Profiling**: Add execution time analysis
4. **Interactive Mode**: Real-time analysis capabilities

## File Structure

```
ORACALE_to_json/
├── files/
│   ├── oracle/                     # Input SQL trigger files
│   ├── expected_ana_json/          # Expected analysis outputs
│   └── sql_json/                   # Generated analysis outputs
├── utilities/
│   ├── sql_analysis.py            # Main analyzer
│   ├── enhanced_sql_analyzer.py   # Enhanced analyzer
│   └── other utility files...
├── requirements.txt               # Dependencies
└── SQL_ANALYSIS_DOCUMENTATION.md # This file
```

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Include comprehensive docstrings
- Add unit tests for new features

### Testing
Test with all three sample triggers:
- `trigger1.sql` - Complex theme management trigger
- `trigger2.sql` - Molecule mapping trigger  
- `trigger3.sql` - Company address trigger

### Validation
Always validate output against expected JSON format in `files/expected_ana_json/`.

## Support & Troubleshooting

### Common Issues

1. **Import Errors**: Install dependencies with `pip install -r requirements.txt`
2. **Parsing Errors**: Check SQL syntax and encoding (UTF-8)
3. **Memory Issues**: Process large files individually

### Debug Mode
Enable debug mode by setting `analyzer.debug = True` for detailed parsing information.

### Performance Tips
- Use enhanced analyzer for better results
- Process files individually for large triggers
- Monitor memory usage for very large SQL files

## License & Credits

This tool was created for Oracle to JSON conversion workflows and incorporates:
- **sqlparse** library for SQL parsing
- **sqlglot** library for SQL transformation
- Custom Oracle PL/SQL analysis logic

---

For questions or issues, refer to the generated validation reports and debug output. 