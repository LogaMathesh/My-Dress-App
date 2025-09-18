import os
import datetime
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from PIL import Image
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import config
from gemini_client import gemini_classifier

UPLOAD_FOLDER = 'uploaded_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB upload limit
CORS(app)

# PostgreSQL connection
conn = psycopg2.connect(
    dbname=os.environ.get("DB_NAME", "loga"),
    user=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASSWORD", "loga"),
    host=os.environ.get("DB_HOST", "localhost"),
    port=os.environ.get("DB_PORT", "5432"),
)
cur = conn.cursor()

# Add favorite column to uploads table if it doesn't exist
try:
    cur.execute("ALTER TABLE uploads ADD COLUMN IF NOT EXISTS favorite BOOLEAN DEFAULT FALSE")
    conn.commit()
except Exception as e:
    print(f"Error adding favorite column: {e}")
    conn.rollback()

# Classification categories are now managed in config.py
# Gemini classifier is initialized in gemini_client.py

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def classify_dress_attributes(image):
    """Classify dress attributes using Gemini API."""
    try:
        if not gemini_classifier.is_configured():
            print("Gemini API not configured, using defaults")
            return {"position": "upper", "style": "casual", "color": "black"}
        
        return gemini_classifier.classify_dress_attributes(image)
    except Exception as e:
        print(f"Classification error: {e}")
        return {"position": "upper", "style": "casual", "color": "black"}


# This function is replaced by classify_dress_attributes which uses Gemini API


# Enhanced prompts are now handled by the Gemini API in gemini_client.py


# This function is replaced by classify_dress_attributes using Gemini API


# This function is replaced by Gemini API classification logic


