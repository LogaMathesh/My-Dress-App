"""
Authentication service.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from extensions.db import get_db
from flask import current_app

class AuthService:
    """Service for user authentication"""
    
    @staticmethod
    def signup(username, password):
        """
        Register a new user.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            tuple: (success: bool, message: str, status_code: int)
        """
        try:
            password_hash = generate_password_hash(password)
            
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hash))
                # Context manager will commit automatically
            
            return True, "Signup successful", 200
        except Exception as e:
            if hasattr(current_app, 'logger'):
                current_app.logger.error(f"Signup error: {e}")
            else:
                print(f"Signup error: {e}")
            # Check if it's a duplicate key error
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                return False, "Username already exists", 400
            return False, f"Database error: {str(e)}", 500
    
    @staticmethod
    def login(username, password):
        """
        Authenticate a user.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            tuple: (success: bool, message: str, status_code: int)
        """
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT password FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                
                if result and check_password_hash(result[0], password):
                    return True, "Login successful", 200
                else:
                    return False, "Invalid credentials", 401
        except Exception as e:
            if hasattr(current_app, 'logger'):
                current_app.logger.error(f"Login error: {e}")
            else:
                print(f"Login error: {e}")
            return False, f"Database error: {str(e)}", 500

