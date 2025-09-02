"""
Workflow Module for Oracle to PostgreSQL Converter

This module handles the conversion workflow page and user interface.
"""

import streamlit as st
from main import (
    read_oracle_triggers_to_json,
    read_json_to_oracle_triggers,
    read_json_to_postsql_triggers
)
from utilities.streamlit_utils import WorkflowManager, UIHelpers, SessionManager
from utilities.workflow_runner import run_single_step, run_all_steps, run_individual_step


def workflow_page():
    """Conversion workflow page."""
    st.title("🔄 Conversion Workflow")
    
    # Function mapping for workflow steps
    workflow_functions = {
        "read_oracle_triggers_to_json": read_oracle_triggers_to_json,
        "read_json_to_oracle_triggers": read_json_to_oracle_triggers,
        "read_json_to_postsql_triggers": read_json_to_postsql_triggers
    }
    
    # Progress indicator
    progress_container = st.container()
    
    # Step controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Run Single Step"):
            run_single_step(workflow_functions)
    
    with col2:
        if st.button("⏩ Run All Steps"):
            run_all_steps(workflow_functions, progress_container)
    
    with col3:
        if st.button("🔄 Reset Workflow"):
            SessionManager.reset_workflow()
            st.rerun()
    
    # Step details
    st.subheader("Workflow Steps")
    
    UIHelpers.display_step_status(WorkflowManager.STEPS, st.session_state.current_step)
    
    # Individual step execution
    for i, step in enumerate(WorkflowManager.STEPS):
        if st.button(f"Run Step {i+1}: {step['name']}", key=f"individual_step_{i}"):
            run_individual_step(step, i, workflow_functions, progress_container)
