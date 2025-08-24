
                    # elif item["type"] == "case_when":
                    #     if "when_clauses" in item:
                    #         for clause in item["when_clauses"]:
                    #             if (
                    #                 "when_value" in clause
                    #                 and "then_statements" in clause
                    #             ):
                    #                 parse_case_when(
                    #                     clause["then_statements"],
                    #                     f"{parent_context}.then_statements",
                    #                 )


                    #     # Process CASE statements in top-level else_statements
                    #     if "else_statements" in item:
                    #         parse_case_when(
                    #             item["else_statements"],
                    #             f"{parent_context}.else_statements",
                    #         )


                    # elif item["type"] == "if_else":
                    #     # Process CASE statements in then_statements, else_if, and else_statements
                    #     if "then_statements" in item:
                    #         parse_case_when(
                    #             item["then_statements"],
                    #             f"{parent_context}.then_statements",
                    #         )
                    #     if "else_if" in item:
                    #         for elsif_block in item["else_if"]:
                    #             if "then_statements" in elsif_block:
                    #                 parse_case_when(
                    #                     elsif_block["then_statements"],
                    #                     f"{parent_context}.else_if.then_statements",
                    #                 )
                    #     if "else_statements" in item:
                    #         parse_case_when(
                    #             item["else_statements"],
                    #             f"{parent_context}.else_statements",
                    #         )
                    # elif item["type"] == "for_loop":
                    #     # Process CASE statements in loop_statements
                    #     if "loop_statements" in item:
                    #         parse_case_when(
                    #             item["loop_statements"],
                    #             f"{parent_context}.loop_statements",
                    #         )