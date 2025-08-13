# SQL Condition Conversion Report

## Summary
- Total conditions: 660
- Successful conversions: 618
- Warnings: 42
- Errors: 0

## Condition Types
- boolean_logic: 30
- date_function: 6
- equality: 96
- in_condition: 12
- inequality: 54
- length_function: 36
- not_null_check: 66
- null_check: 72
- nvl_function: 54
- range: 78
- substr_function: 12
- trigger_combination: 18
- trigger_operation: 66
- unknown: 42
- upper_function: 18

## Detailed Conversions

### Condition 0
**Type:** equality
**Original:** `:NEW.IN_PREP_IND = 'Y'`
**Converted:** `NEW.IN_PREP_IND = 'Y'`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=']

### Condition 1
**Type:** inequality
**Original:** `:NEW.PORTF_PROJ_CD <> 'Y'`
**Converted:** `NEW.PORTF_PROJ_CD != 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - operators: ['OR', '<>']

### Condition 2
**Type:** inequality
**Original:** `:NEW.STATUS_DESC <> 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.STATUS_DESC != 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['<>', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 3
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 4
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 5
**Type:** null_check
**Original:** `V_MOLECULE_RG_NO IS NULL`
**Converted:** `V_MOLECULE_RG_NO IS NULL`
**Components:**
  - operators: ['IS NULL']
  - variables: ['V_MOLECULE_RG_NO']

### Condition 6
**Type:** equality
**Original:** `V_COMPARATOR_IND = 'Y'`
**Converted:** `V_COMPARATOR_IND = 'Y'`
**Components:**
  - operators: ['OR', 'IN', '=']
  - variables: ['V_COMPARATOR_IND']

### Condition 7
**Type:** not_null_check
**Original:** `:NEW.STATUS_DESC IS NOT NULL`
**Converted:** `NEW.STATUS_DESC IS NOT NULL`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['IS NOT NULL']

### Condition 8
**Type:** not_null_check
**Original:** `:NEW.DBA_DESC_CONCAT IS NOT NULL`
**Converted:** `NEW.DBA_DESC_CONCAT IS NOT NULL`
**Components:**
  - columns: ['NEW.DBA_DESC_CONCAT']
  - operators: ['IS NOT NULL']

### Condition 9
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 10
**Type:** length_function
**Original:** `:NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Converted:** `NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC']
  - functions: ['LENGTH']
  - operators: ['OR', 'IS NULL', 'AND', '>']
  - variables: ['V_THEME_DESC_PROPOSAL']

### Condition 11
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 12
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 13
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 14
**Type:** boolean_logic
**Original:** `:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 15
**Type:** null_check
**Original:** `:NEW.PORTF_PROJ_CD = 'Y' AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.PORTF_PROJ_CD = 'Y' AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.MOLECULE_ID']
  - operators: ['OR', '=', 'AND', 'IS NULL']

### Condition 16
**Type:** nvl_function
**Original:** `NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL`
**Converted:** `COALESCE(NEW.MANUAL_SHORT_DESC, NEW.THEME_DESC_PROPOSAL) IS NULL`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC', 'NEW.THEME_DESC_PROPOSAL']
  - functions: ['NVL']
  - operators: ['OR', 'IS NULL']

### Condition 17
**Type:** length_function
**Original:** `LENGTH(:NEW.THEME_NO)`
**Converted:** `LENGTH(NEW.THEME_NO)`
**Components:**
  - columns: ['NEW.THEME_NO']
  - functions: ['LENGTH']

### Condition 18
**Type:** unknown
**Original:** `4`
**Converted:** `4`
**Components:**

### Condition 19
**Type:** unknown
**Original:** `5`
**Converted:** `5`
**Components:**

### Condition 20
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 21
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  5 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 22
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 23
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 24
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'N'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'N'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 25
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 26
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 27
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 28
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 29
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 30
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N' OR (:OLD.IN_PREP_IND = 'Y' AND :NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N' OR (OLD.IN_PREP_IND = 'Y' AND NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND', 'OLD.IN_PREP_IND', 'NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'OR', 'IN', 'IN', '=', 'AND', 'IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 31
**Type:** inequality
**Original:** `:NEW.THEME_NO <> :OLD.THEME_NO`
**Converted:** `NEW.THEME_NO != OLD.THEME_NO`
**Components:**
  - columns: ['NEW.THEME_NO', 'OLD.THEME_NO']
  - operators: ['<>']

### Condition 32
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 33
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' OR:NEW.IN_PREP_IND = 'Y')) UPPER(:NEW.PORTF_PROJ_CD`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' ORNEW.IN_PREP_IND = 'Y')) UPPER(NEW.PORTF_PROJ_CD`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.IN_PREP_IND', 'NEW.PORTF_PROJ_CD']
  - functions: ['UPPER', 'AND']
  - operators: ['OR', '=', 'AND', '<>', 'OR', 'IN', 'IN', '=', 'OR']
  - variables: ['V_STATUS_CD']
**Status:** warning

### Condition 34
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 35
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 36
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 37
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 38
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 39
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 40
**Type:** not_null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL']

### Condition 41
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 42
**Type:** range
**Original:** `V_SEC_MOL_CNT > 0`
**Converted:** `V_SEC_MOL_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEC_MOL_CNT']

### Condition 43
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 44
**Type:** date_function
**Original:** `TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)`
**Converted:** `DATE_TRUNC(TO_DATE(OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = DATE_TRUNC(CURRENT_DATE)`
**Components:**
  - columns: ['OLD.REGISTRAT_DATE']
  - functions: ['TRUNC', 'TRUNC']
  - operators: ['=']

### Condition 45
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 46
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 47
**Type:** equality
**Original:** `V_EVOLVED_NMP_CNT = 0`
**Converted:** `V_EVOLVED_NMP_CNT = 0`
**Components:**
  - operators: ['=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 48
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL AND :OLD.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NULL AND OLD.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 49
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NOT NULL AND :NEW.PROPOSAL_ID <> :OLD.PROPOSAL_ID`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NOT NULL AND NEW.PROPOSAL_ID <> OLD.PROPOSAL_ID`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL', 'AND', '<>']
**Status:** warning

### Condition 50
**Type:** nvl_function
**Original:** `NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0) AND NVL(:OLD.SHORT_NAME, '-') <> NVL(V_SHORT_NAME, '-')`
**Converted:** `COALESCE(NEW.PROPOSAL_ID, 0) = COALESCE(OLD.PROPOSAL_ID, 0) AND COALESCE(OLD.SHORT_NAME, '-') <> COALESCE(V_SHORT_NAME, '-')`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'OLD.SHORT_NAME']
  - functions: ['NVL', 'NVL', 'NVL', 'NVL']
  - operators: ['=', 'AND', 'OR', '<>', 'OR']
  - variables: ['V_SHORT_NAME']
**Status:** warning

### Condition 51
**Type:** range
**Original:** `V_EVOLVED_NMP_CNT > 0`
**Converted:** `V_EVOLVED_NMP_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 52
**Type:** not_null_check
**Original:** `INSERTING AND :NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(:NEW.THEME_NO) = 'Y'`
**Converted:** `INSERTING AND NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(NEW.THEME_NO) = 'Y'`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['GET_THEMES_RANGE_AUTOMATIC_NMP']
  - operators: ['IN', 'IN', 'AND', 'IS NOT NULL', 'AND', '=']
  - trigger_ops: ['INSERTING']
**Status:** warning

### Condition 53
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID']
  - operators: ['IS NOT NULL']

### Condition 54
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL OR (:NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Converted:** `NEW.PROPOSAL_ID IS NULL OR (NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'NEW.PROPOSAL_ID']
  - operators: ['IS NULL', 'OR', 'IS NOT NULL', 'AND', '=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 55
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 56
**Type:** equality
**Original:** `:NEW.IN_PREP_IND = 'Y'`
**Converted:** `NEW.IN_PREP_IND = 'Y'`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=']

### Condition 57
**Type:** inequality
**Original:** `:NEW.PORTF_PROJ_CD <> 'Y'`
**Converted:** `NEW.PORTF_PROJ_CD != 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - operators: ['OR', '<>']

### Condition 58
**Type:** inequality
**Original:** `:NEW.STATUS_DESC <> 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.STATUS_DESC != 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['<>', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 59
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 60
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 61
**Type:** null_check
**Original:** `V_MOLECULE_RG_NO IS NULL`
**Converted:** `V_MOLECULE_RG_NO IS NULL`
**Components:**
  - operators: ['IS NULL']
  - variables: ['V_MOLECULE_RG_NO']

### Condition 62
**Type:** equality
**Original:** `V_COMPARATOR_IND = 'Y'`
**Converted:** `V_COMPARATOR_IND = 'Y'`
**Components:**
  - operators: ['OR', 'IN', '=']
  - variables: ['V_COMPARATOR_IND']

### Condition 63
**Type:** not_null_check
**Original:** `:NEW.STATUS_DESC IS NOT NULL`
**Converted:** `NEW.STATUS_DESC IS NOT NULL`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['IS NOT NULL']

### Condition 64
**Type:** not_null_check
**Original:** `:NEW.DBA_DESC_CONCAT IS NOT NULL`
**Converted:** `NEW.DBA_DESC_CONCAT IS NOT NULL`
**Components:**
  - columns: ['NEW.DBA_DESC_CONCAT']
  - operators: ['IS NOT NULL']

### Condition 65
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 66
**Type:** length_function
**Original:** `:NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Converted:** `NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC']
  - functions: ['LENGTH']
  - operators: ['OR', 'IS NULL', 'AND', '>']
  - variables: ['V_THEME_DESC_PROPOSAL']

### Condition 67
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 68
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 69
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 70
**Type:** boolean_logic
**Original:** `:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 71
**Type:** null_check
**Original:** `:NEW.PORTF_PROJ_CD = 'Y' AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.PORTF_PROJ_CD = 'Y' AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.MOLECULE_ID']
  - operators: ['OR', '=', 'AND', 'IS NULL']

### Condition 72
**Type:** nvl_function
**Original:** `NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL`
**Converted:** `COALESCE(NEW.MANUAL_SHORT_DESC, NEW.THEME_DESC_PROPOSAL) IS NULL`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC', 'NEW.THEME_DESC_PROPOSAL']
  - functions: ['NVL']
  - operators: ['OR', 'IS NULL']

### Condition 73
**Type:** length_function
**Original:** `LENGTH(:NEW.THEME_NO)`
**Converted:** `LENGTH(NEW.THEME_NO)`
**Components:**
  - columns: ['NEW.THEME_NO']
  - functions: ['LENGTH']

### Condition 74
**Type:** unknown
**Original:** `4`
**Converted:** `4`
**Components:**

### Condition 75
**Type:** unknown
**Original:** `5`
**Converted:** `5`
**Components:**

### Condition 76
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 77
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  5 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 78
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 79
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 80
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'N'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'N'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 81
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 82
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 83
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 84
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 85
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 86
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N' OR (:OLD.IN_PREP_IND = 'Y' AND :NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N' OR (OLD.IN_PREP_IND = 'Y' AND NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND', 'OLD.IN_PREP_IND', 'NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'OR', 'IN', 'IN', '=', 'AND', 'IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 87
**Type:** inequality
**Original:** `:NEW.THEME_NO <> :OLD.THEME_NO`
**Converted:** `NEW.THEME_NO != OLD.THEME_NO`
**Components:**
  - columns: ['NEW.THEME_NO', 'OLD.THEME_NO']
  - operators: ['<>']

### Condition 88
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 89
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' OR:NEW.IN_PREP_IND = 'Y')) UPPER(:NEW.PORTF_PROJ_CD`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' ORNEW.IN_PREP_IND = 'Y')) UPPER(NEW.PORTF_PROJ_CD`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.IN_PREP_IND', 'NEW.PORTF_PROJ_CD']
  - functions: ['UPPER', 'AND']
  - operators: ['OR', '=', 'AND', '<>', 'OR', 'IN', 'IN', '=', 'OR']
  - variables: ['V_STATUS_CD']
**Status:** warning

### Condition 90
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 91
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 92
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 93
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 94
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 95
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 96
**Type:** not_null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL']

### Condition 97
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 98
**Type:** range
**Original:** `V_SEC_MOL_CNT > 0`
**Converted:** `V_SEC_MOL_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEC_MOL_CNT']

### Condition 99
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 100
**Type:** date_function
**Original:** `TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)`
**Converted:** `DATE_TRUNC(TO_DATE(OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = DATE_TRUNC(CURRENT_DATE)`
**Components:**
  - columns: ['OLD.REGISTRAT_DATE']
  - functions: ['TRUNC', 'TRUNC']
  - operators: ['=']

### Condition 101
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 102
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 103
**Type:** equality
**Original:** `V_EVOLVED_NMP_CNT = 0`
**Converted:** `V_EVOLVED_NMP_CNT = 0`
**Components:**
  - operators: ['=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 104
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL AND :OLD.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NULL AND OLD.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 105
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NOT NULL AND :NEW.PROPOSAL_ID <> :OLD.PROPOSAL_ID`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NOT NULL AND NEW.PROPOSAL_ID <> OLD.PROPOSAL_ID`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL', 'AND', '<>']
**Status:** warning

### Condition 106
**Type:** nvl_function
**Original:** `NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0) AND NVL(:OLD.SHORT_NAME, '-') <> NVL(V_SHORT_NAME, '-')`
**Converted:** `COALESCE(NEW.PROPOSAL_ID, 0) = COALESCE(OLD.PROPOSAL_ID, 0) AND COALESCE(OLD.SHORT_NAME, '-') <> COALESCE(V_SHORT_NAME, '-')`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'OLD.SHORT_NAME']
  - functions: ['NVL', 'NVL', 'NVL', 'NVL']
  - operators: ['=', 'AND', 'OR', '<>', 'OR']
  - variables: ['V_SHORT_NAME']
**Status:** warning

### Condition 107
**Type:** range
**Original:** `V_EVOLVED_NMP_CNT > 0`
**Converted:** `V_EVOLVED_NMP_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 108
**Type:** not_null_check
**Original:** `INSERTING AND :NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(:NEW.THEME_NO) = 'Y'`
**Converted:** `INSERTING AND NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(NEW.THEME_NO) = 'Y'`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['GET_THEMES_RANGE_AUTOMATIC_NMP']
  - operators: ['IN', 'IN', 'AND', 'IS NOT NULL', 'AND', '=']
  - trigger_ops: ['INSERTING']
**Status:** warning

### Condition 109
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID']
  - operators: ['IS NOT NULL']

### Condition 110
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL OR (:NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Converted:** `NEW.PROPOSAL_ID IS NULL OR (NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'NEW.PROPOSAL_ID']
  - operators: ['IS NULL', 'OR', 'IS NOT NULL', 'AND', '=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 111
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 112
**Type:** equality
**Original:** `:NEW.IN_PREP_IND = 'Y'`
**Converted:** `NEW.IN_PREP_IND = 'Y'`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=']

### Condition 113
**Type:** inequality
**Original:** `:NEW.PORTF_PROJ_CD <> 'Y'`
**Converted:** `NEW.PORTF_PROJ_CD != 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - operators: ['OR', '<>']

### Condition 114
**Type:** inequality
**Original:** `:NEW.STATUS_DESC <> 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.STATUS_DESC != 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['<>', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 115
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 116
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 117
**Type:** null_check
**Original:** `V_MOLECULE_RG_NO IS NULL`
**Converted:** `V_MOLECULE_RG_NO IS NULL`
**Components:**
  - operators: ['IS NULL']
  - variables: ['V_MOLECULE_RG_NO']

### Condition 118
**Type:** equality
**Original:** `V_COMPARATOR_IND = 'Y'`
**Converted:** `V_COMPARATOR_IND = 'Y'`
**Components:**
  - operators: ['OR', 'IN', '=']
  - variables: ['V_COMPARATOR_IND']

### Condition 119
**Type:** not_null_check
**Original:** `:NEW.STATUS_DESC IS NOT NULL`
**Converted:** `NEW.STATUS_DESC IS NOT NULL`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['IS NOT NULL']

### Condition 120
**Type:** not_null_check
**Original:** `:NEW.DBA_DESC_CONCAT IS NOT NULL`
**Converted:** `NEW.DBA_DESC_CONCAT IS NOT NULL`
**Components:**
  - columns: ['NEW.DBA_DESC_CONCAT']
  - operators: ['IS NOT NULL']

### Condition 121
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 122
**Type:** length_function
**Original:** `:NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Converted:** `NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC']
  - functions: ['LENGTH']
  - operators: ['OR', 'IS NULL', 'AND', '>']
  - variables: ['V_THEME_DESC_PROPOSAL']

### Condition 123
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 124
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 125
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 126
**Type:** boolean_logic
**Original:** `:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 127
**Type:** null_check
**Original:** `:NEW.PORTF_PROJ_CD = 'Y' AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.PORTF_PROJ_CD = 'Y' AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.MOLECULE_ID']
  - operators: ['OR', '=', 'AND', 'IS NULL']

### Condition 128
**Type:** nvl_function
**Original:** `NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL`
**Converted:** `COALESCE(NEW.MANUAL_SHORT_DESC, NEW.THEME_DESC_PROPOSAL) IS NULL`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC', 'NEW.THEME_DESC_PROPOSAL']
  - functions: ['NVL']
  - operators: ['OR', 'IS NULL']

### Condition 129
**Type:** length_function
**Original:** `LENGTH(:NEW.THEME_NO)`
**Converted:** `LENGTH(NEW.THEME_NO)`
**Components:**
  - columns: ['NEW.THEME_NO']
  - functions: ['LENGTH']

### Condition 130
**Type:** unknown
**Original:** `4`
**Converted:** `4`
**Components:**

### Condition 131
**Type:** unknown
**Original:** `5`
**Converted:** `5`
**Components:**

### Condition 132
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 133
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  5 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 134
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 135
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 136
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'N'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'N'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 137
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 138
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 139
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 140
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 141
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 142
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N' OR (:OLD.IN_PREP_IND = 'Y' AND :NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N' OR (OLD.IN_PREP_IND = 'Y' AND NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND', 'OLD.IN_PREP_IND', 'NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'OR', 'IN', 'IN', '=', 'AND', 'IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 143
**Type:** inequality
**Original:** `:NEW.THEME_NO <> :OLD.THEME_NO`
**Converted:** `NEW.THEME_NO != OLD.THEME_NO`
**Components:**
  - columns: ['NEW.THEME_NO', 'OLD.THEME_NO']
  - operators: ['<>']

### Condition 144
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 145
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' OR:NEW.IN_PREP_IND = 'Y')) UPPER(:NEW.PORTF_PROJ_CD`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' ORNEW.IN_PREP_IND = 'Y')) UPPER(NEW.PORTF_PROJ_CD`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.IN_PREP_IND', 'NEW.PORTF_PROJ_CD']
  - functions: ['UPPER', 'AND']
  - operators: ['OR', '=', 'AND', '<>', 'OR', 'IN', 'IN', '=', 'OR']
  - variables: ['V_STATUS_CD']
**Status:** warning

### Condition 146
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 147
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 148
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 149
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 150
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 151
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 152
**Type:** not_null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL']

### Condition 153
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 154
**Type:** range
**Original:** `V_SEC_MOL_CNT > 0`
**Converted:** `V_SEC_MOL_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEC_MOL_CNT']

### Condition 155
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 156
**Type:** date_function
**Original:** `TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)`
**Converted:** `DATE_TRUNC(TO_DATE(OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = DATE_TRUNC(CURRENT_DATE)`
**Components:**
  - columns: ['OLD.REGISTRAT_DATE']
  - functions: ['TRUNC', 'TRUNC']
  - operators: ['=']

### Condition 157
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 158
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 159
**Type:** equality
**Original:** `V_EVOLVED_NMP_CNT = 0`
**Converted:** `V_EVOLVED_NMP_CNT = 0`
**Components:**
  - operators: ['=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 160
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL AND :OLD.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NULL AND OLD.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 161
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NOT NULL AND :NEW.PROPOSAL_ID <> :OLD.PROPOSAL_ID`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NOT NULL AND NEW.PROPOSAL_ID <> OLD.PROPOSAL_ID`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL', 'AND', '<>']
**Status:** warning

### Condition 162
**Type:** nvl_function
**Original:** `NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0) AND NVL(:OLD.SHORT_NAME, '-') <> NVL(V_SHORT_NAME, '-')`
**Converted:** `COALESCE(NEW.PROPOSAL_ID, 0) = COALESCE(OLD.PROPOSAL_ID, 0) AND COALESCE(OLD.SHORT_NAME, '-') <> COALESCE(V_SHORT_NAME, '-')`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'OLD.SHORT_NAME']
  - functions: ['NVL', 'NVL', 'NVL', 'NVL']
  - operators: ['=', 'AND', 'OR', '<>', 'OR']
  - variables: ['V_SHORT_NAME']
**Status:** warning

### Condition 163
**Type:** range
**Original:** `V_EVOLVED_NMP_CNT > 0`
**Converted:** `V_EVOLVED_NMP_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 164
**Type:** not_null_check
**Original:** `INSERTING AND :NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(:NEW.THEME_NO) = 'Y'`
**Converted:** `INSERTING AND NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(NEW.THEME_NO) = 'Y'`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['GET_THEMES_RANGE_AUTOMATIC_NMP']
  - operators: ['IN', 'IN', 'AND', 'IS NOT NULL', 'AND', '=']
  - trigger_ops: ['INSERTING']
**Status:** warning

### Condition 165
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID']
  - operators: ['IS NOT NULL']

### Condition 166
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL OR (:NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Converted:** `NEW.PROPOSAL_ID IS NULL OR (NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'NEW.PROPOSAL_ID']
  - operators: ['IS NULL', 'OR', 'IS NOT NULL', 'AND', '=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 167
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 168
**Type:** equality
**Original:** `:NEW.IN_PREP_IND = 'Y'`
**Converted:** `NEW.IN_PREP_IND = 'Y'`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=']

### Condition 169
**Type:** inequality
**Original:** `:NEW.PORTF_PROJ_CD <> 'Y'`
**Converted:** `NEW.PORTF_PROJ_CD != 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - operators: ['OR', '<>']

### Condition 170
**Type:** inequality
**Original:** `:NEW.STATUS_DESC <> 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.STATUS_DESC != 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['<>', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 171
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 172
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 173
**Type:** null_check
**Original:** `V_MOLECULE_RG_NO IS NULL`
**Converted:** `V_MOLECULE_RG_NO IS NULL`
**Components:**
  - operators: ['IS NULL']
  - variables: ['V_MOLECULE_RG_NO']

### Condition 174
**Type:** equality
**Original:** `V_COMPARATOR_IND = 'Y'`
**Converted:** `V_COMPARATOR_IND = 'Y'`
**Components:**
  - operators: ['OR', 'IN', '=']
  - variables: ['V_COMPARATOR_IND']

### Condition 175
**Type:** not_null_check
**Original:** `:NEW.STATUS_DESC IS NOT NULL`
**Converted:** `NEW.STATUS_DESC IS NOT NULL`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['IS NOT NULL']

### Condition 176
**Type:** not_null_check
**Original:** `:NEW.DBA_DESC_CONCAT IS NOT NULL`
**Converted:** `NEW.DBA_DESC_CONCAT IS NOT NULL`
**Components:**
  - columns: ['NEW.DBA_DESC_CONCAT']
  - operators: ['IS NOT NULL']

### Condition 177
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 178
**Type:** length_function
**Original:** `:NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Converted:** `NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC']
  - functions: ['LENGTH']
  - operators: ['OR', 'IS NULL', 'AND', '>']
  - variables: ['V_THEME_DESC_PROPOSAL']

### Condition 179
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 180
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 181
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 182
**Type:** boolean_logic
**Original:** `:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 183
**Type:** null_check
**Original:** `:NEW.PORTF_PROJ_CD = 'Y' AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.PORTF_PROJ_CD = 'Y' AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.MOLECULE_ID']
  - operators: ['OR', '=', 'AND', 'IS NULL']

### Condition 184
**Type:** nvl_function
**Original:** `NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL`
**Converted:** `COALESCE(NEW.MANUAL_SHORT_DESC, NEW.THEME_DESC_PROPOSAL) IS NULL`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC', 'NEW.THEME_DESC_PROPOSAL']
  - functions: ['NVL']
  - operators: ['OR', 'IS NULL']

### Condition 185
**Type:** length_function
**Original:** `LENGTH(:NEW.THEME_NO)`
**Converted:** `LENGTH(NEW.THEME_NO)`
**Components:**
  - columns: ['NEW.THEME_NO']
  - functions: ['LENGTH']

### Condition 186
**Type:** unknown
**Original:** `4`
**Converted:** `4`
**Components:**

### Condition 187
**Type:** unknown
**Original:** `5`
**Converted:** `5`
**Components:**

### Condition 188
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 189
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  5 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 190
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 191
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 192
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'N'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'N'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 193
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 194
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 195
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 196
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 197
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 198
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N' OR (:OLD.IN_PREP_IND = 'Y' AND :NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N' OR (OLD.IN_PREP_IND = 'Y' AND NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND', 'OLD.IN_PREP_IND', 'NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'OR', 'IN', 'IN', '=', 'AND', 'IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 199
**Type:** inequality
**Original:** `:NEW.THEME_NO <> :OLD.THEME_NO`
**Converted:** `NEW.THEME_NO != OLD.THEME_NO`
**Components:**
  - columns: ['NEW.THEME_NO', 'OLD.THEME_NO']
  - operators: ['<>']

### Condition 200
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 201
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' OR:NEW.IN_PREP_IND = 'Y')) UPPER(:NEW.PORTF_PROJ_CD`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' ORNEW.IN_PREP_IND = 'Y')) UPPER(NEW.PORTF_PROJ_CD`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.IN_PREP_IND', 'NEW.PORTF_PROJ_CD']
  - functions: ['UPPER', 'AND']
  - operators: ['OR', '=', 'AND', '<>', 'OR', 'IN', 'IN', '=', 'OR']
  - variables: ['V_STATUS_CD']
**Status:** warning

### Condition 202
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 203
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 204
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 205
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 206
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 207
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 208
**Type:** not_null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL']

### Condition 209
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 210
**Type:** range
**Original:** `V_SEC_MOL_CNT > 0`
**Converted:** `V_SEC_MOL_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEC_MOL_CNT']

### Condition 211
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 212
**Type:** date_function
**Original:** `TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)`
**Converted:** `DATE_TRUNC(TO_DATE(OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = DATE_TRUNC(CURRENT_DATE)`
**Components:**
  - columns: ['OLD.REGISTRAT_DATE']
  - functions: ['TRUNC', 'TRUNC']
  - operators: ['=']

### Condition 213
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 214
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 215
**Type:** equality
**Original:** `V_EVOLVED_NMP_CNT = 0`
**Converted:** `V_EVOLVED_NMP_CNT = 0`
**Components:**
  - operators: ['=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 216
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL AND :OLD.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NULL AND OLD.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 217
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NOT NULL AND :NEW.PROPOSAL_ID <> :OLD.PROPOSAL_ID`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NOT NULL AND NEW.PROPOSAL_ID <> OLD.PROPOSAL_ID`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL', 'AND', '<>']
**Status:** warning

### Condition 218
**Type:** nvl_function
**Original:** `NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0) AND NVL(:OLD.SHORT_NAME, '-') <> NVL(V_SHORT_NAME, '-')`
**Converted:** `COALESCE(NEW.PROPOSAL_ID, 0) = COALESCE(OLD.PROPOSAL_ID, 0) AND COALESCE(OLD.SHORT_NAME, '-') <> COALESCE(V_SHORT_NAME, '-')`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'OLD.SHORT_NAME']
  - functions: ['NVL', 'NVL', 'NVL', 'NVL']
  - operators: ['=', 'AND', 'OR', '<>', 'OR']
  - variables: ['V_SHORT_NAME']
**Status:** warning

### Condition 219
**Type:** range
**Original:** `V_EVOLVED_NMP_CNT > 0`
**Converted:** `V_EVOLVED_NMP_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 220
**Type:** not_null_check
**Original:** `INSERTING AND :NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(:NEW.THEME_NO) = 'Y'`
**Converted:** `INSERTING AND NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(NEW.THEME_NO) = 'Y'`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['GET_THEMES_RANGE_AUTOMATIC_NMP']
  - operators: ['IN', 'IN', 'AND', 'IS NOT NULL', 'AND', '=']
  - trigger_ops: ['INSERTING']
**Status:** warning

### Condition 221
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID']
  - operators: ['IS NOT NULL']

### Condition 222
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL OR (:NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Converted:** `NEW.PROPOSAL_ID IS NULL OR (NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'NEW.PROPOSAL_ID']
  - operators: ['IS NULL', 'OR', 'IS NOT NULL', 'AND', '=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 223
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 224
**Type:** equality
**Original:** `:NEW.IN_PREP_IND = 'Y'`
**Converted:** `NEW.IN_PREP_IND = 'Y'`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=']

### Condition 225
**Type:** inequality
**Original:** `:NEW.PORTF_PROJ_CD <> 'Y'`
**Converted:** `NEW.PORTF_PROJ_CD != 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - operators: ['OR', '<>']

### Condition 226
**Type:** inequality
**Original:** `:NEW.STATUS_DESC <> 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.STATUS_DESC != 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['<>', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 227
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 228
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 229
**Type:** null_check
**Original:** `V_MOLECULE_RG_NO IS NULL`
**Converted:** `V_MOLECULE_RG_NO IS NULL`
**Components:**
  - operators: ['IS NULL']
  - variables: ['V_MOLECULE_RG_NO']

### Condition 230
**Type:** equality
**Original:** `V_COMPARATOR_IND = 'Y'`
**Converted:** `V_COMPARATOR_IND = 'Y'`
**Components:**
  - operators: ['OR', 'IN', '=']
  - variables: ['V_COMPARATOR_IND']

### Condition 231
**Type:** not_null_check
**Original:** `:NEW.STATUS_DESC IS NOT NULL`
**Converted:** `NEW.STATUS_DESC IS NOT NULL`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['IS NOT NULL']

### Condition 232
**Type:** not_null_check
**Original:** `:NEW.DBA_DESC_CONCAT IS NOT NULL`
**Converted:** `NEW.DBA_DESC_CONCAT IS NOT NULL`
**Components:**
  - columns: ['NEW.DBA_DESC_CONCAT']
  - operators: ['IS NOT NULL']

### Condition 233
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 234
**Type:** length_function
**Original:** `:NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Converted:** `NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC']
  - functions: ['LENGTH']
  - operators: ['OR', 'IS NULL', 'AND', '>']
  - variables: ['V_THEME_DESC_PROPOSAL']

### Condition 235
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 236
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 237
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 238
**Type:** boolean_logic
**Original:** `:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 239
**Type:** null_check
**Original:** `:NEW.PORTF_PROJ_CD = 'Y' AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.PORTF_PROJ_CD = 'Y' AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.MOLECULE_ID']
  - operators: ['OR', '=', 'AND', 'IS NULL']

### Condition 240
**Type:** nvl_function
**Original:** `NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL`
**Converted:** `COALESCE(NEW.MANUAL_SHORT_DESC, NEW.THEME_DESC_PROPOSAL) IS NULL`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC', 'NEW.THEME_DESC_PROPOSAL']
  - functions: ['NVL']
  - operators: ['OR', 'IS NULL']

### Condition 241
**Type:** length_function
**Original:** `LENGTH(:NEW.THEME_NO)`
**Converted:** `LENGTH(NEW.THEME_NO)`
**Components:**
  - columns: ['NEW.THEME_NO']
  - functions: ['LENGTH']

### Condition 242
**Type:** unknown
**Original:** `4`
**Converted:** `4`
**Components:**

### Condition 243
**Type:** unknown
**Original:** `5`
**Converted:** `5`
**Components:**

### Condition 244
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 245
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  5 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 246
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 247
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 248
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'N'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'N'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 249
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 250
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 251
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 252
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 253
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 254
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N' OR (:OLD.IN_PREP_IND = 'Y' AND :NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N' OR (OLD.IN_PREP_IND = 'Y' AND NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND', 'OLD.IN_PREP_IND', 'NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'OR', 'IN', 'IN', '=', 'AND', 'IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 255
**Type:** inequality
**Original:** `:NEW.THEME_NO <> :OLD.THEME_NO`
**Converted:** `NEW.THEME_NO != OLD.THEME_NO`
**Components:**
  - columns: ['NEW.THEME_NO', 'OLD.THEME_NO']
  - operators: ['<>']

### Condition 256
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 257
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' OR:NEW.IN_PREP_IND = 'Y')) UPPER(:NEW.PORTF_PROJ_CD`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' ORNEW.IN_PREP_IND = 'Y')) UPPER(NEW.PORTF_PROJ_CD`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.IN_PREP_IND', 'NEW.PORTF_PROJ_CD']
  - functions: ['UPPER', 'AND']
  - operators: ['OR', '=', 'AND', '<>', 'OR', 'IN', 'IN', '=', 'OR']
  - variables: ['V_STATUS_CD']
**Status:** warning

### Condition 258
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 259
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 260
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 261
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 262
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 263
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 264
**Type:** not_null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL']

### Condition 265
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 266
**Type:** range
**Original:** `V_SEC_MOL_CNT > 0`
**Converted:** `V_SEC_MOL_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEC_MOL_CNT']

### Condition 267
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 268
**Type:** date_function
**Original:** `TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)`
**Converted:** `DATE_TRUNC(TO_DATE(OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = DATE_TRUNC(CURRENT_DATE)`
**Components:**
  - columns: ['OLD.REGISTRAT_DATE']
  - functions: ['TRUNC', 'TRUNC']
  - operators: ['=']

### Condition 269
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 270
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 271
**Type:** equality
**Original:** `V_EVOLVED_NMP_CNT = 0`
**Converted:** `V_EVOLVED_NMP_CNT = 0`
**Components:**
  - operators: ['=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 272
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL AND :OLD.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NULL AND OLD.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 273
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NOT NULL AND :NEW.PROPOSAL_ID <> :OLD.PROPOSAL_ID`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NOT NULL AND NEW.PROPOSAL_ID <> OLD.PROPOSAL_ID`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL', 'AND', '<>']
**Status:** warning

### Condition 274
**Type:** nvl_function
**Original:** `NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0) AND NVL(:OLD.SHORT_NAME, '-') <> NVL(V_SHORT_NAME, '-')`
**Converted:** `COALESCE(NEW.PROPOSAL_ID, 0) = COALESCE(OLD.PROPOSAL_ID, 0) AND COALESCE(OLD.SHORT_NAME, '-') <> COALESCE(V_SHORT_NAME, '-')`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'OLD.SHORT_NAME']
  - functions: ['NVL', 'NVL', 'NVL', 'NVL']
  - operators: ['=', 'AND', 'OR', '<>', 'OR']
  - variables: ['V_SHORT_NAME']
**Status:** warning

### Condition 275
**Type:** range
**Original:** `V_EVOLVED_NMP_CNT > 0`
**Converted:** `V_EVOLVED_NMP_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 276
**Type:** not_null_check
**Original:** `INSERTING AND :NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(:NEW.THEME_NO) = 'Y'`
**Converted:** `INSERTING AND NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(NEW.THEME_NO) = 'Y'`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['GET_THEMES_RANGE_AUTOMATIC_NMP']
  - operators: ['IN', 'IN', 'AND', 'IS NOT NULL', 'AND', '=']
  - trigger_ops: ['INSERTING']
**Status:** warning

### Condition 277
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID']
  - operators: ['IS NOT NULL']

### Condition 278
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL OR (:NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Converted:** `NEW.PROPOSAL_ID IS NULL OR (NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'NEW.PROPOSAL_ID']
  - operators: ['IS NULL', 'OR', 'IS NOT NULL', 'AND', '=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 279
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 280
**Type:** equality
**Original:** `:NEW.IN_PREP_IND = 'Y'`
**Converted:** `NEW.IN_PREP_IND = 'Y'`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=']

### Condition 281
**Type:** inequality
**Original:** `:NEW.PORTF_PROJ_CD <> 'Y'`
**Converted:** `NEW.PORTF_PROJ_CD != 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - operators: ['OR', '<>']

### Condition 282
**Type:** inequality
**Original:** `:NEW.STATUS_DESC <> 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.STATUS_DESC != 'CLOSED' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['<>', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 283
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 284
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 285
**Type:** null_check
**Original:** `V_MOLECULE_RG_NO IS NULL`
**Converted:** `V_MOLECULE_RG_NO IS NULL`
**Components:**
  - operators: ['IS NULL']
  - variables: ['V_MOLECULE_RG_NO']

### Condition 286
**Type:** equality
**Original:** `V_COMPARATOR_IND = 'Y'`
**Converted:** `V_COMPARATOR_IND = 'Y'`
**Components:**
  - operators: ['OR', 'IN', '=']
  - variables: ['V_COMPARATOR_IND']

### Condition 287
**Type:** not_null_check
**Original:** `:NEW.STATUS_DESC IS NOT NULL`
**Converted:** `NEW.STATUS_DESC IS NOT NULL`
**Components:**
  - columns: ['NEW.STATUS_DESC']
  - operators: ['IS NOT NULL']

### Condition 288
**Type:** not_null_check
**Original:** `:NEW.DBA_DESC_CONCAT IS NOT NULL`
**Converted:** `NEW.DBA_DESC_CONCAT IS NOT NULL`
**Components:**
  - columns: ['NEW.DBA_DESC_CONCAT']
  - operators: ['IS NOT NULL']

### Condition 289
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 290
**Type:** length_function
**Original:** `:NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Converted:** `NEW.MANUAL_SHORT_DESC IS NULL AND LENGTH(V_THEME_DESC_PROPOSAL) > 30`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC']
  - functions: ['LENGTH']
  - operators: ['OR', 'IS NULL', 'AND', '>']
  - variables: ['V_THEME_DESC_PROPOSAL']

### Condition 291
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 292
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 293
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 294
**Type:** boolean_logic
**Original:** `:NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Converted:** `NEW.IN_PREP_IND = 'N' AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 295
**Type:** null_check
**Original:** `:NEW.PORTF_PROJ_CD = 'Y' AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.PORTF_PROJ_CD = 'Y' AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.MOLECULE_ID']
  - operators: ['OR', '=', 'AND', 'IS NULL']

### Condition 296
**Type:** nvl_function
**Original:** `NVL(:NEW.MANUAL_SHORT_DESC, :NEW.THEME_DESC_PROPOSAL) IS NULL`
**Converted:** `COALESCE(NEW.MANUAL_SHORT_DESC, NEW.THEME_DESC_PROPOSAL) IS NULL`
**Components:**
  - columns: ['NEW.MANUAL_SHORT_DESC', 'NEW.THEME_DESC_PROPOSAL']
  - functions: ['NVL']
  - operators: ['OR', 'IS NULL']

### Condition 297
**Type:** length_function
**Original:** `LENGTH(:NEW.THEME_NO)`
**Converted:** `LENGTH(NEW.THEME_NO)`
**Components:**
  - columns: ['NEW.THEME_NO']
  - functions: ['LENGTH']

### Condition 298
**Type:** unknown
**Original:** `4`
**Converted:** `4`
**Components:**

### Condition 299
**Type:** unknown
**Original:** `5`
**Converted:** `5`
**Components:**

### Condition 300
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 301
**Type:** substr_function
**Original:** `SUBSTR(:NEW.THEME_NO, 1, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 2, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 3, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 4, 1) NOT BETWEEN 0 AND 9 OR SUBSTR(:NEW.THEME_NO, 5, 1) NOT BETWEEN 0 AND 9`
**Converted:** `SUBSTRING(NEW.THEME_NO FROM  1 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  2 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  3 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  4 FOR  1) NOT BETWEEN 0 AND 9 OR SUBSTRING(NEW.THEME_NO FROM  5 FOR  1) NOT BETWEEN 0 AND 9`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR', 'SUBSTR']
  - operators: ['BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND', 'OR', 'BETWEEN', 'AND']

### Condition 302
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 303
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 304
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'N'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'N'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 305
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 306
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y'`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y'`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD']
  - functions: ['UPPER']
  - operators: ['OR', '=']

### Condition 307
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 308
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 309
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 310
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N' OR (:OLD.IN_PREP_IND = 'Y' AND :NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N' OR (OLD.IN_PREP_IND = 'Y' AND NEW.IN_PREP_IND = 'N')) AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND', 'OLD.IN_PREP_IND', 'NEW.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'OR', 'IN', 'IN', '=', 'AND', 'IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 311
**Type:** inequality
**Original:** `:NEW.THEME_NO <> :OLD.THEME_NO`
**Converted:** `NEW.THEME_NO != OLD.THEME_NO`
**Components:**
  - columns: ['NEW.THEME_NO', 'OLD.THEME_NO']
  - operators: ['<>']

### Condition 312
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 313
**Type:** upper_function
**Original:** `UPPER(:NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' OR:NEW.IN_PREP_IND = 'Y')) UPPER(:NEW.PORTF_PROJ_CD`
**Converted:** `UPPER(NEW.PORTF_PROJ_CD) = 'Y' AND(V_STATUS_CD <> 'C' ORNEW.IN_PREP_IND = 'Y')) UPPER(NEW.PORTF_PROJ_CD`
**Components:**
  - columns: ['NEW.PORTF_PROJ_CD', 'NEW.IN_PREP_IND', 'NEW.PORTF_PROJ_CD']
  - functions: ['UPPER', 'AND']
  - operators: ['OR', '=', 'AND', '<>', 'OR', 'IN', 'IN', '=', 'OR']
  - variables: ['V_STATUS_CD']
**Status:** warning

### Condition 314
**Type:** length_function
**Original:** `:NEW.THEME_DESC IS NULL OR LENGTH(:NEW.THEME_DESC) = 0`
**Converted:** `NEW.THEME_DESC IS NULL OR LENGTH(NEW.THEME_DESC) = 0`
**Components:**
  - columns: ['NEW.THEME_DESC', 'NEW.THEME_DESC']
  - functions: ['LENGTH']
  - operators: ['IS NULL', 'OR', '=']

### Condition 315
**Type:** length_function
**Original:** `LENGTH(V_DESCRIPTION) > 90`
**Converted:** `LENGTH(V_DESCRIPTION) > 90`
**Components:**
  - functions: ['LENGTH']
  - operators: ['>']
  - variables: ['V_DESCRIPTION']

### Condition 316
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 317
**Type:** equality
**Original:** `:NEW.OFFICIAL_IND = 'N'`
**Converted:** `NEW.OFFICIAL_IND = 'N'`
**Components:**
  - columns: ['NEW.OFFICIAL_IND']
  - operators: ['IN', '=']

### Condition 318
**Type:** range
**Original:** `V_COUNTER > 0`
**Converted:** `V_COUNTER > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNTER']

### Condition 319
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 320
**Type:** not_null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL']

### Condition 321
**Type:** null_check
**Original:** `:OLD.MOLECULE_ID IS NOT NULL AND :NEW.MOLECULE_ID IS NULL`
**Converted:** `OLD.MOLECULE_ID IS NOT NULL AND NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['OLD.MOLECULE_ID', 'NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 322
**Type:** range
**Original:** `V_SEC_MOL_CNT > 0`
**Converted:** `V_SEC_MOL_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEC_MOL_CNT']

### Condition 323
**Type:** boolean_logic
**Original:** `(:OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Converted:** `(OLD.IN_PREP_IND = 'N') AND V_IS_ADMIN_CNT = 0`
**Components:**
  - columns: ['OLD.IN_PREP_IND']
  - operators: ['IN', 'IN', '=', 'AND', 'IN', '=']
  - variables: ['V_IS_ADMIN_CNT']

### Condition 324
**Type:** date_function
**Original:** `TRUNC(TO_DATE(:OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = TRUNC(SYSDATE)`
**Converted:** `DATE_TRUNC(TO_DATE(OLD.REGISTRAT_DATE, 'DD-MM-YYYY')) = DATE_TRUNC(CURRENT_DATE)`
**Components:**
  - columns: ['OLD.REGISTRAT_DATE']
  - functions: ['TRUNC', 'TRUNC']
  - operators: ['=']

### Condition 325
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 326
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NULL']

### Condition 327
**Type:** equality
**Original:** `V_EVOLVED_NMP_CNT = 0`
**Converted:** `V_EVOLVED_NMP_CNT = 0`
**Components:**
  - operators: ['=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 328
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL AND :OLD.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NULL AND OLD.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NULL', 'AND', 'IS NOT NULL']

### Condition 329
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL AND :OLD.PROPOSAL_ID IS NOT NULL AND :NEW.PROPOSAL_ID <> :OLD.PROPOSAL_ID`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL AND OLD.PROPOSAL_ID IS NOT NULL AND NEW.PROPOSAL_ID <> OLD.PROPOSAL_ID`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID']
  - operators: ['IS NOT NULL', 'AND', 'IS NOT NULL', 'AND', '<>']
**Status:** warning

### Condition 330
**Type:** nvl_function
**Original:** `NVL(:NEW.PROPOSAL_ID, 0) = NVL(:OLD.PROPOSAL_ID, 0) AND NVL(:OLD.SHORT_NAME, '-') <> NVL(V_SHORT_NAME, '-')`
**Converted:** `COALESCE(NEW.PROPOSAL_ID, 0) = COALESCE(OLD.PROPOSAL_ID, 0) AND COALESCE(OLD.SHORT_NAME, '-') <> COALESCE(V_SHORT_NAME, '-')`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'OLD.PROPOSAL_ID', 'OLD.SHORT_NAME']
  - functions: ['NVL', 'NVL', 'NVL', 'NVL']
  - operators: ['=', 'AND', 'OR', '<>', 'OR']
  - variables: ['V_SHORT_NAME']
**Status:** warning

### Condition 331
**Type:** range
**Original:** `V_EVOLVED_NMP_CNT > 0`
**Converted:** `V_EVOLVED_NMP_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 332
**Type:** not_null_check
**Original:** `INSERTING AND :NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(:NEW.THEME_NO) = 'Y'`
**Converted:** `INSERTING AND NEW.THEME_NO IS NOT NULL AND GMD_UTIL_THEMES.GET_THEMES_RANGE_AUTOMATIC_NMP(NEW.THEME_NO) = 'Y'`
**Components:**
  - columns: ['NEW.THEME_NO', 'NEW.THEME_NO']
  - functions: ['GET_THEMES_RANGE_AUTOMATIC_NMP']
  - operators: ['IN', 'IN', 'AND', 'IS NOT NULL', 'AND', '=']
  - trigger_ops: ['INSERTING']
**Status:** warning

### Condition 333
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_ID IS NOT NULL`
**Converted:** `NEW.PROPOSAL_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_ID']
  - operators: ['IS NOT NULL']

### Condition 334
**Type:** null_check
**Original:** `:NEW.PROPOSAL_ID IS NULL OR (:NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Converted:** `NEW.PROPOSAL_ID IS NULL OR (NEW.PROPOSAL_ID IS NOT NULL AND V_EVOLVED_NMP_CNT = 0)`
**Components:**
  - columns: ['NEW.PROPOSAL_ID', 'NEW.PROPOSAL_ID']
  - operators: ['IS NULL', 'OR', 'IS NOT NULL', 'AND', '=']
  - variables: ['V_EVOLVED_NMP_CNT']

### Condition 335
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 336
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 337
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 338
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 339
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 340
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Converted:** `NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['>', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 341
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> NVL (:OLD.MOLECULE_ID, '-1')`
**Converted:** `NEW.MOLECULE_ID != NVL (OLD.MOLECULE_ID, '-1')`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID']
  - operators: ['<>']

### Condition 342
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 343
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 344
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 345
**Type:** equality
**Original:** `:NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['=', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 346
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['<', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 347
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 348
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 349
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 350
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 351
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO AND :NEW.MOLECULE_MAP_CHAR <> :OLD.MOLECULE_MAP_CHAR`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO AND NEW.MOLECULE_MAP_CHAR != OLD.MOLECULE_MAP_CHAR`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_MAP_CHAR', 'OLD.MOLECULE_MAP_CHAR']
  - operators: ['=', 'AND', '=', 'AND', '<>']

### Condition 352
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['=', 'AND', '<>']

### Condition 353
**Type:** range
**Original:** `:OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO`
**Converted:** `OLD.MOLECULE_SEQ_NO < NEW.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_SEQ_NO']
  - operators: ['<']

### Condition 354
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 355
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID != OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '<>']

### Condition 356
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 357
**Type:** inequality
**Original:** `(:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID) AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO`
**Converted:** `(NEW.MOLECULE_ID != OLD.MOLECULE_ID) AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '=']

### Condition 358
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 359
**Type:** range
**Original:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Converted:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEQ_NO_DUPLICATE_CNT']

### Condition 360
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 361
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 362
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 363
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 364
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Converted:** `NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['>', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 365
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> NVL (:OLD.MOLECULE_ID, '-1')`
**Converted:** `NEW.MOLECULE_ID != NVL (OLD.MOLECULE_ID, '-1')`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID']
  - operators: ['<>']

### Condition 366
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 367
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 368
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 369
**Type:** equality
**Original:** `:NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['=', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 370
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['<', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 371
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 372
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 373
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 374
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 375
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO AND :NEW.MOLECULE_MAP_CHAR <> :OLD.MOLECULE_MAP_CHAR`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO AND NEW.MOLECULE_MAP_CHAR != OLD.MOLECULE_MAP_CHAR`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_MAP_CHAR', 'OLD.MOLECULE_MAP_CHAR']
  - operators: ['=', 'AND', '=', 'AND', '<>']

### Condition 376
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['=', 'AND', '<>']

### Condition 377
**Type:** range
**Original:** `:OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO`
**Converted:** `OLD.MOLECULE_SEQ_NO < NEW.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_SEQ_NO']
  - operators: ['<']

### Condition 378
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 379
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID != OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '<>']

### Condition 380
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 381
**Type:** inequality
**Original:** `(:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID) AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO`
**Converted:** `(NEW.MOLECULE_ID != OLD.MOLECULE_ID) AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '=']

### Condition 382
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 383
**Type:** range
**Original:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Converted:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEQ_NO_DUPLICATE_CNT']

### Condition 384
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 385
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 386
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 387
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 388
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Converted:** `NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['>', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 389
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> NVL (:OLD.MOLECULE_ID, '-1')`
**Converted:** `NEW.MOLECULE_ID != NVL (OLD.MOLECULE_ID, '-1')`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID']
  - operators: ['<>']

### Condition 390
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 391
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 392
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 393
**Type:** equality
**Original:** `:NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['=', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 394
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['<', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 395
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 396
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 397
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 398
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 399
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO AND :NEW.MOLECULE_MAP_CHAR <> :OLD.MOLECULE_MAP_CHAR`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO AND NEW.MOLECULE_MAP_CHAR != OLD.MOLECULE_MAP_CHAR`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_MAP_CHAR', 'OLD.MOLECULE_MAP_CHAR']
  - operators: ['=', 'AND', '=', 'AND', '<>']

### Condition 400
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['=', 'AND', '<>']

### Condition 401
**Type:** range
**Original:** `:OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO`
**Converted:** `OLD.MOLECULE_SEQ_NO < NEW.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_SEQ_NO']
  - operators: ['<']

### Condition 402
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 403
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID != OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '<>']

### Condition 404
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 405
**Type:** inequality
**Original:** `(:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID) AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO`
**Converted:** `(NEW.MOLECULE_ID != OLD.MOLECULE_ID) AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '=']

### Condition 406
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 407
**Type:** range
**Original:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Converted:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEQ_NO_DUPLICATE_CNT']

### Condition 408
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 409
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 410
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 411
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 412
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Converted:** `NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['>', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 413
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> NVL (:OLD.MOLECULE_ID, '-1')`
**Converted:** `NEW.MOLECULE_ID != NVL (OLD.MOLECULE_ID, '-1')`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID']
  - operators: ['<>']

### Condition 414
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 415
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 416
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 417
**Type:** equality
**Original:** `:NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['=', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 418
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['<', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 419
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 420
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 421
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 422
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 423
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO AND :NEW.MOLECULE_MAP_CHAR <> :OLD.MOLECULE_MAP_CHAR`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO AND NEW.MOLECULE_MAP_CHAR != OLD.MOLECULE_MAP_CHAR`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_MAP_CHAR', 'OLD.MOLECULE_MAP_CHAR']
  - operators: ['=', 'AND', '=', 'AND', '<>']

### Condition 424
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['=', 'AND', '<>']

### Condition 425
**Type:** range
**Original:** `:OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO`
**Converted:** `OLD.MOLECULE_SEQ_NO < NEW.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_SEQ_NO']
  - operators: ['<']

### Condition 426
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 427
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID != OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '<>']

### Condition 428
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 429
**Type:** inequality
**Original:** `(:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID) AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO`
**Converted:** `(NEW.MOLECULE_ID != OLD.MOLECULE_ID) AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '=']

### Condition 430
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 431
**Type:** range
**Original:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Converted:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEQ_NO_DUPLICATE_CNT']

### Condition 432
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 433
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 434
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 435
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 436
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Converted:** `NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['>', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 437
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> NVL (:OLD.MOLECULE_ID, '-1')`
**Converted:** `NEW.MOLECULE_ID != NVL (OLD.MOLECULE_ID, '-1')`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID']
  - operators: ['<>']

### Condition 438
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 439
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 440
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 441
**Type:** equality
**Original:** `:NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['=', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 442
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['<', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 443
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 444
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 445
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 446
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 447
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO AND :NEW.MOLECULE_MAP_CHAR <> :OLD.MOLECULE_MAP_CHAR`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO AND NEW.MOLECULE_MAP_CHAR != OLD.MOLECULE_MAP_CHAR`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_MAP_CHAR', 'OLD.MOLECULE_MAP_CHAR']
  - operators: ['=', 'AND', '=', 'AND', '<>']

### Condition 448
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['=', 'AND', '<>']

### Condition 449
**Type:** range
**Original:** `:OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO`
**Converted:** `OLD.MOLECULE_SEQ_NO < NEW.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_SEQ_NO']
  - operators: ['<']

### Condition 450
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 451
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID != OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '<>']

### Condition 452
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 453
**Type:** inequality
**Original:** `(:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID) AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO`
**Converted:** `(NEW.MOLECULE_ID != OLD.MOLECULE_ID) AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '=']

### Condition 454
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 455
**Type:** range
**Original:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Converted:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEQ_NO_DUPLICATE_CNT']

### Condition 456
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 457
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 458
**Type:** null_check
**Original:** `:NEW.MOLECULE_ID IS NULL`
**Converted:** `NEW.MOLECULE_ID IS NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NULL']

### Condition 459
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 460
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Converted:** `NEW.MOLECULE_SEQ_NO > V_COUNT_T_MAPPINGS`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['>', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 461
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> NVL (:OLD.MOLECULE_ID, '-1')`
**Converted:** `NEW.MOLECULE_ID != NVL (OLD.MOLECULE_ID, '-1')`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID']
  - operators: ['<>']

### Condition 462
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 463
**Type:** range
**Original:** `V_COUNT_T_MOL_MAP > 0`
**Converted:** `V_COUNT_T_MOL_MAP > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_COUNT_T_MOL_MAP']

### Condition 464
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 465
**Type:** equality
**Original:** `:NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO = V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['=', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 466
**Type:** range
**Original:** `:NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Converted:** `NEW.MOLECULE_SEQ_NO < V_COUNT_T_MAPPINGS + 1`
**Components:**
  - columns: ['NEW.MOLECULE_SEQ_NO']
  - operators: ['<', 'IN']
  - variables: ['V_COUNT_T_MAPPINGS']

### Condition 467
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 468
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 469
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 470
**Type:** not_null_check
**Original:** `:NEW.MOLECULE_ID IS NOT NULL`
**Converted:** `NEW.MOLECULE_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.MOLECULE_ID']
  - operators: ['IS NOT NULL']

### Condition 471
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO AND :NEW.MOLECULE_MAP_CHAR <> :OLD.MOLECULE_MAP_CHAR`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO AND NEW.MOLECULE_MAP_CHAR != OLD.MOLECULE_MAP_CHAR`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_MAP_CHAR', 'OLD.MOLECULE_MAP_CHAR']
  - operators: ['=', 'AND', '=', 'AND', '<>']

### Condition 472
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID = :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID = OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['=', 'AND', '<>']

### Condition 473
**Type:** range
**Original:** `:OLD.MOLECULE_SEQ_NO < :NEW.MOLECULE_SEQ_NO`
**Converted:** `OLD.MOLECULE_SEQ_NO < NEW.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['OLD.MOLECULE_SEQ_NO', 'NEW.MOLECULE_SEQ_NO']
  - operators: ['<']

### Condition 474
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 475
**Type:** inequality
**Original:** `:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID AND :NEW.MOLECULE_SEQ_NO <> :OLD.MOLECULE_SEQ_NO`
**Converted:** `NEW.MOLECULE_ID != OLD.MOLECULE_ID AND NEW.MOLECULE_SEQ_NO != OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '<>']

### Condition 476
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 477
**Type:** inequality
**Original:** `(:NEW.MOLECULE_ID <> :OLD.MOLECULE_ID) AND :NEW.MOLECULE_SEQ_NO = :OLD.MOLECULE_SEQ_NO`
**Converted:** `(NEW.MOLECULE_ID != OLD.MOLECULE_ID) AND NEW.MOLECULE_SEQ_NO = OLD.MOLECULE_SEQ_NO`
**Components:**
  - columns: ['NEW.MOLECULE_ID', 'OLD.MOLECULE_ID', 'NEW.MOLECULE_SEQ_NO', 'OLD.MOLECULE_SEQ_NO']
  - operators: ['<>', 'AND', '=']

### Condition 478
**Type:** unknown
**Original:** `INVALID_MAPPING_EXISTS`
**Converted:** `INVALID_MAPPING_EXISTS`
**Components:**
  - operators: ['IN', 'IN']

### Condition 479
**Type:** range
**Original:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Converted:** `V_SEQ_NO_DUPLICATE_CNT > 0`
**Components:**
  - operators: ['>']
  - variables: ['V_SEQ_NO_DUPLICATE_CNT']

### Condition 480
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 481
**Type:** range
**Original:** `CNTR > 0`
**Converted:** `CNTR > 0`
**Components:**
  - operators: ['>']

### Condition 482
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 483
**Type:** nvl_function
**Original:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L')`
**Converted:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN', 'AND', 'IN']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 484
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 485
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) = NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) = COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['=', 'AND', '<>']
**Status:** warning

### Condition 486
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 487
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) <> NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) <> COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>', 'AND', '<>']
**Status:** warning

### Condition 488
**Type:** boolean_logic
**Original:** `:NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Converted:** `NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD']
  - operators: ['=', 'AND', '>']

### Condition 489
**Type:** equality
**Original:** `TO_CHAR(:NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Converted:** `TO_CHAR(NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Components:**
  - columns: ['NEW.VALID_FROM']
  - functions: ['TO_CHAR']
  - operators: ['=']

### Condition 490
**Type:** equality
**Original:** `V_COMPANY_TYPE_CD = 'L'`
**Converted:** `V_COMPANY_TYPE_CD = 'L'`
**Components:**
  - operators: ['=']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 491
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN']

### Condition 492
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 493
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 494
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 495
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 496
**Type:** range
**Original:** `CNTR > 0`
**Converted:** `CNTR > 0`
**Components:**
  - operators: ['>']

### Condition 497
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 498
**Type:** nvl_function
**Original:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L')`
**Converted:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN', 'AND', 'IN']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 499
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 500
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) = NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) = COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['=', 'AND', '<>']
**Status:** warning

### Condition 501
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 502
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) <> NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) <> COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>', 'AND', '<>']
**Status:** warning

### Condition 503
**Type:** boolean_logic
**Original:** `:NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Converted:** `NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD']
  - operators: ['=', 'AND', '>']

### Condition 504
**Type:** equality
**Original:** `TO_CHAR(:NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Converted:** `TO_CHAR(NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Components:**
  - columns: ['NEW.VALID_FROM']
  - functions: ['TO_CHAR']
  - operators: ['=']

### Condition 505
**Type:** equality
**Original:** `V_COMPANY_TYPE_CD = 'L'`
**Converted:** `V_COMPANY_TYPE_CD = 'L'`
**Components:**
  - operators: ['=']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 506
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN']

### Condition 507
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 508
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 509
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 510
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 511
**Type:** range
**Original:** `CNTR > 0`
**Converted:** `CNTR > 0`
**Components:**
  - operators: ['>']

### Condition 512
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 513
**Type:** nvl_function
**Original:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L')`
**Converted:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN', 'AND', 'IN']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 514
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 515
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) = NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) = COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['=', 'AND', '<>']
**Status:** warning

### Condition 516
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 517
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) <> NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) <> COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>', 'AND', '<>']
**Status:** warning

### Condition 518
**Type:** boolean_logic
**Original:** `:NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Converted:** `NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD']
  - operators: ['=', 'AND', '>']

### Condition 519
**Type:** equality
**Original:** `TO_CHAR(:NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Converted:** `TO_CHAR(NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Components:**
  - columns: ['NEW.VALID_FROM']
  - functions: ['TO_CHAR']
  - operators: ['=']

### Condition 520
**Type:** equality
**Original:** `V_COMPANY_TYPE_CD = 'L'`
**Converted:** `V_COMPANY_TYPE_CD = 'L'`
**Components:**
  - operators: ['=']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 521
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN']

### Condition 522
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 523
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 524
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 525
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 526
**Type:** range
**Original:** `CNTR > 0`
**Converted:** `CNTR > 0`
**Components:**
  - operators: ['>']

### Condition 527
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 528
**Type:** nvl_function
**Original:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L')`
**Converted:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN', 'AND', 'IN']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 529
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 530
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) = NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) = COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['=', 'AND', '<>']
**Status:** warning

### Condition 531
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 532
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) <> NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) <> COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>', 'AND', '<>']
**Status:** warning

### Condition 533
**Type:** boolean_logic
**Original:** `:NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Converted:** `NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD']
  - operators: ['=', 'AND', '>']

### Condition 534
**Type:** equality
**Original:** `TO_CHAR(:NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Converted:** `TO_CHAR(NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Components:**
  - columns: ['NEW.VALID_FROM']
  - functions: ['TO_CHAR']
  - operators: ['=']

### Condition 535
**Type:** equality
**Original:** `V_COMPANY_TYPE_CD = 'L'`
**Converted:** `V_COMPANY_TYPE_CD = 'L'`
**Components:**
  - operators: ['=']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 536
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN']

### Condition 537
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 538
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 539
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 540
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 541
**Type:** range
**Original:** `CNTR > 0`
**Converted:** `CNTR > 0`
**Components:**
  - operators: ['>']

### Condition 542
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 543
**Type:** nvl_function
**Original:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L')`
**Converted:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN', 'AND', 'IN']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 544
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 545
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) = NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) = COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['=', 'AND', '<>']
**Status:** warning

### Condition 546
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 547
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) <> NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) <> COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>', 'AND', '<>']
**Status:** warning

### Condition 548
**Type:** boolean_logic
**Original:** `:NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Converted:** `NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD']
  - operators: ['=', 'AND', '>']

### Condition 549
**Type:** equality
**Original:** `TO_CHAR(:NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Converted:** `TO_CHAR(NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Components:**
  - columns: ['NEW.VALID_FROM']
  - functions: ['TO_CHAR']
  - operators: ['=']

### Condition 550
**Type:** equality
**Original:** `V_COMPANY_TYPE_CD = 'L'`
**Converted:** `V_COMPANY_TYPE_CD = 'L'`
**Components:**
  - operators: ['=']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 551
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN']

### Condition 552
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 553
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 554
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 555
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 556
**Type:** range
**Original:** `CNTR > 0`
**Converted:** `CNTR > 0`
**Components:**
  - operators: ['>']

### Condition 557
**Type:** trigger_combination
**Original:** `INSERTING OR UPDATING`
**Converted:** `TG_OP IN ('INSERT', 'UPDATE')`
**Components:**
  - operators: ['IN', 'IN', 'OR', 'IN']
  - trigger_ops: ['INSERTING', 'UPDATING']

### Condition 558
**Type:** nvl_function
**Original:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L')`
**Converted:** `V_COMPANY_TYPE_CD NOT IN ('L', 'A') AND COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN', 'AND', 'IN']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 559
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 560
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) = NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) = COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['=', 'AND', '<>']
**Status:** warning

### Condition 561
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 562
**Type:** nvl_function
**Original:** `NVL(:OLD.VALID_FROM, TRUNC(SYSDATE)) <> NVL(:NEW.VALID_FROM, TRUNC(SYSDATE)) AND :OLD.COUNTRY_ID <> :NEW.COUNTRY_ID`
**Converted:** `COALESCE(OLD.VALID_FROM, TRUNC(SYSDATE)) <> COALESCE(NEW.VALID_FROM, TRUNC(SYSDATE)) AND OLD.COUNTRY_ID <> NEW.COUNTRY_ID`
**Components:**
  - columns: ['OLD.VALID_FROM', 'NEW.VALID_FROM', 'OLD.COUNTRY_ID', 'NEW.COUNTRY_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>', 'AND', '<>']
**Status:** warning

### Condition 563
**Type:** boolean_logic
**Original:** `:NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Converted:** `NEW.ADDRESS_TYPE_CD = 'P' AND CNTR > 0`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD']
  - operators: ['=', 'AND', '>']

### Condition 564
**Type:** equality
**Original:** `TO_CHAR(:NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Converted:** `TO_CHAR(NEW.VALID_FROM, 'dd.mm') = '01.01'`
**Components:**
  - columns: ['NEW.VALID_FROM']
  - functions: ['TO_CHAR']
  - operators: ['=']

### Condition 565
**Type:** equality
**Original:** `V_COMPANY_TYPE_CD = 'L'`
**Converted:** `V_COMPANY_TYPE_CD = 'L'`
**Components:**
  - operators: ['=']
  - variables: ['V_COMPANY_TYPE_CD']

### Condition 566
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) NOT IN ( 'P', 'L')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['NOT IN']

### Condition 567
**Type:** equality
**Original:** `CNTR = 0`
**Converted:** `CNTR = 0`
**Components:**
  - operators: ['=']

### Condition 568
**Type:** trigger_operation
**Original:** `DELETING`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['DELETING']

### Condition 569
**Type:** nvl_function
**Original:** `NVL(:NEW.ADDRESS_TYPE_CD, :OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Converted:** `COALESCE(NEW.ADDRESS_TYPE_CD, OLD.ADDRESS_TYPE_CD) IN ('L', 'P')`
**Components:**
  - columns: ['NEW.ADDRESS_TYPE_CD', 'OLD.ADDRESS_TYPE_CD']
  - functions: ['NVL']
  - operators: ['IN']

### Condition 570
**Type:** equality
**Original:** `TG_OP = 'INSERT'`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['=', 'IN']

### Condition 571
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 572
**Type:** equality
**Original:** `TG_OP = 'DELETE'`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['=']

### Condition 573
**Type:** equality
**Original:** `TG_OP = 'INSERT'`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['=', 'IN']

### Condition 574
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 575
**Type:** equality
**Original:** `TG_OP = 'DELETE'`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['=']

### Condition 576
**Type:** equality
**Original:** `TG_OP = 'INSERT'`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['=', 'IN']

### Condition 577
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 578
**Type:** equality
**Original:** `TG_OP = 'DELETE'`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['=']

### Condition 579
**Type:** equality
**Original:** `TG_OP = 'INSERT'`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['=', 'IN']

### Condition 580
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 581
**Type:** equality
**Original:** `TG_OP = 'DELETE'`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['=']

### Condition 582
**Type:** equality
**Original:** `TG_OP = 'INSERT'`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['=', 'IN']

### Condition 583
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 584
**Type:** equality
**Original:** `TG_OP = 'DELETE'`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['=']

### Condition 585
**Type:** equality
**Original:** `TG_OP = 'INSERT'`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['=', 'IN']

### Condition 586
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 587
**Type:** equality
**Original:** `TG_OP = 'DELETE'`
**Converted:** `TG_OP = 'DELETE'`
**Components:**
  - operators: ['=']

### Condition 588
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 589
**Type:** inequality
**Original:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') <> COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME <> NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') <> COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Converted:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') != COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME != NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') != COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Components:**
  - functions: ['COALESCE', 'COALESCE']
  - operators: ['<>', 'OR', '<>', 'OR', '<>']

### Condition 590
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Components:**
  - operators: ['IN']

### Condition 591
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Components:**
  - operators: ['IN']

### Condition 592
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 593
**Type:** inequality
**Original:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') <> COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME <> NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') <> COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Converted:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') != COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME != NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') != COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Components:**
  - functions: ['COALESCE', 'COALESCE']
  - operators: ['<>', 'OR', '<>', 'OR', '<>']

