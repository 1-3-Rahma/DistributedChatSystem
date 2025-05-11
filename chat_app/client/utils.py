"""
Utility functions for the chat application.
"""
import hashlib
import requests
import socket

# Server connection details
SERVER_IP = 'localhost'
SERVER_PORT = 12345

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_password(password):
    """
    Validates password strength
    Returns (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and numbers"
    
    if not has_special:
        return False, "Password must contain at least one special character"
        
    return True, "Password is strong"

def get_public_ip():
    """Get the public IP address of this machine"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text
    except Exception as e:
        print(f"Error getting public IP: {e}")
        return None

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return "127.0.0.1"
