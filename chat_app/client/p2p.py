"""
P2P connection handling for the chat application.
"""
import socket
import threading
import random
import streamlit as st
import time
import hashlib
from .utils import get_public_ip, get_local_ip

def update_connection_mode(username, mode):
    """Update the connection mode for a user"""
    if st.session_state.client_socket:
        try:
            st.session_state.client_socket.sendall(f"UPDATE_MODE|{username}|{mode}".encode())
        except Exception as e:
            print(f"Error updating connection mode for {username}: {e}")

def receive_p2p_messages(p2p_socket, peer_username):
    """Receive messages from a P2P connection"""
    try:
        p2p_socket.settimeout(None)  # No timeout for message receiving
        
        while True:
            try:
                data = p2p_socket.recv(1024).decode()
                if not data:
                    print(f"[P2P MODE] Connection closed by {peer_username}")
                    break
                
                # Generate a message ID for deduplication
                msg_id = hashlib.md5(f"P2P|{peer_username}|{data}".encode()).hexdigest()
                
                # Skip if we've already processed this message
                if msg_id in st.session_state.message_ids:
                    continue
                
                # Add to processed messages
                st.session_state.message_ids.add(msg_id)
                
                # Print detailed message info to terminal
                print("\n" + "="*50)
                print(f"[P2P MESSAGE RECEIVED] From: {peer_username}")
                print(f"[P2P MESSAGE RECEIVED] Content: {data}")
                print(f"[P2P MESSAGE RECEIVED] Message ID: {msg_id[:8]}...")
                print(f"[P2P MESSAGE RECEIVED] Connection: Direct P2P")
                print("="*50 + "\n")
                
                # Process the message
                if peer_username not in st.session_state.messages:
                    st.session_state.messages[peer_username] = []
                
                st.session_state.messages[peer_username].append((peer_username, data))
                
                # Update timestamp to trigger UI refresh
                st.session_state.last_update_time = time.time()
                
            except Exception as e:
                print(f"[P2P MODE] Error receiving message: {e}")
                break
                
    except Exception as e:
        print(f"[P2P MODE] Receive thread error: {e}")
    finally:
        # Clean up
        try:
            p2p_socket.close()
        except:
            pass
        
        if peer_username in st.session_state.p2p_connections:
            del st.session_state.p2p_connections[peer_username]
            print(f"[P2P MODE] Removed {peer_username} from P2P connections")
        
        # Update connection mode back to server relay
        update_connection_mode(peer_username, "Server Relay")

def register_public_ip():
    """Register our public IP with the server"""
    if not st.session_state.client_socket:
        return False
        
    try:
        public_ip = get_public_ip()
        if public_ip:
            print(f"Registering public IP: {public_ip}")
            st.session_state.client_socket.sendall(f"PUBLIC_IP|{public_ip}".encode())
            return True
        return False
    except Exception as e:
        print(f"Error registering public IP: {e}")
        return False

def p2p_server_handler(server_socket):
    """Handle incoming P2P connections"""
    print(f"P2P server handler started on port {st.session_state.p2p_port}")
    
    while st.session_state.p2p_server_running:
        try:
            # Set a timeout to allow checking if we should still be running
            server_socket.settimeout(1.0)
            
            try:
                client_socket, addr = server_socket.accept()
                print(f"Accepted P2P connection from {addr}")
                
                # Set a timeout for receiving the username
                client_socket.settimeout(5.0)
                
                # Receive the username from the client
                username = client_socket.recv(1024).decode()
                print(f"Received username: {username}")
                
                # Check if we already have a connection to this user
                if username in st.session_state.p2p_connections:
                    print(f"Already have a P2P connection with {username}, closing duplicate")
                    try:
                        client_socket.sendall("P2P_DUPLICATE".encode())
                        client_socket.close()
                    except:
                        pass
                    continue
                
                # Send confirmation
                client_socket.sendall("P2P_CONNECTED".encode())
                print(f"Sent P2P_CONNECTED confirmation to {username}")
                
                # Store the connection
                st.session_state.p2p_connections[username] = client_socket
                print(f"Stored P2P connection for {username}")
                
                # Update connection mode
                update_connection_mode(username, "P2P Direct")
                
                # Start a thread to receive messages
                p2p_thread = threading.Thread(
                    target=receive_p2p_messages,
                    args=(client_socket, username),
                    daemon=True
                )
                p2p_thread.start()
                print(f"Started receive thread for {username}")
                
                # Notify the server that we established a P2P connection
                if st.session_state.client_socket:
                    try:
                        st.session_state.client_socket.sendall(f"P2P_ESTABLISHED|{username}".encode())
                        print(f"Notified server about P2P connection with {username}")
                    except Exception as e:
                        print(f"Error notifying server about P2P connection: {e}")
                
                # Force UI update
                st.session_state.last_update_time = time.time()
                
            except socket.timeout:
                # This is just a timeout on accept(), continue the loop
                continue
                
        except Exception as e:
            print(f"P2P server error: {e}")
            time.sleep(1)  # Prevent tight loop in case of repeated errors
    
    print("P2P server handler stopped")

