import os
import datetime
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from PIL import Image
from werkzeug.utils import secure_filename
from transformers import pipeline

UPLOAD_FOLDER = 'uploaded_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

# PostgreSQL connection
conn = psycopg2.connect(
    dbname="loga", user="postgres", password="loga", host="localhost", port="5432"
)
cur = conn.cursor()

# Add favorite column to uploads table if it doesn't exist
try:
    cur.execute("ALTER TABLE uploads ADD COLUMN IF NOT EXISTS favorite BOOLEAN DEFAULT FALSE")
    conn.commit()
except Exception as e:
    print(f"Error adding favorite column: {e}")
    conn.rollback()

# Load zero-shot classification pipeline
classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")

# Define your categories for each attribute (you may adjust these based on your real use case)
POSITION_CATEGORIES = ['upper', 'lower', 'full']
STYLE_CATEGORIES = ['formal', 'traditional', 'casual',]
COLOR_CATEGORIES = ['red', 'blue', 'green', 'black', 'white', 'yellow', 'orange', 'purple', 'brown']

def classify_attribute(image, categories):
    # Use zero-shot classifier to get scores for categories, pick highest
    results = classifier(images=image, candidate_labels=categories)
    if results:
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        return sorted_results[0]['label']
    return 'unknown'

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    password = data['password']

    try:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return jsonify({"message": "Signup successful"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Username already exists or DB error"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()

        if user:
            return jsonify({"message": "Login successful", "user": username}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        conn.rollback()  # Rollback on error
        return jsonify({"error": "Database error", "details": str(e)}), 500


@app.route('/classify', methods=['POST'])
def classify():
    image_file = request.files.get('image')
    username = request.form.get('username')

    if not image_file or not username:
        return jsonify({'error': 'Image or username missing'}), 400

    image_bytes = image_file.read()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    # Check for duplicate image by hash & username
    cur.execute(
        "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
        (username, image_hash)
    )
    existing = cur.fetchone()
    if existing:
        # Compose image URL for frontend access
        image_url = f"http://localhost:5000/image/{os.path.basename(existing[0])}"
        return jsonify({
            'position': existing[1],
            'style': existing[2],
            'color': existing[3],
            'message': 'Duplicate image already uploaded.',
            'image_url': image_url
        })

    # Save image to disk
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(f"{username}_{timestamp}_{image_file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, 'wb') as f:
        f.write(image_bytes)

    # Open image for classification
    img = Image.open(file_path)

    # Classify each attribute separately
    position = classify_attribute(img, POSITION_CATEGORIES)
    style = classify_attribute(img, STYLE_CATEGORIES)
    color = classify_attribute(img, COLOR_CATEGORIES)

    # Save to DB
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
        print(f"Error fetching history: {e}")
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
    destination = data['destination']  # We treat this as style

    # Use the global cursor instead of creating a new one
    cur.execute("""
        SELECT DISTINCT ON (md5_hash) image_path, uploaded_at, style, position, md5_hash
        FROM uploads
        WHERE style = %s
        ORDER BY md5_hash, uploaded_at DESC
    """, (destination,))

    results = cur.fetchall()

    suggestions = [{
        'image_path': r[0],
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
        # Get current favorite status
        cur.execute("SELECT favorite FROM uploads WHERE id = %s AND username = %s", (upload_id, username))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'status': 'error', 'message': 'Upload not found'}), 404
        
        current_favorite = result[0] if result[0] is not None else False
        new_favorite = not current_favorite
        
        # Update favorite status
        cur.execute("UPDATE uploads SET favorite = %s WHERE id = %s AND username = %s", 
                   (new_favorite, upload_id, username))
        conn.commit()
        
        return jsonify({'status': 'success', 'favorite': new_favorite})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/check-duplicates', methods=['GET'])
def check_duplicates():
    """Check for duplicate entries in the database"""
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
    """Remove duplicate entries, keeping only the most recent one for each image"""
    try:
        # Delete duplicates keeping only the most recent entry for each image_path
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

if __name__ == '__main__':
    app.run(debug=True)
