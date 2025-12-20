"""
Admin and utility routes.
"""
from flask import Blueprint, request, jsonify, current_app
from extensions.db import get_db
from services.image_service import ImageService
import os

# Lazy import to avoid loading CLIP model at startup
def _get_add_image_function():
    """Lazy import of add_image_for_user to avoid loading CLIP model at startup"""
    try:
        from per_user_index import add_image_for_user
        return add_image_for_user
    except ImportError as e:
        if hasattr(current_app, 'logger'):
            current_app.logger.warning(f"Could not import per_user_index: {e}")
        return None

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/check-duplicates', methods=['GET'])
def check_duplicates():
    """Check for duplicate images in database"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT image_path, COUNT(*) as count
                FROM uploads
                GROUP BY image_path
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """)
            duplicates = cur.fetchall()
            
            if duplicates:
                return jsonify({
                    'status': 'found',
                    'duplicates': [{'image_path': d[0], 'count': d[1]} for d in duplicates]
                })
            else:
                return jsonify({'status': 'clean', 'message': 'No duplicates found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/clean-duplicates', methods=['POST'])
def clean_duplicates():
    """Clean duplicate images from database"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM uploads 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM uploads 
                    GROUP BY image_path
                )
            """)
            deleted_count = cur.rowcount
            conn.commit()
            return jsonify({
                'status': 'success',
                'message': f'Removed {deleted_count} duplicate entries'
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/index-existing-images', methods=['POST'])
def index_existing_images():
    """Index all existing images for a user in the chatbot system"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        # Get all existing uploads for the user
        uploads = ImageService.get_all_user_images(username)
        
        # Lazy import chatbot function
        add_image_for_user = _get_add_image_function()
        if add_image_for_user is None:
            return jsonify({
                'error': 'Chatbot service not available (model not loaded)',
                'message': 'Cannot index images - CLIP model is not loaded'
            }), 503
        
        indexed_count = 0
        errors = []
        
        for image_path, position, style, color in uploads:
            if os.path.exists(image_path):
                try:
                    add_image_for_user(username, image_path, style, color)
                    indexed_count += 1
                except Exception as e:
                    errors.append(f"Failed to index {os.path.basename(image_path)}: {str(e)}")
        
        return jsonify({
            'message': f'Indexed {indexed_count} images for chatbot',
            'indexed_count': indexed_count,
            'total_images': len(uploads),
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500


@admin_bp.route('/test-classification', methods=['POST'])
def test_classification():
    """Test different classification methods for comparison"""
    from services.classification_service import ClassificationService
    from utils.file_utils import allowed_file, save_image_file
    from utils.image_utils import validate_image
    from flask import current_app
    import datetime
    from werkzeug.utils import secure_filename
    
    image_file = request.files.get('image')
    
    if not image_file:
        return jsonify({'error': 'Image missing'}), 400
    
    from config import Config
    if not allowed_file(image_file.filename, Config.ALLOWED_EXTENSIONS):
        return jsonify({'error': 'Unsupported file type'}), 400
    
    try:
        # Save temporary image for testing
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"test_{timestamp}_{secure_filename(image_file.filename)}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        image_file.save(file_path)
        img = validate_image(file_path)
        
        if not img:
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': 'Invalid image file'}), 400
        
        # Test classification
        start_time = datetime.datetime.now()
        classification = ClassificationService.classify_all_attributes(img)
        time_taken = (datetime.datetime.now() - start_time).total_seconds()
        
        # Clean up test file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'status': 'success',
            'classification': classification,
            'time_seconds': time_taken
        })
        
    except Exception as e:
        # Clean up on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'status': 'error', 'message': str(e)}), 500

