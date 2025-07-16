#!/usr/bin/env python3
"""
Oracle to PostgreSQL Trigger Converter - Main Entry Point
Optimized modular version with improved structure, performance, and maintainability

=== MODULAR ARCHITECTURE ===
The converter has been broken down into focused, single-responsibility modules:

📂 config.py            - Configuration, constants, and data classes
🗂️ mapping_manager.py   - Oracle to PostgreSQL mappings (Excel & fallback)
🔄 regex_processor.py   - SQL transformation engine with regex patterns
🔍 trigger_parser.py    - Oracle trigger section and variable extraction
📝 postgresql_formatter.py - PostgreSQL DO block formatting
🎯 converter.py         - Main orchestrator class
🖥️ interface.py         - Interactive menu and CLI interface
🚀 main.py             - Entry point (this file)

=== CONVERSION PROCESS ===
Oracle SQL → Parse Sections → Extract Variables → Transform → Format → JSON Output

=== USAGE ===
Interactive Mode: python main.py
CLI Mode:        python main.py trigger1.sql -o output.json -v
Batch Mode:      python main.py orcale --folder -o json
"""

from utilities.interface import main

if __name__ == "__main__":
    """
    Entry point when script is run directly (not imported as module)
    
    This standard Python idiom ensures that main() only runs when the script
    is executed directly, not when it's imported by another script.
    """
    main() 