# OracleTriggerAnalyzer - SQL to JSON Parser Documentation

## Overview

The `OracleTriggerAnalyzer` is a sophisticated parser designed to convert Oracle PL/SQL trigger bodies into structured JSON format. It provides detailed analysis of trigger components including declarations, control structures, SQL statements, and exception handling.

## Architecture

### Core Components

The analyzer follows a hierarchical parsing approach with the following main components:

1. **Initialization & Preprocessing**
2. **Declaration Parsing** (DECLARE section)
3. **Main Section Parsing** (BEGIN...END section)
4. **Structured Output Generation**

### Data Flow

```txt
Raw SQL Content → Structured Lines → Section Separation → Component Parsing → JSON Output
```

## Detailed Parsing Process

### 1. Initialization Phase

#### Constructor (`__init__`)

- Receives raw SQL content as input
- Initializes data structures for parsed components
- Calls `_parse_sql()` to begin the parsing process

#### Key Data Structures

```python
self.structured_lines: List[Dict]  # Processed lines with metadata
self.variables: List[Dict]         # Variable declarations
self.constants: List[Dict]         # Constant declarations  
self.exceptions: List[Dict]        # Exception declarations
self.main_section_lines: Dict      # Parsed main section
self.sql_comments: List[str]       # Extracted comments
```

### 2. SQL Preprocessing

#### Structured Line Conversion (`_convert_to_structured_lines`)

Converts raw SQL into structured format with metadata:

```python
{
    "indent": int,           # Indentation level
    "line": str,             # Line content without leading whitespace
    "line_no": int,          # Line number (1-based)
}
```

#### Comment Removal

- **Block Comments**: Removes `/* ... */` patterns
- **Inline Comments**: Removes `-- ...` patterns
- Preserves comment content in `self.sql_comments`

### 3. Section Separation (`_parse_sql`)

#### DECLARE Section Detection

- Identifies `DECLARE` keyword to mark declaration start
- Locates `BEGIN` keyword to mark declaration end
- Sets boundaries: `self.declare_section = [start_line, end_line]`

#### Main Section Detection

- Identifies `BEGIN` keyword to mark main section start
- Locates `END;` to mark main section end
- Processes main section through `_process_main_section()`

### 4. Declaration Parsing (`_parse_declarations`)

#### Variable Declarations

Parses patterns like:

```sql
v_count NUMBER;
v_name VARCHAR2(100) := 'John';
v_date DATE NOT NULL := SYSDATE;
```

**Output Structure:**

```json
{
    "name": "v_count",
    "data_type": "NUMBER", 
    "default_value": null
}
```

#### Constant Declarations

Parses patterns like:

```sql
C_MAX_RECORDS CONSTANT NUMBER := 100;
C_DEFAULT_NAME CONSTANT VARCHAR2(50) := 'Unknown';
```

**Output Structure:**

```json
{
    "name": "C_MAX_RECORDS",
    "data_type": "NUMBER",
    "value": "100"
}
```

#### Exception Declarations

Parses patterns like:

```sql
my_exception EXCEPTION;
```

**Output Structure:**

```json
{
    "name": "my_exception",
    "type": "EXCEPTION"
}
```

### 5. Main Section Parsing (`_process_main_section`)

The main section parsing follows a hierarchical approach, processing nested structures recursively:

#### 5.1 BEGIN-END Blocks (`_parse_begin_blocks`)

- Identifies top-level BEGIN-END structure
- Separates exception handlers from main statements
- Creates hierarchical structure with nested blocks

**Output Structure:**

```json
{
    "type": "begin_end",
    "begin_line_no": 10,
    "begin_indent": 0,
    "begin_end_statements": [...],
    "exception_handlers": [...],
    "end_line_no": 50
}
```

#### 5.2 Nested BEGIN-END Statements (`_parse_begin_end_statements`)

- Recursively processes nested BEGIN-END blocks
- Maintains indentation-based nesting structure
- Handles exception handlers within blocks

#### 5.3 IF-ELSE Statements (`_parse_if_else`)

Parses conditional structures:

```sql
IF condition THEN
    statements;
ELSIF condition2 THEN
    statements;
ELSE
    statements;
END IF;
```

**Output Structure:**

```json
{
    "type": "if_else",
    "condition": "v_count > 0",
    "if_line_no": 15,
    "then_line_no": 15,
    "then_statements": [...],
    "if_elses": [
        {
            "type": "elif_statement",
            "condition": "v_count = 0",
            "then_statements": [...]
        }
    ],
    "else_statements": [...],
    "end_if_line_no": 25
}
```

#### 5.4 CASE-WHEN Statements (`_parse_case_when`)

Parses case structures:

```sql
CASE variable
    WHEN value1 THEN statements;
    WHEN value2 THEN statements;
    ELSE statements;
END CASE;
```

**Output Structure:**

```json
{
    "type": "case_when",
    "condition": "v_status",
    "case_line_no": 20,
    "when_clauses": [
        {
            "type": "when_statement",
            "condition": "'ACTIVE'",
            "then_statements": [...]
        }
    ],
    "else_statements": [...],
    "end_case_line_no": 35
}
```

#### 5.5 FOR Loops (`_parse_for_loop`)

Parses cursor-based loops:

```sql
FOR record_var IN (SELECT * FROM table) LOOP
    statements;
END LOOP;
```

**Output Structure:**

