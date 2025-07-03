#!/usr/bin/env python3
"""
Debug script to understand Oracle trigger parsing issues
"""

import re
from convert import OracleToPostgreSQLConverter

def debug_trigger1_parsing():
    converter = OracleToPostgreSQLConverter()
    
    # Read trigger1.sql
    with open('orcale/trigger1.sql', 'r') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    print(f"First 500 characters:")
    print(repr(content[:500]))
    print("\n" + "="*50 + "\n")
    
    # Clean content
    cleaned = converter.clean_sql_content(content)
    print(f"Cleaned content size: {len(cleaned)} characters")
    print(f"First 500 characters of cleaned content:")
    print(repr(cleaned[:500]))
    print("\n" + "="*50 + "\n")
    
    # Find BEGIN...END structure
    begin_match = re.search(r'\bbegin\b(.*?)(?:\bexception\b|\bend\b\s*;?\s*$)', cleaned, re.IGNORECASE | re.DOTALL)
    if begin_match:
        main_body = begin_match.group(1).strip()
        print(f"Found main body, size: {len(main_body)} characters")
        print(f"First 500 characters of main body:")
        print(repr(main_body[:500]))
    else:
        print("No clear BEGIN...END structure found, using entire content")
        main_body = cleaned
        
    print("\n" + "="*50 + "\n")
    
    # Look for key patterns
    lines = [line.strip() for line in main_body.split('\n') if line.strip()]
    print(f"Number of non-empty lines: {len(lines)}")
    
    for i, line in enumerate(lines[:20]):  # First 20 lines
        line_upper = line.upper()
        if any(keyword in line_upper for keyword in ['IF', 'INSERTING', 'UPDATING', 'DELETING']):
            print(f"Line {i}: {repr(line)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test the parsing
    sections = converter.extract_sections(content)
    print("Extracted sections:")
    for section, content in sections.items():
        print(f"{section}: {len(content)} characters")
        if content:
            print(f"First 200 chars: {repr(content[:200])}")
        print()

# Test patterns from the actual Oracle files
test_lines = [
    "IF INSERTING THEN IF cntr > 0 THEN RAISE err_ins;",  # trigger3.sql line 21
    "IF INSERTING or UPDATING THEN",  # trigger3.sql line 23
    "IF DELETING THEN IF nvl(:new.address_type_cd, :old.address_type_cd) in ('L', 'P') THEN RAISE err_not_allowed_to_invalidate;",  # trigger3.sql line 197
    "if (inserting) then if (",  # trigger1.sql line 154
    "elsif (updating) then -- check admin access (role 315)",  # trigger1.sql line 364
    "elsif (deleting) then if (",  # trigger1.sql line 533
]

# Test the regex patterns
patterns = [
    r'\bIF\s+\(?\s*INSERTING\s*\)?\s*THEN\b',
    r'\bELSIF\s+\(?\s*INSERTING\s*\)?\s*THEN\b',
    r'\bIF\s+\(?\s*UPDATING\s*\)?\s*THEN\b',
    r'\bELSIF\s+\(?\s*UPDATING\s*\)?\s*THEN\b',
    r'\bIF\s+\(?\s*DELETING\s*\)?\s*THEN\b',
    r'\bELSIF\s+\(?\s*DELETING\s*\)?\s*THEN\b',
    r'\bIF\s+\(?\s*INSERTING\s*\)?\s+[Oo][Rr]\s+\(?\s*UPDATING\s*\)?\s*THEN\b',
]

print("Testing Oracle trigger pattern matching:")
print("=" * 50)

for i, line in enumerate(test_lines):
    print(f"\nLine {i+1}: {line}")
    line_upper = line.upper()
    
    for j, pattern in enumerate(patterns):
        match = re.search(pattern, line_upper)
        if match:
            print(f"  ✓ Pattern {j+1} matches: {pattern}")
            print(f"    Match: '{match.group()}'")
        else:
            print(f"  ✗ Pattern {j+1} no match: {pattern}")

if __name__ == "__main__":
    debug_trigger1_parsing() 