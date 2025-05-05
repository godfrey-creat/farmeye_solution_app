"""
FarmEye: Smart Farm Monitoring System
Configuration settings for different environments.

This module defines configuration classes for different deployment environments:
- Development: For local development with debugging enabled
- Testing: For running automated tests
- Production: For the live application with security features enabled
- Default: Fallback configuration
"""

import os
from datetime import timedelta

# Base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration class with settings common to all environments."""
    
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string-change-in-production'
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Admin account
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@farmeye.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'change-me-in-production'
    
    # JWT settings for API authentication
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@farmeye.com')
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Sensor data settings
    SENSOR_DATA_RETENTION_DAYS = 90  # How long to keep detailed sensor data
    
    # ML model settings
    ML_MODEL_PATH = os.path.join(basedir, 'app/ml/models')
    
    # Google Earth Engine settings (for satellite imagery)
    GEE_SERVICE_ACCOUNT = os.environ.get('GEE_SERVICE_ACCOUNT')
    GEE_PRIVATE_KEY = os.environ.get('GEE_PRIVATE_KEY')
    
    # Other settings
    ITEMS_PER_PAGE = 20  # Pagination default
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        # Create directories if they don't exist
        os.makedirs(os.path.join(basedir, 'app/static/uploads'), exist_ok=True)
        os.makedirs(os.path.join(basedir, 'app/ml/models'), exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f"sqlite:///{os.path.join(basedir, 'data-dev.sqlite')}"
    
    # Add any development-specific settings here
    TEMPLATES_AUTO_RELOAD = True


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        f"sqlite:///{os.path.join(basedir, 'data-test.sqlite')}"
    
    # Use a separate upload folder for tests
    UPLOAD_FOLDER = os.path.join(basedir, 'tests/uploads')
    
    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False
    
    # Use faster hashing for tests
    PASSWORD_HASH_METHOD = 'pbkdf2:sha256:1000'


class ProductionConfig(Config):
    """Production environment configuration."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(basedir, 'data.sqlite')}"
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    @classmethod
    def init_app(cls, app):
        """Initialize the application for production."""
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class DockerConfig(ProductionConfig):
    """Configuration for running in Docker containers."""
    
    @classmethod
    def init_app(cls, app):
        """Initialize the application for Docker deployment."""
        ProductionConfig.init_app(app)
        
        # Log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class HerokuConfig(ProductionConfig):
    """Configuration for Heroku deployment."""
    
    @classmethod
    def init_app(cls, app):
        """Initialize the application for Heroku deployment."""
        ProductionConfig.init_app(app)
        
        # Handle proxy server headers
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)
        
        # Log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


# Dictionary mapping configuration names to their classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
}