def setup_p2p_server():
    """Set up a P2P server to accept incoming connections"""
    print("\n" + "-"*50)
    print("SETTING UP P2P SERVER")
    
    if st.session_state.p2p_server_running:
        print("P2P server already running")
        print("-"*50 + "\n")
        return True
        
    try:
        # Create server socket
        print("Creating server socket...")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Try to bind to a port - use a wider range and randomize to avoid conflicts
        print("Finding available port...")
        # Start with the default port, then try random ports in a wider range
        ports_to_try = [10000] + random.sample(range(10001, 65000), 20)
        
        for port in ports_to_try:
            try:
                # Bind to all interfaces
                server_socket.bind(('0.0.0.0', port))
                st.session_state.p2p_port = port
                break
            except socket.error:
                continue
        else:
            print("Failed to bind to any port")
            print("-"*50 + "\n")
            return False
        
        # Listen for incoming connections
        print(f"Listening on port {st.session_state.p2p_port}...")
        server_socket.listen(5)
        
        # Start a new thread to handle incoming connections
        p2p_server_thread = threading.Thread(
            target=p2p_server_handler,
            args=(server_socket,),
            daemon=True
        )
        p2p_server_thread.start()
        
        st.session_state.p2p_server_running = True
        st.session_state.p2p_server_socket = server_socket
        
        # Register our P2P port with the server
        if st.session_state.client_socket:
            try:
                st.session_state.client_socket.sendall(f"P2P_PORT|{st.session_state.p2p_port}".encode())
                print(f"Registered P2P port {st.session_state.p2p_port} with server")
                
                # Also register our public IP
                register_public_ip()
            except Exception as e:
                print(f"Error registering P2P port with server: {e}")
        
        print("P2P server set up successfully")
        print("-"*50 + "\n")
        
        return True
    except Exception as e:
        print(f"Error setting up P2P server: {e}")
        print("-"*50 + "\n")
        return False