### Condition 594
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Components:**
  - operators: ['IN']

### Condition 595
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Components:**
  - operators: ['IN']

### Condition 596
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 597
**Type:** inequality
**Original:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') <> COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME <> NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') <> COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Converted:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') != COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME != NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') != COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Components:**
  - functions: ['COALESCE', 'COALESCE']
  - operators: ['<>', 'OR', '<>', 'OR', '<>']

### Condition 598
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Components:**
  - operators: ['IN']

### Condition 599
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Components:**
  - operators: ['IN']

### Condition 600
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 601
**Type:** inequality
**Original:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') <> COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME <> NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') <> COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Converted:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') != COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME != NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') != COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Components:**
  - functions: ['COALESCE', 'COALESCE']
  - operators: ['<>', 'OR', '<>', 'OR', '<>']

### Condition 602
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Components:**
  - operators: ['IN']

### Condition 603
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Components:**
  - operators: ['IN']

### Condition 604
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 605
**Type:** inequality
**Original:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') <> COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME <> NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') <> COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Converted:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') != COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME != NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') != COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Components:**
  - functions: ['COALESCE', 'COALESCE']
  - operators: ['<>', 'OR', '<>', 'OR', '<>']

### Condition 606
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Components:**
  - operators: ['IN']

