"""
UI Package for Oracle to PostgreSQL Converter

This package contains all the user interface modules for the Streamlit application,
organized by functionality to maintain clean separation of concerns.

Modules:
- sidebar: Navigation and file statistics sidebar
- dashboard: Main dashboard page
- file_manager: File upload, browse, and management
- configuration: Oracle-PostgreSQL mappings and system settings
- workflow: Conversion workflow management
- analytics: Statistics and analytics visualization
- quick_check: Verification and additional conversion tools
- rest_list: Rest list management functionality
"""

# Import all page functions for easy access
from .sidebar import display_sidebar
from .dashboard import dashboard_page
from .file_manager import file_manager_page
from .configuration import configuration_page
from .workflow import workflow_page
from .analytics import analytics_page
from .quick_check import quick_check_page
from .rest_list import rest_list_page

__all__ = [
    'display_sidebar',
    'dashboard_page',
    'file_manager_page', 
    'configuration_page',
    'workflow_page',
    'analytics_page',
    'quick_check_page',
    'rest_list_page'
]
