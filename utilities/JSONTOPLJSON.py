import json
from typing import Any, Dict, List, Tuple

from utilities.common import (
    logger,
    setup_logging,
    debug,
    info,
    warning,
    error,
    critical,
    alert,
)
import copy

class JSONTOPLJSON:
    def __init__(self, json_data):
        """__init__ function."""
        self.json_data = json_data
        self.sql_content = {
            "declarations": {},
            "on_insert": [],
            "on_update": [],
            "on_delete": [],
        }
        # Create deep copies to avoid modifying the same object
        self.after_parse_on_insert: List[Dict[str, Any]] = []
        self.after_parse_on_update: List[Dict[str, Any]] = []
        self.after_parse_on_delete: List[Dict[str, Any]] = []
        self.declarations: Dict[str, Any] = {}
        self.to_sql()

    def modify_condition(self, condition):
        """
        Modify and clean Oracle trigger condition string for PostgreSQL compatibility.
        
        This function:
        1. Removes Oracle-specific keywords (INSERTING, UPDATING, DELETING)
        2. Removes PostgreSQL TG_OP condition patterns
        3. Cleans up resulting syntax (extra spaces, operators, parentheses)
        4. Returns 'TRUE' if the condition is empty after processing
        
        Args:
            condition (str): Original condition string from Oracle trigger
            
        Returns:
            str: Modified condition suitable for PostgreSQL or 'TRUE' if empty
        """
        debug(f"Starting condition modification: '{condition}'")
        
        # Handle empty or None condition
        if not condition:
            debug("Empty condition provided, returning 'TRUE'")
            return "TRUE"
        
        condition = condition.strip()
        debug(f"Stripped condition: '{condition}'")
        
        # Step 1: Define keywords and patterns to remove
        # Keywords to remove (case-insensitive)
        keywords_to_remove = [
            "INSERTING", "UPDATING", "DELETING"
        ]
        
        # PostgreSQL TG_OP patterns to remove (case-insensitive)
        tg_op_patterns = [
            r"TG_OP\s*=\s*['\"]INSERTING['\"]",
            r"TG_OP\s*=\s*['\"]UPDATING['\"]", 
            r"TG_OP\s*=\s*['\"]DELETING['\"]"
        ]
        
        # Create a copy of the condition to work with
        modified_condition = condition
        
        # Step 2: Remove Oracle trigger keywords (case-insensitive)
        import re
        for keyword in keywords_to_remove:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            before_sub = modified_condition
            modified_condition = pattern.sub("", modified_condition)
            if before_sub != modified_condition:
                debug(f"Removed keyword '{keyword}': '{before_sub}' → '{modified_condition}'")
        
        # Step 3: Remove PostgreSQL TG_OP patterns (case-insensitive)
        for pattern in tg_op_patterns:
            before_sub = modified_condition
            modified_condition = re.sub(pattern, "", modified_condition, flags=re.IGNORECASE)
            if before_sub != modified_condition:
                debug(f"Removed TG_OP pattern '{pattern}': '{before_sub}' → '{modified_condition}'")
        
        # Step 4: Clean up syntax issues resulting from removals
        
        # Replace multiple spaces with single space
        before_sub = modified_condition
        modified_condition = re.sub(r'\s+', ' ', modified_condition)
        if before_sub != modified_condition:
            debug(f"Normalized spaces: '{before_sub}' → '{modified_condition}'")
            
        # Fix double operators
        before_sub = modified_condition
        modified_condition = re.sub(r'\s*AND\s*AND\s*', ' AND ', modified_condition, flags=re.IGNORECASE)
        modified_condition = re.sub(r'\s*OR\s*OR\s*', ' OR ', modified_condition, flags=re.IGNORECASE)
        if before_sub != modified_condition:
            debug(f"Fixed double operators: '{before_sub}' → '{modified_condition}'")
        
        # Remove leading and trailing operators
        before_sub = modified_condition
        modified_condition = re.sub(r'^\s*AND\s*', '', modified_condition, flags=re.IGNORECASE)
        modified_condition = re.sub(r'^\s*OR\s*', '', modified_condition, flags=re.IGNORECASE)
        modified_condition = re.sub(r'\s*AND\s*$', '', modified_condition, flags=re.IGNORECASE)
        modified_condition = re.sub(r'\s*OR\s*$', '', modified_condition, flags=re.IGNORECASE)
        if before_sub != modified_condition:
            debug(f"Removed leading/trailing operators: '{before_sub}' → '{modified_condition}'")
        
        # Clean up parentheses
        before_sub = modified_condition
        modified_condition = re.sub(r'^\s*\(\s*$', '', modified_condition)  # Single opening parenthesis
        modified_condition = re.sub(r'^\s*\)\s*$', '', modified_condition)  # Single closing parenthesis
        modified_condition = re.sub(r'^\s*\(\s*\)\s*$', '', modified_condition)  # Empty parentheses
        if before_sub != modified_condition:
            debug(f"Cleaned up parentheses: '{before_sub}' → '{modified_condition}'")
        
        # Strip whitespace
        modified_condition = modified_condition.strip()
        
        # If condition is empty after processing, return TRUE
        if not modified_condition:
            debug("Condition is empty after processing, returning 'TRUE'")
            return "TRUE"
        
        debug(f"Final modified condition: '{modified_condition}'")
        return modified_condition

    def process_condition(self, condition, condition_type):
        """
        Analyze a trigger condition to determine if it's applicable for a given operation type.
        
        This function:
        1. Determines if a condition contains operation-specific keywords
        2. Evaluates whether the condition applies to the current operation type
        3. Makes decisions about retaining or removing code blocks based on condition applicability
        
        Args:
            condition (str): The SQL condition to analyze
            condition_type (str): The operation type to check for (on_insert, on_update, or on_delete)
            
        Returns:
            bool: True if the condition contains operation-specific logic that should be removed,
                 False if the condition should be retained for this operation type
        """
        # Skip empty conditions
        if not condition:
            debug(f"Empty condition provided for {condition_type}, returning False")
            return False
            
        # Clean up condition for analysis
        condition = condition.strip()
        debug(f"Processing condition for {condition_type}: '{condition}'")
        
        # Remove surrounding parentheses if present for cleaner analysis
        if condition.startswith("(") and condition.endswith(")"):
            condition = condition[1:-1]
            debug(f"Removed outer parentheses: '{condition}'")
        
        # Check for operation-specific keywords in the condition
        condition_dict = {
            "on_insert": condition.find("INSERTING") != -1,
            "on_update": condition.find("UPDATING") != -1,
            "on_delete": condition.find("DELETING") != -1,
        }
        
        # Log which operation keywords were found in this condition
        debug("Operation keywords found in condition:")
        debug(f"  - INSERT keywords: {condition_dict['on_insert']}")
        debug(f"  - UPDATE keywords: {condition_dict['on_update']}")
        debug(f"  - DELETE keywords: {condition_dict['on_delete']}")
        
        # Decision logic:
        # 1. If condition mentions current operation type, remove it (return False)
        # 2. If condition doesn't mention any operation type, keep it for all (return False) 
        # 3. If condition mentions other operations but not this one, keep it (return True)
        
        # Case 1: Condition mentions current operation - remove from current operation's code
        logger.debug(f"condition_dict: {condition_dict} {condition_type} {condition}")
        if condition_dict[condition_type]:
            debug(f"REMOVE: Condition contains {condition_type} keywords")
            return False
            
        # Case 2: Condition doesn't mention any specific operation - keep for all operations
        elif not any(condition_dict.values()):
            debug("KEEP: Condition doesn't contain any operation keywords")
            return False
            
        # Case 3: Condition mentions other operations but not this one - keep for this operation
        else:
            debug(f"KEEP: Condition mentions other operations but not {condition_type}")
            return True

    def _process_on_json(self, statements, json_path="", condition_type:str = "on_insert"):
            """_process_on_json function."""
            item = []
            # Handle nested structures (begin_end blocks, exception handlers, etc.)
            for statement in statements:
                if isinstance(statement, dict) and "type" in statement:
                    if statement["type"] == "begin_end":
                        # Process IF statements in begin_end_statements
                        if "begin_end_statements" in statement:
                            statement["begin_end_statements"] = self._process_on_json(statement["begin_end_statements"],f"{json_path}.begin_end_statements",condition_type,)

                        # Process IF statements in exception_handlers
                        if "exception_handlers" in statement:
                            statement["exception_handlers"] = self._process_on_json(statement["exception_handlers"],f"{json_path}.exception_handlers",condition_type,)
                            for handler_index, handler in enumerate(statement["exception_handlers"]):
                                if "exception_statements" in handler:
                                    handler["exception_statements"] = self._process_on_json(handler["exception_statements"],f"{json_path}.exception_handlers.{handler_index}.exception_statements",condition_type,)

                    elif statement["type"] == "if_else":
                        # Process IF statements in then_statements, if_elses, and else_statements
                        json_path = f"{json_path}.if_else"
                        main_if_else_condition = self.process_condition(statement["condition"], condition_type)
                        statement["condition"] = self.modify_condition(statement["condition"])
                        if "then_statements" in statement:
                            statement["then_statements"] = self._process_on_json(statement["then_statements"],f"{json_path}.then_statements",condition_type,)
                        if "else_statements" in statement:
                            statement["else_statements"] = self._process_on_json(statement["else_statements"],f"{json_path}.else_statements",condition_type,)
                        if "if_elses" in statement:
                            json_path = f"{json_path}.if_elses"
                            after_parse_if_elses = []
                            for i, if_elses_item in enumerate(statement["if_elses"]):
                                if_elses_condition = self.process_condition(if_elses_item["condition"], condition_type)
                                if_elses_item["condition"] = self.modify_condition(if_elses_item["condition"])
                                json_path = f"{json_path}.{i}"
                                if not if_elses_condition:
                                    json_path = f"{json_path}.then_statements"
                                    if_elses_item["then_statements"] = self._process_on_json(if_elses_item["then_statements"],f"{json_path}.then_statements",condition_type,)
                                    after_parse_if_elses.append(if_elses_item)
                            statement["if_elses"] = after_parse_if_elses
                        if  main_if_else_condition and len(statement["if_elses"]) == 0:
                            continue
                        elif main_if_else_condition and len(statement["if_elses"]) > 0:
                            statement["condition"] = self.modify_condition(statement["if_elses"][0]["condition"])
                            statement["then_statements"] = statement["if_elses"][0]["then_statements"]
                            statement["if_elses"] = statement["if_elses"][1:]
                        elif main_if_else_condition:
                            logger.debug(f"if_else_delete_path: {json_path}.if_else -- {statement}")

                    elif statement["type"] == "case_when":
                        # Process main case condition
                        if "condition" in  statement and  statement["condition"]:
                            main_case_condition = self.process_condition( statement["condition"], condition_type)
                            if main_case_condition:
                                # If condition should be removed for this operation, return None
                                debug(f"case_when main condition removal: {json_path}.case_when.condition")
                                return None
                            else:
                                # Modify the condition for PostgreSQL compatibility
                                 statement["condition"] = self.modify_condition( statement["condition"])

                        # Process when clauses conditions and statements
                        if "when_clauses" in statement:
                            for clause_index, clause in enumerate(statement["when_clauses"]):
                                # Process when clause condition
                                if "condition" in clause and clause["condition"]:
                                    when_condition_result = self.process_condition(clause["condition"], condition_type)
                                    if when_condition_result:
                                        # If condition should be removed, skip this when clause
                                        debug(f"when_clause condition removal: {json_path}.when_clauses.{clause_index}.condition")
                                        continue
                                    else:
                                        # Modify the when condition for PostgreSQL compatibility
                                        clause["condition"] = self.modify_condition(clause["condition"])
                                
                                # Process then_statements within when clauses
                                if "then_statements" in clause:
                                    clause["then_statements"] = self._process_on_json(clause["then_statements"],f"{json_path}.then_statements",condition_type,)
                        if "else_statements" in statement:
                            statement["else_statements"] = self._process_on_json(statement["else_statements"],f"{json_path}.else_statements",condition_type,)

                    elif statement["type"] == "for_loop":
                        # Process IF statements in loop_statements
                        if "loop_statements" in statement:
                            statement["loop_statements"] = self._process_on_json(statement["loop_statements"],f"{json_path}.loop_statements",condition_type,)
                item.append(statement)
            return item

    def rest_strings(self,sql_json) -> Dict:
        """
        Find all "rest string" content in various statement types within the JSON structure.


        This method recursively searches through:
        - begin_end_statements
        - exception_statements
        - then_statements
        - else_statements


        Returns:
            List[str]: List of all rest string content found
        """
        strng_convert_json: Dict = {
            "assignment": 0,
            "for_loop": 0,
            "if_else": 0,
            "case_when": 0,
            "begin_end": 0,
            "exception_handler": 0,
            "function_calling": 0,
            "when_statement": 0,
            "elif_statement": 0,
            "select_statement": 0,
            "insert_statement": 0,
            "update_statement": 0,
            "delete_statement": 0,
            "raise_statement": 0,
            "merge_statement": 0,
            "null_statement": 0,
            "return_statement": 0,
            "with_statement": 0,
            "bulk_statement": 0,
        }

        def extract_rest_strings_from_item(statement):
            """Recursively extract rest strings from any statement"""
            if isinstance(statement, dict):
                if "type" in statement:
                    logger.debug(f"statement: {statement}")
                    strng_convert_json[statement["type"]] += 1
                # Recursively process all values in the dictionary
                for value in statement.values():
                    extract_rest_strings_from_item(value)

            elif isinstance(statement, list):
                # Recursively process all items in the list
                for sub_item in statement:
                    extract_rest_strings_from_item(sub_item)

        # Process main_section_lines
        extract_rest_strings_from_item(sql_json)

        return strng_convert_json

    def to_sql(self):
        """
        Clean the JSON data by removing conditional statements that don't apply to specific operations,
        then transform the analysis JSON into an operation-specific target structure.
        
        This function:
        1. Makes deep copies of the original JSON data for each operation type
        2. Processes each copy to filter out operation-specific code blocks
        3. Combines the processed data into the final structure with on_insert, on_update, and on_delete sections
        4. Returns the formatted JSON string
        
        Returns:
            str: JSON string containing the operation-specific trigger code
        """
        debug("=== Starting to_sql() conversion process ===")
        
        # Step 1: Create deep copies of the JSON data for each operation type to process independently
        debug("Creating deep copies of JSON data for each operation type")
        self.after_parse_on_insert = copy.deepcopy(self.json_data.get("main", []))
        self.after_parse_on_update = copy.deepcopy(self.json_data.get("main", []))
        self.after_parse_on_delete = copy.deepcopy(self.json_data.get("main", []))
        self.declarations = copy.deepcopy(self.json_data.get("declarations", {}))
        
        # Log the structure we're working with
        debug("JSON data structure:")
        debug(f"  - Main blocks: {len(self.json_data.get('main', []))} items")
        debug(f"  - Declarations: {len(self.declarations.get('variables', []))} variables, "
              f"{len(self.declarations.get('constants', []))} constants, "
              f"{len(self.declarations.get('exceptions', []))} exceptions")

        # Step 2: Process each operation type to filter relevant code
        debug("=== Processing INSERT operations ===")
        # self.parse_pl_json_on_insert()
        # logger.debug(f"after_parse_on_insert: {self.after_parse_on_insert["begin_end_statements"]}")
        self.after_parse_on_insert["begin_end_statements"] = self._process_on_json(self.after_parse_on_insert["begin_end_statements"], "main.begin_end_statements", "on_insert")
        
        debug("=== Processing UPDATE operations ===")
        # self.parse_pl_json_on_update()
        self.after_parse_on_update["begin_end_statements"] = self._process_on_json(self.after_parse_on_update["begin_end_statements"], "main.begin_end_statements", "on_update")
        
        debug("=== Processing DELETE operations ===")
        # self.parse_pl_json_on_delete()
        self.after_parse_on_delete["begin_end_statements"] = self._process_on_json(self.after_parse_on_delete["begin_end_statements"], "main.begin_end_statements", "on_delete")

        # Step 3: Combine into final structure
        debug("Building final converted structure")
        converted = {
            "on_insert": {
                "declarations": self.declarations,
                "main": self.after_parse_on_insert,
                "conversion_stats": self.rest_strings(self.after_parse_on_insert),
            },
            "on_update": {
                "declarations": self.declarations,
                "main": self.after_parse_on_update,
                "conversion_stats": self.rest_strings(self.after_parse_on_update),
            },
            "on_delete": {
                "declarations": self.declarations,
                "main": self.after_parse_on_delete,
                "conversion_stats": self.rest_strings(self.after_parse_on_delete),
            },
            "metadata" : self.json_data['metadata']
        }

        # Step 4: Convert to JSON string
        debug("Converting to JSON string")
        self.sql_content = json.dumps(converted, ensure_ascii=False, indent=2)
        
        # Log the result size
        debug(f"Generated JSON string with {len(self.sql_content)} characters")
        debug("=== to_sql() conversion complete ===")
        
        return self.sql_content