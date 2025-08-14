# Oracle to PostgreSQL Trigger Converter

A comprehensive tool for converting Oracle PL/SQL triggers to PostgreSQL-compatible SQL with advanced parsing, analysis, and transformation capabilities.

## 🎯 Overview

This project provides a complete solution for migrating Oracle database triggers to PostgreSQL. It features a multi-stage conversion process that:

1. **Parses** Oracle PL/SQL trigger code into structured JSON analysis
2. **Analyzes** the code structure, declarations, and logic flow
3. **Transforms** Oracle-specific syntax to PostgreSQL equivalents
4. **Generates** clean, formatted PostgreSQL SQL code
5. **Validates** the conversion process and results

## 🏗️ Architecture

The converter uses a modular architecture with specialized components:

```txt
Oracle SQL → JSON Analysis → PostgreSQL SQL
     ↓           ↓              ↓
OracleTriggerAnalyzer → FORMATPostsqlTriggerAnalyzer → Final SQL
```

### Core Components

- **`OracleTriggerAnalyzer`**: Parses Oracle PL/SQL into structured JSON
- **`FORMATOracleTriggerAnalyzer`**: Converts JSON back to formatted Oracle SQL
- **`FORMATPostsqlTriggerAnalyzer`**: Transforms JSON to PostgreSQL SQL
- **`JSONTOPLJSON`**: Converts analysis JSON to operation-specific structure
- **`common.py`**: Shared utilities and logging infrastructure

## 📁 Project Structure

```txt
ORACALE_to_json/
├── main.py                          # Main execution script
├── requirements.txt                 # Python dependencies
├── utilities/                       # Core converter modules
│   ├── common.py                   # Shared utilities and logging
│   ├── OracleTriggerAnalyzer.py    # Oracle SQL parser
│   ├── FORMATOracleTriggerAnalyzer.py  # Oracle SQL formatter
│   ├── FORMATPostsqlTriggerAnalyzer.py # PostgreSQL converter
│   ├── JSONTOPLJSON.py             # JSON structure transformer
│   └── oracle_postgresql_mappings.xlsx  # Type/function mappings
├── files/                          # Input/output directories
│   ├── oracle/                     # Original Oracle trigger files
│   ├── format_json/                # JSON analysis output
│   ├── format_sql/                 # Formatted Oracle SQL
│   ├── format_pl_json/             # PostgreSQL JSON structure
│   ├── format_plsql/               # Final PostgreSQL SQL
│   └── expected_json/              # Expected output examples
├── output/                         # Log files
└── docs/                          # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Required packages (see `requirements.txt`)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd ORACALE_to_json
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Place Oracle trigger files:**

   ```bash
   # Copy your Oracle trigger files to files/oracle/
   # Files should be named: trigger1.sql, trigger2.sql, etc.
   ```

4. **Run the converter:**

   ```bash
   python main.py
   ```

## 🔄 Conversion Process

The converter follows a 7-step workflow:

### Step 1: SQL → JSON Analysis

- Parses Oracle trigger files from `files/oracle/`
- Extracts declarations, variables, constants, exceptions
- Analyzes control structures (IF-ELSE, CASE-WHEN, FOR loops)
- Generates structured JSON in `files/format_json/`

### Step 2: JSON → Oracle SQL

- Converts JSON analysis back to formatted Oracle SQL
- Validates parsing accuracy
- Outputs to `files/format_sql/`

### Step 3: JSON Cleaning

- Removes line numbers and metadata
- Optimizes JSON structure
- Prepares for PostgreSQL conversion

### Step 4: Validation

- Compares original and converted files
- Ensures all triggers were processed
- Reports conversion statistics

### Step 5: JSON → PL/JSON

- Transforms analysis JSON to PostgreSQL-compatible structure
- Separates INSERT, UPDATE, DELETE operations
- Outputs to `files/format_pl_json/`

### Step 6: PL/JSON → PostgreSQL Format

- Converts to PostgreSQL trigger structure
- Applies type mappings and function conversions
- Outputs to `files/format_plsql/`

### Step 7: Final SQL Generation

- Generates executable PostgreSQL SQL
- Includes proper DO $$ BEGIN ... END $$ syntax
- Creates final trigger files

## 🛠️ Features

### Advanced Parsing

- **Multi-level nesting support**: Handles complex IF-ELSE, CASE-WHEN, and BEGIN-END blocks
- **Exception handling**: Preserves Oracle exception logic
- **Variable declarations**: Converts Oracle data types to PostgreSQL equivalents
- **Constant processing**: Maintains constant definitions and values

### Smart Conversion

- **Type mapping**: Automatic Oracle → PostgreSQL data type conversion
- **Function translation**: Oracle functions mapped to PostgreSQL equivalents
- **Syntax adaptation**: Oracle-specific syntax converted to PostgreSQL
- **Conditional logic**: Preserves business logic while adapting syntax

### Quality Assurance

- **Comprehensive logging**: Detailed logs for debugging and monitoring
- **Validation checks**: Ensures conversion completeness
- **Performance metrics**: Tracks conversion time for each step
- **Error handling**: Graceful error recovery and reporting

### Configuration

- **Excel mappings**: Configurable type and function mappings via Excel file
- **Customizable output**: Flexible output formatting options
- **Batch processing**: Handles multiple trigger files automatically

## 📊 Supported Oracle Features

### Data Types

- `VARCHAR2` → `VARCHAR`
- `NUMBER` → `NUMERIC`
- `DATE` → `TIMESTAMP`
- `PLS_INTEGER` → `INTEGER`
- `CLOB` → `TEXT`
- And many more...

### Control Structures

- IF-ELSE statements with ELSIF clauses
- CASE-WHEN statements (simple and searched)
- FOR loops with cursor queries
- BEGIN-END blocks with exception handlers
- Nested structures of any depth

### Oracle Functions

- `NVL` → `COALESCE`
- `SUBSTR` → `SUBSTRING`
- `LENGTH` → `LENGTH`
- `TO_DATE` → `TO_TIMESTAMP`
- `RAISE_APPLICATION_ERROR` → `RAISE EXCEPTION`
- And comprehensive function mapping via Excel

### Exception Handling

- Custom exception declarations
- Exception handlers with WHEN clauses
- RAISE statements
- Error message conversion

## 📝 Usage Examples

### Basic Conversion

```bash
# Convert all triggers in files/oracle/
python main.py
```

### File Structure

```txt
files/oracle/
├── trigger1.sql    # Original Oracle trigger
├── trigger2.sql    # Original Oracle trigger
└── trigger3.sql    # Original Oracle trigger

