"""
Celery tasks for async image processing.
"""
import os
import datetime
import hashlib
from celery import Celery
from PIL import Image

# Import config for Celery setup
from config import Config

# Configure Celery
celery_app = Celery(
    'tasks',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND
)

# Update Celery config
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(bind=True)
def process_bulk_images(self, username, file_list):
    """
    Process multiple images asynchronously.
    
    Args:
        username: Username
        file_list: List of dicts with 'filename' and 'content' keys
        
    Returns:
        dict: Results with status and metadata for each image
    """
    # Lazy imports to avoid circular dependencies
    from services.classification_service import ClassificationService
    from services.image_service import ImageService
    from utils.file_utils import allowed_file
    from utils.image_utils import generate_image_hash, validate_image
    from per_user_index import add_image_for_user
    from config import Config
    import psycopg2
    
    results = []
    total = len(file_list)
    
    # Get database connection for Celery task (separate from Flask app context)
    db_conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT
    )
    db_cur = db_conn.cursor()
    
    try:
        for idx, file_info in enumerate(file_list):
            try:
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': idx + 1,
                        'total': total,
                        'results': results
                    }
                )
                
                filename = file_info.get('filename', 'unknown')
                # Decode base64 content if it's a string
                content_data = file_info.get('content', b'')
                if isinstance(content_data, str):
                    import base64
                    file_content = base64.b64decode(content_data)
                else:
                    file_content = content_data
                
                if not filename or not file_content:
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": "Invalid file data"
                    })
                    continue
                
                # Check file extension
                if not allowed_file(filename, Config.ALLOWED_EXTENSIONS):
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": "Unsupported file type"
                    })
                    continue
                
                # Generate file path
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                file_path = os.path.join(Config.UPLOAD_FOLDER, f"{username}_{timestamp}_{filename}")
                
                # Ensure directory exists
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                
                # Save file
                with open(file_path, "wb") as f:
                    f.write(file_content)
                
                # Validate image
                img = validate_image(file_path)
                if not img:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": "Invalid image file"
                    })
                    continue
                
                # Generate hash
                image_hash = generate_image_hash(file_content)
                
                # Check for duplicates (using direct DB connection)
                db_cur.execute(
                    "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
                    (username, image_hash)
                )
                existing = db_cur.fetchone()
                
                if existing:
                    # Clean up duplicate file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    existing_filename = os.path.basename(existing[0])
                    results.append({
                        "filename": filename,
                        "status": "duplicate",
                        "message": "Image already uploaded",
                        "image_url": f"http://{Config.HOST}:{Config.PORT}/image/{existing_filename}",
                        "position": existing[1],
                        "style": existing[2],
                        "color": existing[3]
                    })
                    continue
                
                # Classify image
                classification = ClassificationService.classify_all_attributes(img)
                
                # Save to database
                try:
                    db_cur.execute(
                        "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (username, file_path, classification['position'], classification['style'], classification['color'], image_hash, datetime.datetime.now())
                    )
                    db_conn.commit()
                except Exception as e:
                    db_conn.rollback()
                    # Clean up on error
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": f"Database error: {str(e)}"
                    })
                    continue
                
                # Index for chatbot (lazy import to avoid loading model at startup)
                # This is critical - images must be indexed for chatbot to work
                try:
                    # Lazy import to avoid loading CLIP model in Celery worker
                    from per_user_index import add_image_for_user
                    image_id = add_image_for_user(
                        username,
                        file_path,
                        classification['style'],
                        classification['color']
                    )
                    if image_id:
                        print(f"Successfully indexed image for chatbot: {filename} (ID: {image_id})")
                    else:
                        print(f"Warning: Image indexing returned None for: {filename}")
                except Exception as e:
                    # Log but don't fail the task - indexing is important but shouldn't block upload
                    import traceback
                    print(f"Warning: Failed to index image for chatbot: {e}")
                    traceback.print_exc()
                
                # Success
                results.append({
                    "filename": filename,
                    "status": "success",
                    "image_url": f"http://{Config.HOST}:{Config.PORT}/image/{os.path.basename(file_path)}",
                    "position": classification['position'],
                    "style": classification['style'],
                    "color": classification['color']
                })
                
            except Exception as e:
                results.append({
                    "filename": file_info.get('filename', 'unknown'),
                    "status": "error",
                    "message": str(e)
                })
    finally:
        # Close database connection
        db_cur.close()
        db_conn.close()
    
    return {'results': results}
