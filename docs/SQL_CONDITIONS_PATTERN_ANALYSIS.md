# SQL Conditions Pattern Analysis

## Overview

This document analyzes the SQL conditions extracted from Oracle trigger conversion logs, categorizing them by pattern type and complexity for systematic breakdown and conversion.

## Pattern Categories

### 1. Basic Comparison Operators

#### 1.1 Equality Comparisons

```
:NEW.IN_PREP_IND = 'Y'
:NEW.OFFICIAL_IND = 'N'
:NEW.PORTF_PROJ_CD = 'Y'
V_COMPARATOR_IND = 'Y'
V_COUNTER > 0
```

**Pattern Breakdown:**

- **Structure**: `column = value` or `variable = value`
- **Components**:
  - Column reference (`:NEW.column_name` or `:OLD.column_name`)
  - Variable reference (`V_variable_name`)
  - Literal value (`'Y'`, `'N'`, `0`, etc.)
- **Conversion**: Direct mapping to PostgreSQL equality operators

#### 1.2 Inequality Comparisons

```
:NEW.PORTF_PROJ_CD <> 'Y'
:NEW.STATUS_DESC <> 'CLOSED'
:NEW.THEME_NO <> :OLD.THEME_NO
```

**Pattern Breakdown:**

- **Structure**: `column <> value` or `column1 <> column2`
- **Components**: Column references, literal values, or other columns
- **Conversion**: `<>` maps to `!=` in PostgreSQL

#### 1.3 Range Comparisons

```
V_COUNTER > 0
LENGTH(V_DESCRIPTION) > 90
:NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS
```

**Pattern Breakdown:**

- **Structure**: `expression > value` or `function(column) > value`
- **Components**: Functions, columns, variables, numeric literals
- **Conversion**: Direct mapping to PostgreSQL comparison operators

### 2. NULL/NOT NULL Conditions

#### 2.1 IS NULL Checks

```
:NEW.MOLECULE_ID IS NULL
V_MOLECULE_RG_NO IS NULL
:NEW.MANUAL_SHORT_DESC IS NULL
```

**Pattern Breakdown:**

- **Structure**: `column IS NULL` or `variable IS NULL`
- **Components**: Column or variable references
- **Conversion**: Direct mapping to PostgreSQL `IS NULL`

#### 2.2 IS NOT NULL Checks

```
:NEW.MOLECULE_ID IS NOT NULL
:NEW.STATUS_DESC IS NOT NULL
:NEW.DBA_DESC_CONCAT IS NOT NULL
```

**Pattern Breakdown:**

- **Structure**: `column IS NOT NULL` or `variable IS NOT NULL`
- **Components**: Column or variable references
- **Conversion**: Direct mapping to PostgreSQL `IS NOT NULL`

### 3. Complex Boolean Logic

#### 3.1 AND Combinations

```
:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0
:NEW.PORTF_PROJ_CD = 'Y' AND :NEW.MOLECULE_ID IS NULL
:NEW.STATUS_DESC <> 'CLOSED' AND V_IS_ADMIN_CNT = 0
```

**Pattern Breakdown:**

- **Structure**: `condition1 AND condition2`
- **Components**: Multiple simple conditions joined by AND
- **Conversion**: Direct mapping to PostgreSQL AND operator

#### 3.2 OR Combinations

```
:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0
INSERTING OR UPDATING
```

**Pattern Breakdown:**

- **Structure**: `condition1 OR condition2`
- **Components**: Multiple conditions joined by OR
- **Conversion**: Direct mapping to PostgreSQL OR operator

#### 3.3 Complex Nested Logic

```
(:OLD.IN_PREP_IND = 'N' OR (:OLD.IN_PREP_IND = 'Y' AND :NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0
```

**Pattern Breakdown:**

- **Structure**: `(condition1 OR (condition2 AND condition3)) AND condition4`
- **Components**: Nested parentheses with mixed AND/OR logic
- **Conversion**: Preserve parentheses and operator precedence