# After conversion:
files/format_plsql/
├── trigger1.sql    # PostgreSQL trigger
├── trigger2.sql    # PostgreSQL trigger
└── trigger3.sql    # PostgreSQL trigger
```

### Sample Output

```sql
-- PostgreSQL Trigger for trigger1
-- Generated on: 2025-08-14 16:08:04

DO $$
DECLARE
  V_COUNTER integer;
  V_CODE varchar(2);
  -- ... more declarations
BEGIN
  -- Converted Oracle logic
  SELECT COALESCE(TXO_SECURITY.GET_USERID, current_user) INTO V_USERID;
  
  IF (:NEW.IN_PREP_IND = 'Y') THEN
    IF (:NEW.PORTF_PROJ_CD <> 'Y') THEN
      RAISE EXCEPTION 'In-prep theme must be portfolio project';
    END IF;
  END IF;
  -- ... more converted logic
END $$;
```

## 🔧 Configuration

### Excel Mappings File

The `utilities/oracle_postgresql_mappings.xlsx` file contains:

- **data_type_mappings**: Oracle → PostgreSQL data type conversions
- **function_mappings**: Oracle → PostgreSQL function translations
- **exception_mappings**: Oracle exception → PostgreSQL message mappings

### Logging Configuration

Logs are written to both console and timestamped files in `output/`:

- **Console**: INFO level and above
- **File**: DEBUG level and above with detailed context

## 📈 Performance

The converter is optimized for:

- **Large triggers**: Handles triggers with 800+ lines
- **Complex logic**: Processes deeply nested control structures
- **Batch processing**: Efficiently converts multiple files
- **Memory usage**: Streamlined processing to minimize memory footprint

Typical performance metrics:

- **Parsing**: ~0.1-0.5 seconds per trigger
- **Conversion**: ~0.2-1.0 seconds per trigger
- **Total workflow**: ~2-5 seconds for 6 triggers

## 🐛 Troubleshooting

### Common Issues

1. **File not found errors**
   - Ensure Oracle trigger files are in `files/oracle/`
   - Check file naming convention: `trigger1.sql`, `trigger2.sql`, etc.

2. **Parsing errors**
   - Check Oracle SQL syntax validity
   - Verify trigger structure follows standard PL/SQL format

3. **Conversion issues**
   - Review Excel mappings file for missing type/function mappings
   - Check log files for detailed error information

### Debug Mode

Enable detailed logging by modifying `common.py`:

```python
DEBUG_ANALYZER = True  # Enable debug logging
```

## 📚 Documentation

Additional documentation available in `docs/`:

- `SQL_ANALYSIS_DOCUMENTATION.md`: Detailed parsing documentation
- `SQL_CONDITIONS_CONVERSION_GUIDE.md`: Condition conversion guide
- `ENHANCED_BEGIN_END_PARSING.md`: Block parsing details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

For issues and questions:

1. Check the log files in `output/` for detailed error information
2. Review the documentation in `docs/`
3. Create an issue with detailed error description and sample code

---

**Note**: This converter handles most common Oracle trigger patterns but may require manual review for complex custom logic or Oracle-specific features not covered by the mapping rules.
