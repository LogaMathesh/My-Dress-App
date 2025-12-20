"""
Image history and management routes.
"""
from flask import Blueprint, request, jsonify
from services.image_service import ImageService

history_bp = Blueprint('history', __name__)

@history_bp.route('/history/<username>', methods=['GET'])
def get_history(username):
    """Get upload history for a user"""
    try:
        results = ImageService.get_user_history(username)
        return jsonify(results)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@history_bp.route('/delete_upload', methods=['POST'])
def delete_upload():
    """Delete an uploaded image"""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    upload_id = data.get('upload_id')
    username = data.get('username')
    
    if not upload_id or not username:
        return jsonify({'status': 'error', 'message': 'Upload ID and username required'}), 400
    
    try:
        success = ImageService.delete_image(upload_id, username)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Upload not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@history_bp.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    """Toggle favorite status for an image"""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    upload_id = data.get('upload_id')
    username = data.get('username')
    
    if not upload_id or not username:
        return jsonify({'status': 'error', 'message': 'Upload ID and username required'}), 400
    
    try:
        result = ImageService.toggle_favorite(upload_id, username)
        if result:
            return jsonify(result)
        else:
            return jsonify({'status': 'error', 'message': 'Upload not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500





