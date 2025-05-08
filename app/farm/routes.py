# app/farm/routes.py
import os
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import db
from . import farm
from .forms import FarmForm, ImageUploadForm, SensorDataForm
from .models import Farm, FarmImage, SensorData, Alert
from ..auth.models import User
#from ..decorators import permission_required
from ..ml.utils import process_farm_image

@farm.route('/dashboard')
@login_required
def dashboard():
    """Display farmer's dashboard with overview of farms"""
    # Get user's farms and alerts even if not approved
    farms = Farm.query.filter_by(user_id=current_user.id).all()
    alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(5).all()
    
    # Display warning message but don't redirect
    if not current_user.is_approved:
        flash('Your account is pending approval. Some features may be limited.', 'warning')
    
    # Always render the template directly, don't redirect
    return render_template('dashboard/index.html', 
                          farms=farms, 
                          alerts=alerts, 
                          active_page='dashboard')

@farm.route('/field_map')
@login_required
def field_map():
    """Display field map view"""
    # You would add your field map logic here
    return render_template('dashboard/field_map.html', active_page='field_map')

@farm.route('/analytics')
@login_required
def analytics():
    """Display analytics view"""
    # You would add your analytics logic here
    return render_template('dashboard/analytics.html', active_page='analytics')

@farm.route('/irrigation')
@login_required
def irrigation():
    """Display irrigation management view"""
    # You would add your irrigation logic here
    return render_template('dashboard/irrigation.html', active_page='irrigation')

@farm.route('/weather')
@login_required
def weather():
    """Display weather forecast view"""
    # You would add your weather logic here
    return render_template('dashboard/weather.html', active_page='weather')

@farm.route('/pest_control')
@login_required
def pest_control():
    """Display pest control view"""
    # You would add your pest control logic here
    return render_template('dashboard/pest_control.html', active_page='pest_control')

@farm.route('/schedule')
@login_required
def schedule():
    """Display schedule view"""
    # You would add your schedule logic here
    return render_template('dashboard/schedule.html', active_page='schedule')

