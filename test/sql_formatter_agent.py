
import re
import sqlparse
from sqlparse import format as sql_format
import os
from datetime import datetime

class SQLCodeFormatterAgent:
    """
    AI Agent for SQL Code Formatting, Validation, and Comment Removal

    This agent provides comprehensive SQL code processing capabilities:
    - Formats SQL code with proper indentation and universal formatting rules
    - Removes all types of comments (single-line and multi-line)
    - Validates syntax and identifies potential errors
    - Generates detailed reports and saves cleaned files
    """

    def __init__(self, indent_width=4, keyword_case='upper'):
        """
        Initialize the SQL Code Formatter Agent

        Args:
            indent_width (int): Number of spaces for indentation (default: 4)
            keyword_case (str): Case for SQL keywords - 'upper' or 'lower' (default: 'upper')
        """
        self.indent_width = indent_width
        self.keyword_case = keyword_case
        self.validation_errors = []
        self.processing_stats = {
            'files_processed': 0,
            'total_size_reduction': 0,
            'total_comments_removed': 0,
            'total_errors_found': 0
        }

    def remove_comments(self, sql_code):
        """
        Remove all SQL comments from the code

        Args:
            sql_code (str): Original SQL code with comments

        Returns:
            str: SQL code with comments removed
        """
        original_length = len(sql_code)

        # Remove single line comments (-- comment)
        sql_code = re.sub(r'--.*$', '', sql_code, flags=re.MULTILINE)

        # Remove multi-line comments (/* comment */)
        sql_code = re.sub(r'/\*.*?\*/', '', sql_code, flags=re.DOTALL)

        # Remove empty lines that were left after comment removal
        lines = sql_code.split('\n')
        non_empty_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                non_empty_lines.append(line)

        cleaned_code = '\n'.join(non_empty_lines)
        comments_removed = original_length - len(cleaned_code)

        return cleaned_code, comments_removed

    def format_sql_code(self, sql_code):
        """
        Format SQL code with universal formatting rules

        Args:
            sql_code (str): SQL code to format

        Returns:
            str: Formatted SQL code
        """
        try:
            # Use sqlparse to format the SQL with universal rules
            formatted = sql_format(
                sql_code,
                reindent=True,
                keyword_case=self.keyword_case,
                identifier_case='lower',
                strip_comments=False,
                indent_width=self.indent_width,
                indent_tabs=False,
                comma_first=False,
                truncate_strings=500
            )

            # Additional formatting for PL/SQL specific constructs
            formatted = self._format_plsql_constructs(formatted)

            return formatted
        except Exception as e:
            self.validation_errors.append(f"Formatting error: {str(e)}")
            return sql_code

    def _format_plsql_constructs(self, sql_code):
        """
        Apply additional formatting rules for PL/SQL constructs

        Args:
            sql_code (str): SQL code to enhance formatting

        Returns:
            str: Enhanced formatted SQL code
        """
        # Ensure proper spacing around operators
        sql_code = re.sub(r'(\w)([<>=!]+)(\w)', r'\1 \2 \3', sql_code)

        # Ensure proper spacing after commas
        sql_code = re.sub(r',(\S)', r', \1', sql_code)

        # Ensure proper spacing around := operator
        sql_code = re.sub(r'(\w)(:=)(\w)', r'\1 \2 \3', sql_code)

        return sql_code

    def validate_sql_syntax(self, sql_code):
        """
        Perform comprehensive SQL syntax validation

        Args:
            sql_code (str): SQL code to validate

        Returns:
            list: List of validation errors found
        """
        errors = []

        # Check for basic PL/SQL structure
        if not re.search(r'\bdeclare\b|\bbegin\b', sql_code, re.IGNORECASE):
            errors.append("Missing DECLARE or BEGIN block")

        # Check for unmatched parentheses
        open_parens = sql_code.count('(')
        close_parens = sql_code.count(')')
        if open_parens != close_parens:
            errors.append(f"Unmatched parentheses: {open_parens} opening, {close_parens} closing")

        # Check for missing semicolons in key statements
        lines = sql_code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip().lower()
            if stripped:
                # Check for statements that should end with semicolon
                sql_statements = ['update', 'insert', 'delete', 'select', 'create', 'drop', 'alter']
                if any(stripped.startswith(keyword) for keyword in sql_statements):
                    if not stripped.endswith(';') and not any(stripped.endswith(word) for word in ['then', 'loop', 'begin']):
                        # Look ahead to see if the statement continues on next line
                        continue_keywords = ['where', 'and', 'or', 'set', 'values', 'from', 'into', 'order', 'group', 'having']
                        next_line_continues = False
                        if i < len(lines):
                            next_stripped = lines[i].strip().lower() if i < len(lines) else ""
                            if any(next_stripped.startswith(kw) for kw in continue_keywords):
                                next_line_continues = True

                        if not next_line_continues:
                            errors.append(f"Line {i}: Possible missing semicolon after SQL statement")

        # Check for IF-THEN-END IF matching
        if_count = len(re.findall(r'\bif\b', sql_code, re.IGNORECASE))
        then_count = len(re.findall(r'\bthen\b', sql_code, re.IGNORECASE))
        endif_count = len(re.findall(r'\bend\s+if\b', sql_code, re.IGNORECASE))

        if if_count != then_count:
            errors.append(f"Mismatched IF-THEN statements: {if_count} IF, {then_count} THEN")

        if if_count != endif_count:
            errors.append(f"Mismatched IF-END IF statements: {if_count} IF, {endif_count} END IF")

        # Check for LOOP-END LOOP matching
        loop_count = len(re.findall(r'\bloop\b', sql_code, re.IGNORECASE))
        endloop_count = len(re.findall(r'\bend\s+loop\b', sql_code, re.IGNORECASE))

        if loop_count != endloop_count:
            errors.append(f"Mismatched LOOP-END LOOP statements: {loop_count} LOOP, {endloop_count} END LOOP")

        # Check for BEGIN-END matching
        begin_count = len(re.findall(r'\bbegin\b', sql_code, re.IGNORECASE))
        end_count = len(re.findall(r'\bend\s*;', sql_code, re.IGNORECASE))

        if begin_count != end_count:
            errors.append(f"Mismatched BEGIN-END blocks: {begin_count} BEGIN, {end_count} END")

        # Check for common PL/SQL issues
        self._check_common_plsql_issues(sql_code, errors)

        return errors

    def _check_common_plsql_issues(self, sql_code, errors):
        """
        Check for common PL/SQL specific issues

        Args:
            sql_code (str): SQL code to check
            errors (list): List to append errors to
        """
        # Check for exception handling
        if 'exception' in sql_code.lower() and 'when others then' not in sql_code.lower():
            errors.append("Exception block found but no WHEN OTHERS clause detected")

        # Check for cursor declarations without proper handling
        cursor_declares = len(re.findall(r'cursor\s+\w+\s+is', sql_code, re.IGNORECASE))
        cursor_opens = len(re.findall(r'open\s+\w+', sql_code, re.IGNORECASE))
        cursor_closes = len(re.findall(r'close\s+\w+', sql_code, re.IGNORECASE))

        if cursor_declares > 0 and (cursor_opens != cursor_declares or cursor_closes != cursor_declares):
            errors.append(f"Cursor handling issue: {cursor_declares} declared, {cursor_opens} opened, {cursor_closes} closed")

    def process_file(self, content, filename):
        """
        Process a single SQL file with comprehensive formatting and validation

        Args:
            content (str): File content to process
            filename (str): Name of the file being processed

        Returns:
            dict: Processing results and statistics
        """
        print(f"\n{'='*60}")
        print(f"🔄 Processing: {filename}")
        print(f"{'='*60}")

        original_length = len(content)

        # Step 1: Remove comments
        print("🧹 Step 1: Removing comments...")
        content_no_comments, comments_removed = self.remove_comments(content)
        print(f"   ✅ Removed {comments_removed:,} characters of comments")

        # Step 2: Format code
        print("✨ Step 2: Applying universal formatting rules...")
        formatted_content = self.format_sql_code(content_no_comments)
        print(f"   ✅ Applied {self.keyword_case} case keywords and {self.indent_width}-space indentation")

        # Step 3: Validate syntax
        print("🔍 Step 3: Performing syntax validation...")
        validation_errors = self.validate_sql_syntax(formatted_content)
        print(f"   ✅ Completed validation check")

        # Display results
        formatted_length = len(formatted_content)
        size_reduction = original_length - formatted_length
        reduction_pct = (size_reduction / original_length) * 100 if original_length > 0 else 0

        print(f"\n📊 Processing Results for {filename}:")
        print(f"   📏 Original size: {original_length:,} characters")
        print(f"   📏 Processed size: {formatted_length:,} characters")
        print(f"   💾 Size reduction: {size_reduction:,} characters ({reduction_pct:.1f}%)")
        print(f"   🧹 Comments removed: {comments_removed:,} characters")

        print(f"\n🔍 Validation Results:")
        if validation_errors:
            print(f"   ❌ {len(validation_errors)} issues found:")
            for i, error in enumerate(validation_errors, 1):
                print(f"      {i}. {error}")
        else:
            print("   ✅ No major syntax errors detected")

        # Save formatted file
        output_filename = f"formatted_{filename}"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            print(f"\n💾 Formatted code saved to: {output_filename}")
        except Exception as e:
            print(f"\n❌ Error saving file: {str(e)}")

        # Update statistics
        self.processing_stats['files_processed'] += 1
        self.processing_stats['total_size_reduction'] += size_reduction
        self.processing_stats['total_comments_removed'] += comments_removed
        self.processing_stats['total_errors_found'] += len(validation_errors)

        return {
            'filename': filename,
            'original_length': original_length,
            'formatted_length': formatted_length,
            'size_reduction': size_reduction,
            'reduction_percentage': reduction_pct,
            'comments_removed': comments_removed,
            'errors': validation_errors,
            'success': True
        }

    def process_multiple_files(self, file_paths):
        """
        Process multiple SQL files

        Args:
            file_paths (list): List of file paths to process

        Returns:
            list: List of processing results for each file
        """
        results = []

        print("🤖 SQL Code Formatter and Validator Agent")
        print("=" * 50)
        print("Features:")
        print("✅ Universal SQL formatting rules")
        print("✅ Complete comment removal")
        print("✅ Comprehensive syntax validation")
        print("✅ Detailed error reporting")
        print("✅ Processing statistics")

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                filename = os.path.basename(file_path)
                result = self.process_file(content, filename)
                results.append(result)

            except Exception as e:
                print(f"\n❌ Error processing {file_path}: {str(e)}")
                results.append({
                    'filename': os.path.basename(file_path),
                    'error': str(e),
                    'success': False
                })

        self._generate_summary_report(results)
        return results

    def _generate_summary_report(self, results):
        """
        Generate a comprehensive summary report

        Args:
            results (list): List of processing results
        """
        successful_results = [r for r in results if r.get('success', False)]

        print(f"\n📈 COMPREHENSIVE PROCESSING SUMMARY")
        print("=" * 60)

        if successful_results:
            total_original = sum(r['original_length'] for r in successful_results)
            total_formatted = sum(r['formatted_length'] for r in successful_results)
            total_reduction = sum(r['size_reduction'] for r in successful_results)
            total_comments = sum(r['comments_removed'] for r in successful_results)
            total_errors = sum(len(r['errors']) for r in successful_results)

            print(f"📁 Files Successfully Processed: {len(successful_results)}")
            print(f"📏 Total Original Size: {total_original:,} characters")
            print(f"📏 Total Processed Size: {total_formatted:,} characters")
            print(f"💾 Total Size Reduction: {total_reduction:,} characters ({(total_reduction/total_original)*100:.1f}%)")
            print(f"🧹 Total Comments Removed: {total_comments:,} characters")
            print(f"⚠️  Total Issues Found: {total_errors}")

            print(f"\n📋 File-by-File Summary:")
            print("-" * 40)
            for result in successful_results:
                print(f"\n📄 {result['filename']}:")
                print(f"   Size: {result['original_length']:,} → {result['formatted_length']:,} ({result['reduction_percentage']:.1f}% reduction)")
                print(f"   Comments: {result['comments_removed']:,} characters removed")
                print(f"   Issues: {len(result['errors'])} found")

            # Error analysis
            print(f"\n⚠️  DETAILED ERROR ANALYSIS:")
            print("-" * 35)
            for result in successful_results:
                if result['errors']:
                    print(f"\n🔴 {result['filename']} - {len(result['errors'])} issues:")
                    for i, error in enumerate(result['errors'], 1):
                        print(f"   {i}. {error}")

        # Process failed files
        failed_results = [r for r in results if not r.get('success', False)]
        if failed_results:
            print(f"\n❌ FAILED PROCESSING:")
            print("-" * 25)
            for result in failed_results:
                print(f"🔴 {result['filename']}: {result.get('error', 'Unknown error')}")

        print(f"\n🎯 RECOMMENDATIONS:")
        print("-" * 20)
        print("1. Review IF-THEN-END IF block matching")
        print("2. Check LOOP-END LOOP statement pairing")
        print("3. Verify semicolon placement for SQL statements")
        print("4. Consider manual review of complex nested structures")
        print("5. Test formatted code before deployment")

        print(f"\n✅ Processing Complete!")
        print(f"📁 Check your directory for formatted_*.sql files")
        print(f"🕒 Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Example usage:
if __name__ == "__main__":
    # Initialize the agent
    agent = SQLCodeFormatterAgent(indent_width=4, keyword_case='upper')

    # Process files (example)
    # file_paths = ['trigger1.sql', 'trigger2.sql', 'trigger3.sql']
    # results = agent.process_multiple_files(file_paths)

    print("SQL Code Formatter Agent is ready!")
    print("Use agent.process_multiple_files(['file1.sql', 'file2.sql']) to process files")
