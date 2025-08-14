#!/usr/bin/env python3
"""
Test script to demonstrate call by reference vs call by value in Python
"""

import copy

def demonstrate_call_by_reference():
    """Demonstrate call by reference behavior"""
    
    print("=== Call by Reference Demonstration ===\n")
    
    # Original data
    original_data = {
        "main": [
            {
                "type": "if_else",
                "condition": "(INSERTING)",
                "then_statements": [{"type": "test", "value": "original"}]
            }
        ]
    }
    
    print("1. Original data:")
    print(f"   Original: {original_data['main'][0]['then_statements'][0]['value']}")
    
    # PROBLEM: Multiple references to same object
    print("\n2. PROBLEM: Multiple references to same object:")
    ref1 = original_data.get("main", [])
    ref2 = original_data.get("main", [])
    ref3 = original_data.get("main", [])
    
    print(f"   ref1 is ref2: {ref1 is ref2}")  # True - same object!
    print(f"   ref2 is ref3: {ref2 is ref3}")  # True - same object!
    
    # Modify one reference
    ref1[0]['then_statements'][0]['value'] = "modified"
    print(f"   After modifying ref1: {ref1[0]['then_statements'][0]['value']}")
    print(f"   ref2 also changed: {ref2[0]['then_statements'][0]['value']}")
    print(f"   ref3 also changed: {ref3[0]['then_statements'][0]['value']}")
    
    # SOLUTION: Deep copies
    print("\n3. SOLUTION: Deep copies:")
    copy1 = copy.deepcopy(original_data.get("main", []))
    copy2 = copy.deepcopy(original_data.get("main", []))
    copy3 = copy.deepcopy(original_data.get("main", []))
    
    print(f"   copy1 is copy2: {copy1 is copy2}")  # False - different objects!
    print(f"   copy2 is copy3: {copy2 is copy3}")  # False - different objects!
    
    # Modify one copy
    copy1[0]['then_statements'][0]['value'] = "copy1_modified"
    copy2[0]['then_statements'][0]['value'] = "copy2_modified"
    copy3[0]['then_statements'][0]['value'] = "copy3_modified"
    
    print(f"   copy1: {copy1[0]['then_statements'][0]['value']}")
    print(f"   copy2: {copy2[0]['then_statements'][0]['value']}")
    print(f"   copy3: {copy3[0]['then_statements'][0]['value']}")
    
    print("\n=== Summary ===")
    print("✓ Call by Reference: Modifications affect all references to the same object")
    print("✓ Deep Copy: Each copy is independent and can be modified separately")
    print("✓ Your JSONTOPLJSON now uses deep copies to avoid this issue!")

if __name__ == "__main__":
    demonstrate_call_by_reference()
