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
        alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(5).all()
        return render_template('dashboard/index.html', 
                              farms=farms, 
                              alerts=alerts, 
                              active_page='dashboard')
    return redirect(url_for('auth.login'))


# @main.route('/about')
# def about():
#    """About page"""
#    return render_template('about.html')

# @main.route('/contact')
# def contact():
#    """Contact page"""
#    return render_template('contact.html')