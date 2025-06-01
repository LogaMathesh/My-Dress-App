from PIL import Image
from transformers import pipeline
from flask import Flask, jsonify, request
from flask_cors import CORS
import io
import psycopg2
import json
import os
from datetime import datetime
from flask import send_from_directory

UPLOAD_FOLDER = 'uploaded_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def connect_db():
    return psycopg2.connect(
        dbname="loga",
        user="postgres",
        password="loga",
        host="localhost",
        port="5432"
    )

model_name = "openai/clip-vit-large-patch14-336"
classifier = pipeline("zero-shot-image-classification", model=model_name, device="cpu")

DEFAULT_CATEGORIES = [
    'T-shirt/top', 'Trouser', 'Coat',
    'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot',
    'Formal wear', 'Casual wear', 'Sports wear', 'Traditional wear'
]

@app.route('/')
def home():
    return "Welcome to Fashion Classifier API"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    print("Received data:", data)

    if not data:
        return jsonify({"message": "Invalid data"}), 400

    username = data['username']
    password = data['password']

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        print("User already exists")
        return jsonify({"message": "User already exists"}), 409

    try:
        cur.execute(
            "INSERT INTO users (username, password, image_path) VALUES (%s, %s, %s)",
            (username, password, json.dumps([]))
        )
        conn.commit()
    except Exception as e:
        print("Database error:", e)
        return jsonify({"message": "Database error"}), 500
    finally:
        cur.close()
        conn.close()

    print("User registered successfully")
    return jsonify({"message": "User registered successfully"}), 200


@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    username = data['username']
    password = data['password']
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/upload_and_classify', methods=['POST'])
def upload_and_classify():
    try:
        if 'image' not in request.files or 'username' not in request.form:
            return jsonify({"error": "Image and username are required"}), 400

        username = request.form['username']
        image_file = request.files['image']

        if not image_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return jsonify({"error": "Invalid file type."}), 400

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{username}_{timestamp}_{image_file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        image_file.save(file_path)

        img = Image.open(file_path)
        results = classifier(images=img, candidate_labels=DEFAULT_CATEGORIES)
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        top_prediction = sorted_results[0] if sorted_results else {}

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT image_path FROM users WHERE username=%s", (username,))
        existing_data = cur.fetchone()

        image_data = {
            "file_path": file_path,
            "classification": top_prediction
        }

        updated_json = []
        if existing_data and existing_data[0]:
            updated_json = existing_data[0]
        updated_json.append(image_data)

        cur.execute("UPDATE users SET image_path = %s WHERE username = %s", (json.dumps(updated_json), username))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "top_prediction": top_prediction,
            "file_saved": file_path
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/get_user_images', methods=['GET'])
def get_user_images():
    username = request.args.get('username')
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT image_path FROM users WHERE username = %s", (username,))
    data = cur.fetchone()
    cur.close()
    conn.close()

    if data and data[0]:
        return jsonify({"username": username, "image_data": data[0]})
    else:
        return jsonify({"message": "No image data found"}), 404
@app.route('/uploaded_images/<path:filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
