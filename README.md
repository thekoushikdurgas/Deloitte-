# Oracle to PostgreSQL Trigger Converter

This Python script converts Oracle PL/SQL trigger code to PostgreSQL code wrapped in JSON format.

## Features

The converter handles the following Oracle to PostgreSQL conversions:

### Data Types

- `varchar2` → `varchar`
- `pls_integer` → `integer`
- `simple_integer` → `integer`
- `number` → `numeric`

### Functions

- `substr()` → `SUBSTRING(text FROM start FOR length)`
- `nvl()` → `COALESCE()`
- `sysdate` → `CURRENT_DATE`
- `length()` → `LENGTH()`
- `trim()` → `TRIM()`

### Sequence Generation

- Oracle `ROWNUM` sequences → PostgreSQL `generate_series()`
- Complex Oracle queries → Simplified PostgreSQL equivalents

### Exception Handling

- Oracle custom exceptions → PostgreSQL `RAISE EXCEPTION`
- Proper error message mapping
- `raise_application_error` → `RAISE EXCEPTION`

### Variable References

- `:new.field_name` → `:new_field_name`
- `:old.field_name` → `:old_field_name`

### Function Calls

- `package.function()` → `schema$function()` (PostgreSQL style)
- Preserves table references like `gmd.themes`

### User Context

- Oracle user functions → PostgreSQL parameters
- `txo_security.get_userid` → `:ins_user`

## Usage

### Folder Processing (Default)

Process all `.sql` files from the Oracle folder and output to JSON folder:

```bash
# Process all files from 'orcale' folder to 'json' folder
python convert.py

# Use custom folder names
python convert.py --oracle-folder my_oracle_files --json-folder my_json_output

# Verbose output
python convert.py --verbose
```

### Single File Processing

Convert individual files:

```bash
# File mode - specify input file
python convert.py --mode file input_trigger.sql

# File mode with custom output
python convert.py --mode file input_trigger.sql -o output_trigger.json

# File mode with verbose output
python convert.py --mode file input_trigger.sql -o output.json --verbose
```

### Help

```bash
python convert.py --help
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode { file ,folder}` | Processing mode | `folder` |
| `--oracle-folder` | Oracle SQL files folder | `orcale` |
| `--json-folder` | Output JSON files folder | `json` |
| `-o, --output` | Output file (file mode only) | `input.json` |
| `-v, --verbose` | Verbose output | `False` |
| `-h, --help` | Show help message | - |

## Folder Structure

The converter expects the following folder structure:

```txt
your-project/
├── convert.py           # The converter script
├── orcale/             # Oracle SQL files (input)
│   ├── trigger1.sql
│   ├── trigger2.sql
│   └── ...
└── json/               # PostgreSQL JSON files (output)
    ├── trigger1.json
    ├── trigger2.json
    └── ...
```

## Example Output

When you run the converter, you'll see:

```bash
🚀 Starting folder processing...
📁 Oracle folder: orcale
📁 JSON folder: json
🔍 Found 2 SQL file(s) in 'orcale'
Warning: orcale/trigger2.sql is empty, skipping...
✅ Successfully converted orcale/trigger1.sql → json/trigger1.json

🎉 Conversion complete: 1/2 files converted successfully
```

## Input/Output Example

### Input (Oracle PL/SQL)

```sql
declare
   invalid_theme_no exception;
   v_counter pls_integer;
   v_description varchar2(500);
begin
   if (inserting) then
      if (substr(:new.theme_no, 1, 1) not between 0 and 9) then
         raise invalid_theme_no;
      end if;
      
      select nvl(txo_security.get_userid, user) into v_userid from dual;
      
      insert into themes(theme_no, registrat_date, theme_desc)
      values (:new.theme_no, sysdate, :new.theme_desc);
   end if;
exception
   when invalid_theme_no then
      raise_application_error(-20101, 'Invalid theme number');
end;
```

### Output (PostgreSQL JSON)

```json
{
    "on_insert": [
        {
            "type": "sql",
            "sql": "DO $$ DECLARE v_counter integer; v_description varchar(500); v_userid varchar(30); BEGIN IF (SUBSTRING(:new_theme_no FROM 1 FOR 1) !~ '^[0-9]$') THEN RAISE EXCEPTION 'MDM_V_THEMES_IOF: Invalid theme number'; END IF; v_userid := :ins_user; INSERT INTO themes(theme_no, registrat_date, theme_desc) VALUES (:new_theme_no, CURRENT_DATE, :new_theme_desc); END $$;"
        }
    ]
}
```

## JSON Output Structure

The output JSON contains separate sections for each trigger operation:

- `on_insert`: Contains PostgreSQL code for INSERT operations
- `on_update`: Contains PostgreSQL code for UPDATE operations  
- `on_delete`: Contains PostgreSQL code for DELETE operations

Each section contains an array of SQL blocks with:

- `type`: Always "sql"
- `sql`: The converted PostgreSQL code wrapped in a DO block

## Features:-

### Smart Processing

- 🔍 **Auto-discovery**: Finds all `.sql` files in the Oracle folder
- ⚠️ **Empty file detection**: Skips empty files with warnings
- 📁 **Auto-creation**: Creates output directories automatically
- 📊 **Progress tracking**: Shows conversion progress and success rate

### Error Handling

- ❌ **Detailed error messages**: Clear error reporting with file names
- 🐛 **Verbose debugging**: Optional stack traces for troubleshooting
- 🔄 **Batch processing**: Continues processing other files if one fails

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Limitations

- Complex Oracle-specific features may need manual adjustment
- Some data type conversions may require review
- Custom Oracle packages need manual mapping to PostgreSQL equivalents
- Generated code should be tested before production use

## Notes

- The converter preserves the business logic while adapting syntax
- All Oracle exceptions are converted to PostgreSQL `RAISE EXCEPTION` statements
- Variable declarations are properly converted to PostgreSQL format
- Schema and table references are preserved where appropriate
- Empty SQL files are automatically skipped with warnings