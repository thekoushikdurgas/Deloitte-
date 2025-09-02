"""
Workflow Runner Utilities for Oracle to PostgreSQL Converter

This module contains the workflow execution functions separated from the UI logic.
"""

import streamlit as st
from utilities.streamlit_utils import WorkflowManager, SessionManager


def run_single_step(workflow_functions):
    """Run a single workflow step."""
    current_step = st.session_state.current_step
    
    if current_step < len(WorkflowManager.STEPS):
        step = WorkflowManager.STEPS[current_step]
        
        # Check prerequisites
        if not WorkflowManager.can_run_step(current_step):
            prerequisites = WorkflowManager.get_step_prerequisites(current_step)
            st.warning(f"Cannot run step. Prerequisites: {', '.join(prerequisites)}")
            return
        
        function_name = step['function_name']
        if function_name not in workflow_functions:
            st.error(f"Function {function_name} not found")
            return
            
        with st.spinner(f"Running: {step['name']}..."):
            try:
                workflow_functions[function_name]()
                SessionManager.advance_workflow_step()
                SessionManager.add_to_history(step['name'], "Success")
                st.success(f"Completed: {step['name']}")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error in {step['name']}: {str(e)}")
                SessionManager.add_to_history(step['name'], "Error", str(e))
    else:
        st.info("All steps completed!")


def run_all_steps(workflow_functions, progress_container):
    """Run all workflow steps sequentially."""
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, step in enumerate(WorkflowManager.STEPS):
            status_text.text(f"Running: {step['name']}...")
            progress_bar.progress(i / len(WorkflowManager.STEPS))
            
            function_name = step['function_name']
            if function_name not in workflow_functions:
                st.error(f"Function {function_name} not found")
                return
            
            try:
                workflow_functions[function_name]()
                SessionManager.add_to_history(step['name'], "Success")
                
            except Exception as e:
                st.error(f"Error in {step['name']}: {str(e)}")
                SessionManager.add_to_history(step['name'], "Error", str(e))
                return
        
        progress_bar.progress(1.0)
        status_text.text("All steps completed!")
        st.session_state.current_step = len(WorkflowManager.STEPS)
        
        st.balloons()


def run_individual_step(step, step_index, workflow_functions, progress_container):
    """Run a specific workflow step."""
    # Check prerequisites
    if not WorkflowManager.can_run_step(step_index):
        prerequisites = WorkflowManager.get_step_prerequisites(step_index)
        st.warning(f"Cannot run step. Prerequisites: {', '.join(prerequisites)}")
        return
    
    function_name = step['function_name']
    if function_name not in workflow_functions:
        st.error(f"Function {function_name} not found")
        return
    
    with progress_container:
        with st.spinner(f"Running: {step['name']}..."):
            try:
                workflow_functions[function_name]()
                st.session_state.current_step = max(st.session_state.current_step, step_index + 1)
                SessionManager.add_to_history(step['name'], "Success")
                st.success(f"Completed: {step['name']}")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error in {step['name']}: {str(e)}")
                SessionManager.add_to_history(step['name'], "Error", str(e))
