import os
import json
import re
import copy

class JSONTOPLJSON:
    def __init__(self, json_data):
        self.json_data = json_data
        self.sql_content = ""
        self.to_sql()
    
    def to_sql(self):
        # Transform analysis JSON into target structure and split by operation
        # {
        #   "declarations": {...},
        #   "on_insert": [...],
        #   "on_update": [...],
        #   "on_delete": [...]
        # }
        declarations = self.json_data.get("declarations", {})

        # Extract the main statements array. The input usually has:
        # "main": [ { "type": "begin_block", "sqls": [ ... ] } ]
        main = self.json_data.get("main", [])
        if main and isinstance(main, list):
            first = main[0]
            if isinstance(first, dict) and first.get("type") == "begin_block" and isinstance(first.get("sqls"), list):
                main_statements = first.get("sqls", [])
            else:
                # Fallback: use main as-is
                main_statements = main
        else:
            main_statements = []

        # Helper to detect operation token in condition strings
        def _condition_has_op(condition_value: str, op_token: str) -> bool:
            if not isinstance(condition_value, str):
                return False
            text = condition_value.upper()
            return op_token in text

        # Build pruned if_else node for a specific branch
        def _build_if_node_for_branch(condition_value: str, then_sql_block):
            return {
                "type": "if_else",
                "condition": condition_value,
                "then_sql": copy.deepcopy(then_sql_block),
            }

        # Recursively distribute statements by operation
        def _distribute(statements):
            ins, upd, dele = [], [], []
            if not isinstance(statements, list):
                return ins, upd, dele

            for stmt in statements:
                # Strings are unconditional text lines -> all ops
                if isinstance(stmt, str):
                    ins.append(stmt)
                    upd.append(stmt)
                    dele.append(stmt)
                    continue

                if not isinstance(stmt, dict):
                    # Unknown node, replicate
                    ins.append(copy.deepcopy(stmt))
                    upd.append(copy.deepcopy(stmt))
                    dele.append(copy.deepcopy(stmt))
                    continue

                node_type = stmt.get("type")

                # Unwrap begin blocks by distributing their children
                if node_type == "begin_block" and isinstance(stmt.get("sqls"), list):
                    cins, cupd, cdel = _distribute(stmt.get("sqls", []))
                    ins.extend(cins)
                    upd.extend(cupd)
                    dele.extend(cdel)
                    continue

                # If-else with operation conditions
                if node_type == "if_else":
                    cond = stmt.get("condition", "")
                    then_sql = stmt.get("then_sql", [])
                    else_if = stmt.get("else_if_statement")
                    else_stmt = stmt.get("else_statement")

                    matched_any_op = False

                    # Primary condition routing
                    if _condition_has_op(cond, "INSERTING"):
                        ins.append(_build_if_node_for_branch(cond, then_sql))
                        matched_any_op = True
                    if _condition_has_op(cond, "UPDATING"):
                        upd.append(_build_if_node_for_branch(cond, then_sql))
                        matched_any_op = True
                    if _condition_has_op(cond, "DELETING"):
                        dele.append(_build_if_node_for_branch(cond, then_sql))
                        matched_any_op = True

                    # Else-if branch may target other operations
                    if isinstance(else_if, dict):
                        ei_cond = else_if.get("condition", "")
                        ei_then = else_if.get("then_sql", [])
                        if _condition_has_op(ei_cond, "INSERTING"):
                            ins.append(_build_if_node_for_branch(ei_cond, ei_then))
                            matched_any_op = True
                        if _condition_has_op(ei_cond, "UPDATING"):
                            upd.append(_build_if_node_for_branch(ei_cond, ei_then))
                            matched_any_op = True
                        if _condition_has_op(ei_cond, "DELETING"):
                            dele.append(_build_if_node_for_branch(ei_cond, ei_then))
                            matched_any_op = True

                        # Some inputs chain multiple else_if (nested under else_if_statement)
                        # Support simple chaining via nested else_if_statement
                        nested_else_if = else_if.get("else_if_statement")
                        while isinstance(nested_else_if, dict):
                            nei_cond = nested_else_if.get("condition", "")
                            nei_then = nested_else_if.get("then_sql", [])
                            if _condition_has_op(nei_cond, "INSERTING"):
                                ins.append(_build_if_node_for_branch(nei_cond, nei_then))
                                matched_any_op = True
                            if _condition_has_op(nei_cond, "UPDATING"):
                                upd.append(_build_if_node_for_branch(nei_cond, nei_then))
                                matched_any_op = True
                            if _condition_has_op(nei_cond, "DELETING"):
                                dele.append(_build_if_node_for_branch(nei_cond, nei_then))
                                matched_any_op = True
                            nested_else_if = nested_else_if.get("else_if_statement")

                    # If none of the conditions mention operations, treat entire node as universal
                    if not matched_any_op:
                        ins.append(copy.deepcopy(stmt))
                        upd.append(copy.deepcopy(stmt))
                        dele.append(copy.deepcopy(stmt))

                    # Note: we intentionally drop else_statement in per-op pruning to avoid
                    # bringing non-op branches into op-specific arrays
                    continue

                # Default: replicate node across ops
                ins.append(copy.deepcopy(stmt))
                upd.append(copy.deepcopy(stmt))
                dele.append(copy.deepcopy(stmt))

            return ins, upd, dele

        on_insert, on_update, on_delete = _distribute(main_statements)

        converted = {
            "declarations": declarations,
            "on_insert": on_insert,
            "on_update": on_update,
            "on_delete": on_delete,
        }

        # Store pretty JSON string for writer
        self.sql_content = json.dumps(converted, ensure_ascii=False, indent=2)
        return self.sql_content


def read_json_to_oracle_triggers() -> None:
    # Define directories
    json_dir = "files/format_json"
    sql_out_dir = "files/format_pl_json"

    # Ensure directories exist
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    if not os.path.exists(sql_out_dir):
        os.makedirs(sql_out_dir)

    # Process each analysis JSON file
    json_files = [f for f in os.listdir(json_dir) if f.endswith("_analysis.json")]

    for json_file in json_files:
        match = re.search(r"trigger(\d+)_analysis\.json$", json_file)
        if not match:
            # Skip non-trigger analysis files
            continue
        trigger_num = match.group(1)
        json_path = os.path.join(json_dir, json_file)
        with open(json_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)

        analyzer = JSONTOPLJSON(analysis)
        sql_content = analyzer.to_sql()

        # Save as JSON with the new structure
        out_filename = f"trigger{trigger_num}.json"
        out_path = os.path.join(sql_out_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sql_content)
        print(f"Created {out_filename}")


if __name__ == "__main__":
    read_json_to_oracle_triggers()
    print("PostSQL JSON conversion complete!")
