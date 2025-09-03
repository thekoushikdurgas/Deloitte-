# Oracle to PostgreSQL Converter - Streamlit Web Interface

A comprehensive web-based interface for converting Oracle trigger SQL files to PostgreSQL format with full workflow management and visualization capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Streamlit application:**

   ```bash
   streamlit run app.py
   ```

3. **Access the application:**
   Open your browser and navigate to `http://localhost:8501`

## 📋 Features

### 🏠 Dashboard

- **Overview Statistics**: Real-time file counts across all directories
- **Workflow Status**: Visual representation of conversion progress
- **Recent Activity**: Timeline of conversion operations
- **Quick Actions**: Direct navigation to key features

### 📁 File Manager

- **File Upload**: Drag-and-drop Oracle SQL file upload
- **File Browser**: Navigate and view files across all directories
- **Content Viewer**: Syntax-highlighted display of SQL and JSON files
- **Download Manager**: Create and download conversion result packages

### ⚙️ Configuration

- **Oracle-PostgreSQL Mappings**:
  - View and edit data type mappings
  - Manage function conversion mappings
  - Upload/download mapping configurations
- **System Settings**:
  - Directory management
  - Logging configuration

### 🔄 Conversion Workflow

- **Step-by-Step Execution**: Run individual conversion steps
- **Batch Processing**: Execute complete workflow
- **Progress Tracking**: Real-time progress indicators
- **Prerequisites Checking**: Automatic validation of input requirements

### 📊 Analytics & Statistics

- **File Distribution Charts**: Interactive pie and bar charts
- **Conversion Timeline**: Visual timeline of operations
- **Success Rate Metrics**: Performance statistics
- **Historical Data**: Complete conversion history

### 📋 Rest List Manager

- **Unprocessed Items Tracking**: View items that couldn't be converted
- **File-based Filtering**: Filter by source file
- **Export Capabilities**: Download rest list data
- **Visual Analytics**: Charts showing unprocessed items by file

## 🏗️ Architecture

### Directory Structure

```
ORACLE_to_json/
├── app.py                          # Main Streamlit application
├── main.py                         # Original CLI workflow
├── requirements.txt                # Python dependencies
├── README_STREAMLIT.md            # This documentation
├── files/                         # File processing directories
│   ├── oracle/                    # Input Oracle SQL files
│   ├── format_json/              # JSON analysis output
│   ├── format_sql/               # Formatted Oracle SQL
│   ├── format_pl_json/           # PL/JSON format
│   └── format_plsql/             # PostgreSQL output
├── utilities/                     # Core processing modules
│   ├── OracleTriggerAnalyzer.py  # SQL parsing and analysis
│   ├── FormatSQL.py              # SQL formatting and conversion
│   ├── JSONTOPLJSON.py           # JSON to PL/JSON transformation
│   ├── streamlit_utils.py        # Streamlit utility functions
│   ├── common.py                 # Shared utilities
│   ├── oracle_postgresql_mappings.xlsx  # Conversion mappings
│   └── rest_list.csv             # Unprocessed items tracking
└── output/                       # Log files
```

### Conversion Workflow

The application follows a structured 6-step conversion process:

1. **Oracle SQL → JSON Analysis**
   - Input: `files/oracle/*.sql`
   - Output: `files/format_json/*_analysis.json`
   - Process: Parse Oracle trigger syntax into structured JSON

2. **JSON → Formatted Oracle SQL**
   - Input: `files/format_json/*_analysis.json`
   - Output: `files/format_sql/*.sql`
   - Process: Generate clean, formatted Oracle SQL

3. **JSON → PL/JSON Format**
   - Input: `files/format_json/*_analysis.json`
   - Output: `files/format_pl_json/*.json`
   - Process: Transform to operation-specific structure

4. **PL/JSON → PostgreSQL Format**
   - Input: `files/format_pl_json/*.json`
   - Output: `files/format_plsql/*_postgresql.json`
   - Process: Convert to PostgreSQL trigger format

5. **JSON → PostgreSQL SQL**
   - Input: `files/format_json/*_analysis.json`
   - Output: `files/format_plsql/*_postgresql.sql`
   - Process: Direct conversion to PostgreSQL SQL

6. **Generate Final PostgreSQL**
   - Input: `files/format_plsql/*_postgresql.json`
   - Output: `files/format_plsql/*.sql`
   - Process: Create final PostgreSQL SQL files

## 🔧 Configuration

### Oracle-PostgreSQL Mappings

The application uses Excel-based configuration files for mapping Oracle constructs to PostgreSQL equivalents:

#### Data Type Mappings (`data_type_mappings` sheet)

