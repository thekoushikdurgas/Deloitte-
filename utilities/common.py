import os
import logging
from datetime import datetime
from typing import Optional

# Configure logging
def setup_logging(log_dir="output", log_level="INFO"):
    """
    Set up logging configuration to output to both console and file.
    
    Args:
        log_dir (str): Directory to store log files
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        tuple: (logger, log_file_path)
    """
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create a timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"oracle_conversion_{timestamp}.log")
    
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Clear any existing handlers (in case setup_logging is called multiple times)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatters with more detailed information
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    
    # Create file handler for all log messages
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Create console handler with configurable log level
    console_handler = logging.StreamHandler()
    console_level = getattr(logging, log_level.upper(), logging.INFO)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

# Global logger instance
logger, log_file = setup_logging()

# For backward compatibility with existing code
DEBUG_ANALYZER = True

def debug(msg: str, *args, **kwargs) -> None:
    """Legacy debug function that now uses the logger."""
    if DEBUG_ANALYZER:
        logger.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs) -> None:
    """Info level logging."""
    logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs) -> None:
    """Warning level logging."""
    logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs) -> None:
    """Error level logging."""
    logger.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs) -> None:
    """Critical level logging."""
    logger.critical(msg, *args, **kwargs)

def alert(msg: str, *args, **kwargs) -> None:
    """Alert level logging (same as critical)."""
    logger.critical(f"🚨 ALERT: {msg}", *args, **kwargs)

# Custom logging levels for better categorization
def log_parsing_start(component: str, details: Optional[str] = None) -> None:
    """Log the start of a parsing operation."""
    msg = f"Starting {component} parsing"
    if details:
        msg += f": {details}"
    logger.info(f"🔄 {msg}")

def log_parsing_complete(component: str, details: Optional[str] = None) -> None:
    """Log the completion of a parsing operation."""
    msg = f"Completed {component} parsing"
    if details:
        msg += f": {details}"
    logger.info(f"✅ {msg}")

def log_parsing_error(component: str, error_msg: str, line_no: Optional[int] = None) -> None:
    """Log parsing errors with context."""
    msg = f"Error in {component}: {error_msg}"
    if line_no:
        msg += f" (line {line_no})"
    logger.error(f"❌ {msg}")

def log_structure_found(structure_type: str, line_no: int, details: Optional[str] = None) -> None:
    """Log when a structure is found during parsing."""
    msg = f"Found {structure_type} at line {line_no}"
    if details:
        msg += f": {details}"
    logger.debug(f"🔍 {msg}")

def log_nesting_level(level: int, context: str) -> None:
    """Log nesting level information."""
    indent = "  " * level
    logger.debug(f"📊 {indent}Nesting level {level} in {context}")

def log_performance(operation: str, duration: float) -> None:
    """Log performance metrics."""
    logger.debug(f"⏱️ {operation} completed in {duration:.3f}s")