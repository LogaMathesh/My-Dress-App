from celery import Celery
from config import Config
import time

# Create Celery app
celery_app = Celery(
    "celery_worker",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND
)

# Optional configurations
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Example background task
@celery_app.task(name="process_image_task")
def process_image_task(image_path):
    """
    Dummy background image processing task.
    Replace this logic with your actual model inference or embedding generation.
    """
    print(f"[Celery] Started processing image: {image_path}")
    time.sleep(5)  # simulate a long-running task
    result = {"status": "completed", "image_path": image_path}
    print(f"[Celery] Finished processing image: {image_path}")
    return result