| Oracle Type | PostgreSQL Type |
|-------------|-----------------|
| VARCHAR2    | VARCHAR         |
| NUMBER      | NUMERIC         |
| DATE        | TIMESTAMP       |
| CLOB        | TEXT            |

#### Function Mappings (`function_mappings` sheet)

| Oracle Function | PostgreSQL Function |
|-----------------|-------------------|
| SYSDATE         | CURRENT_TIMESTAMP |
| NVL             | COALESCE          |
| SUBSTR          | SUBSTRING         |
| INSTR           | POSITION          |

#### Function List (`function_list` sheet)

List of recognized Oracle functions for parsing.

### Configuration Management

- **View/Edit**: Interactive table editing in the web interface
- **Upload**: Replace configuration with new Excel file
- **Download**: Export current configuration
- **Validation**: Automatic validation of mapping data

## 📊 Monitoring and Analytics

### File Statistics

- Real-time counts of files in each directory
- Visual charts showing distribution
- Progress tracking across workflow steps

### Conversion History

- Complete timeline of all operations
- Success/failure tracking
- Performance metrics
- Error logging and analysis

### Rest List Management

- Items that couldn't be automatically converted
- File-by-file breakdown
- Export capabilities for manual review
- Visual analytics for identifying patterns

## 🚀 Usage Guide

### Basic Workflow

1. **Upload Oracle SQL Files**
   - Navigate to File Manager → Upload Files
   - Select your Oracle trigger SQL files
   - Files are automatically saved to `files/oracle/`

2. **Run Conversion**
   - Go to Conversion Workflow
   - Click "Run All Steps" for complete conversion
   - Or run individual steps as needed

3. **Monitor Progress**
   - View real-time progress indicators
   - Check Analytics for detailed statistics
   - Review any errors or warnings

4. **Download Results**
   - Use File Manager → Download Results
   - Download individual files or complete package
   - Review PostgreSQL output files

### Advanced Features

#### Custom Mappings

1. Navigate to Configuration → Oracle-PostgreSQL Mappings
2. Edit mapping tables directly in the interface
3. Upload custom mapping Excel files
4. Download configurations for backup

#### Batch Processing

1. Upload multiple Oracle SQL files
2. Use "Run All Steps" for automated processing
3. Monitor progress in real-time
4. Review results in Analytics

#### Error Analysis

1. Check Rest List Manager for unprocessed items
2. Review conversion history for failed operations
3. Use file browser to examine intermediate outputs
4. Adjust mappings as needed and re-run

## 🔧 Troubleshooting

### Common Issues

**Files not appearing after upload**

- Check File Manager → Browse Files
- Ensure files have .sql extension
- Verify directory permissions

**Conversion steps failing**

- Check Analytics → Conversion History for error details
- Verify prerequisite files exist
- Review Oracle-PostgreSQL mappings
- Check log files in output/ directory

**Missing directories**

- Use Quick Actions → Create Directories
- Or check Configuration → Directory Configuration

**Performance issues**

- Monitor file sizes in Analytics
- Consider processing files in smaller batches
- Check system resources

### Support

For issues and feature requests:

1. Check the conversion history for error details
2. Review rest list for unprocessed items
3. Examine log files in the output/ directory
4. Verify configuration mappings

## 🔄 Integration with CLI

The Streamlit application integrates seamlessly with the existing CLI workflow:

- **CLI Mode**: Use `python main.py` for command-line processing
- **Web Mode**: Use `streamlit run app.py` for web interface
- **Shared Configuration**: Both modes use the same configuration files
- **Compatible Outputs**: All output formats are identical

## 📈 Performance

### Optimization Features

- **Incremental Processing**: Only process changed files
- **Progress Tracking**: Real-time progress indicators
- **Error Recovery**: Continue processing after errors
- **Batch Operations**: Efficient multi-file processing

### Monitoring

- **File Statistics**: Track processing volume
- **Success Rates**: Monitor conversion quality
- **Performance Metrics**: Execution time tracking
- **Resource Usage**: Memory and processing optimization

## 🔮 Future Enhancements

- **Database Connectivity**: Direct database import/export
- **Advanced Mapping Editor**: Visual mapping interface
- **Parallel Processing**: Multi-threaded conversion
- **Cloud Integration**: AWS/Azure deployment options
- **API Endpoints**: RESTful API for integration
- **User Management**: Multi-user support with roles

---

## License

This project follows the same license as the parent Oracle to PostgreSQL converter project.

## Contributing

1. Follow the existing code structure
2. Add utility functions to `utilities/streamlit_utils.py`
3. Maintain consistent UI patterns
4. Update documentation for new features
5. Test thoroughly with various SQL file types