```json
{
    "type": "for_loop",
    "loop_variable": "record_var",
    "for_expression": "(SELECT * FROM table)",
    "for_line_no": 30,
    "for_statements": [...],
    "end_for_line_no": 40
}
```

#### 5.6 SQL Statements (`_parse_sql_statements`)

Categorizes and parses various SQL statement types:

**Supported Statement Types:**
- `SELECT` statements
- `INSERT` statements  
- `UPDATE` statements
- `DELETE` statements
- `RAISE` statements
- `NULL` statements
- `RETURN` statements
- Assignment statements (`:=`)

**Output Structure:**

```json
{
    "type": "select_statement",
    "sql_statement": "SELECT COUNT(*) INTO v_count FROM employees",
    "statement_line_no": 45,
    "statement_indent": 4
}
```

#### 5.7 Function Calls (`_parse_function_calling_statements`)

Parses function invocations with parameter analysis:

**Supported Functions:**
- `RAISE_APPLICATION_ERROR`
- `DBMS_OUTPUT.PUT_LINE`
- `TXO_UTIL.SET_WARNING`
- MDM utility functions

**Output Structure:**

```json
{
    "type": "function_calling",
    "function_name": "RAISE_APPLICATION_ERROR",
    "parameters": {
        "parameter_type": "positional",
        "positional_params": ["-20101", "'Invalid input'"],
        "named_params": {},
        "raw_text": "-20101, 'Invalid input'"
    }
}
```

#### 5.8 Exception Handlers (`_parse_exception_handlers`)

Parses exception handling blocks:

```sql
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        statements;
    WHEN OTHERS THEN
        statements;
```

**Output Structure:**

```json
{
    "type": "exception_handler",
    "exception_name": "NO_DATA_FOUND",
    "when_line_no": 55,
    "then_line_no": 55,
    "exception_statements": [...]
}
```

### 6. Parameter Parsing

#### Function Parameter Analysis

The parser handles two types of function parameters:

**Named Parameters:**

```sql
MDM_UTIL_ADDRESSES.MODIFY_COMPANY_ADDRESS(
    P_COMPANY_CD => :NEW.COMPANY_CD,
    P_ADDRESS_TYPE => 'PRIMARY'
);
```

**Positional Parameters:**

```sql
RAISE_APPLICATION_ERROR(-20101, 'Error message');
```

#### Parameter Parsing Logic

- **Comma Splitting**: Handles nested parentheses and quotes
- **Arrow Detection**: Identifies `=>` for named parameters
- **Type Detection**: Auto-detects parameter type based on function name and content

### 7. JSON Output Generation (`to_json`)

#### Final Structure

```json
{
    "declarations": {
        "variables": [...],
        "constants": [...],
        "exceptions": [...]
    },
    "main": {
        "type": "begin_end",
        "begin_end_statements": [...],
        "exception_handlers": [...]
    },
    "sql_comments": [...],
    "rest_strings": [...],
    "conversion_stats": {
        "declaration_count": 5,
        "comment_count": 3,
        "rest_string_count": 10,
        "sql_convert_count": {
            "select_statement": 2,
            "insert_statement": 1,
            "if_else": 3,
            "for_loop": 1
        }
    },
    "metadata": {
        "parse_timestamp": "2024-01-15T10:30:00",
        "parser_version": "1.0"
    }
}
```

## Key Features

### 1. Hierarchical Parsing

- Maintains nested structure based on indentation
- Recursively processes nested blocks
- Preserves statement relationships

### 2. Robust Error Handling

- Graceful handling of malformed SQL
- Detailed logging for debugging
- Fallback mechanisms for edge cases

### 3. Comprehensive Coverage

- All major PL/SQL constructs supported
- Comment preservation and extraction
- Metadata and statistics generation

### 4. Extensible Design

- Modular parsing functions
- Easy to add new statement types
- Configurable parsing rules

## Usage Example

```python
# Initialize analyzer with SQL content
analyzer = OracleTriggerAnalyzer(sql_content)

# Generate JSON output
result = analyzer.to_json()

# Access parsed components
variables = result["declarations"]["variables"]
main_section = result["main"]
statistics = result["conversion_stats"]
```

## Performance Considerations

### Optimization Strategies

1. **Fast Path Checks**: Skip processing for lines without target patterns
2. **Structured Line Format**: Pre-process lines to avoid repeated string operations
3. **Recursive Processing**: Efficient handling of nested structures
4. **Memory Management**: Cleanup of intermediate data structures

### Scalability

- Handles large trigger bodies efficiently
- Memory usage scales linearly with input size
- Processing time optimized for typical trigger sizes

## Limitations and Considerations

### Known Limitations

1. **Complex Nested Structures**: Very deeply nested structures may require additional testing
2. **Dynamic SQL**: Limited support for dynamic SQL constructs
3. **Custom Functions**: Function parameter parsing may need customization for new function types

### Best Practices

1. **Input Validation**: Ensure SQL is well-formed before parsing
2. **Error Handling**: Check conversion statistics for parsing quality
3. **Testing**: Test with various trigger formats to ensure compatibility

## Conclusion

The OracleTriggerAnalyzer provides a comprehensive solution for converting Oracle PL/SQL triggers into structured JSON format. Its hierarchical parsing approach, robust error handling, and detailed output make it suitable for analysis, documentation, and transformation tasks involving Oracle triggers.

The modular design allows for easy extension and customization, while the detailed statistics and metadata provide insights into the parsing process and results.
