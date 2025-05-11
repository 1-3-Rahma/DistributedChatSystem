"""
Entry point for the chat application client.
Run with: streamlit run run_client.py
"""
import streamlit as st
import os

# Set page config must be the first Streamlit command
st.set_page_config(page_title="Distributed Chat System", layout="wide")

# Import directly from the client directory
from client.session_state import initialize_session_state
from client.gui import render_gui

# Check if running on Streamlit Cloud
is_cloud = os.environ.get('IS_STREAMLIT_CLOUD', False)
if is_cloud:
    # Update server connection details for cloud deployment
    import client.auth as auth
    auth.SERVER_HOST = os.environ.get('SERVER_HOST', 'your-server-ip')
    auth.SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))

# Initialize the session state
initialize_session_state()

# Render the main GUI
render_gui()


