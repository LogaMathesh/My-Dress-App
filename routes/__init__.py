"""
Route blueprints.
"""
from flask import Blueprint

def register_blueprints(app):
    """Register all route blueprints"""
    from .health import health_bp
    from .auth import auth_bp
    from .upload import upload_bp
    from .history import history_bp
    from .suggestions import suggestions_bp
    from .chatbot import chatbot_bp
    from .admin import admin_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(suggestions_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(admin_bp)

