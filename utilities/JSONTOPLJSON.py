import json

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
        self.main_json = {}
        self.to_sql()

    def process_condition(self, condition, condition_type):
        '''
        
        '''
        condition = condition.strip()
        if condition.startswith("(") and condition.endswith(")"):
            condition = condition[1:-1]
        condition_dict ={
            "on_insert": condition.find("INSERTING") != -1 or condition.find("INSERT") != -1,
            "on_update": condition.find("UPDATING") != -1 or condition.find("UPDATE") != -1,
            "on_delete": condition.find("DELETING") != -1 or condition.find("DELETE") != -1,
        }
        # logger.debug(condition_dict)
        # Insert/Delete
        if condition_dict[condition_type]:
            # logger.debug(f"{condition_type}--Insert--{condition}")
            return False
        elif not condition_dict["on_insert"] and not condition_dict["on_update"] and not condition_dict["on_delete"]:
            # logger.debug(f"{condition_type}--Insert--{condition}")
            return False
        else:
            # logger.debug(f"{condition_type}--Delete--{condition}")
            return True

    def parse_pl_json(self, condition_type):
        """
        Parse the PL/JSON data and return the SQL content.
        """
        def process_pl_json_in_list(statements_list, json_path=""):
            if not statements_list:
                return
            after_parese = {}
            i = 0
            while i < len(statements_list):
                item = statements_list[i]
                # Handle nested structures (begin_end blocks, exception handlers, etc.)
                if isinstance(item, dict) and "type" in item:
                    if item["type"] == "begin_end":
                        # Process IF statements in begin_end_statements
                        if "begin_end_statements" in item:
                            process_pl_json_in_list(item["begin_end_statements"],f"{json_path}.begin_end_statements")

                        # Process IF statements in exception_handlers
                        if "exception_handlers" in item:
                            for handler in item["exception_handlers"]:
                                if "exception_statements" in handler:
                                    process_pl_json_in_list(handler["exception_statements"],f"{json_path}.exception_statements")

                    elif item["type"] == "if_else":
                        # Process IF statements in then_statements, else_if, and else_statements
                        main_if = self.process_condition(item["condition"], condition_type)
                        if "then_statements" in item:
                            process_pl_json_in_list(item["then_statements"],f"{json_path}.then_statements")

                        if "else_if" in item:
                            for elsif_block in item["else_if"]:
                                if(self.process_condition(elsif_block["condition"], condition_type)):
                                    logger.debug(f"{json_path}.else_if")
                                process_pl_json_in_list(elsif_block["then_statements"],f"{json_path}.else_if.then_statements")

                        if "else_statements" in item:
                            process_pl_json_in_list(item["else_statements"],f"{json_path}.else_statements")

                    elif item["type"] == "case_when":
                        main_case = self.process_condition(item["case_expression"], condition_type)
                        # Process IF statements in when_clauses (then_statements and else_statements)
                        if "when_clauses" in item:
                            for clause in item["when_clauses"]:
                                if "then_statements" in clause:
                                    if(self.process_condition(clause["when_value"], condition_type)):
                                        logger.debug(f"{json_path}.then_statements")
                                    process_pl_json_in_list(clause["then_statements"],f"{json_path}.then_statements")
                        if "else_statements" in item:
                            process_pl_json_in_list(item["else_statements"],f"{json_path}.else_statements")

                    elif item["type"] == "for_loop":
                        # Process IF statements in loop_statements
                        if "loop_statements" in item:
                            process_pl_json_in_list(item["loop_statements"],f"{json_path}.loop_statements")

                i += 1

        # Process the main_section_lines
        process_pl_json_in_list(self.main_json, "main")

        # logger.debug("IF-ELSEIF-ELSE parsing complete")
        return self.main_json

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
        self.main_json = main
        on_insert = self.parse_pl_json("on_insert")
        on_update = self.parse_pl_json("on_update")
        on_delete = self.parse_pl_json("on_delete")

        converted = {
            "declarations": declarations,
            "on_insert": on_insert,
            "on_update": on_update,
            "on_delete": on_delete,
        }

        # Store pretty JSON string for writer
        self.sql_content = json.dumps(converted, ensure_ascii=False, indent=2)
        return self.sql_content
