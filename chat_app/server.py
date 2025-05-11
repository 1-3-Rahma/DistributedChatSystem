"""
Server for the chat application.
"""
import socket
import threading
import json
import os
import hashlib

# Server configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000

# Global variables
clients = {}  # Dictionary to store connected clients: {username: socket}
client_addresses = {}  # Dictionary to store client addresses: {username: (ip, port)}
client_p2p_ports = {}  # Dictionary to store client P2P ports: {username: port}
user_credentials = {}  # Dictionary to store user credentials: {username: password_hash}

def save_user_credentials():
    """Save user credentials to a file"""
    with open("user_credentials.json", "w") as f:
        json.dump(user_credentials, f)

def load_user_credentials():
    """Load user credentials from a file"""
    if os.path.exists("user_credentials.json"):
        with open("user_credentials.json", "r") as f:
            return json.load(f)
    return {}

def broadcast_online_users():
    """Broadcast the list of online users to all clients"""
    online_users = list(clients.keys())
    users_str = ",".join(online_users)
    
    for username, client_socket in clients.items():
        try:
            client_socket.sendall(f"USERS|{users_str}".encode())
        except:
            pass  # Handle failed sends silently

def broadcast_message(sender, message, exclude=None):
    """Broadcast a message to all connected clients except the sender"""
    for username, client_socket in clients.items():
        if username != exclude:
            try:
                client_socket.sendall(f"BROADCAST|{sender}|{message}".encode())
            except:
                pass  # Handle failed sends silently

