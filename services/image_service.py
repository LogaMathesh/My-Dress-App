"""
Image service for database operations.
"""
import os
import datetime
from extensions.db import get_db
from flask import current_app, url_for

class ImageService:
    """Service for image-related database operations"""
    
    @staticmethod
    def check_duplicate(username, image_hash):
        """
        Check if an image with the same hash already exists for the user.
        
        Args:
            username: Username
            image_hash: MD5 hash of the image
            
        Returns:
            dict or None: Existing image data or None if not found
        """
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
                (username, image_hash)
            )
            existing = cur.fetchone()
            if existing:
                return {
                    'image_path': existing[0],
                    'position': existing[1],
                    'style': existing[2],
                    'color': existing[3]
                }
            return None
    
    @staticmethod
    def save_image(username, image_path, position, style, color, image_hash):
        """
        Save image metadata to database.
        
        Args:
            username: Username
            image_path: Path to the image file
            position: Position classification
            style: Style classification
            color: Color classification
            image_hash: MD5 hash of the image
            
        Returns:
            int: ID of the inserted record
        """
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (username, image_path, position, style, color, image_hash, datetime.datetime.now())
            )
            image_id = cur.fetchone()[0]
            # Context manager will commit automatically
            return image_id
    
    @staticmethod
    def get_user_history(username):
        """
        Get upload history for a user.
        
        Args:
            username: Username
            
        Returns:
            list: List of upload records
        """
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, image_path, position, style, color, uploaded_at, favorite FROM uploads WHERE username = %s ORDER BY uploaded_at DESC",
                (username,)
            )
            uploads = cur.fetchall()
            
            results = []
            for upload in uploads:
                filename = os.path.basename(upload[1])
                results.append({
                    'id': upload[0],
                    'image_url': f"http://{current_app.config['HOST']}:{current_app.config['PORT']}/image/{filename}",
                    'position': upload[2],
                    'style': upload[3],
                    'color': upload[4],
                    'uploaded_at': upload[5].isoformat() if upload[5] else None,
                    'favorite': upload[6] if upload[6] is not None else False
                })
            
            return results
    
    @staticmethod
    def delete_image(upload_id, username):
        """
        Delete an image and its database record.
        
        Args:
            upload_id: ID of the upload record
            username: Username (for security)
            
        Returns:
            bool: True if successful, False otherwise
        """
        with get_db() as conn:
            cur = conn.cursor()
            # Get image path
            cur.execute("SELECT image_path FROM uploads WHERE id = %s AND username = %s", (upload_id, username))
            result = cur.fetchone()
            
            if not result:
                return False
            
            image_path = result[0]
            
            # Delete file if it exists
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting file {image_path}: {e}")
            
            # Delete database record
            cur.execute("DELETE FROM uploads WHERE id = %s AND username = %s", (upload_id, username))
            # Context manager will commit automatically
            return True
    
    @staticmethod
    def toggle_favorite(upload_id, username):
        """
        Toggle favorite status for an image.
        
        Args:
            upload_id: ID of the upload record
            username: Username
            
        Returns:
            dict: {'success': bool, 'favorite': bool} or None if not found
        """
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT favorite FROM uploads WHERE id = %s AND username = %s", (upload_id, username))
            result = cur.fetchone()
            
            if not result:
                return None
            
            current_favorite = result[0] if result[0] is not None else False
            new_favorite = not current_favorite
            
            cur.execute("UPDATE uploads SET favorite = %s WHERE id = %s AND username = %s",
                       (new_favorite, upload_id, username))
            # Context manager will commit automatically
            
            return {'success': True, 'favorite': new_favorite}
    
    @staticmethod
    def get_suggestions(username, style):
        """
        Get image suggestions based on style.
        
        Args:
            username: Username
            style: Style to match
            
        Returns:
            list: List of suggested images
        """
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT ON (md5_hash) image_path, uploaded_at, style, position, md5_hash
                FROM uploads
                WHERE style = %s AND username = %s
                ORDER BY md5_hash, uploaded_at DESC
            """, (style, username))
            
            results = cur.fetchall()
            
            suggestions = []
            for r in results:
                filename = os.path.basename(r[0])
                suggestions.append({
                    'image_url': f"http://{current_app.config['HOST']}:{current_app.config['PORT']}/image/{filename}",
                    'uploaded_at': r[1].isoformat() if r[1] else None,
                    'style': r[2],
                    'position': r[3]
                })
            
            return suggestions
    
    @staticmethod
    def get_all_user_images(username):
        """
        Get all images for a user (for indexing).
        
        Args:
            username: Username
            
        Returns:
            list: List of (image_path, position, style, color) tuples
        """
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT image_path, position, style, color FROM uploads WHERE username = %s",
                (username,)
            )
            return cur.fetchall()

