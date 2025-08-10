import os
from datetime import datetime
from typing import Any, Dict, List, Union


JsonNode = Union[Dict[str, Any], str]


DEBUG_FORMATTER: bool = True


def debug(msg: str) -> None:
    if DEBUG_FORMATTER:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fname = os.path.basename(__file__)
        print(f"[{now} {fname}] {msg}")


class FORMATOracleTriggerAnalyzer:
    """
    Render Oracle PL/SQL trigger body from analysis JSON produced by the analyzer.

    Architecture and flow:
    - Input: a dict with keys like `declarations`, `main`, `sql_comments`.
    - Declarations are rendered first under a `DECLARE` section.
    - The first `main` block is rendered inside a `BEGIN ... EXCEPTION ... END;` wrapper.
    - Helper methods recursively render nested structures (IF/ELSIF/ELSE, CASE, FOR, BEGIN blocks).
    - String utilities assist with indentation and safe string literal emission.
    """

    def __init__(self, analysis: Dict[str, Any]):
        self.analysis = analysis
        self.indent_unit = "  "
        debug(f"Initialized with analysis keys: {list(self.analysis.keys())}")

    def to_sql(self) -> str:
        debug("Rendering to SQL started")
        lines: List[str] = []
        # Declarations
        decl = self.analysis.get("declarations", {})
        debug(f"Rendering declarations: keys={list(decl.keys()) if isinstance(decl, dict) else type(decl)}")
        decl_lines = self._render_declarations(decl)
        if decl_lines:
            lines.append("DECLARE")
            lines.extend(self._indent_lines(decl_lines, 1))
        # Main blocks
        main_blocks = self.analysis.get("main", [])
        debug(f"Rendering main blocks: count={len(main_blocks) if isinstance(main_blocks, list) else 0}")
        if main_blocks:
            # Wrap the first main block as the executable block
            block_sql = self._render_begin_block(main_blocks[0], indent_level=0, wrap_begin_end=True)
            lines.extend(block_sql)

        # Additional comments, if any
        sql_comments: List[str] = self.analysis.get("sql_comments", [])
        if sql_comments:
            lines.append("")
            lines.append("-- Additional comments from analysis")
            for comment in sql_comments:
                for c_line in str(comment).splitlines():
                    prefix = "-- " if not c_line.strip().startswith("--") else ""
                    lines.append(f"{prefix}{c_line}")

        result = "\n".join(lines).rstrip() + "\n"
        debug(f"Rendering to SQL finished, length={len(result)} chars")
        return result

    # -----------------------------
    # Rendering helpers
    # -----------------------------
    def _render_declarations(self, decl: Dict[str, Any]) -> List[str]:
        lines: List[str] = []
        # Variables
        for var in decl.get("variables", []) or []:
            name = var.get("name")
            data_type = var.get("data_type")
            default_value = var.get("default_value")
            debug(f"Variable decl: name={name}, type={data_type}, default={default_value}")
            if not name or not data_type:
                continue
            if default_value is None:
                lines.append(f"{name} {data_type};")
            else:
                lines.append(f"{name} {data_type} := {default_value};")

        # Constants
        for const in decl.get("constants", []) or []:
            name = const.get("name")
            data_type = const.get("data_type")
            value = const.get("value")
            debug(f"Constant decl: name={name}, type={data_type}, value={value}")
            if not name or not data_type:
                continue
            lines.append(f"{name} CONSTANT {data_type} := {value};")

        # Exceptions
        for exc in decl.get("exceptions", []) or []:
            name = exc.get("name")
            debug(f"Exception decl: name={name}")
            if not name:
                continue
            lines.append(f"{name} EXCEPTION;")

        return lines

    def _render_begin_block(self, node: Dict[str, Any], indent_level: int, wrap_begin_end: bool = False) -> List[str]:
        lines: List[str] = []
        if wrap_begin_end:
            lines.append("BEGIN")
        sqls: List[JsonNode] = node.get("sqls", []) or []
        debug(f"Begin block: wrap={wrap_begin_end}, sqls={len(sqls)}")
        lines.extend(self._render_sql_list(sqls, indent_level + (1 if wrap_begin_end else 0)))

        # Exception handlers
        handlers = node.get("exception_handlers", []) or []
        if handlers:
            lines.append(self._indent("EXCEPTION", indent_level + (1 if wrap_begin_end else 0)))
            for h in handlers:
                debug(f"Rendering exception handler for: {h.get('exception_name')}")
                lines.extend(self._render_exception_handler(h, indent_level + (2 if wrap_begin_end else 1)))

        if wrap_begin_end:
            lines.append("END;")
        return lines

    def _render_exception_handler(self, handler: Dict[str, Any], indent_level: int) -> List[str]:
        lines: List[str] = []
        exc_name = handler.get("exception_name", "OTHERS")
        when_header = f"WHEN {exc_name} THEN" if exc_name.upper() != "OTHERS" else "WHEN OTHERS THEN"
        lines.append(self._indent(when_header, indent_level - 1))
        # New schema: handler contains a 'sqls' array with actions
        actions = handler.get("sqls", []) or []
        debug(f"Handler actions count: {len(actions)}")
        if not actions:
            lines.append(self._indent("NULL;", indent_level))
            return lines
        for action in actions:
            # function calling (e.g., raise_application_error)
            a_type = (action.get("type") or "").strip()
            debug(f"Handler action type: {a_type}")
            if a_type in {"function calling", "function_calling"}:
                func = (action.get("function_name") or "").strip()
                if func.lower() == "raise_application_error":
                    param = action.get("parameter", {}) or {}
                    code = str(param.get("handler_code", ""))
                    msg = self._plsql_string_literal(str(param.get("handler_string", "")))
                    lines.append(self._indent(f"RAISE_APPLICATION_ERROR({code}, {msg});", indent_level))
                else:
                    # Generic function call not explicitly supported: skip or render as comment
                    # Here we skip unless a raw 'sql' exists
                    sql = action.get("sql")
                    if sql:
                        sql_txt = sql if sql.strip().endswith(";") else sql + ";"
                        lines.append(self._indent(sql_txt, indent_level))
            elif a_type == "RAISE_statements":
                sql = action.get("sql")
                if sql:
                    sql_txt = sql if sql.strip().endswith(";") else sql + ";"
                    lines.append(self._indent(sql_txt, indent_level))
            else:
                # Fallback: try generic sql rendering
                sql = action.get("sql")
                if sql:
                    sql_txt = sql if sql.strip().endswith(";") else sql + ";"
                    lines.append(self._indent(sql_txt, indent_level))
        return lines

    def _render_sql_list(self, items: List[JsonNode], indent_level: int) -> List[str]:
        lines: List[str] = []
        pending_call: List[str] = []

        def flush_pending():
            nonlocal pending_call
            if pending_call:
                text = "\n".join(pending_call).rstrip()
                if text and not text.endswith(";"):
                    text += ";"
                for t_line in text.splitlines():
                    lines.append(self._indent(t_line, indent_level))
                pending_call = []

        for item in items:
            # Raw string lines may be individual lines of a multi-line call
            if isinstance(item, str):
                raw = item.strip()
                if raw.upper() == "THEN":
                    # Spurious token preserved in analysis; skip it
                    continue
                pending_call.append(raw)
                # Heuristic: if this line closes a call with ')' (and not a comma), flush
                if raw.endswith(")"):
                    flush_pending()
                continue

            # Structured node; flush any pending raw prior to it
            flush_pending()

            if not isinstance(item, dict):
                continue
            node_type = item.get("type")
            debug(f"Render node type: {node_type}")
            if node_type == "assignment_statements":
                var = item.get("variable")
                val = item.get("value")
                if var is not None and val is not None:
                    lines.append(self._indent(f"{var} := {val};", indent_level))
            elif node_type in {"select_statements", "update_statements", "insert_statements", "delete_statements", "RAISE_statements"}:
                sql = item.get("sql")
                if sql:
                    sql_text = sql.strip()
                    if not sql_text.endswith(";"):
                        sql_text += ";"
                    lines.append(self._indent(sql_text, indent_level))
            elif node_type in {"function calling", "function_calling"}:
                # Render function calling shape (primarily raise_application_error)
                func = (item.get("function_name") or "").strip()
                if func.lower() == "raise_application_error":
                    param = item.get("parameter", {}) or {}
                    code = str(param.get("handler_code", ""))
                    msg = self._plsql_string_literal(str(param.get("handler_string", "")))
                    lines.append(self._indent(f"RAISE_APPLICATION_ERROR({code}, {msg});", indent_level))
                else:
                    sql = item.get("sql")
                    if sql:
                        sql_text = sql.strip()
                        if not sql_text.endswith(";"):
                            sql_text += ";"
                        lines.append(self._indent(sql_text, indent_level))
            elif node_type == "if_else":
                lines.extend(self._render_if_else(item, indent_level))
            elif node_type == "begin_block":
                # Nested BEGIN block
                lines.append(self._indent("BEGIN", indent_level))
                inner_sqls = item.get("sqls", []) or []
                debug(f"Nested begin block with {len(inner_sqls)} statements")
                lines.extend(self._render_sql_list(inner_sqls, indent_level + 1))
                handlers = item.get("exception_handlers", []) or []
                if handlers:
                    lines.append(self._indent("EXCEPTION", indent_level + 1))
                    for h in handlers:
                        debug(f"Nested handler for: {h.get('exception_name')}")
                        lines.extend(self._render_exception_handler(h, indent_level + 2))
                lines.append(self._indent("END;", indent_level))
            elif "exception_name" in item and isinstance(item.get("sqls"), list):
                # Exception action wrapper in main flow; render its inner sqls
                inner_actions = item.get("sqls", [])
                # Reuse handler rendering for actions, but without WHEN header: we just emit actions
                for act in inner_actions:
                    a_type = (act.get("type") or "").strip()
                    debug(f"Inline exception action type: {a_type}")
                    if a_type in {"function calling", "function_calling"}:
                        func = (act.get("function_name") or "").strip()
                        if func.lower() == "raise_application_error":
                            param = act.get("parameter", {}) or {}
                            code = str(param.get("handler_code", ""))
                            msg = self._plsql_string_literal(str(param.get("handler_string", "")))
                            lines.append(self._indent(f"RAISE_APPLICATION_ERROR({code}, {msg});", indent_level))
                        else:
                            sql = act.get("sql")
                            if sql:
                                sql_text = sql.strip()
                                if not sql_text.endswith(";"):
                                    sql_text += ";"
                                lines.append(self._indent(sql_text, indent_level))
                    elif a_type == "RAISE_statements":
                        sql = act.get("sql")
                        if sql:
                            sql_text = sql.strip()
                            if not sql_text.endswith(";"):
                                sql_text += ";"
                            lines.append(self._indent(sql_text, indent_level))
                    else:
                        sql = act.get("sql")
                        if sql:
                            sql_text = sql.strip()
                            if not sql_text.endswith(";"):
                                sql_text += ";"
                            lines.append(self._indent(sql_text, indent_level))
            elif node_type == "case_when_statements":
                lines.extend(self._render_case_when(item, indent_level))
            elif node_type == "for_loop":
                loop_var = item.get("loop_variable") or "i"
                cursor_query = item.get("cursor_query") or "SELECT 1 FROM DUAL"
                debug(f"FOR loop: var={loop_var}, cursor_query_len={len(cursor_query)}")
                lines.append(self._indent(f"FOR {loop_var} IN ( {cursor_query} ) LOOP", indent_level))
                loop_body = item.get("loop_body", []) or []
                lines.extend(self._render_sql_list(loop_body, indent_level + 1))
                lines.append(self._indent("END LOOP;", indent_level))
            else:
                # Unknown node type: try to render any embedded SQL
                sql = item.get("sql")
                if sql:
                    sql_text = sql.strip()
                    if not sql_text.endswith(";"):
                        sql_text += ";"
                    lines.append(self._indent(sql_text, indent_level))

        # Flush pending raw at the end
        flush_pending()
        return lines

    def _render_if_else(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        lines: List[str] = []
        condition = node.get("condition", "1=1")
        debug(f"IF condition: {condition}")
        lines.append(self._indent(f"IF {condition} THEN", indent_level))
        then_sql = node.get("then_sql", []) or []
        lines.extend(self._render_sql_list(then_sql, indent_level + 1))

        # Chain of elsif
        current = node
        while current.get("else_if_statement"):
            current = current.get("else_if_statement")
            cond = current.get("condition", "1=1")
            debug(f"ELSIF condition: {cond}")
            lines.append(self._indent(f"ELSIF {cond} THEN", indent_level))
            then_part = current.get("then_sql", []) or []
            lines.extend(self._render_sql_list(then_part, indent_level + 1))

        # Else part
        else_stmt = current.get("else_statement")
        if else_stmt is not None:
            debug("ELSE branch present")
            lines.append(self._indent("ELSE", indent_level))
            else_list: List[JsonNode] = else_stmt if isinstance(else_stmt, list) else [else_stmt]  # type: ignore
            lines.extend(self._render_sql_list(else_list, indent_level + 1))

        lines.append(self._indent("END IF;", indent_level))
        return lines

    def _render_case_when(self, node: Dict[str, Any], indent_level: int) -> List[str]:
        lines: List[str] = []
        case_expr = node.get("case_expression")
        when_clauses: List[Dict[str, Any]] = node.get("when_clauses", []) or []
        searched_case = not case_expr or str(case_expr).strip() == ""
        debug(f"CASE statement: searched={searched_case}, when_count={len(when_clauses)}")

        if searched_case:
            lines.append(self._indent("CASE", indent_level))
            for clause in when_clauses:
                when_val = clause.get("when_value")
                lines.append(self._indent(f"WHEN {when_val} THEN", indent_level + 1))
                then_stmt = clause.get("then_statement", []) or []
                lines.extend(self._render_sql_list(then_stmt, indent_level + 2))
                else_stmt = clause.get("else_statement")
                if else_stmt is not None:
                    debug("CASE WHEN has ELSE branch")
                    lines.append(self._indent("ELSE", indent_level + 1))
                    else_list: List[JsonNode] = else_stmt if isinstance(else_stmt, list) else [else_stmt]  # type: ignore
                    lines.extend(self._render_sql_list(else_list, indent_level + 2))
            lines.append(self._indent("END CASE;", indent_level))
        else:
            lines.append(self._indent(f"CASE {case_expr}", indent_level))
            for clause in when_clauses:
                when_val = clause.get("when_value")
                lines.append(self._indent(f"WHEN {when_val} THEN", indent_level + 1))
                then_stmt = clause.get("then_statement", []) or []
                lines.extend(self._render_sql_list(then_stmt, indent_level + 2))
                else_stmt = clause.get("else_statement")
                if else_stmt is not None:
                    debug("CASE (simple) WHEN has ELSE branch")
                    lines.append(self._indent("ELSE", indent_level + 1))
                    else_list: List[JsonNode] = else_stmt if isinstance(else_stmt, list) else [else_stmt]  # type: ignore
                    lines.extend(self._render_sql_list(else_list, indent_level + 2))
            lines.append(self._indent("END CASE;", indent_level))
        return lines

    # -----------------------------
    # Utilities
    # -----------------------------
    def _indent(self, text: str, level: int) -> str:
        return f"{self.indent_unit * max(level, 0)}{text}"

    def _indent_lines(self, lines: List[str], level: int) -> List[str]:
        return [self._indent(line, level) for line in lines]

    def _plsql_string_literal(self, s: str) -> str:
        # Escape single quotes for PL/SQL string literals
        return "'" + s.replace("'", "''") + "'"
