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
            "INSERTING", "UPDATING", "DELETING", 
            "INSERT", "UPDATE", "DELETE"
        ]
        
        # PostgreSQL TG_OP patterns to remove (case-insensitive)
        tg_op_patterns = [
            r"TG_OP\s*=\s*['\"]INSERT['\"]",
            r"TG_OP\s*=\s*['\"]UPDATE['\"]", 
            r"TG_OP\s*=\s*['\"]DELETE['\"]"
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
            "on_insert": condition.find("INSERTING") != -1 or condition.find("INSERT") != -1,
            "on_update": condition.find("UPDATING") != -1 or condition.find("UPDATE") != -1,
            "on_delete": condition.find("DELETING") != -1 or condition.find("DELETE") != -1,
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

    def parse_pl_json_on_insert(self):
        """parse_pl_json_on_insert function."""
        def process_on_insert_json(
            statements, json_path="", condition_type="on_insert"
        ):
            """process_on_insert_json function."""
            item = statements
            # Handle nested structures (begin_end blocks, exception handlers, etc.)
            if isinstance(item, dict) and "type" in item:
                if item["type"] == "begin_end":
                    # Process IF statements in begin_end_statements
                    if "begin_end_statements" in item:
                        for i, item1 in enumerate(item["begin_end_statements"]):
                            item["begin_end_statements"][i] = process_on_insert_json(
                                item1,
                                f"{json_path}.begin_end_statements.{i}",
                                condition_type,
                            )

                    # Process IF statements in exception_handlers
                    if "exception_handlers" in item:
                        for handler_index, handler in enumerate(
                            item["exception_handlers"]
                        ):
                            if "exception_statements" in handler:
                                for i, item1 in enumerate(
                                    handler["exception_statements"]
                                ):
                                    handler["exception_statements"][i] = (
                                        process_on_insert_json(
                                            item1,
                                            f"{json_path}.exception_handlers.{handler_index}.exception_statements.{i}",
                                            condition_type,
                                        )
                                    )

                elif item["type"] == "if_else":
                    # Process IF statements in then_statements, else_if, and else_statements
                    json_path = f"{json_path}.if_else"
                    item["condition"] = self.modify_condition(item["condition"])
                    main_if_else_condition = self.process_condition(
                        item["condition"], condition_type
                    )
                    if "then_statements" in item:
                        for i, item1 in enumerate(item["then_statements"]):
                            item["then_statements"][i] = process_on_insert_json(
                                item1,
                                f"{json_path}.then_statements.{i}",
                                condition_type,
                            )
                    if "else_statements" in item:
                        for i, item1 in enumerate(item["else_statements"]):
                            item["else_statements"][i] = process_on_insert_json(
                                item1,
                                f"{json_path}.else_statements.{i}",
                                condition_type,
                            )
                    if "else_if" in item and len(item["else_if"]) > 0:
                        json_path = f"{json_path}.else_if"
                        after_parse_else_if = []
                        for i, else_if_item in enumerate(item["else_if"]):
                            else_if_item["condition"] = self.modify_condition(else_if_item["condition"])
                            json_path = f"{json_path}.{i}"
                            else_if_condition = self.process_condition(
                                else_if_item["condition"], condition_type
                            )
                            if not else_if_condition:
                                json_path = f"{json_path}.then_statements"
                                for j, item1 in enumerate(
                                    else_if_item["then_statements"]
                                ):
                                    json_path = f"{json_path}.then_statements.{j}"
                                    else_if_item["then_statements"][j] = (
                                        process_on_insert_json(
                                            item1, json_path, condition_type
                                        )
                                    )
                                after_parse_else_if.append(else_if_item)
                        item["else_if"] = after_parse_else_if

                    if main_if_else_condition and len(item["else_if"]) == 0:
                        return None
                    elif main_if_else_condition and len(item["else_if"]) > 0:
                        item["condition"] = self.modify_condition(item["else_if"][0]["condition"])
                        item["then_statements"] = item["else_if"][0]["then_statements"]
                        item["else_if"] = item["else_if"][1:]

                    elif main_if_else_condition:
                        logger.debug(
                            f"if_else_delete_path: {json_path}.if_else -- {item}"
                        )

                elif item["type"] == "case_when":

                    #     logger.debug(f"delete path: {json_path}.case_when")
                    #     # return None
                    # Process IF statements in when_clauses (then_statements and else_statements)
                    if "when_clauses" in item:
                        for clause_index, clause in enumerate(item["when_clauses"]):

                            #         clause["when_value"], condition_type
                            #     ):
                            #         logger.debug(f"delete path: {json_path}.when_value")
                            #         # return None
                                for i, item1 in enumerate(clause["then_statements"]):
                                    clause["then_statements"][i] = (
                                        process_on_insert_json(
                                            item1,
                                            f"{json_path}.when_clauses.{clause_index}.then_statements.{i}",
                                            condition_type,
                                        )
                                    )
                    if "else_statements" in item:
                        for i, item1 in enumerate(item["else_statements"]):
                            item["else_statements"][i] = process_on_insert_json(
                                item1,
                                f"{json_path}.else_statements.{i}",
                                condition_type,
                            )

                elif item["type"] == "for_loop":
                    # Process IF statements in loop_statements
                    if "loop_statements" in item:
                        for i, item1 in enumerate(item["loop_statements"]):
                            item["loop_statements"][i] = process_on_insert_json(
                                item1,
                                f"{json_path}.loop_statements.{i}",
                                condition_type,
                            )
            return item

        for u, main_item in enumerate(self.after_parse_on_insert):
            logger.debug(f"after_parse_on_insert: {main_item["begin_end_statements"]}")
            for r, begin_end_item in enumerate(main_item["begin_end_statements"]):
                json_path = f"main.begin_end_statements.{r}.begin_end_statements"
                self.after_parse_on_insert[u]["begin_end_statements"][r] = (
                    process_on_insert_json(begin_end_item, json_path, "on_insert")
                )

    def parse_pl_json_on_update(self):
        """parse_pl_json_on_update function."""
        def process_on_update_json(
            statements, json_path="", condition_type="on_update"
        ):
            """process_on_update_json function."""
            item = statements
            # Handle nested structures (begin_end blocks, exception handlers, etc.)
            if isinstance(item, dict) and "type" in item:
                if item["type"] == "begin_end":
                    # Process IF statements in begin_end_statements
                    if "begin_end_statements" in item:
                        for i, item1 in enumerate(item["begin_end_statements"]):
                            item["begin_end_statements"][i] = process_on_update_json(
                                item1,
                                f"{json_path}.begin_end_statements.{i}",
                                condition_type,
                            )

                    # Process IF statements in exception_handlers
                    if "exception_handlers" in item:
                        for handler_index, handler in enumerate(
                            item["exception_handlers"]
                        ):
                            if "exception_statements" in handler:
                                for i, item1 in enumerate(
                                    handler["exception_statements"]
                                ):
                                    handler["exception_statements"][i] = (
                                        process_on_update_json(
                                            item1,
                                            f"{json_path}.exception_handlers.{handler_index}.exception_statements.{i}",
                                            condition_type,
                                        )
                                    )

                elif item["type"] == "if_else":
                    # Process IF statements in then_statements, else_if, and else_statements
                    json_path = f"{json_path}.if_else"
                    item["condition"] = self.modify_condition(item["condition"])
                    main_if_else_condition = self.process_condition(
                        item["condition"], condition_type
                    )
                    if "else_if" in item and len(item["else_if"]) > 0:
                        json_path = f"{json_path}.else_if"
                        after_parse_else_if = []
                        for i, else_if_item in enumerate(item["else_if"]):
                            else_if_item["condition"] = self.modify_condition(else_if_item["condition"])
                            json_path = f"{json_path}.{i}"
                            else_if_condition = self.process_condition(
                                else_if_item["condition"], condition_type
                            )
                            if not else_if_condition:
                                json_path = f"{json_path}.then_statements"
                                for j, item1 in enumerate(
                                    else_if_item["then_statements"]
                                ):
                                    json_path = f"{json_path}.then_statements.{j}"
                                    else_if_item["then_statements"][j] = (
                                        process_on_update_json(
                                            item1, json_path, condition_type
                                        )
                                    )
                                after_parse_else_if.append(else_if_item)
                        item["else_if"] = after_parse_else_if
                    if "then_statements" in item:
                        for i, item1 in enumerate(item["then_statements"]):
                            item["then_statements"][i] = process_on_update_json(
                                item1,
                                f"{json_path}.then_statements.{i}",
                                condition_type,
                            )
                    if "else_statements" in item:
                        for i, item1 in enumerate(item["else_statements"]):
                            item["else_statements"][i] = process_on_update_json(
                                item1,
                                f"{json_path}.else_statements.{i}",
                                condition_type,
                            )
                    if main_if_else_condition and len(item["else_if"]) == 0:
                        return None
                    elif main_if_else_condition and len(item["else_if"]) > 0:
                        item["condition"] = self.modify_condition(item["else_if"][0]["condition"])
                        item["then_statements"] = item["else_if"][0]["then_statements"]
                        item["else_if"] = item["else_if"][1:]
                    elif main_if_else_condition:
                        logger.debug(
                            f"if_else_delete_path: {json_path}.if_else -- {item}"
                        )

                elif item["type"] == "case_when":

                    #     logger.debug(f"delete path: {json_path}.case_when")
                    #     # return None
                    # Process IF statements in when_clauses (then_statements and else_statements)
                    if "when_clauses" in item:
                        for clause_index, clause in enumerate(item["when_clauses"]):
                            if "then_statements" in clause:

                                #     clause["when_value"], condition_type
                                # ):
                                #     logger.debug(f"delete path: {json_path}.when_value")
                                #     # return None
                                for i, item1 in enumerate(clause["then_statements"]):
                                    clause["then_statements"][i] = (
                                        process_on_update_json(
                                            item1,
                                            f"{json_path}.when_clauses.{clause_index}.then_statements.{i}",
                                            condition_type,
                                        )
                                    )
                    if "else_statements" in item:
                        for i, item1 in enumerate(item["else_statements"]):
                            item["else_statements"][i] = process_on_update_json(
                                item1,
                                f"{json_path}.else_statements.{i}",
                                condition_type,
                            )

                elif item["type"] == "for_loop":
                    # Process IF statements in loop_statements
                    if "loop_statements" in item:
                        for i, item1 in enumerate(item["loop_statements"]):
                            item["loop_statements"][i] = process_on_update_json(
                                item1,
                                f"{json_path}.loop_statements.{i}",
                                condition_type,
                            )
            return item

        for u, main_item in enumerate(self.after_parse_on_update):
            for r, begin_end_item in enumerate(main_item["begin_end_statements"]):
                json_path = f"main.begin_end_statements.{r}.begin_end_statements"
                self.after_parse_on_update[u]["begin_end_statements"][r] = (
                    process_on_update_json(begin_end_item, json_path, "on_update")
                )

    def parse_pl_json_on_delete(self):
        """parse_pl_json_on_delete function."""
        def process_on_delete_json(
            statements, json_path="", condition_type="on_delete"
        ):
            """process_on_delete_json function."""
            item = statements
            # Handle nested structures (begin_end blocks, exception handlers, etc.)
            if isinstance(item, dict) and "type" in item:
                if item["type"] == "begin_end":
                    # Process IF statements in begin_end_statements
                    if "begin_end_statements" in item:
                        for i, item1 in enumerate(item["begin_end_statements"]):
                            item["begin_end_statements"][i] = process_on_delete_json(
                                item1,
                                f"{json_path}.begin_end_statements.{i}",
                                condition_type,
                            )

                    # Process IF statements in exception_handlers
                    if "exception_handlers" in item:
                        for handler_index, handler in enumerate(
                            item["exception_handlers"]
                        ):
                            if "exception_statements" in handler:
                                for i, item1 in enumerate(
                                    handler["exception_statements"]
                                ):
                                    handler["exception_statements"][i] = (
                                        process_on_delete_json(
                                            item1,
                                            f"{json_path}.exception_handlers.{handler_index}.exception_statements.{i}",
                                            condition_type,
                                        )
                                    )

                elif item["type"] == "if_else":
                    # Process IF statements in then_statements, else_if, and else_statements
                    json_path = f"{json_path}.if_else"
                    item["condition"] = self.modify_condition(item["condition"])
                    main_if_else_condition = self.process_condition(
                        item["condition"], condition_type
                    )
                    if "else_if" in item and len(item["else_if"]) > 0:
                        json_path = f"{json_path}.else_if"
                        after_parse_else_if = []
                        for i, else_if_item in enumerate(item["else_if"]):
                            else_if_item["condition"] = self.modify_condition(else_if_item["condition"])
                            json_path = f"{json_path}.{i}"
                            else_if_condition = self.process_condition(
                                else_if_item["condition"], condition_type
                            )
                            if not else_if_condition:
                                json_path = f"{json_path}.then_statements"
                                for j, item1 in enumerate(
                                    else_if_item["then_statements"]
                                ):
                                    json_path = f"{json_path}.then_statements.{j}"
                                    else_if_item["then_statements"][j] = (
                                        process_on_delete_json(
                                            item1, json_path, condition_type
                                        )
                                    )
                                after_parse_else_if.append(else_if_item)
                        item["else_if"] = after_parse_else_if
                    if "then_statements" in item:
                        for i, item1 in enumerate(item["then_statements"]):
                            item["then_statements"][i] = process_on_delete_json(
                                item1,
                                f"{json_path}.then_statements.{i}",
                                condition_type,
                            )
                    if "else_statements" in item:
                        for i, item1 in enumerate(item["else_statements"]):
                            item["else_statements"][i] = process_on_delete_json(
                                item1,
                                f"{json_path}.else_statements.{i}",
                                condition_type,
                            )
                    if main_if_else_condition and len(item["else_if"]) == 0:
                        return None
                    elif main_if_else_condition and len(item["else_if"]) > 0:
                        item["condition"] = self.modify_condition(item["else_if"][0]["condition"])
                        item["then_statements"] = item["else_if"][0]["then_statements"]
                        item["else_if"] = item["else_if"][1:]
                    elif main_if_else_condition:
                        logger.debug(
                            f"if_else_delete_path: {json_path}.if_else -- {item}"
                        )

                elif item["type"] == "case_when":

                    # logger.debug(f"delete path: {json_path}.case_when")
                    # return None
                    # Process IF statements in when_clauses (then_statements and else_statements)
                    if "when_clauses" in item:
                        for clause_index, clause in enumerate(item["when_clauses"]):
                            if "then_statements" in clause:

                                # logger.debug(f"delete path: {json_path}.when_value")
                                # return None
                                for i, item1 in enumerate(clause["then_statements"]):
                                    clause["then_statements"][i] = (
                                        process_on_delete_json(
                                            item1,
                                            f"{json_path}.when_clauses.{clause_index}.then_statements.{i}",
                                            condition_type,
                                        )
                                    )
                    if "else_statements" in item:
                        for i, item1 in enumerate(item["else_statements"]):
                            item["else_statements"][i] = process_on_delete_json(
                                item1,
                                f"{json_path}.else_statements.{i}",
                                condition_type,
                            )

                elif item["type"] == "for_loop":
                    # Process IF statements in loop_statements
                    if "loop_statements" in item:
                        for i, item1 in enumerate(item["loop_statements"]):
                            item["loop_statements"][i] = process_on_delete_json(
                                item1,
                                f"{json_path}.loop_statements.{i}",
                                condition_type,
                            )
            return item

        for u, main_item in enumerate(self.after_parse_on_delete):
            for r, begin_end_item in enumerate(main_item["begin_end_statements"]):
                json_path = f"main.begin_end_statements.{r}.begin_end_statements"
                self.after_parse_on_delete[u]["begin_end_statements"][r] = (
                    process_on_delete_json(begin_end_item, json_path, "on_delete")
                )

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
        self.parse_pl_json_on_insert()
        
        debug("=== Processing UPDATE operations ===")
        self.parse_pl_json_on_update()
        
        debug("=== Processing DELETE operations ===")
        self.parse_pl_json_on_delete()

        # Step 3: Combine into final structure
        debug("Building final converted structure")
        converted = {
            "on_insert": {
                "declarations": self.declarations,
                "main": self.after_parse_on_insert
            },
            "on_update": {
                "declarations": self.declarations,
                "main": self.after_parse_on_update
            },
            "on_delete": {
                "declarations": self.declarations,
                "main": self.after_parse_on_delete
            }
        }

        # Step 4: Convert to JSON string
        debug("Converting to JSON string")
        self.sql_content = json.dumps(converted, ensure_ascii=False, indent=2)
        
        # Log the result size
        debug(f"Generated JSON string with {len(self.sql_content)} characters")
        debug("=== to_sql() conversion complete ===")
        
        return self.sql_content