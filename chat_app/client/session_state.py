"""
Manages the Streamlit session state for the chat application.
"""
import streamlit as st
import queue
import time

def initialize_session_state():
    """Initialize all session state variables"""
    # Message storage
    if "messages" not in st.session_state:
        st.session_state.messages = {}  # Dictionary to store messages by username
    if "message_ids" not in st.session_state:
        st.session_state.message_ids = set()  # Set to track processed message IDs
    if "input_keys" not in st.session_state:
        st.session_state.input_keys = {}  # Track input keys to handle clearing
    if "last_sent_message" not in st.session_state:
        st.session_state.last_sent_message = ""  # Track the last sent message
    
    # Connection state
    if "client_socket" not in st.session_state:
        st.session_state.client_socket = None
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "chat_with" not in st.session_state:
        st.session_state.chat_with = ""
    if "message_queue" not in st.session_state:
        st.session_state.message_queue = queue.Queue()
    if "thread_running" not in st.session_state:
        st.session_state.thread_running = False
    if "online_users" not in st.session_state:
        st.session_state.online_users = []
    if "last_update_time" not in st.session_state:
        st.session_state.last_update_time = time.time()
    
    # P2P state
    if "connection_type" not in st.session_state:
        st.session_state.connection_type = "client-server"  # Default to client-server mode
    if "mode_selected" not in st.session_state:
        st.session_state.mode_selected = False
    if "p2p_mode_enabled" not in st.session_state:
        st.session_state.p2p_mode_enabled = False
    if "p2p_server_running" not in st.session_state:
        st.session_state.p2p_server_running = False
    if "p2p_port" not in st.session_state:
        st.session_state.p2p_port = 0  # Will be set when P2P server starts
    if "p2p_connections" not in st.session_state:
        st.session_state.p2p_connections = {}  # Dictionary to store P2P connections
    
    # P2P request state
    if "pending_p2p_requests" not in st.session_state:
        st.session_state.pending_p2p_requests = []
    if "p2p_rejections" not in st.session_state:
        st.session_state.p2p_rejections = []
    if "rejected_p2p_users" not in st.session_state:
        st.session_state.rejected_p2p_users = []
    
    # UI state
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = True  # Enable auto-refresh by default
    if "refresh_thread_running" not in st.session_state:
        st.session_state.refresh_thread_running = False
    if "mode_selected" not in st.session_state:
        st.session_state.mode_selected = False
    if "connection_type" not in st.session_state:
        st.session_state.connection_type = None  # Will be either "client-server" or "p2p"




