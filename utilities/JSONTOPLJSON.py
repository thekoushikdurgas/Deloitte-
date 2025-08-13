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
    log_parsing_start,
    log_parsing_complete,
    log_parsing_error,
    log_structure_found,
    log_nesting_level,
    log_performance,
)


class JSONTOPLJSON:
    def __init__(self, json_data):
        self.json_data = json_data
        self.sql_content = ""
        self.main_json: List = []
        self.after_parse_on_insert: List = []
        self.after_parse_on_update: List = []
        self.after_parse_on_delete: List = []
        self.to_sql()

    def process_condition(self, condition, condition_type):
        """
        condition_type: on_insert, on_update, on_delete
        condition: condition string
        return: True if condition is met, False otherwise
        """
        condition = condition.strip()
        if condition.startswith("(") and condition.endswith(")"):
            condition = condition[1:-1]
        condition_dict = {
            "on_insert": condition.find("INSERTING") != -1
            or condition.find("INSERT") != -1,
            "on_update": condition.find("UPDATING") != -1
            or condition.find("UPDATE") != -1,
            "on_delete": condition.find("DELETING") != -1
            or condition.find("DELETE") != -1,
        }
        # logger.debug(condition_dict)
        # Insert/Delete
        if condition_dict[condition_type]:
            # logger.debug(f"{condition_type}--Insert--{condition}")
            return False
        elif (
            not condition_dict["on_insert"]
            and not condition_dict["on_update"]
            and not condition_dict["on_delete"]
        ):
            # logger.debug(f"{condition_type}--Insert--{condition}")
            return False
        else:
            # logger.debug(f"{condition_type}--Delete--{condition}")
            return True
        
    def parse_pl_json_on_insert(self):
        
        def process_on_insert_json(statements, json_path=""):
            item = statements
            condition_type = "on_insert"
            # Handle nested structures (begin_end blocks, exception handlers, etc.)
            if isinstance(item, dict) and "type" in item:
                if item["type"] == "begin_end":
                    # Process IF statements in begin_end_statements
                    if "begin_end_statements" in item:
                        for i, item1 in enumerate(item["begin_end_statements"]):
                            item["begin_end_statements"][i] = process_on_insert_json(item1,f"{json_path}.begin_end_statements")

                    # Process IF statements in exception_handlers
                    if "exception_handlers" in item:
                        for handler in item["exception_handlers"]:
                            if "exception_statements" in handler:
                                for i, item1 in enumerate(handler["exception_statements"]):
                                    handler["exception_statements"][i] = process_on_insert_json(item1,f"{json_path}.exception_statements")

                # elif item["type"] == "if_else":
                #     logger.debug(f"json_path: {json_path}")
                #     # Process IF statements in then_statements, else_if, and else_statements
                #     json_path = f"{json_path}.if_else"
                #     main_if_else_condition = self.process_condition(item["condition"], condition_type)

                #     if "else_if" in item and len(item["else_if"]) > 0:
                #         json_path = f"{json_path}.else_if"
                #         # after_parse_else_if = item["else_if"]
                #         i = 0
                #         while i < len(item["else_if"]):
                #             json_path = f"{json_path}.{i}"
                #             else_if_condition = self.process_condition(item["else_if"][i]["condition"], condition_type)
                #             logger.debug(f"{condition_type} -- {else_if_condition} -- {item['else_if'][i]['condition']}--{item}")
                #             if not else_if_condition:
                #                 json_path = f"{json_path}.then_statements"
                #                 for j, item1 in enumerate(item["else_if"][i]["then_statements"]):
                #                     json_path = f"{json_path}.then_statements.{j}"
                #                     item["else_if"][i]["then_statements"][j] = process_on_insert_json(item1,json_path)
                                
                #             else:
                #                 item["else_if"].pop(i)
                #                 i -= 1
                #             i += 1
                #         logger.debug(f"item_else_if: {item['else_if']}")
                #         # item["else_if"] = after_parse_else_if
                #     if "then_statements" in item:
                #         for i, item1 in enumerate(item["then_statements"]):
                #             item["then_statements"][i] = process_on_insert_json(item1,f"{json_path}.then_statements")

                #     if "else_statements" in item:
                #         for i, item1 in enumerate(item["else_statements"]):
                #             item["else_statements"][i] = process_on_insert_json(item1,f"{json_path}.else_statements")
                #     if main_if_else_condition and len(item["else_if"]) == 0:
                #         logger.debug(f"delete path: {json_path}.if_else")

                elif item["type"] == "case_when":
                    if self.process_condition(item["case_expression"], condition_type):
                        logger.debug(f"delete path: {json_path}.case_when")
                    # Process IF statements in when_clauses (then_statements and else_statements)
                    if "when_clauses" in item:
                        for clause in item["when_clauses"]:
                            if "then_statements" in clause:
                                if self.process_condition(clause["when_value"], condition_type):
                                    logger.debug(f"delete path: {json_path}.when_value")
                                for i, item1 in enumerate(clause["then_statements"]):
                                    clause["then_statements"][i] = process_on_insert_json(item1,f"{json_path}.then_statements")
                    if "else_statements" in item:
                        for i, item1 in enumerate(item["else_statements"]):
                            item["else_statements"][i] = process_on_insert_json(item1,f"{json_path}.else_statements")

                elif item["type"] == "for_loop":
                    # Process IF statements in loop_statements
                    if "loop_statements" in item:
                        for i, item1 in enumerate(item["loop_statements"]):
                            item["loop_statements"][i] = process_on_insert_json(item1,f"{json_path}.loop_statements")
            return item
        main_json = self.main_json
        for frist_begin_end in main_json:
            for item in frist_begin_end["begin_end_statements"]:
                self.after_parse_on_insert.append(process_on_insert_json(item, "main.begin_end_statements.0"))
                
    def parse_pl_json_on_update(self):
        def process_on_update_json(statements, json_path=""):
            item = statements
            condition_type = "on_update"
            return item
        main_json = self.main_json
        for frist_begin_end in main_json:
            for item in frist_begin_end["begin_end_statements"]:
                self.after_parse_on_update.append(process_on_update_json(item, "main.begin_end_statements.0"))
    
    def parse_pl_json_on_delete(self):
        def process_on_delete_json(statements, json_path=""):
            item = statements
            condition_type = "on_delete"
            return item
        main_json = self.main_json
        for frist_begin_end in main_json:
            for item in frist_begin_end["begin_end_statements"]:
                self.after_parse_on_delete.append(process_on_delete_json(item, "main.begin_end_statements.0"))
    
    def to_sql(self):
        # Transform analysis JSON into target structure and split by operation
        # {
        #   "declarations": {...},
        #   "on_insert": [...],
        #   "on_update": [...],
        #   "on_delete": [...]
        # }
        declarations = self.json_data.get("declarations", {})

        main = self.json_data.get("main", [])
        self.parse_pl_json_on_insert()
        self.parse_pl_json_on_update()
        self.parse_pl_json_on_delete()
        self.main_json = main

        converted = {
            "declarations": declarations,
            "on_insert": self.after_parse_on_insert,
            "on_update": self.after_parse_on_update,
            "on_delete": self.after_parse_on_delete,
        }

        # Store pretty JSON string for writer
        self.sql_content = json.dumps(converted, ensure_ascii=False, indent=2)
        return self.sql_content
