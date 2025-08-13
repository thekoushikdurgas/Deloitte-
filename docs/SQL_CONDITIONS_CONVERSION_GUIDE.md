# SQL Conditions Conversion Guide: Oracle to PostgreSQL

## Overview

This guide provides practical step-by-step instructions for converting Oracle SQL conditions to PostgreSQL, based on the patterns identified in the log analysis.

## Conversion Process

### Step 1: Pattern Identification

First, identify the type of condition you're dealing with:

```python
def identify_condition_type(condition):
    """Identify the type of SQL condition for conversion"""
    condition = condition.strip()
    
    # Basic comparisons
    if '=' in condition and 'IS NULL' not in condition:
        return 'equality'
    elif '<>' in condition:
        return 'inequality'
    elif '>' in condition or '<' in condition:
        return 'range'
    
    # NULL checks
    elif 'IS NULL' in condition:
        return 'null_check'
    elif 'IS NOT NULL' in condition:
        return 'not_null_check'
    
    # Functions
    elif 'NVL(' in condition:
        return 'nvl_function'
    elif 'SUBSTR(' in condition:
        return 'substr_function'
    elif 'LENGTH(' in condition:
        return 'length_function'
    elif 'UPPER(' in condition:
        return 'upper_function'
    elif 'TRUNC(' in condition or 'TO_DATE(' in condition:
        return 'date_function'
    
    # Complex logic
    elif ' AND ' in condition or ' OR ' in condition:
        return 'boolean_logic'
    
    # Trigger operations
    elif condition in ['INSERTING', 'UPDATING', 'DELETING']:
        return 'trigger_operation'
    
    # IN conditions
    elif ' IN (' in condition:
        return 'in_condition'
    elif ' NOT IN (' in condition:
        return 'not_in_condition'
    
    # BETWEEN conditions
    elif ' BETWEEN ' in condition:
        return 'between_condition'
    
    return 'unknown'
```

### Step 2: Component Extraction

Extract the key components from each condition:

```python
def extract_components(condition):
    """Extract components from SQL condition"""
    components = {
        'columns': [],
        'functions': [],
        'literals': [],
        'operators': [],
        'variables': []
    }
    
    # Extract column references
    import re
    column_pattern = r':(NEW|OLD)\.\w+'
    columns = re.findall(column_pattern, condition)
    components['columns'] = columns
    
    # Extract functions
    function_pattern = r'\w+\([^)]+\)'
    functions = re.findall(function_pattern, condition)
    components['functions'] = functions
    
    # Extract operators
    operator_pattern = r'(=|<>|>|<|>=|<=|AND|OR|IN|NOT IN|BETWEEN|IS NULL|IS NOT NULL)'
    operators = re.findall(operator_pattern, condition, re.IGNORECASE)
    components['operators'] = operators
    
    return components
```

### Step 3: Systematic Conversion

#### 3.1 Basic Comparison Conversions

```python
def convert_basic_comparison(condition):
    """Convert basic comparison operators"""
    # Replace Oracle inequality operator
    condition = condition.replace('<>', '!=')
    
    # Replace Oracle trigger operations
    condition = condition.replace('INSERTING', "TG_OP = 'INSERT'")
    condition = condition.replace('UPDATING', "TG_OP = 'UPDATE'")
    condition = condition.replace('DELETING', "TG_OP = 'DELETE'")
    
    return condition
```

#### 3.2 Function Conversions

```python
def convert_functions(condition):
    """Convert Oracle functions to PostgreSQL equivalents"""
    
    # NVL to COALESCE
    import re
    nvl_pattern = r'NVL\(([^,]+),([^)]+)\)'
    condition = re.sub(nvl_pattern, r'COALESCE(\1,\2)', condition)
    
    # SUBSTR to SUBSTRING
    substr_pattern = r'SUBSTR\(([^,]+),([^,]+),([^)]+)\)'
    condition = re.sub(substr_pattern, r'SUBSTRING(\1 FROM \2 FOR \3)', condition)
    
    # Date functions
    condition = condition.replace('SYSDATE', 'CURRENT_DATE')
    condition = condition.replace('TRUNC(', 'DATE_TRUNC(')
    
    return condition
```

#### 3.3 Complex Logic Conversion

```python
def convert_complex_logic(condition):
    """Convert complex boolean logic while preserving structure"""
    
    # Handle nested parentheses
    # This requires a more sophisticated parser for complex cases
    
    # Basic AND/OR conversions (already compatible)
    # PostgreSQL uses same AND/OR operators as Oracle
    
    # Handle trigger operation combinations
    if 'INSERTING OR UPDATING' in condition:
        condition = condition.replace('INSERTING OR UPDATING', 
                                    "TG_OP IN ('INSERT', 'UPDATE')")
    
    return condition
```

### Step 4: Complete Conversion Examples

#### Example 1: Simple Equality

```sql
-- Oracle
:NEW.IN_PREP_IND = 'Y'

-- PostgreSQL (same syntax)
NEW.IN_PREP_IND = 'Y'
```

#### Example 2: Inequality with Function

```sql
-- Oracle
:NEW.PORTF_PROJ_CD <> 'Y'

-- PostgreSQL
NEW.PORTF_PROJ_CD != 'Y'
```

#### Example 3: NVL Function

```sql
-- Oracle
NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL

-- PostgreSQL
COALESCE(NEW.MANUAL_SHORT_DESC, NEW.THEME_DESC_PROPOSAL) IS NULL
```