### Condition 607
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Components:**
  - operators: ['IN']

### Condition 608
**Type:** equality
**Original:** `TG_OP = 'UPDATE'`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['=']

### Condition 609
**Type:** inequality
**Original:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') <> COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME <> NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') <> COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Converted:** `COALESCE (OLD.PROD_FAM_NAME_STATUS_CD, 'X') != COALESCE (NEW.PROD_FAM_NAME_STATUS_CD, 'X') OR OLD.PROD_FAM_NAME != NEW.PROD_FAM_NAME OR COALESCE(OLD.ACT_SUBSTANCE_NAME, 'X') != COALESCE(NEW.ACT_SUBSTANCE_NAME, 'X')`
**Components:**
  - functions: ['COALESCE', 'COALESCE']
  - operators: ['<>', 'OR', '<>', 'OR', '<>']

### Condition 610
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('T', 'R')`
**Components:**
  - operators: ['IN']

### Condition 611
**Type:** in_condition
**Original:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Converted:** `NEW.PROD_FAM_NAME_STATUS_CD IN ('G', 'I')`
**Components:**
  - operators: ['IN']

### Condition 612
**Type:** null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(:NEW.EVOLVED_THEME_NO IS NULL OR :NEW.EVOLVED_THEME_NO = :OLD.EVOLVED_THEME_NO) AND :NEW.MOLECULE_TYPE_ID = :OLD.MOLECULE_TYPE_ID AND :NEW.PHARMACOLOGICAL_TYPE_ID = :OLD.PHARMACOLOGICAL_TYPE_ID AND :NEW.PROPOSAL_NAME = :OLD.PROPOSAL_NAME`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(NEW.EVOLVED_THEME_NO IS NULL OR NEW.EVOLVED_THEME_NO = OLD.EVOLVED_THEME_NO) AND NEW.MOLECULE_TYPE_ID = OLD.MOLECULE_TYPE_ID AND NEW.PHARMACOLOGICAL_TYPE_ID = OLD.PHARMACOLOGICAL_TYPE_ID AND NEW.PROPOSAL_NAME = OLD.PROPOSAL_NAME`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'NEW.EVOLVED_THEME_NO', 'NEW.EVOLVED_THEME_NO', 'OLD.EVOLVED_THEME_NO', 'NEW.MOLECULE_TYPE_ID', 'OLD.MOLECULE_TYPE_ID', 'NEW.PHARMACOLOGICAL_TYPE_ID', 'OLD.PHARMACOLOGICAL_TYPE_ID', 'NEW.PROPOSAL_NAME', 'OLD.PROPOSAL_NAME']
  - functions: ['AND']
  - operators: ['=', 'AND', 'IS NULL', 'OR', '=', 'AND', '=', 'AND', '=', 'AND', '=']

### Condition 613
**Type:** boolean_logic
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND :OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.PROPOSAL_STATUS_CD']
  - operators: ['=', 'IN', 'AND', '=']

### Condition 614
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND :OLD.EVOLVED_THEME_NO IS NOT NULL`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND OLD.EVOLVED_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.EVOLVED_THEME_NO']
  - operators: ['=', 'AND', 'IS NOT NULL']

