import os
import logging
from datetime import datetime

# Configure logging
def setup_logging(log_dir="output"):
    """Set up logging configuration to output to both console and file."""
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
    
    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    
    # Create file handler for all log messages
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

# Global logger instance
logger, log_file = setup_logging()

# For backward compatibility with existing code
DEBUG_ANALYZER = True
def debug(msg: str) -> None:
    """Legacy debug function that now uses the logger."""
    if DEBUG_ANALYZER:
        logger.debug(msg)