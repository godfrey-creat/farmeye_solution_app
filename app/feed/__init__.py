from flask import Blueprint
from .routes import feed_bp

def init_app(app):
    """Initialize the feed module and register blueprints"""
    app.register_blueprint(feed_bp)