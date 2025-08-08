#!/usr/bin/env python3
"""
User Interface for Oracle to PostgreSQL Trigger Converter

This module provides both interactive menu-driven interface and command-line
interface for the converter. It handles user input, command-line argument
parsing, and provides a user-friendly experience.
"""

import sys
import argparse
import os
import glob
from datetime import datetime
from .config import Config
from .converter import OracleToPostgreSQLConverter
from .sql_formatter_agent import SQLCodeFormatterAgent


def format_oracle_files(oracle_folder: str, format_folder: str, verbose: bool = False):
    """
    Format Oracle SQL files from oracle folder to format_oracle folder
    
    Args:
        oracle_folder (str): Source folder containing Oracle SQL files
        format_folder (str): Destination folder for formatted files
        verbose (bool): Enable verbose output and save detailed report
    """
    try:
        # Create output directories if they don't exist
        os.makedirs(format_folder, exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
        # Find all SQL files in the oracle folder
        sql_files = glob.glob(os.path.join(oracle_folder, "*.sql"))
        
        if not sql_files:
            print(f"❌ No SQL files found in {oracle_folder}")
            return
            
        print(f"📁 Found {len(sql_files)} SQL files to format:")
        for file in sql_files:
            print(f"   • {os.path.basename(file)}")
        
        # Initialize the SQL formatter agent
        formatter = SQLCodeFormatterAgent(indent_width=4, keyword_case='upper')
        
        # Process each file and collect results
        formatted_files = []
        processing_results = []
        start_time = datetime.now()
        
        for sql_file in sql_files:
            try:
                # Read the original file
                with open(sql_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Format the content
                filename = os.path.basename(sql_file)
                result = formatter.process_file(content, filename)
                
                if result.get('success', False):
                    # The formatter already saves the file, we need to move it to our target folder
                    source_file = f"formatted_{filename}"
                    output_file = os.path.join(format_folder, f"formatted_{filename}")
                    
                    # Move the file from current directory to target folder
                    if os.path.exists(source_file):
                        try:
                            # Read the content and write to target location
                            with open(source_file, 'r', encoding='utf-8') as f:
                                formatted_content = f.read()
                            with open(output_file, 'w', encoding='utf-8') as f:
                                f.write(formatted_content)
                            # Remove the temporary file
                            os.remove(source_file)
                            formatted_files.append(output_file)
                            
                            # Store result for report
                            result['input_file'] = sql_file
                            result['output_file'] = output_file
                            processing_results.append(result)
                            
                        except Exception as e:
                            print(f"❌ Error moving formatted file for {filename}: {str(e)}")
                    else:
                        print(f"❌ Formatted file not found for {filename}")
                    
                    if verbose:
                        print(f"✅ Formatted: {filename} → formatted_{filename}")
                        print(f"   Size: {result['original_length']:,} → {result['formatted_length']:,} characters")
                        print(f"   Reduction: {result['reduction_percentage']:.1f}%")
                        if result.get('errors'):
                            print(f"   Issues found: {len(result['errors'])}")
                else:
                    print(f"❌ Failed to format {filename}: {result.get('error', 'Unknown error')}")
                    # Store failed result
                    failed_result = {'input_file': sql_file, 'filename': filename, 'success': False, 'error': result.get('error', 'Unknown error')}
                    processing_results.append(failed_result)
                    
            except Exception as e:
                print(f"❌ Error processing {sql_file}: {str(e)}")
                # Store error result
                error_result = {'input_file': sql_file, 'filename': os.path.basename(sql_file), 'success': False, 'error': str(e)}
                processing_results.append(error_result)
        
        end_time = datetime.now()
        processing_duration = end_time - start_time
        
        # Generate and save report if verbose mode is enabled
        if verbose and processing_results:
            report_path = generate_formatting_report(processing_results, oracle_folder, format_folder, start_time, end_time, processing_duration)
            print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Summary
        print(f"\n🎨 Formatting completed!")
        print(f"✅ Successfully formatted: {len(formatted_files)} files")
        print(f"📁 Output directory: {format_folder}")
        
        if formatted_files:
            print(f"\n📋 Formatted files:")
            for file in formatted_files:
                print(f"   • {os.path.basename(file)}")
                
    except Exception as e:
        print(f"❌ Error during formatting: {str(e)}")


def generate_formatting_report(results, oracle_folder, format_folder, start_time, end_time, duration):
    """
    Generate a detailed formatting report and save it to output directory
    
    Args:
        results (list): List of processing results for each file
        oracle_folder (str): Source folder path
        format_folder (str): Destination folder path
        start_time (datetime): Processing start time
        end_time (datetime): Processing end time
        duration (timedelta): Total processing duration
    
    Returns:
        str: Path to the generated report file
    """
    # Generate report filename with timestamp
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")
    report_filename = f"oracle_formatting_report_{timestamp}.txt"
    report_path = os.path.join("output", report_filename)
    
    successful_results = [r for r in results if r.get('success', False)]
    failed_results = [r for r in results if not r.get('success', False)]
    
    # Calculate statistics
    total_files = len(results)
    successful_files = len(successful_results)
    failed_files = len(failed_results)
    
    if successful_results:
        total_original_size = sum(r.get('original_length', 0) for r in successful_results)
        total_formatted_size = sum(r.get('formatted_length', 0) for r in successful_results)
        total_size_reduction = sum(r.get('size_reduction', 0) for r in successful_results)
        total_comments_removed = sum(r.get('comments_removed', 0) for r in successful_results)
        total_errors_found = sum(len(r.get('errors', [])) for r in successful_results)
        avg_reduction_pct = (total_size_reduction / total_original_size * 100) if total_original_size > 0 else 0
    else:
        total_original_size = total_formatted_size = total_size_reduction = total_comments_removed = total_errors_found = avg_reduction_pct = 0
    
    # Generate report content
    report_content = f"""
============================================================
📄 ORACLE SQL FORMATTING REPORT
============================================================

📅 Generated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
⏱️  Processing Duration: {duration.total_seconds():.2f} seconds

============================================================
📂 DIRECTORIES
============================================================
📁 Source Folder: {oracle_folder}
📁 Output Folder: {format_folder}
📁 Report Location: output/

============================================================
📊 SUMMARY STATISTICS
============================================================
📄 Total Files Processed: {total_files}
✅ Successfully Formatted: {successful_files}
❌ Failed to Format: {failed_files}
⏱️  Average Processing Time: {(duration.total_seconds() / total_files):.2f} seconds per file

============================================================
📏 SIZE ANALYSIS
============================================================
📏 Total Original Size: {total_original_size:,} characters
📏 Total Formatted Size: {total_formatted_size:,} characters
💾 Total Size Reduction: {total_size_reduction:,} characters
📊 Average Size Reduction: {avg_reduction_pct:.1f}%
🧹 Total Comments Removed: {total_comments_removed:,} characters

============================================================
🔍 VALIDATION SUMMARY
============================================================
⚠️  Total Issues Found: {total_errors_found}
📊 Average Issues per File: {(total_errors_found / successful_files):.1f} (for successful files)

============================================================
📋 DETAILED FILE RESULTS
============================================================
"""

    # Add detailed results for each file
    for i, result in enumerate(results, 1):
        filename = result.get('filename', 'Unknown')
        report_content += f"\n{i}. FILE: {filename}\n"
        report_content += f"   {'='*50}\n"
        
        if result.get('success', False):
            report_content += f"   ✅ Status: Successfully formatted\n"
            report_content += f"   📁 Input: {result.get('input_file', 'N/A')}\n"
            report_content += f"   📁 Output: {result.get('output_file', 'N/A')}\n"
            report_content += f"   📏 Original Size: {result.get('original_length', 0):,} characters\n"
            report_content += f"   📏 Formatted Size: {result.get('formatted_length', 0):,} characters\n"
            report_content += f"   💾 Size Reduction: {result.get('size_reduction', 0):,} characters ({result.get('reduction_percentage', 0):.1f}%)\n"
            report_content += f"   🧹 Comments Removed: {result.get('comments_removed', 0):,} characters\n"
            
            errors = result.get('errors', [])
            report_content += f"   ⚠️  Issues Found: {len(errors)}\n"
            if errors:
                report_content += f"   📝 Issue Details:\n"
                for j, error in enumerate(errors, 1):
                    report_content += f"      {j}. {error}\n"
        else:
            report_content += f"   ❌ Status: Failed to format\n"
            report_content += f"   📁 Input: {result.get('input_file', 'N/A')}\n"
            report_content += f"   🔴 Error: {result.get('error', 'Unknown error')}\n"

    # Add recommendations section
    report_content += f"""
============================================================
🎯 RECOMMENDATIONS
============================================================
1. Review IF-THEN-END IF block matching issues
2. Check LOOP-END LOOP statement pairing
3. Verify semicolon placement for SQL statements
4. Consider manual review of complex nested structures
5. Test formatted code before deployment
6. Address any failed formatting attempts

============================================================
📊 FORMATTING FEATURES APPLIED
============================================================
✅ Comment removal and code cleaning
✅ Keyword standardization (UPPERCASE)
✅ Consistent indentation (4 spaces)
✅ Syntax validation and error reporting
✅ Comprehensive processing statistics

============================================================
🏁 REPORT END
============================================================
Generated by Oracle to PostgreSQL Trigger Converter (Optimized)
Report saved at: {report_path}
"""

    # Write report to file
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        return report_path
    except Exception as e:
        print(f"❌ Error saving report: {str(e)}")
        return None


def show_interactive_menu():
    """
    Display interactive menu and get user choice
    
    This function provides a user-friendly menu system for the converter.
    It handles input validation and provides clear options for different
    conversion scenarios.
    
    Returns:
        String representing the user's menu choice ('1', '2', '3', '4', or '5')
    """
    # Display the main menu header with clear branding
    print("\n" + "="*60)
    print("🚀 Oracle to PostgreSQL Trigger Converter (Optimized)")
    print("="*60)
    
    # Show all available options with clear descriptions
    print("\n1. 📁 Convert entire folder (default: orcale → json)")
    print("2. 📁 Convert folder with custom names")
    print("3. 📄 Convert single file")
    print("4. 🎨 Format Oracle SQL files (oracle → format_oracle)")
    print("5. ❓ Show help")
    print("6. 🚪 Exit")
    
    # Input validation loop - keep asking until valid choice
    while True:
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6']:
                return choice  # Valid choice, return it
            print("❌ Invalid choice. Please enter 1-6.")
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n👋 Goodbye!")
            sys.exit(0)


def show_help():
    """
    Display comprehensive help information about the converter
    """
    print("\n📖 Help - Oracle to PostgreSQL Trigger Converter")
    print("="*60)
    print("This optimized tool converts Oracle PL/SQL triggers to PostgreSQL format.")
    print("\n🔄 Conversion Features:")
    print("  • Data type mappings (VARCHAR2 → VARCHAR, NUMBER → NUMERIC, etc.)")
    print("  • Function mappings (SUBSTR → SUBSTRING, NVL → COALESCE, etc.)")
    print("  • Exception handling conversion")
    print("  • Variable reference conversion (:new.field → :new_field)")
    print("  • Package function calls (pkg.func → pkg$func)")
    print("  • Wraps output in PostgreSQL DO blocks")
    print("\n🎨 Formatting Features:")
    print("  • SQL code formatting with proper indentation")
    print("  • Comment removal and code cleaning")
    print("  • Syntax validation and error reporting")
    print("  • Processing statistics and detailed reports")
    print("\n📁 Input/Output:")
    print("  • Conversion: Oracle PL/SQL trigger files (.sql) → PostgreSQL JSON (.json)")
    print("  • Formatting: Oracle SQL files (.sql) → Formatted SQL files (.sql)")
    print("\n⚙️  Configuration:")
    print(f"  • Mappings loaded from {Config.DEFAULT_EXCEL_FILE}")
    print("  • Falls back to built-in mappings if Excel unavailable")


def run_interactive_mode():
    """
    Run the converter in interactive mode with menu system
    """
    # Initialize the converter once for the interactive session
    converter = OracleToPostgreSQLConverter()
    
    # Main interactive loop - keep showing menu until user exits
    while True:
        choice = show_interactive_menu()
        
        # -------------------------------------------------------------------------
        # OPTION 1: Convert entire folder with default settings
        # -------------------------------------------------------------------------
        if choice == '1':
            try:
                verbose = input("Verbose output? (y/n): ").strip().lower() == 'y'
                print(f"\n🔄 Converting {Config.DEFAULT_ORACLE_FOLDER} → {Config.DEFAULT_JSON_FOLDER}")
                converter.process_folder(Config.DEFAULT_ORACLE_FOLDER, Config.DEFAULT_JSON_FOLDER, verbose)
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  Operation cancelled by user")
                continue
            
        # -------------------------------------------------------------------------
        # OPTION 2: Convert folder with custom folder names
        # -------------------------------------------------------------------------
        elif choice == '2':
            try:
                oracle_folder = input(f"Oracle folder ({Config.DEFAULT_ORACLE_FOLDER}): ").strip() or Config.DEFAULT_ORACLE_FOLDER
                json_folder = input(f"JSON folder ({Config.DEFAULT_JSON_FOLDER}): ").strip() or Config.DEFAULT_JSON_FOLDER
                verbose = input("Verbose output? (y/n): ").strip().lower() == 'y'
                print(f"\n🔄 Converting {oracle_folder} → {json_folder}")
                converter.process_folder(oracle_folder, json_folder, verbose)
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  Operation cancelled by user")
                continue
            
        # -------------------------------------------------------------------------
        # OPTION 3: Convert single file
        # -------------------------------------------------------------------------
        elif choice == '3':
            try:
                input_file = input("Input Oracle SQL file: ").strip()
                if not input_file:
                    print("❌ Input file path cannot be empty")
                    continue
                    
                output_file = input("Output JSON file (optional): ").strip()
                if not output_file:
                    # Generate output filename automatically
                    output_file = input_file.replace('.sql', '.json')
                    
                verbose = input("Verbose output? (y/n): ").strip().lower() == 'y'
                
                print(f"\n🔄 Converting {input_file} → {output_file}")
                result = converter.convert_file(input_file, output_file, verbose)
                
                if result.success:
                    sections_info = f" ({len(result.sections_converted)} sections)" if result.sections_converted else ""
                    print(f"✅ Successfully converted: {result.input_file} → {result.output_file}{sections_info}")
                else:
                    print(f"❌ Conversion failed: {result.error_message}")
                    
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  Operation cancelled by user")
                continue
                
        # -------------------------------------------------------------------------
        # OPTION 4: Format Oracle SQL files
        # -------------------------------------------------------------------------
        elif choice == '4':
            try:
                oracle_folder = input(f"Oracle folder (files/oracle): ").strip() or "files/oracle"
                format_folder = input(f"Format output folder (files/format_oracle): ").strip() or "files/format_oracle"
                verbose = input("Verbose output? (y/n): ").strip().lower() == 'y'
                print(f"\n🎨 Formatting Oracle SQL files: {oracle_folder} → {format_folder}")
                format_oracle_files(oracle_folder, format_folder, verbose)
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  Operation cancelled by user")
                continue
        
        # -------------------------------------------------------------------------
        # OPTION 5: Show help information
        # -------------------------------------------------------------------------
        elif choice == '5':
            show_help()
            try:
                input("\nPress Enter to continue...")
            except (EOFError, KeyboardInterrupt):
                pass
            continue  # Return to menu
            
        # -------------------------------------------------------------------------
        # OPTION 6: Exit application
        # -------------------------------------------------------------------------
        elif choice == '6':
            print("\n👋 Goodbye!")
            break
        
        # Ask if user wants to perform another operation
        try:
            continue_choice = input("\nPerform another operation? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\n👋 Goodbye!")
                break
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break


def run_command_line_mode():
    """
    Run the converter in command-line mode with arguments
    """
    # Set up command line argument parser
    parser = argparse.ArgumentParser(
        description='Convert Oracle PL/SQL triggers to PostgreSQL format',
        epilog='Examples:\n'
               '  python main.py trigger1.sql                    # Convert single file\n'
               '  python main.py orcale --folder -o json -v      # Convert folder with verbose output\n'
               '  python main.py trigger1.sql -o output.json     # Convert with custom output name',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Define command line arguments
    parser.add_argument('input', help='Input Oracle SQL file or folder path')
    parser.add_argument('-o', '--output', help='Output JSON file or folder path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--folder', action='store_true', help='Force folder processing mode')
    
    # Parse the command line arguments
    args = parser.parse_args()
    
    # Initialize converter for command line mode
    converter = OracleToPostgreSQLConverter()
    
    # Determine processing mode: folder or single file
    import os
    if args.folder or os.path.isdir(args.input):
        # -------------------------------------------------------------------------
        # FOLDER PROCESSING MODE
        # -------------------------------------------------------------------------
        output_folder = args.output or Config.DEFAULT_JSON_FOLDER
        print(f"🔄 Processing folder: {args.input} → {output_folder}")
        
        results = converter.process_folder(args.input, output_folder, args.verbose)
        
        # Exit with error code if no files were successfully converted
        if not any(r.success for r in results):
            sys.exit(1)
            
    else:
        # -------------------------------------------------------------------------
        # SINGLE FILE PROCESSING MODE
        # -------------------------------------------------------------------------
        output_file = args.output or args.input.replace('.sql', '.json')
        print(f"🔄 Processing file: {args.input} → {output_file}")
        
        result = converter.convert_file(args.input, output_file, args.verbose)
        
        if result.success:
            print(f"✅ Conversion completed successfully")
        else:
            print(f"❌ Conversion failed: {result.error_message}")
            sys.exit(1)  # Exit with error code for failed conversion


def main():
    """
    Main entry point for the Oracle to PostgreSQL Trigger Converter
    
    This function determines whether to run in interactive mode (menu-driven)
    or command-line mode (with arguments) and handles the overall application flow.
    
    Modes:
    - Interactive Mode: No command line arguments - shows menu system
    - Command Line Mode: Arguments provided - direct execution
    """
    if len(sys.argv) == 1:
        # =============================================================================
        # INTERACTIVE MODE - MENU-DRIVEN INTERFACE
        # =============================================================================
        run_interactive_mode()
    else:
        # =============================================================================
        # COMMAND LINE MODE - DIRECT EXECUTION WITH ARGUMENTS
        # =============================================================================
        run_command_line_mode() 