"""
Chatbot routes for image search and indexing.
"""
from flask import Blueprint, request, jsonify, current_app
from utils.file_utils import allowed_file
from config import Config
from werkzeug.utils import secure_filename
import os
import uuid

# Lazy import to avoid loading CLIP model at startup
def _get_chatbot_functions():
    """Lazy import of chatbot functions to avoid loading CLIP model at startup"""
    try:
        from per_user_index import add_image_for_user, query_user
        return add_image_for_user, query_user
    except ImportError as e:
        if hasattr(current_app, 'logger'):
            current_app.logger.warning(f"Could not import chatbot functions: {e}")
        else:
            print(f"Warning: Could not import chatbot functions: {e}")
        return None, None

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chatbot/upload', methods=['POST'])
def chatbot_upload():
    """Upload image for chatbot indexing"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get user_id from request
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Get optional metadata
        style = request.form.get('style', 'Unknown')
        color = request.form.get('color', 'Unknown')
        
        # Get upload directory from config
        from flask import current_app
        upload_dir = current_app.config['UPLOAD_FOLDER']
        
        # Create user directory
        user_dir = os.path.join(upload_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(user_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Add to user's index (lazy import)
        add_image_for_user, _ = _get_chatbot_functions()
        if add_image_for_user is None:
            return jsonify({'error': 'Chatbot service not available (model not loaded)'}), 503
        
        nid = add_image_for_user(user_id, file_path, style, color)
        
        if nid is None:
            return jsonify({'error': 'Failed to process image'}), 500
        
        return jsonify({
            'message': 'Image uploaded and indexed successfully',
            'image_id': nid,
            'filename': unique_filename
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@chatbot_bp.route('/chatbot/query', methods=['POST'])
def chatbot_query():
    """Query chatbot for similar images"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        query_text = data.get('query', '').strip()
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        if not query_text:
            return jsonify({'error': 'Query text required'}), 400
        
        # Query user's index - limit to top 3 results (lazy import)
        _, query_user = _get_chatbot_functions()
        if query_user is None:
            return jsonify({'error': 'Chatbot service not available (model not loaded)'}), 503
        
        results = query_user(user_id, query_text, top_k=3)
        
        # Format results for frontend with additional deduplication
        formatted_results = []
        seen_urls = set()
        
        from flask import current_app
        base_url = f"http://{current_app.config['HOST']}:{current_app.config['PORT']}"
        
        for result in results:
            filename = os.path.basename(result['path'])
            image_url = f'{base_url}/image/{filename}'
            
            # Skip if we've already seen this URL
            if image_url not in seen_urls:
                seen_urls.add(image_url)
                formatted_results.append({
                    'url': image_url,
                    'style': result.get('style', 'Unknown'),
                    'color': result.get('color', 'Unknown'),
                    'score': result.get('score', 0.0)
                })
                
                # Stop at 3 results
                if len(formatted_results) >= 3:
                    break
        
        return jsonify({
            'results': formatted_results,
            'query': query_text,
            'count': len(formatted_results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Query failed: {str(e)}'}), 500


@chatbot_bp.route('/chatbot/status', methods=['GET'])
def chatbot_status():
    """Check chatbot service status"""
    return jsonify({
        'status': 'active',
        'message': 'Chatbot service is running'
    }), 200

