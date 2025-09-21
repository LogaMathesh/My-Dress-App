import os
import json
import faiss
import numpy as np
from embed_utils import embed_image, embed_text

INDEX_DIR = "indexes"
os.makedirs(INDEX_DIR, exist_ok=True)

def _user_paths(user_id):
    """Get file paths for user's index and metadata"""
    return (os.path.join(INDEX_DIR, f"{user_id}.index"),
            os.path.join(INDEX_DIR, f"{user_id}_meta.json"))

def _create_new_index(dim):
    """Create a new FAISS index with the given dimension"""
    return faiss.IndexIDMap(faiss.IndexFlatIP(dim))

def load_user_index(user_id, dim):
    """Load or create user's FAISS index and metadata"""
    idx_path, meta_path = _user_paths(user_id)
    if os.path.exists(idx_path) and os.path.exists(meta_path):
        idx = faiss.read_index(idx_path)
        meta = json.load(open(meta_path))
    else:
        idx = _create_new_index(dim)
        meta = {"_next_id": 1, "items": {}}
        faiss.write_index(idx, idx_path)
        json.dump(meta, open(meta_path, "w"))
    return idx, meta

def save_user_index(user_id, idx, meta):
    """Save user's FAISS index and metadata"""
    idx_path, meta_path = _user_paths(user_id)
    faiss.write_index(idx, idx_path)
    json.dump(meta, open(meta_path, "w"))

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

def query_user(user_id, text_query, top_k=3):
    """Query user's index with text and return similar images"""
    vec = embed_text(text_query)
    if vec is None:
        return []
    
    idx, meta = load_user_index(user_id, vec.shape[0])
    if idx.ntotal == 0:
        print(f"No images indexed for user {user_id}")
        return []
    
    print(f"Searching {idx.ntotal} indexed images for user {user_id}")
    
    # Search for more results to account for potential duplicates
    search_k = min(top_k * 2, idx.ntotal)
    D, I = idx.search(np.array([vec]), search_k)
    
    results = []
    seen_paths = set()  # Track seen image paths to avoid duplicates
    
    print(f"Raw search results: {len(D[0])} items")
    for i, (dist, rid) in enumerate(zip(D[0], I[0])):
        if int(rid) == -1: 
            continue
        item = meta["items"].get(str(int(rid)))
        if item:
            print(f"Result {i+1}: ID={rid}, Path={item['path']}, Score={dist:.3f}")
            if item["path"] not in seen_paths:
                seen_paths.add(item["path"])
                results.append({
                    "score": float(dist), 
                    "path": item["path"],
                    "style": item.get("style", "Unknown"),
                    "color": item.get("color", "Unknown")
                })
                print(f"Added unique result: {item['path']}")
                # Stop when we have enough unique results
                if len(results) >= top_k:
                    break
            else:
                print(f"Skipped duplicate: {item['path']}")
    
    print(f"Final results: {len(results)} unique images")
    return results
