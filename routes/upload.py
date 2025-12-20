"""
Image upload and classification routes.
"""
from flask import Blueprint, request, jsonify, send_from_directory
from services.upload_service import UploadService
from async_tasks.tasks import process_bulk_images
from celery.result import AsyncResult
from flask import current_app
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/test', methods=['GET'])
def test_upload_endpoint():
    """Test endpoint to verify upload route is accessible"""
    return jsonify({
        'status': 'success',
        'message': 'Upload endpoint is working',
        'endpoint': '/upload-multiple'
    }), 200

@upload_bp.route('/classify', methods=['POST'])
def classify():
    """Classify a single image"""
    image_file = request.files.get('image')
    username = request.form.get('username')
    
    if not image_file or not username:
        return jsonify({'error': 'Image or username missing'}), 400
    
    result, status_code = UploadService.process_upload(image_file, username)
    return jsonify(result), status_code


@upload_bp.route('/upload-multiple', methods=['POST'])
def upload_multiple():
    """Upload multiple images asynchronously"""
    try:
        current_app.logger.info(f"Received upload request. Method: {request.method}")
        current_app.logger.info(f"Content-Type: {request.content_type}")
        current_app.logger.info(f"Form keys: {list(request.form.keys())}")
        current_app.logger.info(f"Files: {list(request.files.keys())}")
        
        username = request.form.get('username')
        files = request.files.getlist('images')
        
        current_app.logger.info(f"Username: {username}, Files count: {len(files) if files else 0}")
        
        if not username:
            current_app.logger.warning("No username provided")
            return jsonify({'error': 'Username is required'}), 400
        
        if not files or len(files) == 0:
            current_app.logger.warning("No files provided")
            return jsonify({'error': 'No files provided'}), 400
        
        # Prepare files for Celery (convert to base64 for JSON serialization)
        import base64
        file_infos = []
        for f in files:
            if f.filename:
                try:
                    file_content = f.read()
                    if len(file_content) == 0:
                        current_app.logger.warning(f"Empty file: {f.filename}")
                        continue
                    file_infos.append({
                        'filename': f.filename,
                        'content': base64.b64encode(file_content).decode('utf-8'),
                        'size': len(file_content)
                    })
                    current_app.logger.info(f"Added file: {f.filename}, size: {len(file_content)} bytes")
                except Exception as e:
                    current_app.logger.error(f"Error reading file {f.filename}: {e}")
                    continue
        
        if not file_infos:
            current_app.logger.warning("No valid files to upload")
            return jsonify({'error': 'No valid files to upload'}), 400
        
        current_app.logger.info(f"Prepared {len(file_infos)} files for processing")
        
        # Check if Celery is connected (non-blocking check)
        try:
            from async_tasks.tasks import celery_app
            # Try to inspect active tasks (this will fail if worker not connected)
            inspect = celery_app.control.inspect()
            if inspect:
                active = inspect.active()
                if active is None:
                    current_app.logger.warning("Celery worker may not be connected (no active workers found)")
                else:
                    current_app.logger.info("Celery connection verified")
            else:
                current_app.logger.warning("Could not create Celery inspector")
        except Exception as e:
            current_app.logger.warning(f"Celery connection check failed (will try anyway): {e}")
            # Don't fail here - let the task.delay() call fail if worker is not available
        
        # Start the task
        try:
            current_app.logger.info(f"Attempting to create Celery task for {len(file_infos)} files")
            task = process_bulk_images.delay(username, file_infos)
            current_app.logger.info(f"Task created successfully: {task.id}")
            
            return jsonify({
                'task_id': task.id,
                'message': f'Upload started for {len(file_infos)} image(s)',
                'total_files': len(file_infos),
                'status': 'started'
            }), 202
        except Exception as e:
            current_app.logger.error(f"Error starting upload task: {e}", exc_info=True)
            error_msg = str(e)
            if 'not connected' in error_msg.lower() or 'broker' in error_msg.lower():
                return jsonify({
                    'error': 'Celery worker not available. Please make sure Celery worker is running.',
                    'details': error_msg
                }), 503
            return jsonify({
                'error': f'Failed to start upload: {error_msg}',
                'details': str(e)
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Unexpected error in upload_multiple: {e}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@upload_bp.route('/upload-status/<task_id>', methods=['GET'])
def upload_status(task_id):
    """Get status of bulk upload task"""
    from async_tasks.tasks import celery_app
    try:
        current_app.logger.info(f"Checking status for task: {task_id}")
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state == 'PENDING':
            return jsonify({
                'status': 'pending', 
                'progress': 0, 
                'current': 0,
                'total': 0,
                'results': [],
                'message': 'Task is waiting to be processed'
            })
        elif task_result.state == 'PROGRESS':
            meta = task_result.info
            current = meta.get('current', 0)
            total = meta.get('total', 0)
            progress = int((current / total * 100)) if total > 0 else 0
            results = meta.get('results', [])
            
            # Count success/error/duplicate
            success_count = sum(1 for r in results if r.get('status') == 'success')
            error_count = sum(1 for r in results if r.get('status') == 'error')
            duplicate_count = sum(1 for r in results if r.get('status') == 'duplicate')
            
            return jsonify({
                'status': 'in_progress', 
                'progress': progress,
                'current': current,
                'total': total,
                'results': results,
                'success_count': success_count,
                'error_count': error_count,
                'duplicate_count': duplicate_count,
                'message': f'Processing {current} of {total} images...'
            })
        elif task_result.state == 'SUCCESS':
            result_data = task_result.result
            results = result_data.get('results', []) if isinstance(result_data, dict) else []
            
            # Count success/error/duplicate
            success_count = sum(1 for r in results if r.get('status') == 'success')
            error_count = sum(1 for r in results if r.get('status') == 'error')
            duplicate_count = sum(1 for r in results if r.get('status') == 'duplicate')
            
            return jsonify({
                'status': 'completed', 
                'progress': 100,
                'current': len(results),
                'total': len(results),
                'results': results,
                'success_count': success_count,
                'error_count': error_count,
                'duplicate_count': duplicate_count,
                'message': f'Completed: {success_count} successful, {error_count} errors, {duplicate_count} duplicates'
            })
        elif task_result.state == 'FAILURE':
            return jsonify({
                'status': 'failed', 
                'progress': 0,
                'current': 0,
                'total': 0,
                'results': [],
                'error': str(task_result.info) if task_result.info else 'Task failed',
                'message': 'Upload task failed'
            })
        else:
            return jsonify({
                'status': task_result.state.lower(),
                'progress': 0,
                'current': 0,
                'total': 0,
                'results': [],
                'message': f'Task status: {task_result.state}'
            })
    except Exception as e:
        current_app.logger.error(f"Error getting task status: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to get task status'
        }), 500


@upload_bp.route('/classify-async', methods=['POST'])
def classify_async():
    """Async classification endpoint"""
    username = request.form.get('username')
    files = request.files.getlist('image')
    
    if not username or not files:
        return jsonify({"status": "error", "message": "Missing username or files"}), 400
    
    # Prepare files for Celery
    file_infos = []
    for f in files:
        file_infos.append({
            'filename': f.filename,
            'content': f.read()
        })
    
    task = process_bulk_images.delay(username, file_infos)
    return jsonify({"status": "success", "task_id": task.id})


@upload_bp.route('/task-status/<task_id>')
def task_status(task_id):
    """Get async task status"""
    from async_tasks.tasks import celery_app
    task = celery_app.AsyncResult(task_id)
    
    if task.state == "PENDING":
        return jsonify({"status": "pending"})
    elif task.state == "SUCCESS":
        return jsonify({"status": "success", "result": task.result})
    elif task.state == "FAILURE":
        return jsonify({"status": "failure", "message": str(task.result)})
    else:
        return jsonify({"status": task.state})


@upload_bp.route('/image/<filename>')
def get_image(filename):
    """Serve uploaded images"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)


@upload_bp.route('/uploaded_images/<path:filename>')
def serve_uploaded_image(filename):
    """Serve uploaded images (alternative route)"""
    upload_folder = os.path.join(os.getcwd(), 'uploaded_images')
    return send_from_directory(upload_folder, filename)

