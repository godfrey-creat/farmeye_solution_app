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
from .models import Farm, FarmImage, SensorData, Alert, CropHealth, Sensor, WeatherData
#from ..decorators import permission_required
from ..ml.utils import process_farm_image
import openai
import requests
from flask import current_app
from config import Config
from sqlalchemy import func

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
    
    # Get all farms belonging to the current user
    farms = Farm.query.filter_by(user_id=current_user.id).all()
    
    # Prepare data structure for frontend mapping
    map_data = []
    for farm in farms:
        sensors = [
            {
                'id': sensor.id,
                'type': sensor.sensor_type,
                'location': sensor.location,
                'latitude': data.latitude,
                'longitude': data.longitude,
                'value': data.value,
                'unit': data.unit,
                'timestamp': data.timestamp
            }
            for sensor in farm.sensors
            for data in sensor.sensor_data if data.latitude and data.longitude
        ]
        
        images = [
            {
                'id': img.id,
                'url': img.image_url,
                'type': img.image_type,
                'upload_date': img.upload_date
            }
            for img in farm.images
        ]
        
        map_data.append({
            'farm': {
                'id': farm.id,
                'name': farm.name,
                'location': farm.location,
                'size': farm.size,
                'crop_type': farm.crop_type
            },
            'sensors': sensors,
            'images': images
        })

    return render_template(
        'dashboard/field_map.html',
        active_page='field_map',
        map_data=map_data
    )

@farm.route('/analytics')
@login_required
def analytics():
    """Display analytics view"""

    # Get all farms for the logged-in user
    farms = Farm.query.filter_by(user_id=current_user.id).all()
    farm_ids = [farm.id for farm in farms]

    # Sensor data trends (grouped by type)
    sensor_stats = (
        SensorData.query
        .filter(SensorData.farm_id.in_(farm_ids))
        .with_entities(SensorData.sensor_type, func.count(SensorData.id), func.avg(SensorData.value))
        .group_by(SensorData.sensor_type)
        .all()
    )

    sensor_data_summary = [
        {'type': s[0], 'count': s[1], 'avg_value': round(s[2], 2) if s[2] else None}
        for s in sensor_stats
    ]

    # Crop health history (latest status per farm)
    crop_health_data = (
        CropHealth.query
        .filter(CropHealth.farm_id.in_(farm_ids))
        .order_by(CropHealth.assessment_date.desc())
        .all()
    )

    # Weather data trends (e.g., avg temperature, rainfall)
    weather_stats = (
        WeatherData.query
        .filter(WeatherData.farm_id.in_(farm_ids))
        .with_entities(
            func.avg(WeatherData.temperature),
            func.avg(WeatherData.humidity),
            func.avg(WeatherData.rainfall),
            func.avg(WeatherData.wind_speed)
        )
        .first()
    )

    # Alert summary
    alert_summary = (
        Alert.query
        .filter(Alert.farm_id.in_(farm_ids))
        .with_entities(Alert.alert_type, func.count(Alert.id))
        .group_by(Alert.alert_type)
        .all()
    )

    alert_data = [{'type': a[0], 'count': a[1]} for a in alert_summary]

    return render_template(
        'dashboard/analytics.html',
        active_page='analytics',
        farms=farms,
        sensor_summary=sensor_data_summary,
        crop_health=crop_health_data,
        weather_avg={
            'temperature': round(weather_stats[0], 2) if weather_stats[0] else None,
            'humidity': round(weather_stats[1], 2) if weather_stats[1] else None,
            'rainfall': round(weather_stats[2], 2) if weather_stats[2] else None,
            'wind_speed': round(weather_stats[3], 2) if weather_stats[3] else None,
        },
        alerts=alert_data
    )

@farm.route('/irrigation')
@login_required
def irrigation():
    """Display irrigation management view"""

    # Sample/mock data
    irrigation_schedules = [
        {"zone": "North Field", "start_time": "06:00", "duration": "30 mins"},
        {"zone": "South Field", "start_time": "18:00", "duration": "45 mins"}
    ]

    moisture_data = [
        {"zone": "North Field", "moisture": 35},
        {"zone": "South Field", "moisture": 40},
        {"zone": "East Field", "moisture": 28},
        {"zone": "West Field", "moisture": 50}
    ]

    return render_template(
        'dashboard/irrigation.html',
        active_page='irrigation',
        irrigation_schedules=irrigation_schedules,
        moisture_data=moisture_data
    )


