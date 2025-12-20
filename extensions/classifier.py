"""
Image classification model initialization.
"""
from transformers import pipeline
from flask import current_app
import threading

_classifier = None
_lock = threading.Lock()

def get_classifier():
    """Get or initialize the classifier (lazy loading)"""
    global _classifier
    
    if _classifier is None:
        with _lock:
            if _classifier is None:
                try:
                    from flask import has_app_context, current_app
                    if has_app_context():
                        model_name = current_app.config.get('CLASSIFICATION_MODEL', 'openai/clip-vit-base-patch32')
                        logger = current_app.logger
                    else:
                        from config import Config
                        model_name = Config.CLASSIFICATION_MODEL
                        logger = None
                    
                    _classifier = pipeline("zero-shot-image-classification", model=model_name)
                    if logger:
                        logger.info(f"✅ Classifier loaded: {model_name}")
                    else:
                        print(f"✅ Classifier loaded: {model_name}")
                except Exception as e:
                    if logger:
                        logger.error(f"❌ Failed to load classifier: {e}")
                    else:
                        print(f"❌ Failed to load classifier: {e}")
                    raise
    
    return _classifier
