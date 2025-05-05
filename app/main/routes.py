# app/main/routes.py
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from . import main
from ..auth.models import User

@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# run.py - Application entry point
import os
from app import create_app, db
from app.auth.models import User, Role
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'development')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """Make database objects available in Flask shell"""
    return dict(db=db, User=User, Role=Role)

@app.cli.command()
def create_admin():
    """Create a default admin user"""
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@farmeye.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')  # Use a secure password in production
    
    if User.query.filter_by(email=admin_email).first() is None:
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role is None:
            from app.auth.models import Role, Permission
            admin_role = Role(name='Admin')
            admin_role.permissions = Permission.ADMIN | Permission.APPROVE_USERS | Permission.VIEW_DATA | Permission.UPLOAD_DATA
            db.session.add(admin_role)
            db.session.commit()
        
        admin = User(
            email=admin_email,
            username='admin',
            password=admin_password,
            first_name='Admin',
            last_name='User',
            phone_number='1234567890',
            role=admin_role,
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
    else:
        print('Admin user already exists.')

if __name__ == '__main__':
    app.run(debug=True)