### Condition 615
**Type:** null_check
**Original:** `:NEW.EXPLORATORY_THEME_NO IS NULL AND :OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Converted:** `NEW.EXPLORATORY_THEME_NO IS NULL AND OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.EXPLORATORY_THEME_NO', 'OLD.EXPLORATORY_THEME_NO']
  - operators: ['OR', 'OR', 'IS NULL', 'AND', 'OR', 'OR', 'IS NOT NULL']

### Condition 616
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 617
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 618
**Type:** not_null_check
**Original:** `:NEW.PARTNER_ID IS NOT NULL`
**Converted:** `NEW.PARTNER_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PARTNER_ID']
  - operators: ['IS NOT NULL']

### Condition 619
**Type:** nvl_function
**Original:** `NVL(:OLD.PARTNER_ID, 'NULL') <> NVL(:NEW.PARTNER_ID, 'NULL')`
**Converted:** `COALESCE(OLD.PARTNER_ID, 'NULL') <> COALESCE(NEW.PARTNER_ID, 'NULL')`
**Components:**
  - columns: ['OLD.PARTNER_ID', 'NEW.PARTNER_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>']
**Status:** warning

### Condition 620
**Type:** null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(:NEW.EVOLVED_THEME_NO IS NULL OR :NEW.EVOLVED_THEME_NO = :OLD.EVOLVED_THEME_NO) AND :NEW.MOLECULE_TYPE_ID = :OLD.MOLECULE_TYPE_ID AND :NEW.PHARMACOLOGICAL_TYPE_ID = :OLD.PHARMACOLOGICAL_TYPE_ID AND :NEW.PROPOSAL_NAME = :OLD.PROPOSAL_NAME`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(NEW.EVOLVED_THEME_NO IS NULL OR NEW.EVOLVED_THEME_NO = OLD.EVOLVED_THEME_NO) AND NEW.MOLECULE_TYPE_ID = OLD.MOLECULE_TYPE_ID AND NEW.PHARMACOLOGICAL_TYPE_ID = OLD.PHARMACOLOGICAL_TYPE_ID AND NEW.PROPOSAL_NAME = OLD.PROPOSAL_NAME`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'NEW.EVOLVED_THEME_NO', 'NEW.EVOLVED_THEME_NO', 'OLD.EVOLVED_THEME_NO', 'NEW.MOLECULE_TYPE_ID', 'OLD.MOLECULE_TYPE_ID', 'NEW.PHARMACOLOGICAL_TYPE_ID', 'OLD.PHARMACOLOGICAL_TYPE_ID', 'NEW.PROPOSAL_NAME', 'OLD.PROPOSAL_NAME']
  - functions: ['AND']
  - operators: ['=', 'AND', 'IS NULL', 'OR', '=', 'AND', '=', 'AND', '=', 'AND', '=']

### Condition 621
**Type:** boolean_logic
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND :OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.PROPOSAL_STATUS_CD']
  - operators: ['=', 'IN', 'AND', '=']

### Condition 622
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND :OLD.EVOLVED_THEME_NO IS NOT NULL`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND OLD.EVOLVED_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.EVOLVED_THEME_NO']
  - operators: ['=', 'AND', 'IS NOT NULL']