@farm.route('/register', methods=['GET', 'POST'])
@login_required
def register_farm():
    """Register a new farm"""
    if not current_user.is_approved:
        flash('Your account must be approved before registering a farm.', 'warning')
        return redirect(url_for('farm.dashboard'))
    
    form = FarmForm()
    if form.validate_on_submit():
        farm = Farm(
            name=form.name.data,
            location=form.location.data,
            size_acres=form.size_acres.data,
            crop_type=form.crop_type.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(farm)
        db.session.commit()
        flash('Farm registered successfully!', 'success')
        return redirect(url_for('farm.view_farm', farm_id=farm.id))
    
    # Create a template for this in the next phase
    return render_template('farm/register_farm.html', form=form, active_page='dashboard')

@farm.route('/view/<int:farm_id>')
@login_required
def view_farm(farm_id):
    """View details of a specific farm"""
    farm = Farm.query.get_or_404(farm_id)
    
    # Ensure user owns this farm or is admin
    if farm.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to view this farm.', 'danger')
        # Return to dashboard directly instead of potential redirect chain
        return render_template('dashboard/index.html',
                             farms=Farm.query.filter_by(user_id=current_user.id).all(),
                             alerts=Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(5).all(),
                             active_page='dashboard')
    
    # Get farm images
    images = FarmImage.query.filter_by(farm_id=farm_id).order_by(FarmImage.upload_date.desc()).all()
    
    # Get recent sensor data
    sensor_data = SensorData.query.filter_by(farm_id=farm_id).order_by(SensorData.timestamp.desc()).limit(20).all()
    
    # Get alerts for this farm
    alerts = Alert.query.filter_by(farm_id=farm_id).order_by(Alert.created_at.desc()).all()
    
    # Create a template for this in the next phase
    return render_template('farm/view_farm.html', 
                          farm=farm, 
                          images=images, 
                          sensor_data=sensor_data, 
                          alerts=alerts,
                          active_page='dashboard')

@farm.route('/edit/<int:farm_id>', methods=['GET', 'POST'])
@login_required
def edit_farm(farm_id):
    """Edit farm details"""
    farm = Farm.query.get_or_404(farm_id)
    
    # Ensure user owns this farm or is admin
    if farm.user_id != current_user.id and not current_user.is_admin():
        abort(403)  # Forbidden
    
    form = FarmForm()
    
    if form.validate_on_submit():
        farm.name = form.name.data
        farm.location = form.location.data
        farm.size_acres = form.size_acres.data
        farm.crop_type = form.crop_type.data
        farm.description = form.description.data
        farm.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Farm details updated successfully!', 'success')
        return redirect(url_for('farm.view_farm', farm_id=farm.id))
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.name.data = farm.name
        form.location.data = farm.location
        form.size_acres.data = farm.size_acres
        form.crop_type.data = farm.crop_type
        form.description.data = farm.description
    
    # Create a template for this in the next phase
    return render_template('farm/edit_farm.html', 
                          form=form, 
                          farm=farm,
                          active_page='dashboard')

@farm.route('/upload_image/<int:farm_id>', methods=['GET', 'POST'])
@login_required
def upload_image(farm_id):
    """Upload farm image for analysis"""
    farm = Farm.query.get_or_404(farm_id)
    
    # Ensure user owns this farm or is admin
    if farm.user_id != current_user.id and not current_user.is_admin():
        abort(403)  # Forbidden
    
    form = ImageUploadForm()
    
    if form.validate_on_submit():
        # Save uploaded image
        image_file = form.image.data
        filename = secure_filename(image_file.filename)
        # Generate unique filename to prevent overwrites
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create upload path
        upload_path = os.path.join(
            current_app.root_path, 
            current_app.config['UPLOAD_FOLDER'], 
            'images'
        )
        
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        file_path = os.path.join(upload_path, unique_filename)
        image_file.save(file_path)
        
        # Create database record
        farm_image = FarmImage(
            filename=unique_filename,
            path=f"/static/uploads/images/{unique_filename}",
            image_type=form.image_type.data,
            farm_id=farm.id,
            user_id=current_user.id
        )
        
        db.session.add(farm_image)
        db.session.commit()
        
        # Process image with ML model (asynchronously)
        process_farm_image(farm_image.id)
        
        flash('Image uploaded successfully! It will be analyzed shortly.', 'success')
        return redirect(url_for('farm.view_farm', farm_id=farm.id))
    
    # Create a template for this in the next phase
    return render_template('farm/upload_image.html', 
                          form=form, 
                          farm=farm,
                          active_page='dashboard')

@farm.route('/add_sensor_data/<int:farm_id>', methods=['GET', 'POST'])
@login_required
def add_sensor_data(farm_id):
    """Manually add sensor data"""
    farm = Farm.query.get_or_404(farm_id)
    
    # Ensure user owns this farm or is admin
    if farm.user_id != current_user.id and not current_user.is_admin():
        abort(403)  # Forbidden
    
    form = SensorDataForm()
    
    if form.validate_on_submit():
        sensor_data = SensorData(
            sensor_type=form.sensor_type.data,
            value=form.value.data,
            unit=form.unit.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            farm_id=farm.id,
            user_id=current_user.id
        )
        
        db.session.add(sensor_data)
        db.session.commit()
        
        flash('Sensor data added successfully!', 'success')
        return redirect(url_for('farm.view_farm', farm_id=farm.id))
    
    # Create a template for this in the next phase
    return render_template('farm/add_sensor_data.html', 
                          form=form, 
                          farm=farm,
                          active_page='dashboard')

@farm.route('/alerts')
@login_required
def alerts():
    """View all alerts for user's farms"""
    # Get user's farms
    farm_ids = [farm.id for farm in Farm.query.filter_by(user_id=current_user.id).all()]
    
    # Get alerts for these farms
    alerts = Alert.query.filter(Alert.farm_id.in_(farm_ids)).order_by(Alert.created_at.desc()).all()
    
    # You could create a specialized alerts page or use the partials/alerts.html component
    return render_template('farm/alerts.html', 
                          alerts=alerts,
                          active_page='dashboard')

@farm.route('/mark_alert_read/<int:alert_id>', methods=['POST'])
@login_required
def mark_alert_read(alert_id):
    """Mark an alert as read"""
    alert = Alert.query.get_or_404(alert_id)
    
    # Ensure user owns this alert's farm or is admin
    if alert.user_id != current_user.id and not current_user.is_admin():
        abort(403)  # Forbidden
    
    alert.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})