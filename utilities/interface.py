#!/usr/bin/env python3
"""
User Interface for Oracle to PostgreSQL Trigger Converter

This module provides both interactive menu-driven interface and command-line
interface for the converter. It handles user input, command-line argument
parsing, and provides a user-friendly experience.
"""

import sys
import argparse
from .config import Config
from .converter import OracleToPostgreSQLConverter


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
    print("4. ❓ Show help")
    print("5. 🚪 Exit")
    
    # Input validation loop - keep asking until valid choice
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice  # Valid choice, return it
            print("❌ Invalid choice. Please enter 1-5.")
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
    print("\n📁 Input/Output:")
    print("  • Input: Oracle PL/SQL trigger files (.sql)")
    print("  • Output: PostgreSQL triggers in JSON format (.json)")
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
        # OPTION 4: Show help information
        # -------------------------------------------------------------------------
        elif choice == '4':
            show_help()
            try:
                input("\nPress Enter to continue...")
            except (EOFError, KeyboardInterrupt):
                pass
            continue  # Return to menu
            
        # -------------------------------------------------------------------------
        # OPTION 5: Exit application
        # -------------------------------------------------------------------------
        elif choice == '5':
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