#### Example 4: Complex Boolean Logic

```sql
-- Oracle
:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0

-- PostgreSQL
NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0
```

#### Example 5: Trigger Operations

```sql
-- Oracle
INSERTING OR UPDATING

-- PostgreSQL
TG_OP IN ('INSERT', 'UPDATE')
```

#### Example 6: Date Functions

```sql
-- Oracle
TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)

-- PostgreSQL
DATE_TRUNC('day', TO_DATE(OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = DATE_TRUNC('day', CURRENT_DATE)
```

#### Example 7: Substring Functions

```sql
-- Oracle
SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9

-- PostgreSQL
SUBSTRING(NEW.THEME_NO FROM 1 FOR 1) NOT BETWEEN 0 AND 9
```

### Step 5: Validation and Testing

```python
def validate_conversion(original, converted):
    """Validate that the conversion preserves logic"""
    
    # Check for syntax errors
    try:
        # Basic syntax validation
        if 'NVL(' in converted:
            raise ValueError("NVL function not converted to COALESCE")
        if '<>' in converted:
            raise ValueError("<> operator not converted to !=")
        if 'INSERTING' in converted or 'UPDATING' in converted or 'DELETING' in converted:
            raise ValueError("Trigger operations not converted to TG_OP")
            
        return True
    except Exception as e:
        print(f"Validation error: {e}")
        return False

def test_conversion():
    """Test conversion with sample conditions"""
    
    test_cases = [
        (":NEW.IN_PREP_IND = 'Y'", "NEW.IN_PREP_IND = 'Y'"),
        ("NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0)", 
         "COALESCE(NEW.PROPOSAL_ID, 0) = COALESCE(OLD.PROPOSAL_ID, 0)"),
        ("INSERTING OR UPDATING", "TG_OP IN ('INSERT', 'UPDATE')"),
        ("SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9",
         "SUBSTRING(NEW.THEME_NO FROM 1 FOR 1) NOT BETWEEN 0 AND 9")
    ]
    
    for original, expected in test_cases:
        converted = convert_condition(original)
        assert converted == expected, f"Expected {expected}, got {converted}"
        print(f"✓ {original} → {converted}")

def convert_condition(condition):
    """Main conversion function"""
    
    # Step 1: Identify type
    condition_type = identify_condition_type(condition)
    
    # Step 2: Apply appropriate conversion
    if condition_type == 'equality':
        return convert_basic_comparison(condition)
    elif condition_type == 'nvl_function':
        return convert_functions(condition)
    elif condition_type == 'trigger_operation':
        return convert_basic_comparison(condition)
    elif condition_type == 'boolean_logic':
        return convert_complex_logic(condition)
    else:
        # Apply all conversions
        condition = convert_basic_comparison(condition)
        condition = convert_functions(condition)
        condition = convert_complex_logic(condition)
        return condition
```

### Step 6: Batch Processing

```python
def batch_convert_conditions(conditions_list):
    """Convert a list of conditions"""
    
    converted_conditions = []
    conversion_log = []
    
    for i, condition in enumerate(conditions_list):
        try:
            original = condition.strip()
            converted = convert_condition(original)
            
            converted_conditions.append(converted)
            conversion_log.append({
                'index': i,
                'original': original,
                'converted': converted,
                'status': 'success'
            })
            
        except Exception as e:
            conversion_log.append({
                'index': i,
                'original': condition,
                'converted': None,
                'status': 'error',
                'error': str(e)
            })
    
    return converted_conditions, conversion_log

# Example usage
conditions_from_log = [
    ":NEW.IN_PREP_IND = 'Y'",
    "NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL",
    "INSERTING OR UPDATING",
    "SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9",
    ":NEW.PORTF_PROJ_CD <> 'Y'"
]

converted, log = batch_convert_conditions(conditions_from_log)

for entry in log:
    if entry['status'] == 'success':
        print(f"✓ {entry['original']} → {entry['converted']}")
    else:
        print(f"✗ {entry['original']} → ERROR: {entry['error']}")
```

## Best Practices

### 1. Always Test Conversions

- Test each conversion with sample data
- Verify logic equivalence
- Check for edge cases

### 2. Handle Edge Cases

- Empty strings vs NULL values
- Date format differences
- Function parameter differences

### 3. Performance Considerations

- Some PostgreSQL functions may have different performance characteristics
- Consider indexing implications
- Test with realistic data volumes

### 4. Documentation

- Document all conversions
- Maintain conversion logs
- Create regression tests

## Common Pitfalls

1. **Case Sensitivity**: PostgreSQL is case-sensitive by default
2. **Date Formats**: Oracle and PostgreSQL may handle dates differently
3. **NULL Handling**: NVL vs COALESCE behavior differences
4. **Function Parameters**: Some functions have different parameter orders
5. **Trigger Context**: OLD/NEW references work differently in PostgreSQL

## Conclusion

This systematic approach ensures reliable conversion of Oracle SQL conditions to PostgreSQL while preserving business logic and maintaining code quality. The key is to:

1. **Identify patterns** systematically
2. **Apply conversions** consistently
3. **Validate results** thoroughly
4. **Test extensively** with real data
5. **Document everything** for future maintenance

This guide provides the foundation for building automated conversion tools and maintaining consistency across large-scale migrations.
