"""
Upload service for handling image uploads and processing.
"""
import os
from services.classification_service import ClassificationService
from services.image_service import ImageService
from utils.file_utils import save_image_file, allowed_file
from utils.image_utils import generate_image_hash, validate_image
from flask import current_app

# Lazy import to avoid loading CLIP model at startup
def _get_add_image_function():
    """Lazy import of add_image_for_user to avoid loading CLIP model at startup"""
    try:
        from per_user_index import add_image_for_user
        return add_image_for_user
    except ImportError as e:
        try:
            from flask import has_app_context, current_app
            if has_app_context():
                current_app.logger.warning(f"Could not import per_user_index: {e}")
            else:
                print(f"Warning: Could not import per_user_index: {e}")
        except:
            print(f"Warning: Could not import per_user_index: {e}")
        return None

class UploadService:
    """Service for handling image uploads"""
    
    @staticmethod
    def process_upload(file, username):
        """
        Process an image upload: validate, classify, and save.
        
        Args:
            file: FileStorage object from Flask
            username: Username
            
        Returns:
            dict: Result with classification and image URL, or error message
        """
        # Validate file
        if not file or not file.filename:
            return {'error': 'No file provided'}, 400
        
        if not allowed_file(file.filename):
            return {'error': 'Unsupported file type'}, 400
        
        # Read file bytes for hash calculation
        file.seek(0)
        image_bytes = file.read()
        file.seek(0)  # Reset for saving
        image_hash = generate_image_hash(image_bytes)
        
        # Check for duplicates
        existing = ImageService.check_duplicate(username, image_hash)
        if existing:
            filename = os.path.basename(existing['image_path'])
            return {
                'position': existing['position'],
                'style': existing['style'],
                'color': existing['color'],
                'message': 'Duplicate image already uploaded.',
                'image_url': f"http://{current_app.config['HOST']}:{current_app.config['PORT']}/image/{filename}"
            }, 200
        
        # Save file
        file_path, filename = save_image_file(file, username)
        if not file_path:
            return {'error': 'Failed to save file'}, 500
        
        # Validate image
        img = validate_image(file_path)
        if not img:
            # Clean up invalid file
            if os.path.exists(file_path):
                os.remove(file_path)
            return {'error': 'Invalid image file'}, 400
        
        # Classify image
        classification = ClassificationService.classify_all_attributes(img)
        
        # Save to database
        try:
            ImageService.save_image(
                username,
                file_path,
                classification['position'],
                classification['style'],
                classification['color'],
                image_hash
            )
        except Exception as e:
            current_app.logger.error(f"Error saving to database: {e}")
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            return {'error': 'Failed to save to database'}, 500
        
        # Index for chatbot (lazy import to avoid loading model at startup)
        # This is critical - images must be indexed automatically for chatbot to work
        try:
            add_image_func = _get_add_image_function()
            if add_image_func:
                image_id = add_image_func(
                    username,
                    file_path,
                    classification['style'],
                    classification['color']
                )
                if image_id:
                    try:
                        if hasattr(current_app, 'logger'):
                            current_app.logger.info(f"Image indexed for chatbot: {filename} (ID: {image_id})")
                    except:
                        print(f"Image indexed for chatbot: {filename} (ID: {image_id})")
                else:
                    try:
                        if hasattr(current_app, 'logger'):
                            current_app.logger.warning(f"Image indexing returned None for: {filename}")
                    except:
                        print(f"Warning: Image indexing returned None for: {filename}")
            else:
                try:
                    if hasattr(current_app, 'logger'):
                        current_app.logger.warning("Chatbot indexing not available (model not loaded)")
                except:
                    print("Warning: Chatbot indexing not available (model not loaded)")
        except Exception as e:
            import traceback
            try:
                if hasattr(current_app, 'logger'):
                    current_app.logger.warning(f"Failed to index image for chatbot: {e}")
                    current_app.logger.debug(traceback.format_exc())
            except:
                print(f"Warning: Failed to index image for chatbot: {e}")
                traceback.print_exc()
        
        # Return result
        return {
            'position': classification['position'],
            'style': classification['style'],
            'color': classification['color'],
            'image_url': f"http://{current_app.config['HOST']}:{current_app.config['PORT']}/image/{filename}"
        }, 200