### Condition 623
**Type:** null_check
**Original:** `:NEW.EXPLORATORY_THEME_NO IS NULL AND :OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Converted:** `NEW.EXPLORATORY_THEME_NO IS NULL AND OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.EXPLORATORY_THEME_NO', 'OLD.EXPLORATORY_THEME_NO']
  - operators: ['OR', 'OR', 'IS NULL', 'AND', 'OR', 'OR', 'IS NOT NULL']

### Condition 624
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 625
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 626
**Type:** not_null_check
**Original:** `:NEW.PARTNER_ID IS NOT NULL`
**Converted:** `NEW.PARTNER_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PARTNER_ID']
  - operators: ['IS NOT NULL']

### Condition 627
**Type:** nvl_function
**Original:** `NVL(:OLD.PARTNER_ID, 'NULL') <> NVL(:NEW.PARTNER_ID, 'NULL')`
**Converted:** `COALESCE(OLD.PARTNER_ID, 'NULL') <> COALESCE(NEW.PARTNER_ID, 'NULL')`
**Components:**
  - columns: ['OLD.PARTNER_ID', 'NEW.PARTNER_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>']
**Status:** warning

### Condition 628
**Type:** null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(:NEW.EVOLVED_THEME_NO IS NULL OR :NEW.EVOLVED_THEME_NO = :OLD.EVOLVED_THEME_NO) AND :NEW.MOLECULE_TYPE_ID = :OLD.MOLECULE_TYPE_ID AND :NEW.PHARMACOLOGICAL_TYPE_ID = :OLD.PHARMACOLOGICAL_TYPE_ID AND :NEW.PROPOSAL_NAME = :OLD.PROPOSAL_NAME`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(NEW.EVOLVED_THEME_NO IS NULL OR NEW.EVOLVED_THEME_NO = OLD.EVOLVED_THEME_NO) AND NEW.MOLECULE_TYPE_ID = OLD.MOLECULE_TYPE_ID AND NEW.PHARMACOLOGICAL_TYPE_ID = OLD.PHARMACOLOGICAL_TYPE_ID AND NEW.PROPOSAL_NAME = OLD.PROPOSAL_NAME`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'NEW.EVOLVED_THEME_NO', 'NEW.EVOLVED_THEME_NO', 'OLD.EVOLVED_THEME_NO', 'NEW.MOLECULE_TYPE_ID', 'OLD.MOLECULE_TYPE_ID', 'NEW.PHARMACOLOGICAL_TYPE_ID', 'OLD.PHARMACOLOGICAL_TYPE_ID', 'NEW.PROPOSAL_NAME', 'OLD.PROPOSAL_NAME']
  - functions: ['AND']
  - operators: ['=', 'AND', 'IS NULL', 'OR', '=', 'AND', '=', 'AND', '=', 'AND', '=']

### Condition 629
**Type:** boolean_logic
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND :OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.PROPOSAL_STATUS_CD']
  - operators: ['=', 'IN', 'AND', '=']

### Condition 630
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND :OLD.EVOLVED_THEME_NO IS NOT NULL`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND OLD.EVOLVED_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.EVOLVED_THEME_NO']
  - operators: ['=', 'AND', 'IS NOT NULL']

