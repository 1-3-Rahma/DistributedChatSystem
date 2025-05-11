"""
Streamlit GUI for the chat application.
"""
import streamlit as st
import time
import queue
import threading
from .auth import login, register, logout
from .messaging import process_message, send_message
from .p2p import enable_p2p_mode, update_connection_mode, register_public_ip, accept_p2p_request, reject_p2p_request
from .utils import get_public_ip, get_local_ip

def apply_custom_css():
    """Apply custom CSS styling to the application"""
    st.markdown("""
    <style>
        .main {
            background-color: #f5f7f9;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            border-radius: 20px;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            transition-duration: 0.4s;
            cursor: pointer;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        .chat-header {
            background-color: #075E54;
            color: white;
            padding: 10px;
            border-radius: 10px 10px 0 0;
            margin-bottom: 10px;
        }
        .user-card {
            background-color: white;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .user-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .sender-msg {
            text-align: right;
            background-color: #DCF8C6;
            padding: 0px 8px;
            border-radius: 15px 0 15px 15px;
            margin: 5px 0;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .receiver-msg {
            text-align: left;
            background-color: white;
            padding: 0px 8px;
            border-radius: 0 15px 15px 15px;
            margin: 5px 0;
            max-width: 80%;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .input-container {
            display: flex;
            margin-top: 10px;
        }
        .stTextInput input {
            border-radius: 20px;
            padding: 10px;
            border: 1px solid #ccc;
        }
        .app-title {
            color: #075E54;
            text-align: center;
            margin-bottom: 20px;
        }
        .status-indicator {
            height: 10px;
            width: 10px;
            background-color: #4CAF50;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }
        /* Customize the chat form */
        .chat-form {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 0 0 10px 10px;
            border: 1px solid #d1d1d1;
            border-top: none;
        }
        /* Style for empty chat */
        .empty-chat {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #888;
            font-style: italic;
            background-color: #E5DDD5; /* WhatsApp-like light brown background */
            background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4AkEEjIZty4BpQAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAANklEQVQ4y2NgGAWjYOiD/0iYkImBgYGBiYGBgZGRkYERm0vQxZkYGBgYmUjR/H8UjIJRMHQAAOcvDBWzGtr9AAAAAElFTkSuQmCC");
            border-radius: 10px;
            padding: 20px;
        }
        /* Style for timestamp */
        .message-time {
            font-size: 0.7em;
            opacity: 0.7;
            margin-top: 2px;
        }
    </style>
    """, unsafe_allow_html=True)

def show_mode_selection_screen():
    """Display the connection mode selection screen"""
    st.title("Choose Connection Mode")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); height: 100%;">
            <h3 style="text-align: center; color: #2196F3;">🌐 Client-Server Mode</h3>
            <hr>
            <p><strong>How it works:</strong> All messages are relayed through the central server.</p>
            <ul>
                <li>More reliable connection</li>
                <li>Works across different networks</li>
                <li>Server stores message history</li>
                <li>Better for public networks</li>
            </ul>
            <p><strong>Best for:</strong> General chatting, public networks, or when P2P connections fail.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Select Client-Server Mode"):
            st.session_state.connection_type = "client-server"
            st.session_state.mode_selected = True
            st.session_state.p2p_mode_enabled = False
            print("\n" + "="*50)
            print("CLIENT-SERVER MODE SELECTED")
            print("All messages will be relayed through the central server")
            print("="*50 + "\n")
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); height: 100%;">
            <h3 style="text-align: center; color: #FF5722;">🔗 Peer-to-Peer Mode</h3>
            <hr>
            <p><strong>How it works:</strong> Direct connections between users when possible.</p>
            <ul>
                <li>More private communication</li>
                <li>Lower latency</li>
                <li>No server storage of messages</li>
                <li>Better for local networks</li>
            </ul>
            <p><strong>Best for:</strong> Private chats, local networks, and faster communication.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Select P2P Mode"):
            st.session_state.connection_type = "p2p"
            st.session_state.mode_selected = True
            st.session_state.p2p_mode_enabled = True
            
            # Set up P2P server
            if enable_p2p_mode():
                print("\n" + "="*50)
                print("P2P MODE SELECTED")
                print(f"P2P server started on port {st.session_state.p2p_port}")
                print("Direct connections will be established when possible")
                print("="*50 + "\n")
            else:
                print("\n" + "="*50)
                print("P2P MODE SELECTED BUT SERVER SETUP FAILED")
                print("Falling back to client-server mode for now")
                print("You can try enabling P2P mode again from the options panel")
                print("="*50 + "\n")
            
            st.rerun()

