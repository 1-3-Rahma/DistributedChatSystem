"""
Streamlit deployment entry point
"""
import os
import sys

# Add the chat_app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the client
from chat_app.run_client import *