### Condition 631
**Type:** null_check
**Original:** `:NEW.EXPLORATORY_THEME_NO IS NULL AND :OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Converted:** `NEW.EXPLORATORY_THEME_NO IS NULL AND OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.EXPLORATORY_THEME_NO', 'OLD.EXPLORATORY_THEME_NO']
  - operators: ['OR', 'OR', 'IS NULL', 'AND', 'OR', 'OR', 'IS NOT NULL']

### Condition 632
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 633
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 634
**Type:** not_null_check
**Original:** `:NEW.PARTNER_ID IS NOT NULL`
**Converted:** `NEW.PARTNER_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PARTNER_ID']
  - operators: ['IS NOT NULL']

### Condition 635
**Type:** nvl_function
**Original:** `NVL(:OLD.PARTNER_ID, 'NULL') <> NVL(:NEW.PARTNER_ID, 'NULL')`
**Converted:** `COALESCE(OLD.PARTNER_ID, 'NULL') <> COALESCE(NEW.PARTNER_ID, 'NULL')`
**Components:**
  - columns: ['OLD.PARTNER_ID', 'NEW.PARTNER_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>']
**Status:** warning

### Condition 636
**Type:** null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(:NEW.EVOLVED_THEME_NO IS NULL OR :NEW.EVOLVED_THEME_NO = :OLD.EVOLVED_THEME_NO) AND :NEW.MOLECULE_TYPE_ID = :OLD.MOLECULE_TYPE_ID AND :NEW.PHARMACOLOGICAL_TYPE_ID = :OLD.PHARMACOLOGICAL_TYPE_ID AND :NEW.PROPOSAL_NAME = :OLD.PROPOSAL_NAME`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(NEW.EVOLVED_THEME_NO IS NULL OR NEW.EVOLVED_THEME_NO = OLD.EVOLVED_THEME_NO) AND NEW.MOLECULE_TYPE_ID = OLD.MOLECULE_TYPE_ID AND NEW.PHARMACOLOGICAL_TYPE_ID = OLD.PHARMACOLOGICAL_TYPE_ID AND NEW.PROPOSAL_NAME = OLD.PROPOSAL_NAME`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'NEW.EVOLVED_THEME_NO', 'NEW.EVOLVED_THEME_NO', 'OLD.EVOLVED_THEME_NO', 'NEW.MOLECULE_TYPE_ID', 'OLD.MOLECULE_TYPE_ID', 'NEW.PHARMACOLOGICAL_TYPE_ID', 'OLD.PHARMACOLOGICAL_TYPE_ID', 'NEW.PROPOSAL_NAME', 'OLD.PROPOSAL_NAME']
  - functions: ['AND']
  - operators: ['=', 'AND', 'IS NULL', 'OR', '=', 'AND', '=', 'AND', '=', 'AND', '=']

### Condition 637
**Type:** boolean_logic
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND :OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.PROPOSAL_STATUS_CD']
  - operators: ['=', 'IN', 'AND', '=']

### Condition 638
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND :OLD.EVOLVED_THEME_NO IS NOT NULL`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND OLD.EVOLVED_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.EVOLVED_THEME_NO']
  - operators: ['=', 'AND', 'IS NOT NULL']

