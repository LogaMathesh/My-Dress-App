"""
ChromaDB vector database service for image embeddings.
Handles per-user collections for image search and chatbot functionality.
"""
import os
import sys
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from flask import current_app
import threading

# Add parent directory to path for embed_utils import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from embed_utils import embed_image, embed_text

# Thread-safe singleton for ChromaDB client
_client = None
_client_lock = threading.Lock()
_persist_directory = None

def get_chroma_client():
    """Get or create ChromaDB client (singleton)"""
    global _client, _persist_directory
    
    if _client is not None:
        return _client
    
    with _client_lock:
        if _client is not None:
            return _client
        
        # Get persist directory from config or use default
        try:
            from flask import current_app
            base_dir = current_app.config.get('INDEX_DIR', 'indexes')
        except:
            from config import Config
            base_dir = Config.INDEX_DIR
        
        _persist_directory = os.path.join(base_dir, 'chroma_db')
        os.makedirs(_persist_directory, exist_ok=True)
        
        # Create ChromaDB client with persistence
        _client = chromadb.PersistentClient(
            path=_persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        return _client


def get_user_collection(user_id: str, create_if_not_exists: bool = True):
    """
    Get or create a ChromaDB collection for a user.
    
    Args:
        user_id: User identifier
        create_if_not_exists: Whether to create collection if it doesn't exist
        
    Returns:
        ChromaDB Collection object or None
    """
    try:
        client = get_chroma_client()
        collection_name = f"user_{user_id}_images"
        
        try:
            collection = client.get_collection(name=collection_name)
            return collection
        except Exception:
            if create_if_not_exists:
                # Create new collection
                collection = client.create_collection(
                    name=collection_name,
                    metadata={"user_id": user_id, "type": "image_embeddings"}
                )
                return collection
            else:
                return None
    except Exception as e:
        print(f"Error getting/creating collection for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def add_image_to_vector_db(
    user_id: str,
    image_path: str,
    style: Optional[str] = None,
    color: Optional[str] = None
) -> Optional[str]:
    """
    Add an image to the user's vector database.
    
    Args:
        user_id: User identifier
        image_path: Path to the image file
        style: Style classification (optional)
        color: Color classification (optional)
        
    Returns:
        Document ID if successful, None otherwise
    """
    try:
        # Generate embedding for the image
        embedding = embed_image(image_path)
        if embedding is None:
            print(f"Failed to generate embedding for image: {image_path}")
            return None
        
        # Get user's collection
        collection = get_user_collection(user_id, create_if_not_exists=True)
        
        # Check if image already exists (by path)
        try:
            existing = collection.get(
                where={"image_path": image_path},
                limit=1
            )
            if existing and existing.get('ids') and len(existing['ids']) > 0:
                print(f"Image already indexed: {image_path}")
                return existing['ids'][0]
        except Exception as e:
            # If query fails, continue with adding
            print(f"Note: Could not check for existing image (will add new): {e}")
            pass
        
        # Generate unique ID for this image
        import hashlib
        image_id = hashlib.md5(image_path.encode()).hexdigest()
        
        # Prepare metadata
        metadata = {
            "image_path": image_path,
            "style": style or "Unknown",
            "color": color or "Unknown"
        }
        
        # Add to collection
        collection.add(
            ids=[image_id],
            embeddings=[embedding.tolist()],
            metadatas=[metadata]
        )
        
        print(f"Successfully indexed image: {image_path} for user: {user_id}")
        return image_id
        
    except Exception as e:
        print(f"Error adding image to vector DB: {e}")
        import traceback
        traceback.print_exc()
        return None


def query_vector_db(
    user_id: str,
    query_text: str,
    top_k: int = 3
) -> List[Dict]:
    """
    Query user's vector database with text.
    
    Args:
        user_id: User identifier
        query_text: Text query to search for
        top_k: Number of results to return
        
    Returns:
        List of result dictionaries with 'path', 'style', 'color', 'score'
    """
    try:
        # Generate text embedding
        query_embedding = embed_text(query_text)
        if query_embedding is None:
            print(f"Failed to generate embedding for query: {query_text}")
            return []
        
        # Get user's collection
        collection = get_user_collection(user_id, create_if_not_exists=False)
        if collection is None:
            print(f"No collection found for user: {user_id}")
            return []
        
        # Query the collection
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k * 2, collection.count()),  # Get more to filter duplicates
            include=['metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        seen_paths = set()
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, (doc_id, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                image_path = metadata.get('image_path', '')
                
                # Skip duplicates
                if image_path in seen_paths:
                    continue
                
                seen_paths.add(image_path)
                
                formatted_results.append({
                    'path': image_path,
                    'style': metadata.get('style', 'Unknown'),
                    'color': metadata.get('color', 'Unknown'),
                    'score': float(1.0 - distance)  # Convert distance to similarity score
                })
                
                # Stop when we have enough results
                if len(formatted_results) >= top_k:
                    break
        
        print(f"Found {len(formatted_results)} results for query: {query_text}")
        return formatted_results
        
    except Exception as e:
        print(f"Error querying vector DB: {e}")
        import traceback
        traceback.print_exc()
        return []


def delete_user_collection(user_id: str) -> bool:
    """
    Delete a user's collection (for cleanup).
    
    Args:
        user_id: User identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_chroma_client()
        collection_name = f"user_{user_id}_images"
        client.delete_collection(name=collection_name)
        return True
    except Exception as e:
        print(f"Error deleting collection for user {user_id}: {e}")
        return False


def get_collection_count(user_id: str) -> int:
    """
    Get the number of images in a user's collection.
    
    Args:
        user_id: User identifier
        
    Returns:
        Number of images indexed
    """
    try:
        collection = get_user_collection(user_id, create_if_not_exists=False)
        if collection is None:
            return 0
        return collection.count()
    except Exception as e:
        print(f"Error getting collection count: {e}")
        return 0

