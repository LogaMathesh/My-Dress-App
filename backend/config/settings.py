import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploaded_images")
MAX_CONTENT_LENGTH = 8 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
