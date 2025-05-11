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
        farms = Farm.query.filter_by(user_id=current_user.id).all()

        # Get recent alerts for notification count
        alerts = Alert.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).order_by(Alert.created_at.desc()).all()

        # Count unread alerts for notification badge
        unread_count = len(alerts)

        return render_template('dashboard/index.html',
                               farms=farms,
                               alerts=alerts,
                               unread_count=unread_count,
                               active_page='dashboard')
    return redirect(url_for('auth.login'))

@main.route('/weather')
@login_required
def weather_redirect():
    """Redirect to the weather dashboard in the weather module"""
    return redirect(url_for('weather.dashboard'))

@main.route('/update_farm_location')
@login_required
def update_farm_location_redirect():
    """Redirect to the update location page in the weather module"""
    return redirect(url_for('weather.update_location'))

@main.route('/pest_control')
@login_required
def pest_control_redirect():
    """Redirect to the pest control dashboard in the pest module"""
    return redirect(url_for('pest.dashboard'))

# @main.route('/about')
# def about():
#    """About page"""
#    return render_template('about.html')

# @main.route('/contact')
# def contact():
#    """Contact page"""
#    return render_template('contact.html')