### 4. Function-Based Conditions

#### 4.1 String Functions

```
LENGTH(:NEW.THEME_NO)
LENGTH(V_DESCRIPTION) > 90
LENGTH(:NEW.THEME_DESC) = 0
UPPER(:NEW.PORTF_PROJ_CD) = 'N'
```

**Pattern Breakdown:**

- **Structure**: `function(column) operator value`
- **Components**: String functions, columns, comparison operators
- **Conversion**:
  - `LENGTH()` → `LENGTH()` (same in PostgreSQL)
  - `UPPER()` → `UPPER()` (same in PostgreSQL)

#### 4.2 Substring Functions

```
SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9
SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9
```

**Pattern Breakdown:**

- **Structure**: `SUBSTR(column, start, length) operator range`
- **Components**: SUBSTR function with position and length parameters
- **Conversion**: `SUBSTR()` → `SUBSTRING()` in PostgreSQL

#### 4.3 Date Functions

```
TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)
TO_CHAR(:NEW.VALID_FROM, 'dd.mm') = '01.01'
```

**Pattern Breakdown:**

- **Structure**: `date_function(date_expression) operator date_value`
- **Components**: Date conversion and formatting functions
- **Conversion**:
  - `TO_DATE()` → `TO_DATE()` (same in PostgreSQL)
  - `TRUNC()` → `DATE_TRUNC()` in PostgreSQL
  - `SYSDATE` → `CURRENT_DATE` in PostgreSQL

### 5. NVL (Null Value Logic) Conditions

#### 5.1 Basic NVL Usage

```
NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL
NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0)
```

**Pattern Breakdown:**

- **Structure**: `NVL(column1, column2) operator value`
- **Components**: NVL function with two parameters
- **Conversion**: `NVL()` → `COALESCE()` in PostgreSQL

#### 5.2 Complex NVL Comparisons

```
NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0) AND NVL(:OLD.SHORT_NAME, '-') <> NVL(V_SHORT_NAME, '-')
```

**Pattern Breakdown:**

- **Structure**: Multiple NVL functions in complex conditions
- **Components**: NVL functions combined with AND/OR logic
- **Conversion**: Replace all `NVL()` with `COALESCE()`

### 6. IN/NOT IN Conditions

#### 6.1 Basic IN Lists

```
:NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')
:NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')
```

**Pattern Breakdown:**

- **Structure**: `column IN (value1, value2, ...)`
- **Components**: Column reference and list of literal values
- **Conversion**: Direct mapping to PostgreSQL IN operator

#### 6.2 NOT IN Conditions

```
NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) NOT IN ('P', 'L')
V_COMPANY_TYPE_CD NOT IN ('L', 'A')
```

**Pattern Breakdown:**

- **Structure**: `expression NOT IN (value1, value2, ...)`
- **Components**: Function results or columns with value lists
- **Conversion**: Direct mapping to PostgreSQL NOT IN operator

### 7. BETWEEN Conditions

#### 7.1 Numeric BETWEEN

```
SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9
```

**Pattern Breakdown:**

- **Structure**: `function(column) NOT BETWEEN min AND max`
- **Components**: Function results with numeric ranges
- **Conversion**: Direct mapping to PostgreSQL BETWEEN operator

### 8. Trigger Operation Conditions

#### 8.1 Basic Trigger Operations

```
INSERTING
UPDATING
DELETING
INSERTING OR UPDATING
```

**Pattern Breakdown:**

- **Structure**: `TG_OP = 'operation'` or direct operation names
- **Components**: Trigger operation identifiers
- **Conversion**:
  - `INSERTING` → `TG_OP = 'INSERT'`
  - `UPDATING` → `TG_OP = 'UPDATE'`
  - `DELETING` → `TG_OP = 'DELETE'`

#### 8.2 Complex Trigger Logic