@farm.route('/weather', methods=['GET', 'POST'])
@login_required
def weather():
    """Display weather forecast view using OpenWeatherMap"""
    city = 'Nairobi'  # Default city
    weather_info = None

    if request.method == 'POST':
        city = request.form.get('city', 'Nairobi')

    api_key = 'OPENWEATHER_API_KEY'  # Replace with your actual API key
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        weather_info = {
            'city': city,
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'].title(),
            'icon': data['weather'][0]['icon'],
            'wind_speed': data['wind']['speed']
        }

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Weather API error: {e}")
        weather_info = None

    return render_template('dashboard/weather.html', active_page='weather', weather=weather_info, city=city)

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


# Personalized advisory
@farm.route('/advisory/<int:farm_id>')
@login_required
def advisory(farm_id):
    """Generate farming advisory based on multiple data sources"""
    # Initialize OpenAI with API key from config
    openai.api_key = current_app.config['OPENAI_API_KEY']
    farm = Farm.query.get_or_404(farm_id)
    
    # Verify farm ownership
    if farm.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    
    # Get latest data from different sources
    latest_image = FarmImage.query.filter_by(farm_id=farm_id).order_by(FarmImage.upload_date.desc()).first()
    latest_sensor = SensorData.query.filter_by(farm_id=farm_id).order_by(SensorData.timestamp.desc()).first()
    
    # Get satellite data (mock - replace with actual API call)
    satellite_data = get_satellite_data(farm.latitude, farm.longitude) if farm.latitude and farm.longitude else None
    
    # Prepare prompt for ChatGPT
    prompt = f"""
    Generate a concise farming advisory (under 100 words) for {farm.crop_type} crops based on:
    - Crop health analysis: {latest_image.analysis_result if latest_image else 'No recent image analysis'}
    - Soil moisture: {latest_sensor.value if latest_sensor else 'No recent sensor data'} {latest_sensor.unit if latest_sensor else ''}
    - Satellite vegetation index: {satellite_data.get('ndvi') if satellite_data else 'No satellite data'}
    - Weather forecast: {get_weather_forecast(farm.location) if farm.location else 'No location data'}
    
    Focus on practical recommendations for irrigation, fertilization, and pest control.
    """
    
    # Get AI-generated advisory
    advisory_text = generate_advisory(prompt)
    
    return render_template('farm/advisory.html',
                         farm=farm,
                         advisory=advisory_text,
                         image_data=latest_image,
                         sensor_data=latest_sensor,
                         satellite_data=satellite_data,
                         active_page='dashboard')

# Helper functions for the advisory route
def get_satellite_data(latitude, longitude):
    """Mock function to get satellite data - replace with actual API call"""
    # In production, you might use APIs like Sentinel Hub, Planet, or NASA's Earthdata
    return {
        'ndvi': 0.78,  # Normalized Difference Vegetation Index
        'health_status': 'healthy',
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d')
    }

def get_weather_forecast(location):
    """Get simplified weather forecast"""
    try:
        weather_params = {
            'q': location,
            'appid': current_app.config['OPENWEATHER_API_KEY'],
            'units': 'metric'
        }
        
        response = requests.get(current_app.config['OPENWEATHER_BASE_URL'], params=weather_params)
        response.raise_for_status()
        data = response.json()
        
        current = data['weather'][0]['description']
        temp = data['main']['temp']
        return f"Current weather: {current}, {temp}°C"
        
    except Exception as e:
        current_app.logger.error(f"Weather error: {str(e)}")
        return "Weather data unavailable"
def generate_advisory(prompt):
    """Generate advisory using ChatGPT 3.5 with concise output"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an agricultural expert providing concise farming advisories under 100 words."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        # Extract and clean the response
        advisory = response.choices[0].message.content.strip()
        
        # Ensure it's under 100 words
        words = advisory.split()
        if len(words) > 100:
            advisory = ' '.join(words[:100]) + '...'
            
        return advisory
        
    except Exception as e:
        current_app.logger.error(f"Failed to generate advisory: {str(e)}")
        return "Could not generate advisory at this time. Please check your farm data manually."