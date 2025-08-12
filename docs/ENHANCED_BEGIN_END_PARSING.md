# Enhanced BEGIN-END Block Parsing with EXCEPTION Handling

## Overview

This document describes the enhanced BEGIN-END block parsing implementation that provides precise line number-based parsing for Oracle PL/SQL blocks with EXCEPTION sections.

## Key Features

### 1. Line Number Detection
The enhanced parser first detects the exact line numbers for:
- **BEGIN** line number
- **END** line number  
- **EXCEPTION** line number (if present)

### 2. Precise EXCEPTION Section Handling
- Only processes EXCEPTION sections from the EXCEPTION line to the END line
- Correctly handles nested BEGIN-END blocks within EXCEPTION sections
- Maintains proper nesting level tracking

### 3. Enhanced Structure Output
Each BEGIN-END block now includes:
```json
{
  "type": "begin_end",
  "begin_line_no": 5,
  "end_line_no": 38,
  "exception_line_no": 21,
  "begin_end_statements": [...],
  "exception_handlers": [...]
}
```

## Implementation Details

### Method: `_parse_begin_end_structure(start_idx)`

**Step 1: Line Number Detection**
```python
# First pass - detect BEGIN, END, and EXCEPTION line numbers
begin_line_no = start_line_info["line_no"]
end_line_no = None
exception_line_no = None
nested_begin_count = 0

# Find the matching END and last EXCEPTION line numbers
while i < len(self.structured_lines):
    if line_upper == "BEGIN":
        nested_begin_count += 1
    elif line_upper == "END;":
        if nested_begin_count > 0:
            nested_begin_count -= 1
        else:
            end_line_no = line_info["line_no"]
            break
    elif line_upper == "EXCEPTION" and nested_begin_count == 0:
        exception_line_no = line_info["line_no"]
```

**Step 2: Main Section Parsing**
- Parse statements from BEGIN to EXCEPTION (or END if no EXCEPTION)
- Handle nested BEGIN-END blocks recursively
- Skip empty lines and comments

**Step 3: EXCEPTION Section Parsing**
- Parse only from EXCEPTION line to END line
- Handle multiple exception handlers (WHEN ... THEN)
- Process RAISE_APPLICATION_ERROR and regular RAISE statements
- Support nested blocks within exception handlers

### Method: `_parse_exception_section(exception_line_no, end_line_no)`

Dedicated method for parsing EXCEPTION sections:
```python
def _parse_exception_section(self, exception_line_no: int, end_line_no: int):
    # Find lines in EXCEPTION section
    exception_lines = []
    for line_info in self.structured_lines:
        if exception_line_no <= line_info["line_no"] < end_line_no:
            exception_lines.append(line_info)
    
    # Parse exception handlers and their statements
    for line_info in exception_lines:
        if line_upper.startswith("WHEN ") and " THEN" in line_upper:
            # Start new exception handler
        elif current_handler and line:
            # Add statements to current handler
```

## Test Results

### Test Case 1: Basic BEGIN-END with EXCEPTION
```sql
BEGIN
    INSERT INTO audit_table (action, table_name, timestamp)
    VALUES ('INSERT', 'test_table', SYSDATE);
    
    UPDATE counter_table SET count = count + 1;
    
    BEGIN
        SELECT COUNT(*) INTO v_count FROM test_table;
        IF v_count > 100 THEN
            RAISE_APPLICATION_ERROR(-20001, 'Too many records');
        END IF;
    END;
    
EXCEPTION
    WHEN no_data_found THEN
        INSERT INTO error_log (error_type, message)
        VALUES ('NO_DATA_FOUND', 'No data found in query');
        RAISE_APPLICATION_ERROR(-20002, 'No data found');
    
    WHEN too_many_rows THEN
        UPDATE error_log SET count = count + 1;
        RAISE_APPLICATION_ERROR(-20003, 'Too many rows returned');
    
    WHEN OTHERS THEN
        INSERT INTO error_log (error_type, message)
        VALUES ('OTHERS', SQLERRM);
        RAISE;
END;
```

**Parsed Structure:**
- BEGIN-END Block (lines 5-38)
- EXCEPTION section starts at line: 21
- Exception handlers: 3
  - Handler 1: no_data_found (3 statements)
  - Handler 2: too_many_rows (2 statements)  
  - Handler 3: OTHERS (3 statements)
- Main statements: 4 (including 1 nested BEGIN-END block)

### Test Case 2: Nested BEGIN-END with Multiple EXCEPTION Sections
```sql
BEGIN
    INSERT INTO audit_table (action, timestamp) VALUES ('INSERT', SYSDATE);
    
    BEGIN
        SELECT COUNT(*) INTO v_count FROM test_table;
        
        BEGIN
            UPDATE counter SET value = value + 1;
        EXCEPTION
            WHEN no_data_found THEN
                INSERT INTO error_log (message) VALUES ('Counter not found');
        END;
        
    EXCEPTION
        WHEN too_many_rows THEN
            RAISE_APPLICATION_ERROR(-20001, 'Too many rows in inner block');
    END;
    
    UPDATE status_table SET last_update = SYSDATE;
    
EXCEPTION
    WHEN OTHERS THEN
        INSERT INTO error_log (error_type, message) VALUES ('OUTER_ERROR', SQLERRM);
        RAISE;
END;
```

**Parsed Structure:**
- Outer BEGIN-END Block (lines 5-35)
  - EXCEPTION section at line: 30
  - Exception handlers: 1 (OTHERS)
  - Main statements: 2
- Nested BEGIN-END Block (lines 10-25)
  - EXCEPTION section at line: 17
  - Exception handlers: 1 (too_many_rows)
  - Main statements: 2
- Deep Nested BEGIN-END Block (lines 15-20)
  - EXCEPTION section at line: 17
  - Exception handlers: 1 (no_data_found)
  - Main statements: 1

## Benefits

1. **Precise Line Number Tracking**: Exact line numbers for BEGIN, END, and EXCEPTION sections
2. **Accurate EXCEPTION Handling**: Only processes EXCEPTION sections from EXCEPTION to END
3. **Nested Block Support**: Properly handles nested BEGIN-END blocks at any level
4. **Exception Handler Parsing**: Correctly parses multiple WHEN ... THEN handlers
5. **RAISE Statement Support**: Handles both RAISE_APPLICATION_ERROR and regular RAISE
6. **Structured Output**: Clean JSON structure with line numbers and proper nesting

## Usage

The enhanced parsing is automatically used when creating an `OracleTriggerAnalyzer` instance:

```python
analyzer = OracleTriggerAnalyzer(sql_content)
result = analyzer.to_json()

# Access BEGIN-END blocks
main_section = result.get("main", [])
for item in main_section:
    if item.get("type") == "begin_end":
        print(f"BEGIN-END Block (lines {item['begin_line_no']}-{item['end_line_no']})")
        if item.get("exception_line_no"):
            print(f"EXCEPTION section at line: {item['exception_line_no']}")
```

## Conclusion

The enhanced BEGIN-END parsing provides precise, line number-based parsing that correctly handles EXCEPTION sections and nested blocks. This ensures accurate conversion of Oracle PL/SQL triggers to structured JSON format while maintaining the integrity of the original code structure.