### Condition 639
**Type:** null_check
**Original:** `:NEW.EXPLORATORY_THEME_NO IS NULL AND :OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Converted:** `NEW.EXPLORATORY_THEME_NO IS NULL AND OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.EXPLORATORY_THEME_NO', 'OLD.EXPLORATORY_THEME_NO']
  - operators: ['OR', 'OR', 'IS NULL', 'AND', 'OR', 'OR', 'IS NOT NULL']

### Condition 640
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 641
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 642
**Type:** not_null_check
**Original:** `:NEW.PARTNER_ID IS NOT NULL`
**Converted:** `NEW.PARTNER_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PARTNER_ID']
  - operators: ['IS NOT NULL']

### Condition 643
**Type:** nvl_function
**Original:** `NVL(:OLD.PARTNER_ID, 'NULL') <> NVL(:NEW.PARTNER_ID, 'NULL')`
**Converted:** `COALESCE(OLD.PARTNER_ID, 'NULL') <> COALESCE(NEW.PARTNER_ID, 'NULL')`
**Components:**
  - columns: ['OLD.PARTNER_ID', 'NEW.PARTNER_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>']
**Status:** warning

### Condition 644
**Type:** null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(:NEW.EVOLVED_THEME_NO IS NULL OR :NEW.EVOLVED_THEME_NO = :OLD.EVOLVED_THEME_NO) AND :NEW.MOLECULE_TYPE_ID = :OLD.MOLECULE_TYPE_ID AND :NEW.PHARMACOLOGICAL_TYPE_ID = :OLD.PHARMACOLOGICAL_TYPE_ID AND :NEW.PROPOSAL_NAME = :OLD.PROPOSAL_NAME`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(NEW.EVOLVED_THEME_NO IS NULL OR NEW.EVOLVED_THEME_NO = OLD.EVOLVED_THEME_NO) AND NEW.MOLECULE_TYPE_ID = OLD.MOLECULE_TYPE_ID AND NEW.PHARMACOLOGICAL_TYPE_ID = OLD.PHARMACOLOGICAL_TYPE_ID AND NEW.PROPOSAL_NAME = OLD.PROPOSAL_NAME`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'NEW.EVOLVED_THEME_NO', 'NEW.EVOLVED_THEME_NO', 'OLD.EVOLVED_THEME_NO', 'NEW.MOLECULE_TYPE_ID', 'OLD.MOLECULE_TYPE_ID', 'NEW.PHARMACOLOGICAL_TYPE_ID', 'OLD.PHARMACOLOGICAL_TYPE_ID', 'NEW.PROPOSAL_NAME', 'OLD.PROPOSAL_NAME']
  - functions: ['AND']
  - operators: ['=', 'AND', 'IS NULL', 'OR', '=', 'AND', '=', 'AND', '=', 'AND', '=']

### Condition 645
**Type:** boolean_logic
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND :OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.PROPOSAL_STATUS_CD']
  - operators: ['=', 'IN', 'AND', '=']

### Condition 646
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND :OLD.EVOLVED_THEME_NO IS NOT NULL`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND OLD.EVOLVED_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.EVOLVED_THEME_NO']
  - operators: ['=', 'AND', 'IS NOT NULL']