```
INSERTING AND :NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(:NEW.THEME_NO) = 'Y'
```

**Pattern Breakdown:**

- **Structure**: `operation AND condition1 AND condition2`
- **Components**: Trigger operations combined with business logic
- **Conversion**: Replace operation names with `TG_OP` comparisons

### 9. COALESCE Conditions

#### 9.1 Basic COALESCE

```
COALESCE(OLD.PROD_FAM_NAME_STATUS_CD, 'X') <> COALESCE(NEW.PROD_FAM_NAME_STATUS_CD, 'X')
```

**Pattern Breakdown:**

- **Structure**: `COALESCE(column1, default1) operator COALESCE(column2, default2)`
- **Components**: COALESCE functions with default values
- **Conversion**: Direct mapping to PostgreSQL COALESCE function

### 10. Complex Multi-Column Conditions

#### 10.1 State Transition Logic

```
:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL
:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NOT NULL
:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NULL
```

**Pattern Breakdown:**

- **Structure**: `old_column condition AND new_column condition`
- **Components**: OLD and NEW column comparisons
- **Conversion**: Direct mapping to PostgreSQL column references

#### 10.2 Business Rule Conditions

```
:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(:NEW.EVOLVED_THEME_NO IS NULL OR :NEW.EVOLVED_THEME_NO = :OLD.EVOLVED_THEME_NO) AND :NEW.MOLECULE_TYPE_ID = :OLD.MOLECULE_TYPE_ID AND :NEW.PHARMACOLOGICAL_TYPE_ID = :OLD.PHARMACOLOGICAL_TYPE_ID AND :NEW.PROPOSAL_NAME = :OLD.PROPOSAL_NAME
```

**Pattern Breakdown:**

- **Structure**: Complex business logic with multiple AND/OR combinations
- **Components**: Constants, column comparisons, nested conditions
- **Conversion**: Replace constants with their values, preserve logic structure

## Conversion Strategy

### 1. Pattern Recognition

1. **Identify condition type** (comparison, null check, function, etc.)
2. **Extract components** (columns, functions, literals, operators)
3. **Map to PostgreSQL equivalent** (functions, operators, syntax)

### 2. Systematic Replacement

1. **Oracle-specific functions** → **PostgreSQL equivalents**
2. **Oracle operators** → **PostgreSQL operators**
3. **Oracle constants** → **PostgreSQL constants**
4. **Oracle trigger syntax** → **PostgreSQL trigger syntax**

### 3. Validation Steps

1. **Syntax validation** - Ensure valid PostgreSQL syntax
2. **Logic validation** - Verify condition logic is preserved
3. **Function validation** - Confirm function mappings are correct
4. **Performance consideration** - Optimize for PostgreSQL execution

## Common Conversion Mappings

| Oracle | PostgreSQL | Notes |
|--------|------------|-------|
| `NVL()` | `COALESCE()` | Null value handling |
| `SUBSTR()` | `SUBSTRING()` | String extraction |
| `SYSDATE` | `CURRENT_DATE` | Current date |
| `TRUNC()` | `DATE_TRUNC()` | Date truncation |
| `<>` | `!=` | Inequality operator |
| `INSERTING` | `TG_OP = 'INSERT'` | Trigger operation |
| `UPDATING` | `TG_OP = 'UPDATE'` | Trigger operation |
| `DELETING` | `TG_OP = 'DELETE'` | Trigger operation |

## Conclusion

This analysis provides a systematic approach to breaking down complex Oracle SQL conditions into manageable patterns that can be systematically converted to PostgreSQL. The key is to:

1. **Categorize** conditions by type and complexity
2. **Identify** the core components and structure
3. **Map** Oracle-specific elements to PostgreSQL equivalents
4. **Preserve** the logical structure and business rules
5. **Validate** the converted conditions for correctness

This approach ensures accurate and maintainable conversions from Oracle to PostgreSQL trigger logic.
