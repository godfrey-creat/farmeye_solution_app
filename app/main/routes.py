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