# from utilities.sql_formatter_agent import SQLCodeFormatterAgent
# import os

# # Initialize agent with custom settings
# agent = SQLCodeFormatterAgent(indent_width=4, keyword_case='upper')

# # Define the Oracle SQL files to process
# oracle_files = [
#     'files/oracle/trigger1.sql',
#     'files/oracle/trigger2.sql', 
#     'files/oracle/trigger3.sql'
# ]

# # Verify files exist before processing
# existing_files = []
# for file_path in oracle_files:
#     if os.path.exists(file_path):
#         existing_files.append(file_path)
#         print(f"✅ Found: {file_path}")
#     else:
#         print(f"❌ Not found: {file_path}")

# if existing_files:
#     print(f"\n🚀 Processing {len(existing_files)} Oracle SQL files...")
#     # Process multiple files
#     results = agent.process_multiple_files(existing_files)
    
#     print(f"\n📊 Processing completed for {len(results)} files")
# else:
#     print("❌ No Oracle SQL files found to process!")

import re
import sqlparse
from typing import List, Dict, Tuple


class OracleTriggerProcessor:
    """
    AI agent to load, strip comments, format, and validate Oracle trigger SQL files.
    """

    def __init__(self, file_paths: List[str]) -> None:
        """
        Initialize the processor with a list of SQL file paths.
        """
        self.file_paths = file_paths
        self.raw_sql: Dict[str, str] = {}
        self.cleaned_sql: Dict[str, str] = {}
        self.formatted_sql: Dict[str, str] = {}
        self.validation_errors: Dict[str, List[str]] = {}

    def load_files(self) -> None:
        """
        Read all files into memory.
        """
        for path in self.file_paths:
            with open(path, 'r', encoding='utf-8') as f:
                self.raw_sql[path] = f.read()

    @staticmethod
    def strip_comments(sql: str) -> str:
        """
        Remove both single-line (`-- ...`) and block (`/* ... */`) comments.
        """
        without_block = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        without_line = re.sub(r'--.*', '', without_block)
        return without_line

    @staticmethod
    def basic_validate(sql: str) -> List[str]:
        """
        Perform basic syntactic checks:
          - Matching BEGIN / END;
          - Parentheses balance;
          - Quotation marks balance.
        """
        errors: List[str] = []

        # Check BEGIN/END; pairs
        begin_count = len(re.findall(r'\bBEGIN\b', sql, flags=re.IGNORECASE))
        end_count = len(re.findall(r'\bEND\s*;', sql, flags=re.IGNORECASE))
        if begin_count != end_count:
            errors.append(f"Mismatched BEGIN vs END; count: {begin_count} vs {end_count}")

        # Parentheses
        if sql.count('(') != sql.count(')'):
            errors.append(f"Unbalanced parentheses: {sql.count('(')} vs {sql.count(')')}")

        # Quotation marks (single and double)
        single_quotes = sql.count("'")
        if single_quotes % 2 != 0:
            errors.append("Unbalanced single quotes")
        double_quotes = sql.count('"')
        if double_quotes % 2 != 0:
            errors.append("Unbalanced double quotes")

        return errors

    @staticmethod
    def format_sql(sql: str) -> str:
        """
        Format SQL using sqlparse for consistent indentation and casing.
        """
        formatted = sqlparse.format(
            sql,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower',
            strip_comments=False
        )
        return formatted

    def process_all(self) -> None:
        """
        Execute the full pipeline on all files.
        """
        self.load_files()
        for path, content in self.raw_sql.items():
            # Strip comments
            cleaned = self.strip_comments(content)
            self.cleaned_sql[path] = cleaned

            # Validate
            errs = self.basic_validate(cleaned)
            self.validation_errors[path] = errs

            # Format
            self.formatted_sql[path] = self.format_sql(cleaned)

    def report(self) -> None:
        """
        Print a summary report of validation errors and show formatted SQL.
        """
        for path in self.file_paths:
            print(f"\n=== {path} ===")
            errs = self.validation_errors.get(path, [])
            if errs:
                print("Validation Errors:")
                for e in errs:
                    print(f"  - {e}")
            else:
                print("No validation errors found.")
            print("\nFormatted SQL Preview:")
            preview = "\n".join(self.formatted_sql[path].splitlines()[:20])
            print(preview + ("\n..." if len(self.formatted_sql[path].splitlines()) > 20 else ""))


if __name__ == '__main__':
    # Example usage: replace with your actual file paths
    files = [
        'files/oracle/trigger1.sql',
        'files/oracle/trigger2.sql', 
        'files/oracle/trigger3.sql'
    ]
    agent = OracleTriggerProcessor(files)
    agent.process_all()
    agent.report()
