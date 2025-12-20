"""
Application configuration settings.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey-change-in-production")
    UPLOAD_FOLDER = str(BASE_DIR / "uploaded_images")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB upload limit

    # Database configuration
    DB_NAME = os.getenv("DB_NAME", "loga")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "loga")
    DB_HOST = os.getenv("DB_HOST", "db")  # 'db' will be the PostgreSQL container name
    DB_PORT = os.getenv("DB_PORT", "5432") 
    # Celery configuration (Docker-aware)
    # When running via Docker Compose, Redis service will be reachable at hostname "redis"
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

    # Index directory
    INDEX_DIR = str(BASE_DIR / "indexes")

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Models
    CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "openai/clip-vit-base-patch32")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/clip-vit-large-patch14")

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
