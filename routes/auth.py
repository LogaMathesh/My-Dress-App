"""
Authentication routes.
"""
from flask import Blueprint, request, jsonify
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User signup endpoint"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    success, message, status_code = AuthService.signup(username, password)
    
    if success:
        return jsonify({"message": message, "user": username}), status_code
    else:
        return jsonify({"error": message}), status_code


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    success, message, status_code = AuthService.login(username, password)
    
    if success:
        return jsonify({"message": message, "user": username}), status_code
    else:
        return jsonify({"error": message}), status_code





