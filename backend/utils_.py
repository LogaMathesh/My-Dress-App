import os
import hashlib
from PIL import Image
import psycopg2
from per_user_index import add_image_for_user

# Upload folder
UPLOAD_FOLDER = 'uploaded_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Efficient classification (placeholder or copy your full function from app.py)
def classify_all_attributes_efficient(image):
    # Use your real classifier here or import if refactored
    return {"position": "upper", "style": "casual", "color": "black"}

# Postgres connection
conn = psycopg2.connect(
    dbname=os.environ.get("DB_NAME", "loga"),
    user=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASSWORD", "loga"),
    host=os.environ.get("DB_HOST", "localhost"),
    port=os.environ.get("DB_PORT", "5432"),
)
cur = conn.cursor()
