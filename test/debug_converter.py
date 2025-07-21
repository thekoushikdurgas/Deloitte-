#!/usr/bin/env python3
"""
Debug script to check section parsing
"""

import re
from pathlib import Path

def debug_section_parsing(file_path: str):
    """Debug the section parsing to see what's happening"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"=== DEBUGGING {file_path} ===")
    print(f"Total content length: {len(content)} characters")
    print()
    
    # Find section boundaries
    declare_match = re.search(r'^\s*declare\s*$', content, re.IGNORECASE | re.MULTILINE)
    begin_match = re.search(r'^\s*begin\s*$', content, re.IGNORECASE | re.MULTILINE)
    exception_match = re.search(r'^\s*exception\s*$', content, re.IGNORECASE | re.MULTILINE)
    end_match = re.search(r'^\s*end\s*;\s*$', content, re.IGNORECASE | re.MULTILINE)
    
    print("SECTION BOUNDARIES:")
    if declare_match:
        print(f"  DECLARE found at position {declare_match.start()}-{declare_match.end()}")
    else:
        print("  DECLARE not found")
    
    if begin_match:
        print(f"  BEGIN found at position {begin_match.start()}-{begin_match.end()}")
    else:
        print("  BEGIN not found")
    
    if exception_match:
        print(f"  EXCEPTION found at position {exception_match.start()}-{exception_match.end()}")
    else:
        print("  EXCEPTION not found")
    
    if end_match:
        print(f"  END found at position {end_match.start()}-{end_match.end()}")
    else:
        print("  END not found")
    
    print()
    
    # Extract sections
    declare_section = ""
    main_section = ""
    exception_section = ""
    
    if declare_match and begin_match:
        declare_section = content[declare_match.end():begin_match.start()].strip()
    
    if begin_match:
        end_pos = exception_match.start() if exception_match else (end_match.start() if end_match else len(content))
        main_section = content[begin_match.end():end_pos].strip()
    
    if exception_match and end_match:
        exception_section = content[exception_match.end():end_match.start()].strip()
    
    print("EXTRACTED SECTIONS:")
    print(f"  DECLARE section length: {len(declare_section)} characters")
    print(f"  MAIN section length: {len(main_section)} characters")
    print(f"  EXCEPTION section length: {len(exception_section)} characters")
    print()
    
    if exception_section:
        print("EXCEPTION SECTION CONTENT:")
        print("-" * 50)
        print(exception_section[:1000])  # First 1000 characters
        print("-" * 50)
        print()
        
        # Count 'when' statements
        when_count = len(re.findall(r'\bwhen\s+[a-zA-Z_][a-zA-Z0-9_]*\b', exception_section, re.IGNORECASE))
        print(f"Found {when_count} 'when' statements in exception section")
        
        # Show first few 'when' matches
        when_matches = re.finditer(r'\bwhen\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', exception_section, re.IGNORECASE)
        print("Exception names found:")
        for i, match in enumerate(when_matches):
            if i >= 5:  # Show first 5
                break
            print(f"  - {match.group(1)}")
    
    print("=" * 60)
    print()

if __name__ == "__main__":
    debug_section_parsing("files/oracle/trigger1.sql")
    debug_section_parsing("files/oracle/trigger2.sql")
    debug_section_parsing("files/oracle/trigger3.sql") 