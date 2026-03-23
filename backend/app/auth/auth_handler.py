"""
Authentication module for user signup, login, and password hashing.
"""

from typing import Optional, Dict
from passlib.hash import bcrypt

from app.database.db import create_user, get_user_by_username


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.verify(password, password_hash)


def signup(username: str, password: str) -> Dict:
    """
    Register a new user.
    
    Returns:
        {"success": True, "user_id": int} on success
        {"success": False, "error": str} on failure
    """
    # Validate input
    if not username or len(username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters"}
    
    if not password or len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters"}
    
    # Check if user exists
    existing = get_user_by_username(username)
    if existing:
        return {"success": False, "error": "Username already exists"}
    
    # Create user
    password_hash = hash_password(password)
    user_id = create_user(username, password_hash)
    
    if user_id:
        return {"success": True, "user_id": user_id}
    else:
        return {"success": False, "error": "Failed to create user"}


def login(username: str, password: str) -> Dict:
    """
    Authenticate a user.
    
    Returns:
        {"success": True, "user_id": int, "username": str} on success
        {"success": False, "error": str} on failure
    """
    if not username or not password:
        return {"success": False, "error": "Username and password required"}
    
    # Get user
    user = get_user_by_username(username)
    if not user:
        return {"success": False, "error": "Invalid username or password"}
    
    # Verify password
    if not verify_password(password, user["password_hash"]):
        return {"success": False, "error": "Invalid username or password"}
    
    return {
        "success": True,
        "user_id": user["id"],
        "username": user["username"]
    }
