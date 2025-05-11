"""
Message handling functions for the chat application.
"""
import hashlib
import streamlit as st
import time
import threading

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
            
            # Force UI update if auto-refresh is enabled
            if st.session_state.auto_refresh:
                st.session_state.last_update_time = time.time()
                
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    
    print("Message receiver thread ended")
    st.session_state.thread_running = False

def process_message(msg):
    """Process messages from the message queue"""
    try:
        print(f"Processing message: {msg[:50]}...")
        parts = msg.split('|')
        msg_type = parts[0]
        
        # Generate a message ID for deduplication
        msg_id = hashlib.md5(msg.encode()).hexdigest()
        
        # Skip if we've already processed this message
        if msg_id in st.session_state.message_ids:
            print(f"Skipping duplicate message: {msg[:30]}...")
            return
        
        # Add to processed messages
        st.session_state.message_ids.add(msg_id)
        
        if msg_type == "USERS":
            # Update online users list
            users = parts[1].split(',')
            st.session_state.online_users = users
            print(f"Updated online users: {users}")
            
        elif msg_type == "DIRECT":
            # Direct message: DIRECT|sender|message
            sender, message = parts[1], parts[2]
            
            # Print detailed message info to terminal
            print("\n" + "="*50)
            print(f"[SERVER RELAY MESSAGE RECEIVED] From: {sender}")
            print(f"[SERVER RELAY MESSAGE RECEIVED] Content: {message}")
            print(f"[SERVER RELAY MESSAGE RECEIVED] Connection: Server Relay")
            print("="*50 + "\n")
            
            # Add to messages
            if sender not in st.session_state.messages:
                st.session_state.messages[sender] = []
            
            # Only add if it's not from ourselves or if we're the sender
            if sender != st.session_state.username:
                st.session_state.messages[sender].append((sender, message))
                print(f"Added message from {sender} to chat history")
            
        elif msg_type == "BROADCAST":
            # Broadcast message: BROADCAST|sender|message
            sender, message = parts[1], parts[2]
            print(f"Received broadcast from {sender}: {message[:30]}...")
            
            # Add to broadcast messages
            if "broadcast" not in st.session_state.messages:
                st.session_state.messages["broadcast"] = []
            
            # Only add if it's not from ourselves
            if sender != st.session_state.username:
                st.session_state.messages["broadcast"].append((sender, message))
                print(f"Added broadcast from {sender} to chat history")
            
        elif msg_type == "ERROR":
            # Error message
            error_msg = parts[1]
            print(f"Error from server: {error_msg}")
        
        elif parts[0] == "P2P_REQUEST_NOTIFICATION":
            # P2P connection request notification
            requester = parts[1]
            print(f"[P2P] Received P2P connection request from {requester}")
            
            # Store the pending request in session state
            if "pending_p2p_requests" not in st.session_state:
                st.session_state.pending_p2p_requests = []
            
            # Always add the request, even if it's from a user who previously sent a request
            # This allows users to send multiple requests after rejection
            if requester not in st.session_state.pending_p2p_requests:
                st.session_state.pending_p2p_requests.append(requester)
                print(f"[P2P] Added {requester} to pending P2P requests")
            
            # Update timestamp to trigger UI refresh
            st.session_state.last_update_time = time.time()
        
        elif parts[0] == "P2P_REJECTED":
            # P2P connection request was rejected
            rejecter = parts[1]
            print(f"[P2P] Connection request rejected by {rejecter}")
            
            # Store the rejection notification
            if "p2p_rejections" not in st.session_state:
                st.session_state.p2p_rejections = []
            
            st.session_state.p2p_rejections.append(rejecter)
            
            # Update timestamp to trigger UI refresh
            st.session_state.last_update_time = time.time()
        
        elif parts[0] == "P2P_INFO":
            # P2P connection information: P2P_INFO|username|ip|port
            target_username, target_ip, target_port = parts[1], parts[2], parts[3]
            print(f"[P2P] Received P2P connection info for {target_username}: {target_ip}:{target_port}")
            
            # Import the establish_p2p_connection function
            from .p2p import establish_p2p_connection
            
            # Try to establish the P2P connection
            if establish_p2p_connection(target_username, target_ip, target_port):
                print(f"[P2P] Successfully established P2P connection with {target_username}")
                
                # Set the chat_with to the target username if not already set
                # This ensures that the requester also navigates to the chat
                if st.session_state.chat_with != target_username:
                    st.session_state.chat_with = target_username
                    print(f"[P2P] Navigating to chat with {target_username}")
            else:
                print(f"[P2P] Failed to establish P2P connection with {target_username}")
            
            # Update timestamp to trigger UI refresh
            st.session_state.last_update_time = time.time()
    
    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Message was: {msg}")

def send_message(recipient, message):
    """Send a message to a recipient"""
    try:
        print(f"Sending message to {recipient}: {message[:30]}...")
        
        # Check if we have a P2P connection to this recipient
        if recipient in st.session_state.p2p_connections:
            # Send message through P2P connection
            p2p_socket = st.session_state.p2p_connections[recipient]
            try:
                # Format the message for P2P
                p2p_socket.sendall(message.encode())
                print("\n" + "="*50)
                print(f"[P2P MESSAGE SENT] To: {recipient}")
                print(f"[P2P MESSAGE SENT] Content: {message}")
                print(f"[P2P MESSAGE SENT] Connection: Direct P2P")
                print("="*50 + "\n")
                
                # Add to local state
                if recipient not in st.session_state.messages:
                    st.session_state.messages[recipient] = []
                
                st.session_state.messages[recipient].append((st.session_state.username, message))
                print(f"Added P2P message to local chat history")
                
                # Update timestamp to trigger UI refresh
                st.session_state.last_update_time = time.time()
                
                return True, "Message sent via P2P"
            except Exception as e:
                print(f"Error sending P2P message: {e}")
                # Fall back to server relay if P2P fails
                print(f"Falling back to server relay for {recipient}")
        
        # Send through server if no P2P connection or P2P failed
        st.session_state.client_socket.sendall(f"DIRECT|{recipient}|{message}".encode())
        print("\n" + "="*50)
        print(f"[SERVER RELAY MESSAGE SENT] To: {recipient}")
        print(f"[SERVER RELAY MESSAGE SENT] Content: {message}")
        print(f"[SERVER RELAY MESSAGE SENT] Connection: Server Relay")
        print("="*50 + "\n")
        
        # Add to local state
        if recipient not in st.session_state.messages:
            st.session_state.messages[recipient] = []
        
        st.session_state.messages[recipient].append((st.session_state.username, message))
        print(f"Added direct message to local chat history")
        
        # Update timestamp to trigger UI refresh
        st.session_state.last_update_time = time.time()
        
        return True, "Message sent"
    except Exception as e:
        print(f"Error sending message: {e}")
        return False, f"Failed to send message: {e}"


















