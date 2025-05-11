"""
Authentication functions for the chat application.
"""
import socket
import hashlib
import threading
import streamlit as st
import time

# Server connection details
SERVER_HOST = "localhost"  # Change to your server's IP address
SERVER_PORT = 5000

def receive_messages(client_socket, message_queue):
    """Receive messages from the server and add them to the queue"""
    print("Message receiver thread started")
    
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                print("Connection closed by server")
                break
                
            # Add message to queue for processing
            message_queue.put(data)
            print(f"Received data: {data[:50]}...")
            
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    
    print("Message receiver thread ended")
    st.session_state.thread_running = False

def login(username, password):
    """Log in to the chat server"""
    if not username or not password:
        return False, "Username and password are required"
    
    try:
        # Create a socket connection to the server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_HOST, SERVER_PORT))
        
        # Hash the password for security
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Send login credentials
        s.sendall(f"LOGIN|{username}|{password_hash}".encode())
        
        # Wait for response
        response = s.recv(1024).decode()
        
        if response.startswith("AUTH_SUCCESS"):
            st.session_state.client_socket = s
            st.session_state.username = username
            st.session_state.logged_in = True
            st.session_state.mode_selected = False  # Reset mode selection
            
            # Start the receiving thread with direct socket reference
            if not st.session_state.thread_running:
                receiver_thread = threading.Thread(
                    target=receive_messages, 
                    args=(s, st.session_state.message_queue),
                    daemon=True
                )
                receiver_thread.start()
                st.session_state.thread_running = True
            
            return True, f"Connected as {username}"
        else:
            return False, "Authentication failed. Please check your username and password."
    except Exception as e:
        return False, f"Could not connect: {e}"

def register(username, password):
    """Register a new user account"""
    if not username or not password:
        return False, "Username and password are required"
    
    try:
        # Create a socket connection to the server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_HOST, SERVER_PORT))
        
        # Hash the password for security
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Send registration request
        s.sendall(f"REGISTER|{username}|{password_hash}".encode())
        
        # Wait for response
        response = s.recv(1024).decode()
        
        if response.startswith("SUCCESS"):
            s.close()
            return True, f"User {username} registered successfully. You can now log in."
        else:
            s.close()
            return False, response.split('|')[1]
    except Exception as e:
        return False, f"Could not connect: {e}"

def logout():
    """Log out from the chat server"""
    if st.session_state.client_socket:
        try:
            st.session_state.client_socket.close()
        except:
            pass
    
    # Reset session state
    st.session_state.client_socket = None
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.chat_with = ""
    st.session_state.thread_running = False
    st.session_state.online_users = []
    st.session_state.messages = {}
    st.session_state.message_ids = set()
    st.session_state.mode_selected = False
    st.session_state.p2p_mode_enabled = False
    st.session_state.p2p_server_running = False
    st.session_state.p2p_connections = {}