def handle_client(client_socket, client_address):
    """Handle client connection"""
    print(f"[NEW CONNECTION] {client_address} connected.")
    
    # Wait for login or registration
    try:
        data = client_socket.recv(1024).decode()
        parts = data.split('|')
        
        if parts[0] == "LOGIN":
            # Login request: LOGIN|username|password_hash
            username, password_hash = parts[1], parts[2]
            
            # Check credentials
            if username in user_credentials and user_credentials[username] == password_hash:
                # Authentication successful
                client_socket.sendall("AUTH_SUCCESS".encode())
                
                # Register the client
                clients[username] = client_socket
                client_addresses[username] = client_address
                print(f"[+] {username} authenticated and connected from {client_address}")
                
                # Broadcast updated user list to all clients
                broadcast_online_users()
                
                # Notify all clients about the new user
                broadcast_message("SERVER", f"{username} has joined the chat", username)
            else:
                # Authentication failed
                client_socket.sendall("AUTH_FAILED".encode())
                client_socket.close()
                return
        
        elif parts[0] == "REGISTER":
            # New user registration: REGISTER|username|password_hash
            new_username, new_password_hash = parts[1], parts[2]
            if new_username not in user_credentials:
                user_credentials[new_username] = new_password_hash
                save_user_credentials()
                client_socket.sendall(f"SUCCESS|User {new_username} registered successfully".encode())
            else:
                client_socket.sendall(f"ERROR|Username {new_username} already exists".encode())
            client_socket.close()
            return
        
        else:
            # Unknown request
            client_socket.close()
            return
        
        # Main message handling loop
        username_for_loop = username  # Store username for use in the loop
        
        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                
                # Parse the message format
                parts = data.split('|', 2)
                
                if parts[0] == "DIRECT":
                    # Direct message: DIRECT|recipient|message
                    recipient, msg = parts[1], parts[2]
                    print(f"Direct message from {username_for_loop} to {recipient}: {msg[:30]}...")
                    
                    if recipient in clients:
                        try:
                            # Send message to the recipient
                            clients[recipient].sendall(f"DIRECT|{username_for_loop}|{msg}".encode())
                            print(f"Delivered message to {recipient}")
                        except Exception as e:
                            print(f"Error delivering message to {recipient}: {e}")
                            client_socket.sendall(f"ERROR|Could not deliver message to {recipient}".encode())
                    else:
                        client_socket.sendall(f"ERROR|User {recipient} not connected".encode())
                
                elif parts[0] == "BROADCAST":
                    # Broadcast message: BROADCAST|message
                    msg = parts[1]
                    print(f"Broadcast from {username_for_loop}: {msg[:30]}...")
                    
                    # Send to all clients
                    broadcast_message(username_for_loop, msg)
                
                elif parts[0] == "P2P_REQUEST":
                    # P2P connection request: P2P_REQUEST|target_username
                    target_username = parts[1]
                    print(f"P2P request from {username_for_loop} to {target_username}")
                    
                    if target_username in clients:
                        # Send request notification to target user
                        try:
                            clients[target_username].sendall(f"P2P_REQUEST_NOTIFICATION|{username_for_loop}".encode())
                            print(f"Sent P2P request notification to {target_username}")
                        except Exception as e:
                            print(f"Error sending P2P request notification: {e}")
                            client_socket.sendall(f"ERROR|Failed to send P2P request to {target_username}".encode())
                    else:
                        client_socket.sendall(f"ERROR|User {target_username} not available for P2P".encode())

                elif parts[0] == "P2P_ACCEPT":
                    # P2P accept: P2P_ACCEPT|requester_username
                    requester_username = parts[1]
                    print(f"P2P request accepted: {username_for_loop} accepted request from {requester_username}")
                    
                    # Get the P2P port of the accepting client
                    accepter_port = client_p2p_ports.get(username_for_loop, "0")
                    accepter_ip = client_addresses[username_for_loop][0]
                    
                    # Get the P2P port of the requesting client
                    requester_port = client_p2p_ports.get(requester_username, "0")
                    requester_ip = client_addresses[requester_username][0]
                    
                    print(f"Accepter info: {accepter_ip}:{accepter_port}")
                    print(f"Requester info: {requester_ip}:{requester_port}")
                    
                    # Send P2P info to both clients
                    try:
                        # Send accepter's info to requester
                        clients[requester_username].sendall(f"P2P_INFO|{username_for_loop}|{accepter_ip}|{accepter_port}".encode())
                        print(f"Sent accepter info to requester: {accepter_ip}:{accepter_port}")
                        
                        # Send requester's info to accepter
                        clients[username_for_loop].sendall(f"P2P_INFO|{requester_username}|{requester_ip}|{requester_port}".encode())
                        print(f"Sent requester info to accepter: {requester_ip}:{requester_port}")
                        
                        print(f"Sent P2P connection info to both users")
                    except Exception as e:
                        print(f"Error sending P2P connection info: {e}")

                elif parts[0] == "P2P_REJECT":
                    # P2P reject: P2P_REJECT|requester_username
                    requester_username = parts[1]
                    print(f"P2P request rejected: {username_for_loop} rejected request from {requester_username}")
                    
                    # Notify requester of rejection
                    try:
                        clients[requester_username].sendall(f"P2P_REJECTED|{username_for_loop}".encode())
                        print(f"Sent P2P rejection notification to {requester_username}")
                        
                        # After a short delay, allow the requester to send another request
                        # This is handled client-side, but we log it here for clarity
                        print(f"User {requester_username} can send another P2P request to {username_for_loop}")
                    except Exception as e:
                        print(f"Error sending P2P rejection notification: {e}")

                elif parts[0] == "P2P_PORT":
                    # Store the client's P2P port
                    p2p_port = parts[1]
                    client_p2p_ports[username_for_loop] = p2p_port
                    print(f"User {username_for_loop} registered P2P port: {p2p_port}")
                
                elif parts[0] == "P2P_ESTABLISHED":
                    # Client notifying that P2P connection was established
                    target_username = parts[1]
                    print(f"P2P connection established between {username_for_loop} and {target_username}")
                
                elif parts[0] == "UPDATE_MODE":
                    # Client updating their connection mode
                    target_username, mode = parts[1], parts[2]
                    print(f"User {username_for_loop} updated connection mode for {target_username} to {mode}")
                
            except Exception as e:
                print(f"Error handling client {username_for_loop}: {e}")
                break
        
        # Client disconnected
        print(f"[-] {username_for_loop} disconnected")
        
        # Remove client from dictionaries
        if username_for_loop in clients:
            del clients[username_for_loop]
        if username_for_loop in client_addresses:
            del client_addresses[username_for_loop]
        if username_for_loop in client_p2p_ports:
            del client_p2p_ports[username_for_loop]
        
        # Notify others that user has left
        broadcast_message("SERVER", f"{username_for_loop} has left the chat")
        
        # Broadcast updated user list
        broadcast_online_users()
        
    except Exception as e:
        print(f"Error in client handler: {e}")
    
    finally:
        # Close the socket
        try:
            client_socket.close()
        except:
            pass
        print(f"[-] Connection closed: {client_address}")

def start_server():
    """Start the chat server"""
    # Load user credentials
    global user_credentials
    user_credentials = load_user_credentials()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVER] Listening on {HOST}:{PORT}...")

    while True:
        try:
            client_socket, client_address = server.accept()
            threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True).start()
        except Exception as e:
            print(f"Error accepting connection: {e}")

if __name__ == "__main__":
    start_server()
