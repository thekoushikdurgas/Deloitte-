import json
from utilities.OracleTriggerAnalyzer import OracleTriggerAnalyzer

# Read trigger4.sql
with open("files/oracle/trigger4.sql", "r", encoding="utf-8") as f:
    sql_content = f.read()

# Create analyzer
analyzer = OracleTriggerAnalyzer(sql_content)

# Test the function call parsing
print("Testing function call parsing:")
test_lines = [{'indent': 4, 'line': '    PERFORM MDMTOOL."mdmt_util_history$write_history"( V_ACTION, V_TABLE_NAME, V_SCHEMA_NAME, COL_NAMES, COL_NEW_VALUES, COL_OLD_VALUES );', 'line_no': 21}]

result = analyzer._parse_function_calling(test_lines, 'MDMTOOL."mdmt_util_history$write_history"')
print(f"Parsed result: {json.dumps(result, indent=2)}")

# Check the main section for function calls
print("\nChecking main section for function calls:")
def find_function_calls(item, path=""):
    if isinstance(item, dict):
        if item.get("type") == "function_calling":
            print(f"Found function call at {path}: {item}")
        for key, value in item.items():
            find_function_calls(value, f"{path}.{key}")
    elif isinstance(item, list):
        for i, sub_item in enumerate(item):
            find_function_calls(sub_item, f"{path}[{i}]")

find_function_calls(analyzer.main_section_lines)

# Check the statistics
print(f"\nFunction calling count: {analyzer.strng_convert_json['function_calling']}")
