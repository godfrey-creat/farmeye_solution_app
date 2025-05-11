# PowerShell script to create FarmEye project directory structure
# Set the base directory where the project will be created
$baseDir = ".\farmeye"

# Create the base directory if it doesn't exist
New-Item -Path $baseDir -ItemType Directory -Force

# Create main app directory structure
$appDir = "$baseDir\app"
New-Item -Path $appDir -ItemType Directory -Force
New-Item -Path "$appDir\__init__.py" -ItemType File -Force
New-Item -Path "$appDir\config.py" -ItemType File -Force

# Create authentication module
$authDir = "$appDir\auth"
New-Item -Path $authDir -ItemType Directory -Force
New-Item -Path "$authDir\__init__.py" -ItemType File -Force
New-Item -Path "$authDir\forms.py" -ItemType File -Force
New-Item -Path "$authDir\models.py" -ItemType File -Force
New-Item -Path "$authDir\routes.py" -ItemType File -Force
New-Item -Path "$authDir\utils.py" -ItemType File -Force

# Create admin module
$adminDir = "$appDir\admin"
New-Item -Path $adminDir -ItemType Directory -Force
New-Item -Path "$adminDir\__init__.py" -ItemType File -Force
New-Item -Path "$adminDir\forms.py" -ItemType File -Force
New-Item -Path "$adminDir\routes.py" -ItemType File -Force
New-Item -Path "$adminDir\utils.py" -ItemType File -Force

# Create farm monitoring module
$farmDir = "$appDir\farm"
New-Item -Path $farmDir -ItemType Directory -Force
New-Item -Path "$farmDir\__init__.py" -ItemType File -Force
New-Item -Path "$farmDir\forms.py" -ItemType File -Force
New-Item -Path "$farmDir\models.py" -ItemType File -Force
New-Item -Path "$farmDir\routes.py" -ItemType File -Force
New-Item -Path "$farmDir\utils.py" -ItemType File -Force

# Create machine learning integration module
$mlDir = "$appDir\ml"
New-Item -Path $mlDir -ItemType Directory -Force
New-Item -Path "$mlDir\__init__.py" -ItemType File -Force
New-Item -Path "$mlDir\models.py" -ItemType File -Force
New-Item -Path "$mlDir\utils.py" -ItemType File -Force

# Create static files directories
$staticDir = "$appDir\static"
New-Item -Path $staticDir -ItemType Directory -Force
New-Item -Path "$staticDir\css" -ItemType Directory -Force
New-Item -Path "$staticDir\js" -ItemType Directory -Force
New-Item -Path "$staticDir\img" -ItemType Directory -Force

# Create templates directories and files
$templatesDir = "$appDir\templates"
New-Item -Path $templatesDir -ItemType Directory -Force

# Auth templates
$authTemplatesDir = "$templatesDir\auth"
New-Item -Path $authTemplatesDir -ItemType Directory -Force
New-Item -Path "$authTemplatesDir\login.html" -ItemType File -Force
New-Item -Path "$authTemplatesDir\register.html" -ItemType File -Force
New-Item -Path "$authTemplatesDir\profile.html" -ItemType File -Force

# Admin templates
$adminTemplatesDir = "$templatesDir\admin"
New-Item -Path $adminTemplatesDir -ItemType Directory -Force
New-Item -Path "$adminTemplatesDir\dashboard.html" -ItemType File -Force
New-Item -Path "$adminTemplatesDir\approve_users.html" -ItemType File -Force

# Farm templates
$farmTemplatesDir = "$templatesDir\farm"
New-Item -Path $farmTemplatesDir -ItemType Directory -Force
New-Item -Path "$farmTemplatesDir\dashboard.html" -ItemType File -Force
New-Item -Path "$farmTemplatesDir\upload_image.html" -ItemType File -Force

# Base templates
New-Item -Path "$templatesDir\base.html" -ItemType File -Force
New-Item -Path "$templatesDir\index.html" -ItemType File -Force

# Create migrations directory
$migrationsDir = "$baseDir\migrations"
New-Item -Path $migrationsDir -ItemType Directory -Force

# Create tests directory and files
$testsDir = "$baseDir\tests"
New-Item -Path $testsDir -ItemType Directory -Force
New-Item -Path "$testsDir\__init__.py" -ItemType File -Force
New-Item -Path "$testsDir\test_auth.py" -ItemType File -Force
New-Item -Path "$testsDir\test_admin.py" -ItemType File -Force
New-Item -Path "$testsDir\test_farm.py" -ItemType File -Force

# Create remaining root directory files
New-Item -Path "$baseDir\.gitignore" -ItemType File -Force
New-Item -Path "$baseDir\requirements.txt" -ItemType File -Force
New-Item -Path "$baseDir\config.py" -ItemType File -Force
New-Item -Path "$baseDir\run.py" -ItemType File -Force

Write-Host "FarmEye directory structure has been created successfully!"

# Optional: Create a .gitignore with common Python patterns
$gitignoreContent = @"
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtual environment
venv/
env/
ENV/

# Flask instance folder
instance/

# Flask file uploads
uploads/

# Distribution / packaging
dist/
build/
*.egg-info/

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover

# Database files
*.db
*.sqlite3

# Environment variables
.env
.flaskenv

# IDE specific files
.idea/
.vscode/
*.swp
*.swo
"@

Set-Content -Path "$baseDir\.gitignore" -Value $gitignoreContent

# Optional: Create minimal content for run.py
$runPyContent = @"
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
"@

Set-Content -Path "$baseDir\run.py" -Value $runPyContent

# Optional: Create minimal content for app/__init__.py
$appInitContent = @"
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.farm import bp as farm_bp
    app.register_blueprint(farm_bp, url_prefix='/farm')
    
    @app.route('/')
    def index():
        return 'FarmEye - Farm Monitoring System'
    
    return app
"@

Set-Content -Path "$appDir\__init__.py" -Value $appInitContent

Write-Host "Basic content has been added to key files."