import os
import datetime
import hashlib
from flask import jsonify
from PIL import Image

from config.database import conn, cur
from config.settings import UPLOAD_FOLDER
from utils.file_utils import allowed_file
# from chatbot.indexer import add_image_for_user
# from ai.classifier import classify_all_attributes_efficient
from .utils import save_image_file


def add_image_for_user(user_id, image_path, style=None, color=None):
    """Add an image to user's index with optional metadata"""
    # Check if image is already indexed
    idx, meta = load_user_index(user_id, 512)  # Use default dimension for checking
    for item_id, item_data in meta["items"].items():
        if item_data["path"] == image_path:
            print(f"Image already indexed: {image_path}")
            return int(item_id)
    
    vec = embed_image(image_path)
    if vec is None:
        return None
    
    dim = vec.shape[0]
    idx, meta = load_user_index(user_id, dim)
    nid = meta["_next_id"]
    idx.add_with_ids(np.array([vec]), np.array([nid], dtype="int64"))
    
    # Store metadata including style and color if provided
    meta["items"][str(nid)] = {
        "path": image_path,
        "style": style,
        "color": color
    }
    meta["_next_id"] = nid + 1
    save_user_index(user_id, idx, meta)
    print(f"Indexed new image: {image_path} with ID {nid}")
    return nid

def classify_all_attributes_efficient(image):
    """Efficiently classify all attributes in a single CLIP call for better performance."""
    try:
        # Combine all categories into one comprehensive classification
        all_categories = []
        
        # Position categories
        all_categories.extend([
            "upper body shirt blouse top",
            "lower body pants skirt trousers", 
            "full body dress gown jumpsuit"
        ])
        
        # Style categories
        all_categories.extend([
            "formal business professional office",
            "traditional ethnic cultural heritage",
            "casual everyday relaxed comfortable"
        ])
        
        # Color categories
        all_categories.extend([
            "red clothing", "blue clothing", "green clothing",
            "black clothing", "white clothing", "yellow clothing",
            "orange clothing", "purple clothing", "brown clothing",
            "pink clothing", "gray clothing"
        ])
        
        # Single CLIP call for all categories
        results = classifier(images=image, candidate_labels=all_categories)
        
        if not results or len(results) == 0:
            # Return sensible defaults instead of unknown
            return {"position": "upper", "style": "casual", "color": "black"}
        
        # Sort by confidence score
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Initialize results with defaults instead of unknown
        classification = {"position": "upper", "style": "casual", "color": "black"}
        
        # Process results with very low threshold for better coverage
        for result in sorted_results:
            if result['score'] < 0.05:  # Very low threshold
                continue
                
            label = result['label'].lower()
            
            # Determine position with more flexible matching
            if any(word in label for word in ["upper", "shirt", "blouse", "top", "t-shirt", "garment"]):
                classification["position"] = "upper"
            elif any(word in label for word in ["lower", "pants", "skirt", "trousers", "jeans", "garment"]):
                classification["position"] = "lower"
            elif any(word in label for word in ["full", "dress", "gown", "jumpsuit", "onesie", "garment"]):
                classification["position"] = "full"
            
            # Determine style with more flexible matching
            if any(word in label for word in ["formal", "business", "professional", "office", "corporate", "attire"]):
                classification["style"] = "formal"
            elif any(word in label for word in ["traditional", "ethnic", "cultural", "heritage", "ceremonial"]):
                classification["style"] = "traditional"
            elif any(word in label for word in ["casual", "everyday", "relaxed", "comfortable", "street", "outfit"]):
                classification["style"] = "casual"
            
            # Determine color with more flexible matching
            color_map = {
                "red": "red", "blue": "blue", "green": "green",
                "black": "black", "white": "white", "yellow": "yellow",
                "orange": "orange", "purple": "purple", "brown": "brown",
                "pink": "pink", "gray": "gray"
            }
            for color, clean_color in color_map.items():
                if color in label:
                    classification["color"] = clean_color
                    break
        
        return classification
        
    except Exception as e:
        print(f"Multi-attribute classification error: {e}")
        # Return sensible defaults instead of unknown
        return {"position": "upper", "style": "casual", "color": "black"}


def classify_image_service(request):
    image_file = request.files.get("image")
    username = request.form.get("username")

    if not image_file or not username:
        return jsonify({"error": "Image or username missing"}), 400

    if not allowed_file(image_file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    image_bytes = image_file.read()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    # 🔁 Duplicate check
    cur.execute(
        """
        SELECT image_path, position, style, color
        FROM uploads
        WHERE username = %s AND md5_hash = %s
        """,
        (username, image_hash)
    )

    existing = cur.fetchone()
    if existing:
        image_url = f"http://localhost:5000/image/{os.path.basename(existing[0])}"
        return jsonify({
            "position": existing[1],
            "style": existing[2],
            "color": existing[3],
            "message": "Duplicate image already uploaded.",
            "image_url": image_url
        })

    # 💾 Save image
    filename, file_path = save_image_file(username, image_file, image_bytes)

    try:
        img = Image.open(file_path)
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": "Invalid image file"}), 400

    # 🧠 Classification
    classification = classify_all_attributes_efficient(img)
    position = classification["position"]
    style = classification["style"]
    color = classification["color"]

    # 🗃️ DB insert
    cur.execute(
        """
        INSERT INTO uploads
        (username, image_path, position, style, color, md5_hash, uploaded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (username, file_path, position, style, color, image_hash, datetime.datetime.now())
    )
    conn.commit()

    # 🤖 Chatbot indexing
    try:
        add_image_for_user(username, file_path, style, color)
    except Exception as e:
        print("Chatbot indexing failed:", e)

    image_url = f"http://localhost:5000/image/{filename}"

    return jsonify({
        "position": position,
        "style": style,
        "color": color,
        "image_url": image_url
    })