def establish_p2p_connection(target_username, target_ip, target_port):
    """Establish a P2P connection with another user with enhanced NAT traversal"""
    print("\n" + "-"*50)
    print(f"ESTABLISHING P2P CONNECTION WITH {target_username}")
    print(f"Target IP: {target_ip}, Port: {target_port}")
    
    # Check if we already have a connection to this user
    if target_username in st.session_state.p2p_connections:
        print(f"P2P connection with {target_username} already exists")
        print("-"*50 + "\n")
        return True
    
    # Make sure our P2P server is running
    if not st.session_state.p2p_server_running:
        print("P2P server not running, attempting to start...")
        if not setup_p2p_server():
            print("Failed to set up P2P server")
            print("-"*50 + "\n")
            return False
        print(f"P2P server started on port {st.session_state.p2p_port}")
    
    # Try multiple connection strategies
    connection_successful = False
    p2p_socket = None
    
    # Strategy 1: Direct connection to provided IP and port
    try:
        print(f"Strategy 1: Direct connection to {target_ip}:{target_port}")
        p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        p2p_socket.settimeout(5)  # 5 second timeout
        p2p_socket.connect((target_ip, int(target_port)))
        
        # Send our username
        p2p_socket.sendall(st.session_state.username.encode())
        
        # Wait for confirmation
        response = p2p_socket.recv(1024).decode()
        
        if response.startswith("P2P_CONNECTED"):
            print("Strategy 1 successful: Direct connection established")
            connection_successful = True
        else:
            print(f"Strategy 1 failed: Unexpected response: {response}")
            p2p_socket.close()
            p2p_socket = None
    except Exception as e:
        print(f"Strategy 1 failed: {e}")
        if p2p_socket:
            p2p_socket.close()
            p2p_socket = None
    
    # If connection was successful with any strategy
    if connection_successful and p2p_socket:
        print(f"P2P CONNECTION ESTABLISHED WITH {target_username}")
        print("-"*50 + "\n")
        
        # Store the connection
        st.session_state.p2p_connections[target_username] = p2p_socket
        
        # Update connection mode
        update_connection_mode(target_username, "P2P Direct")
        
        # Start a thread to receive messages
        p2p_thread = threading.Thread(
            target=receive_p2p_messages,
            args=(p2p_socket, target_username),
            daemon=True
        )
        p2p_thread.start()
        
        # Notify the server that we established a P2P connection
        if st.session_state.client_socket:
            try:
                st.session_state.client_socket.sendall(f"P2P_ESTABLISHED|{target_username}".encode())
            except Exception as e:
                print(f"Error notifying server about P2P connection: {e}")
        
        # Set the chat_with to the target username to navigate to their chat
        st.session_state.chat_with = target_username
        print(f"[P2P] Navigating to chat with {target_username}")
        
        # Force UI update
        st.session_state.last_update_time = time.time()
        
        return True
    else:
        print("ALL P2P CONNECTION STRATEGIES FAILED")
        print("Falling back to server relay mode")
        print("-"*50 + "\n")
        return False

def enable_p2p_mode():
    """Enable P2P mode if not already enabled"""
    if st.session_state.p2p_mode_enabled:
        return True
    
    # Try to set up P2P server
    if setup_p2p_server():
        st.session_state.p2p_mode_enabled = True
        return True
    else:
        print("Failed to set up P2P server")
        return False

def accept_p2p_request(requester_username):
    """Accept a P2P connection request from another user"""
    print(f"[P2P] Accepting connection request from {requester_username}")
    
    if not st.session_state.client_socket:
        print("[P2P] Cannot accept request: Not connected to server")
        return False
    
    try:
        # Send acceptance to server
        st.session_state.client_socket.sendall(f"P2P_ACCEPT|{requester_username}".encode())
        print(f"[P2P] Sent acceptance to server for {requester_username}")
        
        # Remove from pending requests
        if requester_username in st.session_state.pending_p2p_requests:
            st.session_state.pending_p2p_requests.remove(requester_username)
        
        # Set the chat_with to the requester to navigate to their chat
        st.session_state.chat_with = requester_username
        print(f"[P2P] Navigating to chat with {requester_username}")
        
        return True
    except Exception as e:
        print(f"[P2P] Error accepting P2P request: {e}")
        return False

def reject_p2p_request(requester_username):
    """Reject a P2P connection request from another user"""
    print(f"[P2P] Rejecting connection request from {requester_username}")
    
    if not st.session_state.client_socket:
        print("[P2P] Cannot reject request: Not connected to server")
        return False
    
    try:
        # Send rejection to server
        st.session_state.client_socket.sendall(f"P2P_REJECT|{requester_username}".encode())
        print(f"[P2P] Sent rejection to server for {requester_username}")
        
        # Remove from pending requests
        if requester_username in st.session_state.pending_p2p_requests:
            st.session_state.pending_p2p_requests.remove(requester_username)
            
        # Clear any previous rejections from this user to allow new requests
        if hasattr(st.session_state, 'rejected_p2p_users') and requester_username in st.session_state.rejected_p2p_users:
            st.session_state.rejected_p2p_users.remove(requester_username)
        
        return True
    except Exception as e:
        print(f"[P2P] Error rejecting P2P request: {e}")
        return False


