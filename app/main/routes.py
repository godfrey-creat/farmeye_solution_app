# app/main/routes.py
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from . import main
from ..auth.models import User
from ..farm.models import Farm, Alert

@main.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        # Fetch farms and alerts for the authenticated user
        farms = Farm.query.filter_by(user_id=current_user.id).all()
        alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(5).all()

        # Define soil health data
        soil_health = {
            "status": "Good",
            "quality": 76,
            "nitrogen": 42,
            "phosphorus": 28,
            "ph_level": 6.8,
            "organic_matter": 4.2
        }

        # Define moisture data
        moisture = {
            "status": "Optimal",
            "current_level": 34,  # measured in percentage
            "recommendation": "No irrigation needed",
            "last_measured": "Today at 10:00 AM"
        }

        # Define growth data
        growth = {
            "status": "On Track",
            "current_stage": "Vegetative",
            "days_to_next_stage": 12,
            "recommendation": "Regular monitoring needed"
        }

        # Render the dashboard template with all variables
        return render_template(
            'dashboard/index.html', 
            farms=farms, 
            alerts=alerts, 
            soil_health=soil_health, 
            moisture=moisture, 
            growth=growth, 
            active_page='dashboard'
        )
    
    # Redirect non-authenticated users to the login page
    return redirect(url_for('auth.login'))