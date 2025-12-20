"""
Image suggestion routes.
"""
from flask import Blueprint, request, jsonify
from services.image_service import ImageService

suggestions_bp = Blueprint('suggestions', __name__)

@suggestions_bp.route('/get-suggestions', methods=['POST'])
def get_suggestions():
    """Get image suggestions based on destination/style"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    destination = data.get('destination')
    username = data.get('username')
    
    if not destination:
        return jsonify({'error': 'Destination is required'}), 400
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    try:
        suggestions = ImageService.get_suggestions(username, destination)
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500





