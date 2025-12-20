"""
Flask extensions initialization.
"""
from flask import Flask
from .db import init_db, get_db_connection
from .classifier import get_classifier

def init_extensions(app):
    """Initialize all Flask extensions"""
    # Initialize database connection
    init_db(app)
    
    # Classifier will be loaded lazily when needed
    # This avoids loading heavy models at startup
    pass

__all__ = ['init_extensions', 'get_db_connection', 'get_classifier']
