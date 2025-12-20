from celery import Celery
from PIL import Image
import os
import time

# Configure Celery with Redis directly
app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Additional configuration
app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)

@app.task(bind=True)
def process_image(self, image_path, filename):
    """Process a single image"""
    try:
        print(f"Processing: {filename}")
        
        # Simulate processing
        time.sleep(2)
        
        # Open and process image
        img = Image.open(image_path)
        
        max_width = 800
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save processed image
        processed_dir = 'processed'
        os.makedirs(processed_dir, exist_ok=True)
        processed_path = os.path.join(processed_dir, f'processed_{filename}')
        img.save(processed_path, optimize=True, quality=85)
        
        print(f"Completed: {filename}")
        
        return {
            'status': 'success',
            'filename': filename,
            'processed_path': processed_path
        }
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        raise