def display_p2p_status():
    """Display P2P connection status in the UI"""
    st.markdown("<div class='chat-header'><h4>🔌 P2P Connection Status</h4></div>", unsafe_allow_html=True)
    
    # Display pending P2P requests
    if hasattr(st.session_state, 'pending_p2p_requests') and st.session_state.pending_p2p_requests:
        st.markdown("""
        <div style="background-color: #cce5ff; color: #004085; padding: 10px; 
                    border-radius: 5px; margin-bottom: 10px;">
            <strong>Pending P2P Connection Requests</strong>
        </div>
        """, unsafe_allow_html=True)
        
        for requester in st.session_state.pending_p2p_requests:
            st.markdown(f"Request from: **{requester}**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Accept {requester}", key=f"btn_accept_p2p_{requester}"):
                    if accept_p2p_request(requester):
                        st.success(f"Accepted P2P request from {requester}")
                        # The chat_with is already set in the accept_p2p_request function
                        time.sleep(1)
                        st.rerun()
            with col2:
                if st.button(f"Reject {requester}", key=f"btn_reject_p2p_{requester}"):
                    if reject_p2p_request(requester):
                        st.success(f"Rejected P2P request from {requester}")
                        time.sleep(1)
                        st.rerun()
    
    # Display P2P rejection notifications
    if hasattr(st.session_state, 'p2p_rejections') and st.session_state.p2p_rejections:
        for rejecter in st.session_state.p2p_rejections:
            st.warning(f"{rejecter} rejected your P2P connection request")
            
            # Add a button to dismiss the notification
            if st.button(f"Dismiss", key=f"btn_dismiss_rejection_{rejecter}"):
                st.session_state.p2p_rejections.remove(rejecter)
                st.rerun()
    
    if not st.session_state.p2p_mode_enabled:
        st.markdown("""
        <div style="background-color: #f8d7da; color: #721c24; padding: 10px; 
                    border-radius: 5px; margin-bottom: 10px;">
            <strong>P2P Mode Disabled</strong>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if not st.session_state.p2p_server_running:
        st.markdown("""
        <div style="background-color: #f8d7da; color: #721c24; padding: 10px; 
                    border-radius: 5px; margin-bottom: 10px;">
            <strong>P2P Server Not Running</strong>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start P2P Server", key="btn_start_p2p_server"):
            if enable_p2p_mode():
                st.success(f"P2P server started on port {st.session_state.p2p_port}")
                st.rerun()
            else:
                st.error("Failed to start P2P server")
        return
    
    # Display active P2P connections
    st.markdown(f"""
    <div style="background-color: {'#d4edda' if st.session_state.p2p_connections else '#fff3cd'}; 
                color: {'#155724' if st.session_state.p2p_connections else '#856404'}; 
                padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        <strong>P2P Server:</strong> Running on port {st.session_state.p2p_port}<br>
        <strong>Active P2P Connections:</strong> {len(st.session_state.p2p_connections)}
    </div>
    """, unsafe_allow_html=True)
    
    # List active P2P connections
    if st.session_state.p2p_connections:
        st.markdown("<strong>Connected Peers:</strong>", unsafe_allow_html=True)
        for username in st.session_state.p2p_connections:
            st.markdown(f"- {username}", unsafe_allow_html=True)
    
    # Add a button to request P2P connections with all users
    if st.button("Request P2P with All Users", key="btn_request_all_p2p"):
        for username in st.session_state.online_users:
            if username != st.session_state.username and username not in st.session_state.p2p_connections:
                # Send P2P request to server
                try:
                    st.session_state.client_socket.sendall(f"P2P_REQUEST|{username}".encode())
                    print(f"Sent P2P request to {username}")
                except Exception as e:
                    print(f"Error sending P2P request to {username}: {e}")
        
        st.success("Sent P2P connection requests to all online users")
        time.sleep(1)
        st.rerun()

def display_p2p_troubleshooter():
    """Display P2P connection troubleshooting tools"""
    st.markdown("<div class='chat-header'><h4>🔧 P2P Troubleshooter</h4></div>", unsafe_allow_html=True)
    
    # Show local and public IP
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    st.markdown(f"""
    <div style='background-color: white; padding: 10px; border-radius: 10px; margin-bottom: 10px; font-size: 0.9em;'>
        <p><strong>Local IP:</strong> {local_ip}</p>
        <p><strong>Public IP:</strong> {public_ip}</p>
        <p><strong>P2P Port:</strong> {st.session_state.get('p2p_port', 'Not set')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Force P2P connection
    st.markdown("<h5>Force P2P Connection</h5>", unsafe_allow_html=True)
    online_users = [user for user in st.session_state.online_users if user != st.session_state.username]
    
    if online_users:
        selected_user = st.selectbox("Select user:", online_users, key="select_p2p_user")
        
        if st.button(f"Request P2P with {selected_user}", key=f"btn_force_p2p_{selected_user}"):
            try:
                st.session_state.client_socket.sendall(f"P2P_REQUEST|{selected_user}".encode())
                st.info(f"Sent P2P request to {selected_user}")
            except Exception as e:
                st.error(f"Failed to send P2P request: {e}")
    else:
        st.info("No users available for P2P connection")

def render_chat_interface():
    """Render the main chat interface"""
    # Process any pending messages
    while not st.session_state.message_queue.empty():
        msg = st.session_state.message_queue.get()
        process_message(msg)
    
    # Layout with sidebar for users and main area for chat
    col1, col2 = st.columns([1, 3])
    
    # User list in the sidebar
    with col1:
        st.markdown("<div class='chat-header'><h4>👥 Online Users</h4></div>", unsafe_allow_html=True)
        
        # Display broadcast option
        st.markdown(
            f"""
            <div class="user-card" style="background-color: {'#e6f7ff' if st.session_state.chat_with == 'broadcast' else 'white'}; cursor: pointer;" 
                 onclick="parent.document.querySelector('[data-testid=stFormSubmitButton]').click()">
                <strong>📢 Broadcast</strong><br>
                <small>Send to everyone</small>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        if st.button("Chat with Broadcast", key="btn_chat_broadcast"):
            st.session_state.chat_with = "broadcast"
            st.rerun()

    
        #Display online users
        if st.session_state.online_users:
            for user in st.session_state.online_users:
                if user != st.session_state.username:  # Don't show ourselves
                    # Determine if this user has a P2P connection
                    has_p2p = user in st.session_state.p2p_connections
                    
                    st.markdown(
                        f"""
                        <div class="user-card" style="background-color: {'#e6f7ff' if st.session_state.chat_with == user else 'white'}; cursor: pointer;"
                             onclick="parent.document.querySelector('[data-testid=stFormSubmitButton]').click()">
                            <strong>{user}</strong>
                            <span style="float: right; color: {'green' if has_p2p else 'gray'};">
                                {'🔗 P2P' if has_p2p else '🌐 Server'}
                            </span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    if st.button(f"Chat with {user}", key=f"btn_chat_{user}"):
                        st.session_state.chat_with = user
                        st.rerun()
        else:
            st.info("No other users online")
    

    # Auto-refresh toggle
    st.checkbox("Auto-refresh UI", value=st.session_state.auto_refresh, key="auto_refresh")    
    # Force refresh button
    if st.button("Force Refresh"):
        st.rerun()
    # Chat area in the main column
    with col2:
        if st.session_state.chat_with:
            # Chat header
            recipient = st.session_state.chat_with
            st.markdown(
                f"""
                <div class='chat-header'>
                    <h4>{'📢 Broadcast' if recipient == 'broadcast' else f'💬 Chat with {recipient}'}</h4>
                    <small>{'Message everyone' if recipient == 'broadcast' else f"{'🔗 P2P Connection' if recipient in st.session_state.p2p_connections else '🌐 Server Connection'}"}</small>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Chat messages container
            chat_container = st.container()
            with chat_container:
                # Display messages
                if recipient in st.session_state.messages and st.session_state.messages[recipient]:
                    
                    for sender, message in st.session_state.messages[recipient]:
                        current_time = time.strftime("%H:%M")
                        
                        if sender == st.session_state.username:
                            # Our message
                            st.markdown(
                                f"""
                                <div class='sender-msg'>
                                    <small style='opacity: 0.7;'>You</small><br>
                                    {message}
                                    <div class='message-time'>{current_time}</div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        else:
                            # Their message
                            st.markdown(
                                f"""
                                <div class='receiver-msg'>
                                    <small style='opacity: 0.7;'>{sender}</small><br>
                                    {message}
                                    <div class='message-time'>{current_time}</div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                # else:
                #     # Empty chat
                #     st.markdown(
                #         """
                #         <div class='empty-chat'>
                #             <div style='font-size: 40px; margin-bottom: 10px;'>💬</div>
                #             <div>No messages yet</div>
                #             <div>Start the conversation!</div>
                #         </div>
                #         """,
                #         unsafe_allow_html=True
                #     )
            
            # Message input
            with st.form(key=f"chat_form_{recipient}_{st.session_state.input_keys.get(recipient, 0)}", clear_on_submit=True):
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    message = st.text_input("Type a message", key=f"input_{recipient}_{st.session_state.input_keys.get(recipient, 0)}")
                
                with col2:
                    submit = st.form_submit_button("Send")
                
                if submit and message:
                    success, error = send_message(recipient, message)
                    if not success:
                        st.error(error)
                    else:
                        # Update input key to clear the field
                        if recipient not in st.session_state.input_keys:
                            st.session_state.input_keys[recipient] = 0
                        st.session_state.input_keys[recipient] += 1
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        # else:
        #     # No chat selected
        #     st.markdown(
        #         """
        #         <div class='empty-chat'>
        #             <div style='font-size: 40px; margin-bottom: 10px;'>👈</div>
        #             <div>Select a user from the list to start chatting</div>
        #         </div>
        #         """,
        #         unsafe_allow_html=True
        #     )

def render_gui():
    """Main function to render the chat application GUI"""
    # Apply custom CSS
    apply_custom_css()
    
    # Display app title
    st.markdown("<h1 class='app-title'>💬 Chat System</h1>", unsafe_allow_html=True)
    
    # Login section
    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                with st.form("login_form"):
                    st.markdown("<h3 style='text-align: center; color: #075E54;'>Welcome Back!</h3>", unsafe_allow_html=True)
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submit_button = st.form_submit_button("Login")
                    
                    if submit_button:
                        success, message = login(username, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            with tab2:
                with st.form("register_form"):
                    st.markdown("<h3 style='text-align: center; color: #075E54;'>Create Account</h3>", unsafe_allow_html=True)
                    new_username = st.text_input("Choose Username")
                    new_password = st.text_input("Choose Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    register_button = st.form_submit_button("Register")
                    
                    if register_button:
                        if not new_username or not new_password:
                            st.error("Username and password are required")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            success, message = register(new_username, new_password)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Mode selection screen
    elif not st.session_state.mode_selected:
        show_mode_selection_screen()
    
    # Main chat interface
    else:
        # Top bar with user info and logout button
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div style="padding: 10px; background-color: #075E54; color: white; border-radius: 10px;">
                <span class="status-indicator"></span> Connected as <strong>{st.session_state.username}</strong>
                <span style="margin-left: 20px;">Mode: <strong>{st.session_state.connection_type.upper()}</strong></span>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("Logout"):
                logout()
                st.rerun()
        
        # Main content
        tab1, tab2 = st.tabs(["Chat", "Settings"])
        
        with tab1:
            render_chat_interface()
        
        with tab2:
            # P2P settings
            display_p2p_status()
            
            # P2P troubleshooter
            display_p2p_troubleshooter()
            
            # # Auto-refresh toggle
            # st.checkbox("Auto-refresh UI", value=st.session_state.auto_refresh, key="auto_refresh")
            
            # # Force refresh button
            # if st.button("Force Refresh"):
            #     st.rerun()

# Auto-refresh function that can be called in a thread
def auto_refresh():
    try:
        if st.session_state.get("auto_refresh", False) and st.session_state.get("logged_in", False):
            time.sleep(0.5)  # Short delay
            st.rerun()
    except Exception as e:
        print(f"Auto-refresh error: {e}")
        time.sleep(1)  # Wait a bit before trying again