# This function is replaced by Gemini API classification logic


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    password = data['password']

    try:
        password_hash = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        return jsonify({"message": "Signup successful", "user": username}), 200
    except Exception:
        conn.rollback()
        return jsonify({"error": "Username already exists or DB error"}), 400


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cur.fetchone()

        if result and check_password_hash(result[0], password):
            return jsonify({"message": "Login successful", "user": username}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500


@app.route('/classify', methods=['POST'])
def classify():
    image_file = request.files.get('image')
    username = request.form.get('username')

    if not image_file or not username:
        return jsonify({'error': 'Image or username missing'}), 400

    if not allowed_file(image_file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    image_bytes = image_file.read()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    # Check duplicates
    cur.execute(
        "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
        (username, image_hash)
    )
    existing = cur.fetchone()
    if existing:
        image_url = f"http://localhost:5000/image/{os.path.basename(existing[0])}"
        return jsonify({
            'position': existing[1],
            'style': existing[2],
            'color': existing[3],
            'message': 'Duplicate image already uploaded.',
            'image_url': image_url
        })

    # Save new image
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(f"{username}_{timestamp}_{image_file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, 'wb') as f:
        f.write(image_bytes)

    try:
        img = Image.open(file_path)
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Invalid image file'}), 400

    # Use Gemini API for classification
    classification = classify_dress_attributes(img)
    position = classification["position"]
    style = classification["style"]
    color = classification["color"]

    cur.execute(
        "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (username, file_path, position, style, color, image_hash, datetime.datetime.now())
    )
    conn.commit()

    image_url = f"http://localhost:5000/image/{filename}"
    return jsonify({
        'position': position,
        'style': style,
        'color': color,
        'image_url': image_url
    })


@app.route('/history/<username>', methods=['GET'])
def get_history(username):
    try:
        cur.execute(
            "SELECT id, image_path, position, style, color, uploaded_at, favorite FROM uploads WHERE username = %s ORDER BY uploaded_at DESC",
            (username,)
        )
        uploads = cur.fetchall()

        results = []
        for upload in uploads:
            results.append({
                'id': upload[0],
                'image_url': f"http://localhost:5000/image/{os.path.basename(upload[1])}",
                'position': upload[2],
                'style': upload[3],
                'color': upload[4],
                'uploaded_at': upload[5].isoformat(),
                'favorite': upload[6] if upload[6] is not None else False
            })

        return jsonify(results)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/delete_upload', methods=['POST'])
def delete_upload():
    data = request.get_json()
    upload_id = data.get('upload_id')

    try:
        cur.execute("SELECT image_path FROM uploads WHERE id = %s", (upload_id,))
        img = cur.fetchone()
        if img:
            image_path = img[0]
            if os.path.exists(image_path):
                os.remove(image_path)

        cur.execute("DELETE FROM uploads WHERE id = %s", (upload_id,))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/image/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/get-suggestions', methods=['POST'])
def get_suggestions():
    data = request.json
    destination = data['destination']
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    cur.execute("""
        SELECT DISTINCT ON (md5_hash) image_path, uploaded_at, style, position, md5_hash
        FROM uploads
        WHERE style = %s AND username = %s
        ORDER BY md5_hash, uploaded_at DESC
    """, (destination, username))

    results = cur.fetchall()

    suggestions = [{
        'image_url': f"http://localhost:5000/image/{os.path.basename(r[0])}",
        'uploaded_at': r[1],
        'style': r[2],
        'position': r[3]
    } for r in results]

    return jsonify({'suggestions': suggestions})


@app.route('/uploaded_images/<path:filename>')
def serve_uploaded_image(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'uploaded_images'), filename)


@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json()
    upload_id = data.get('upload_id')
    username = data.get('username')

    try:
        cur.execute("SELECT favorite FROM uploads WHERE id = %s AND username = %s", (upload_id, username))
        result = cur.fetchone()

        if not result:
            return jsonify({'status': 'error', 'message': 'Upload not found'}), 404

        current_favorite = result[0] if result[0] is not None else False
        new_favorite = not current_favorite

        cur.execute("UPDATE uploads SET favorite = %s WHERE id = %s AND username = %s",
                   (new_favorite, upload_id, username))
        conn.commit()

        return jsonify({'status': 'success', 'favorite': new_favorite})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/check-duplicates', methods=['GET'])
def check_duplicates():
    try:
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


@app.route('/clean-duplicates', methods=['POST'])
def clean_duplicates():
    try:
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
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/test-classification', methods=['POST'])
def test_classification():
    """Test Gemini API classification."""
    image_file = request.files.get('image')
    
    if not image_file:
        return jsonify({'error': 'Image missing'}), 400
    
    if not allowed_file(image_file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400
    
    try:
        # Save temporary image for testing
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"test_{timestamp}_{secure_filename(image_file.filename)}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_file.read())
        
        img = Image.open(file_path)
        
        # Test Gemini classification
        start_time = datetime.datetime.now()
        classification = classify_dress_attributes(img)
        time_taken = (datetime.datetime.now() - start_time).total_seconds()
        
        # Clean up test file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'status': 'success',
            'result': {
                'position': classification["position"],
                'style': classification["style"],
                'color': classification["color"],
                'time_seconds': time_taken,
                'method': 'Gemini API classification'
            },
            'api_configured': gemini_classifier.is_configured()
        })
        
    except Exception as e:
        # Clean up on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Removed: This function was specific to CLIP model comparison


# This endpoint is now redundant since /classify uses Gemini API


# Configuration endpoints for API key management
@app.route('/config/api-key', methods=['POST'])
def set_api_key():
    """Set Gemini API key."""
    data = request.get_json()
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400
    
    try:
        success = config.set_gemini_api_key(api_key)
        if success:
            # Reinitialize classifier with new API key
            gemini_classifier.__init__()
            return jsonify({
                'status': 'success',
                'message': 'API key configured successfully',
                'configured': gemini_classifier.is_configured()
            })
        else:
            return jsonify({'error': 'Failed to save API key'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/config/status', methods=['GET'])
def get_config_status():
    """Get configuration status."""
    return jsonify({
        'gemini_configured': config.is_configured(),
        'model': config.get_gemini_model(),
        'categories': config.get_classification_categories()
    })


@app.route('/config/test-connection', methods=['POST'])
def test_gemini_connection():
    """Test Gemini API connection."""
    try:
        success, message = gemini_classifier.test_connection()
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message,
            'configured': gemini_classifier.is_configured()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'configured': False
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