### Condition 647
**Type:** null_check
**Original:** `:NEW.EXPLORATORY_THEME_NO IS NULL AND :OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Converted:** `NEW.EXPLORATORY_THEME_NO IS NULL AND OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.EXPLORATORY_THEME_NO', 'OLD.EXPLORATORY_THEME_NO']
  - operators: ['OR', 'OR', 'IS NULL', 'AND', 'OR', 'OR', 'IS NOT NULL']

### Condition 648
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 649
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 650
**Type:** not_null_check
**Original:** `:NEW.PARTNER_ID IS NOT NULL`
**Converted:** `NEW.PARTNER_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PARTNER_ID']
  - operators: ['IS NOT NULL']

### Condition 651
**Type:** nvl_function
**Original:** `NVL(:OLD.PARTNER_ID, 'NULL') <> NVL(:NEW.PARTNER_ID, 'NULL')`
**Converted:** `COALESCE(OLD.PARTNER_ID, 'NULL') <> COALESCE(NEW.PARTNER_ID, 'NULL')`
**Components:**
  - columns: ['OLD.PARTNER_ID', 'NEW.PARTNER_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>']
**Status:** warning

### Condition 652
**Type:** null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(:NEW.EVOLVED_THEME_NO IS NULL OR :NEW.EVOLVED_THEME_NO = :OLD.EVOLVED_THEME_NO) AND :NEW.MOLECULE_TYPE_ID = :OLD.MOLECULE_TYPE_ID AND :NEW.PHARMACOLOGICAL_TYPE_ID = :OLD.PHARMACOLOGICAL_TYPE_ID AND :NEW.PROPOSAL_NAME = :OLD.PROPOSAL_NAME`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED AND(NEW.EVOLVED_THEME_NO IS NULL OR NEW.EVOLVED_THEME_NO = OLD.EVOLVED_THEME_NO) AND NEW.MOLECULE_TYPE_ID = OLD.MOLECULE_TYPE_ID AND NEW.PHARMACOLOGICAL_TYPE_ID = OLD.PHARMACOLOGICAL_TYPE_ID AND NEW.PROPOSAL_NAME = OLD.PROPOSAL_NAME`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'NEW.EVOLVED_THEME_NO', 'NEW.EVOLVED_THEME_NO', 'OLD.EVOLVED_THEME_NO', 'NEW.MOLECULE_TYPE_ID', 'OLD.MOLECULE_TYPE_ID', 'NEW.PHARMACOLOGICAL_TYPE_ID', 'OLD.PHARMACOLOGICAL_TYPE_ID', 'NEW.PROPOSAL_NAME', 'OLD.PROPOSAL_NAME']
  - functions: ['AND']
  - operators: ['=', 'AND', 'IS NULL', 'OR', '=', 'AND', '=', 'AND', '=', 'AND', '=']

### Condition 653
**Type:** boolean_logic
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND :OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_TERMINATED AND OLD.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_EVOLVED`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.PROPOSAL_STATUS_CD']
  - operators: ['=', 'IN', 'AND', '=']

### Condition 654
**Type:** not_null_check
**Original:** `:NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND :OLD.EVOLVED_THEME_NO IS NOT NULL`
**Converted:** `NEW.PROPOSAL_STATUS_CD = C_PROPOSAL_STATUS_ACTIVE AND OLD.EVOLVED_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.PROPOSAL_STATUS_CD', 'OLD.EVOLVED_THEME_NO']
  - operators: ['=', 'AND', 'IS NOT NULL']

### Condition 655
**Type:** null_check
**Original:** `:NEW.EXPLORATORY_THEME_NO IS NULL AND :OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Converted:** `NEW.EXPLORATORY_THEME_NO IS NULL AND OLD.EXPLORATORY_THEME_NO IS NOT NULL`
**Components:**
  - columns: ['NEW.EXPLORATORY_THEME_NO', 'OLD.EXPLORATORY_THEME_NO']
  - operators: ['OR', 'OR', 'IS NULL', 'AND', 'OR', 'OR', 'IS NOT NULL']

### Condition 656
**Type:** trigger_operation
**Original:** `INSERTING`
**Converted:** `TG_OP = 'INSERT'`
**Components:**
  - operators: ['IN', 'IN']
  - trigger_ops: ['INSERTING']

### Condition 657
**Type:** trigger_operation
**Original:** `UPDATING`
**Converted:** `TG_OP = 'UPDATE'`
**Components:**
  - operators: ['IN']
  - trigger_ops: ['UPDATING']

### Condition 658
**Type:** not_null_check
**Original:** `:NEW.PARTNER_ID IS NOT NULL`
**Converted:** `NEW.PARTNER_ID IS NOT NULL`
**Components:**
  - columns: ['NEW.PARTNER_ID']
  - operators: ['IS NOT NULL']

### Condition 659
**Type:** nvl_function
**Original:** `NVL(:OLD.PARTNER_ID, 'NULL') <> NVL(:NEW.PARTNER_ID, 'NULL')`
**Converted:** `COALESCE(OLD.PARTNER_ID, 'NULL') <> COALESCE(NEW.PARTNER_ID, 'NULL')`
**Components:**
  - columns: ['OLD.PARTNER_ID', 'NEW.PARTNER_ID']
  - functions: ['NVL', 'NVL']
  - operators: ['<>']
**Status:** warning
