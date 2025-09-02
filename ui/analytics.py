"""
Analytics Module for Oracle to PostgreSQL Converter

This module handles analytics and statistics visualization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utilities.streamlit_utils import FileManager, SessionManager


def analytics_page():
    """Analytics and statistics page."""
    st.title("📊 Analytics & Statistics")
    
    # File statistics
    st.subheader("📈 File Statistics")
    
    stats = FileManager.get_file_stats()
    
    # Create charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart of file counts
        if any(stats.values()):
            fig_bar = px.bar(
                x=list(stats.keys()),
                y=list(stats.values()),
                title="Files by Directory",
                labels={'x': 'Directory', 'y': 'File Count'}
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, width='stretch')
        else:
            st.info("No files found in any directory")
    
    with col2:
        # Pie chart
        if any(stats.values()):
            non_zero_stats = {k: v for k, v in stats.items() if v > 0}
            if non_zero_stats:
                fig_pie = px.pie(
                    values=list(non_zero_stats.values()),
                    names=list(non_zero_stats.keys()),
                    title="File Distribution"
                )
                st.plotly_chart(fig_pie, width='stretch')
            else:
                st.info("No files to display in pie chart")
        else:
            st.info("No files found for pie chart")
    
    # Conversion history
    st.subheader("📋 Conversion History")
    
    if st.session_state.conversion_history:
        df_history = pd.DataFrame(st.session_state.conversion_history)
        
        # Summary metrics
        total_conversions = len(df_history)
        successful_conversions = len(df_history[df_history['status'] == 'Success'])
        failed_conversions = len(df_history[df_history['status'].str.contains('Error', na=False)])
        success_rate = (successful_conversions / total_conversions * 100) if total_conversions > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Operations", total_conversions)
        with col2:
            st.metric("Successful", successful_conversions)
        with col3:
            st.metric("Failed", failed_conversions)
        with col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Timeline chart
        if len(df_history) > 1:
            st.subheader("📈 Operation Timeline")
            df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
            fig_timeline = px.scatter(
                df_history, 
                x='timestamp', 
                y='step',
                color='status',
                title="Conversion Operations Timeline",
                color_discrete_map={'Success': 'green', 'Error': 'red'}
            )
            st.plotly_chart(fig_timeline, width='stretch')
        
        # History table
        st.dataframe(df_history, use_container_width=True)
        
        # Clear history
        if st.button("🗑️ Clear History"):
            SessionManager.clear_history()
            st.rerun()
    
    else:
        st.info("No conversion history available.")
