import os
from flask import Flask, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from .config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


@login_manager.unauthorized_handler
def unauthorized():
    from flask import request, jsonify, redirect, url_for

    if request.path.startswith("/api/"):
        return jsonify({"error": "Unauthorized", "message": "Please log in"}), 401
    return redirect(url_for("auth.login"))


mail = Mail()


def create_app(config_name=None):
    """Create and configure the Flask application"""
    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Initialize error handlers
    from . import errors

    errors.init_app(app)

    # Configure CORS
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            }
        },
    )

    def wind_direction(degrees):
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]

    # Register as a template filter
    app.jinja_env.globals.update(wind_direction=wind_direction)

    # Register blueprints
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    from .admin import admin as admin_blueprint

    app.register_blueprint(admin_blueprint, url_prefix="/admin")

    from .farm import farm as farm_blueprint

    app.register_blueprint(farm_blueprint, url_prefix="/farm")

    from .weather import weather as weather_blueprint

    app.register_blueprint(weather_blueprint, url_prefix="/weather")

    from .api import api as api_blueprint

    app.register_blueprint(api_blueprint, url_prefix="/api")

    from .pest import pest as pest_blueprint

    app.register_blueprint(pest_blueprint, url_prefix="/pest")

    from .irrigation import irrigation as irrigation_blueprint

    app.register_blueprint(irrigation_blueprint, url_prefix="/irrigation")

    from app.tasks import task as task_blueprint

    # Context processor to make weather data available to all templates

    from app.tasks import task as task_blueprint

    app.register_blueprint(task_blueprint, url_prefix="/tasks")

    @app.context_processor
    def inject_weather():
        from flask_login import current_user
        from .farm.models import Farm
        from .weather.routes import get_mock_weather_data

        if current_user.is_authenticated:
            try:
                # Get user's farm
                farm = Farm.query.filter_by(user_id=current_user.id).first()
                if farm and farm.location:
                    # Use mock data for simplicity - replace with real API call if needed
                    weather_data = get_mock_weather_data()
                    return {"current": weather_data["current"]}
            except Exception as e:
                app.logger.error(f"Error loading weather data: {str(e)}")

        # Return empty data if user not authenticated or if there was an error
        return {"current": None}

    return app
