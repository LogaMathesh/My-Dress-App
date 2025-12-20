import os
import datetime
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER
def save_image_file(username, image_file, image_bytes):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(f"{username}_{timestamp}_{image_file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return filename, file_path
