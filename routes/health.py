"""
Health check and test endpoints.
"""
from flask import Blueprint, jsonify
from flask import current_app

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'dress-app-backend',
        'message': 'Backend is running'
    }), 200

@health_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Backend is responding',
        'endpoint': '/test'
    }), 200





