# app/admin/routes.py
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from .. import db
from . import admin
from ..auth.models import User, Permission, Role
from ..farm.models import Farm, FarmImage, SensorData, Alert
from ..decorators import admin_required
from ..utils.email import send_email

@admin.before_request
def before_request():
    """Ensure user is authenticated and has admin permissions"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    if not current_user.is_admin():
        flash('You do not have permission to access this area.', 'danger')
        return redirect(url_for('main.index'))

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with overview of system"""
    stats = {
        'total_users': User.query.count(),
        'pending_approvals': User.query.filter_by(is_approved=False).count(),
        'total_farms': Farm.query.count(),
        'total_images': FarmImage.query.count(),
        'recent_alerts': Alert.query.order_by(Alert.created_at.desc()).limit(5).all()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin.route('/pending_approvals')
@login_required
@admin_required
def pending_approvals():
    """Display list of users pending approval"""
    users = User.query.filter_by(is_approved=False).order_by(User.created_at.desc()).all()
    return render_template('admin/pending_approvals.html', users=users)

@admin.route('/users')
@login_required
@admin_required
def users():
    """Display list of all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    """Approve a user registration"""
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    
    # Send approval notification to user
    send_email(
        user.email,
        'Account Approved',
        'auth/email/account_approved',
        user=user
    )
    
    flash(f'User {user.username} has been approved.', 'success')
    return redirect(url_for('admin.pending_approvals'))

@admin.route('/reject_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    """Reject and delete a user registration"""
    user = User.query.get_or_404(user_id)
    username = user.username
    
    # Send rejection notification to user
    send_email(
        user.email,
        'Account Registration Rejected',
        'auth/email/account_rejected',
        user=user
    )
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been rejected and removed.', 'success')
    return redirect(url_for('admin.pending_approvals'))

@admin.route('/farms')
@login_required
@admin_required
def farms():
    """Display list of all farms"""
    farms = Farm.query.order_by(Farm.created_at.desc()).all()
    return render_template('admin/farms.html', farms=farms)

@admin.route('/farm/<int:farm_id>')
@login_required
@admin_required
def farm_details(farm_id):
    """Display details of a specific farm"""
    farm = Farm.query.get_or_404(farm_id)
    images = FarmImage.query.filter_by(farm_id=farm_id).order_by(FarmImage.upload_date.desc()).all()
    sensor_data = SensorData.query.filter_by(farm_id=farm_id).order_by(SensorData.timestamp.desc()).limit(50).all()
    alerts = Alert.query.filter_by(farm_id=farm_id).order_by(Alert.created_at.desc()).all()
    
    return render_template('admin/farm_details.html', farm=farm, images=images, 
                           sensor_data=sensor_data, alerts=alerts)

@admin.route('/summary')
@login_required
@admin_required
def summary():
    """Display system summary and statistics"""
    # Get statistics for dashboard
    user_stats = {
        'total': User.query.count(),
        'admins': User.query.join(Role).filter(Role.name == 'Admin').count(),
        'farmers': User.query.join(Role).filter(Role.name == 'Farmer').count(),
        'pending': User.query.filter_by(is_approved=False).count()
    }
    
    farm_stats = {
        'total': Farm.query.count(),
        'avg_size': db.session.query(db.func.avg(Farm.size_acres)).scalar() or 0,
        'images': FarmImage.query.count(),
        'sensors': SensorData.query.distinct(SensorData.sensor_type).count()
    }
    
    return render_template('admin/summary.html', user_stats=user_stats, farm_stats=farm_stats)