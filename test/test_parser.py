#!/usr/bin/env python3
"""Debug script to test section parsing"""

import re
from pathlib import Path

def debug_section_parsing():
    """Debug the section parsing logic"""
    
    # Read trigger1.sql
    trigger_file = Path("files/oracle/trigger1.sql")
    with open(trigger_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Original content length: {len(content)}")
    print(f"First 500 chars:\n{content[:500]}")
    print("\n" + "="*80 + "\n")
    
    # Find keywords
    declare_match = re.search(r'\bdeclare\b', content, re.IGNORECASE)
    begin_match = re.search(r'\bbegin\b', content, re.IGNORECASE)
    exception_match = re.search(r'\bexception\b', content, re.IGNORECASE)
    end_match = re.search(r'\bend\s*;?\s*$', content, re.IGNORECASE)
    
    print(f"DECLARE found at: {declare_match.span() if declare_match else 'Not found'}")
    print(f"BEGIN found at: {begin_match.span() if begin_match else 'Not found'}")
    print(f"EXCEPTION found at: {exception_match.span() if exception_match else 'Not found'}")
    print(f"END found at: {end_match.span() if end_match else 'Not found'}")
    print("\n" + "="*80 + "\n")
    
    if declare_match and begin_match:
        # Extract DECLARE section
        declare_start = declare_match.end()
        declare_end = begin_match.start()
        declare_section = content[declare_start:declare_end].strip()
        
        print(f"DECLARE section length: {len(declare_section)}")
        print(f"DECLARE section preview:\n{declare_section[:300]}")
        print("\n" + "="*80 + "\n")
        
        # Extract main SQL section
        main_start = begin_match.end()
        main_end = exception_match.start() if exception_match else (end_match.start() if end_match else len(content))
        main_sql_section = content[main_start:main_end].strip()
        
        print(f"Main SQL section length: {len(main_sql_section)}")
        print(f"Main SQL section preview:\n{main_sql_section[:500]}")
        print("\n" + "="*80 + "\n")
        
        # Extract EXCEPTION section
        if exception_match:
            exception_start = exception_match.end()
            exception_end = end_match.start() if end_match else len(content)
            exception_section = content[exception_start:exception_end].strip()
            
            print(f"EXCEPTION section length: {len(exception_section)}")
            print(f"EXCEPTION section preview:\n{exception_section[:300]}")

if __name__ == "__main__":
    debug_section_parsing() 