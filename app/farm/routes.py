# app/farm/routes.py
import os
import uuid
from datetime import datetime, timedelta
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
    abort,
    session,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import db
from . import farm
from .forms import FarmForm, ImageUploadForm, SensorDataForm, FarmRegistrationForm, FieldForm
from .models import (
    Farm,
    FarmImage,
    Field,
    BoundaryMarker,
    SensorData,
    Alert,
    FarmTeamMember,
    FarmStage,
    PestControl,
    CropHealth,
    Sensor,
    WeatherData,
)
from ..auth.models import User
from ..decorators import require_farm_registration
from ..ml.utils import process_farm_image
import requests
from sqlalchemy import func
import openai


@farm.route("/dashboard")
@login_required
@require_farm_registration
def dashboard():
    """Display farmer's dashboard with overview of farms"""
    # Get user's farms and alerts even if not approved
    farms = Farm.query.filter_by(user_id=current_user.id).all()
    alerts = (
        Alert.query.filter_by(user_id=current_user.id)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    # Display warning message but don't redirect
    if not current_user.is_approved:
        flash(
            "Your account is pending approval. Some features may be limited.", "warning"
        )

    # Get the latest soil moisture data
    soil_moisture = None
    farm_stage = None
    if farms:
        soil_moisture = (
            SensorData.query.filter_by(farm_id=farms[0].id, sensor_type="soil_moisture")
            .order_by(SensorData.timestamp.desc())
            .first()
        )
        farm_stage = FarmStage.query.filter_by(
            farm_id=farms[0].id, status="Active"
        ).first()

    # Calculate moisture metrics
    moisture = {
        "status": "Normal",
        "current_level": soil_moisture.value if soil_moisture else 64,
        "optimal_range": "60-80%",
        "last_reading": soil_moisture.timestamp if soil_moisture else datetime.utcnow(),
        "last_irrigation": "2 days ago",
        "next_irrigation": "Tomorrow",
    }

    # Calculate field health metrics
    field_health = {
        "status": "Excellent",
        "overall_health": "82",
        "improvement": "2",
        "improvement_direction": "up",
    }

    # Calculate soil health metrics
    soil_health = {
        "status": "Good",
        "overall_health": 76,
        "quality": 76,
        "nitrogen": 42,  # ppm
        "phosphorus": 28,  # ppm
        "ph_level": 6.8,
        "organic_matter": 4.2,  # percentage
        "moisture": moisture["current_level"],  # percentage
        "last_irrigation": moisture["last_irrigation"],
        "next_irrigation": moisture["next_irrigation"],
    }

    # Calculate growth metrics
    growth = {
        "status": "On Track",
        "stage": farm_stage.stage_name if farm_stage else "Vegetative",
        "progress": 45,  # percentage completion of current stage
        "days": "28/62",  # days in current growth cycle
        "next_stage": "Flowering (in 14 days)",
        "harvest_date": "August 15",
    }

    # Always render the template directly, don't redirect
    return render_template(
        "dashboard/index.html",
        farms=farms,
        alerts=alerts,
        field_health=field_health,
        soil_health=soil_health,
        moisture=moisture,
        growth=growth,
        active_page="dashboard",
    )


@farm.route("/field_map")
@login_required
@require_farm_registration
def field_map():
    """Display field map view with enhanced data"""
    # Get all farms belonging to the current user
    farms = Farm.query.filter_by(user_id=current_user.id).all()
    
    # Prepare data structure for frontend mapping
    map_data = []
    for farm in farms:
        # Get sensor data for the farm
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
        
        # Get farm images
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
        "dashboard/field_map.html", 
        active_page="field_map",
        map_data=map_data
    )


@farm.route("/analytics")
@login_required
@require_farm_registration
def analytics():
    """Display enhanced analytics view with farm performance metrics"""
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
        "dashboard/analytics.html",
        active_page="analytics",
        farms=farms,
        sensor_summary=sensor_data_summary,
        crop_health=crop_health_data,
        weather_avg={
            'temperature': round(weather_stats[0], 2) if weather_stats and weather_stats[0] else None,
            'humidity': round(weather_stats[1], 2) if weather_stats and weather_stats[1] else None,
            'rainfall': round(weather_stats[2], 2) if weather_stats and weather_stats[2] else None,
            'wind_speed': round(weather_stats[3], 2) if weather_stats and weather_stats[3] else None,
        },
        alerts=alert_data
    )


@farm.route("/irrigation")
@login_required
@require_farm_registration
def irrigation():
    """Display enhanced irrigation management view with zone data"""
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
        "dashboard/irrigation.html",
        active_page="irrigation",
        irrigation_schedules=irrigation_schedules,
        moisture_data=moisture_data
    )


@farm.route('/weather', methods=['GET', 'POST'])
@login_required
@require_farm_registration
def weather():
    """Display weather forecast view using OpenWeatherMap"""
    city = 'Nairobi'  # Default city
    weather_info = None

    if request.method == 'POST':
        city = request.form.get('city', 'Nairobi')

    api_key = current_app.config.get('OPENWEATHER_API_KEY')  # Get from config
    if api_key:
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
    else:
        flash("Weather API key not configured.", "warning")

    return render_template('dashboard/weather.html', active_page='weather', weather=weather_info, city=city)


@farm.route("/pest_control")
@login_required
@require_farm_registration
def pest_control():
    """Display pest control view"""
    # Redirect to the pest control module
    return redirect(url_for("pest.dashboard"))


@farm.route("/schedule")
@login_required
@require_farm_registration
def schedule():
    """Display schedule view"""
    # You would add your schedule logic here
    return render_template("dashboard/schedule.html", active_page="schedule")


@farm.route("/register", methods=["GET", "POST"])
@farm.route("/register_farm", methods=["GET", "POST"])
@login_required
def register_farm():
    """Handle farm registration for new users"""
    has_farm = Farm.query.filter_by(user_id=current_user.id).first() is not None
    if has_farm and request.method == "GET":
        return redirect(url_for("farm.dashboard"))

    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            try:
                # Begin transaction
                db.session.begin_nested()

                # Process farms
                for farm_data in data.get("farms", []):

                    crop_type = "Mixed"
                    if farm_data.get("fields") and len(farm_data["fields"]) > 0:
                        first_field = farm_data["fields"][0]
                        if first_field.get("cropType"):
                            crop_type = first_field["cropType"]

                    farm = Farm(
                        name=farm_data["name"],
                        region=farm_data["region"],
                        location=farm_data.get("location", farm_data["region"]),
                        size=farm_data.get("size", 0.0),
                        size_acres=farm_data.get("size_acres", 0.0),
                        crop_type=farm_data.get("cropType", crop_type),
                        description=farm_data.get("description", ""),
                        water_source=farm_data.get("waterSource", "NA"),
                        irrigation_type=farm_data.get("irrigationType", "NA"),
                        latitude=farm_data.get("latitude"),
                        longitude=farm_data.get("longitude"),
                        # Set defaults for fields to be updated later
                        soil_type="NA",
                        ph_level=None,
                        soil_notes="To be updated",
                        user_id=current_user.id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(farm)
                    db.session.flush()

                    # Process fields
                    for field_data in farm_data.get("fields", []):
                        field = Field(
                            name=field_data["name"],
                            farm_id=farm.id,
                            created_at=datetime.utcnow(),
                        )
                        db.session.add(field)
                        db.session.flush()

                        # Process boundaries
                        for boundary in field_data.get("boundaries", []):
                            marker = BoundaryMarker(
                                field_id=field.id,
                                latitude=float(boundary["lat"]),
                                longitude=float(boundary["lng"]),
                                created_at=datetime.utcnow(),
                            )
                            db.session.add(marker)

                # Process team members
                for member in data.get("teamMembers", []):
                    user = User.query.filter_by(email=member["email"]).first()
                    if not user:
                        user = User(
                            email=member["email"],
                            username=member["email"].split("@")[0],
                            first_name=member["firstName"],
                            last_name=member["lastName"],
                            user_type="team_member",
                            is_approved=False,
                        )
                        db.session.add(user)
                        db.session.flush()

                    # Add team member to farms
                    for farm in Farm.query.filter_by(user_id=current_user.id).all():
                        exists = FarmTeamMember.query.filter_by(
                            farm_id=farm.id, user_id=user.id
                        ).first()

                        if not exists:
                            team_member = FarmTeamMember(
                                farm_id=farm.id,
                                user_id=user.id,
                                role=member["role"],
                                added_at=datetime.utcnow(),
                                added_by=current_user.id,
                            )
                            db.session.add(team_member)

                db.session.commit()
                return jsonify(
                    {"success": True, "message": "Farm registration successful!"}
                )

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Farm registration error: {str(e)}")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "An error occurred during registration. Please try again.",
                        }
                    ),
                    500,
                )
    # For GET requests, render the registration page with CSRF protection
    form = FarmRegistrationForm()
    return render_template(
        "farm/farm_registration_standalone.html",
        form=form,
        current_user=current_user,  # Add current_user to template context
    )


@farm.route('/add-field/<int:farm_id>', methods=['GET', 'POST'])
@login_required
@require_farm_registration
def add_field(farm_id):
    """Add a new field to a farm"""
    # Check farm ownership
    farm = Farm.query.get_or_404(farm_id)
    if farm.user_id != current_user.id and not current_user.is_admin():
        abort(403)  # Forbidden
    
    form = FieldForm()
    if form.validate_on_submit():
        field = Field(
            name=form.field_name.data,
            crop_type=form.crop_type.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            farming_method=form.farming_method.data,
            smart_devices=','.join(form.smart_devices.data),
            monitoring_goals=','.join(form.monitoring_goals.data),
            farm_id=farm_id
        )
        db.session.add(field)
        db.session.commit()
        flash("Field added successfully!", "success")
        if form.add_another.data:
            return redirect(url_for('farm.add_field', farm_id=farm_id))
        else:
            return redirect(url_for('farm.dashboard'))
    return render_template('farm/add_field.html', form=form, farm=farm)


@farm.route("/view/<int:farm_id>")
@login_required
@require_farm_registration
def view_farm(farm_id):
    """View details of a specific farm"""
    farm = Farm.query.get_or_404(farm_id)

    # Ensure user owns this farm or is admin
    if farm.user_id != current_user.id and not current_user.is_admin():
        flash("You do not have permission to view this farm.", "danger")
        # Return to dashboard directly instead of potential redirect chain
        return render_template(
            "dashboard/index.html",
            farms=Farm.query.filter_by(user_id=current_user.id).all(),
            alerts=Alert.query.filter_by(user_id=current_user.id)
            .order_by(Alert.created_at.desc())
            .limit(5)
            .all(),
            active_page="dashboard",
        )

    # Get farm images
    images = (
        FarmImage.query.filter_by(farm_id=farm_id)
        .order_by(FarmImage.upload_date.desc())
        .all()
    )

    # Get recent sensor data
    sensor_data = (
        SensorData.query.filter_by(farm_id=farm_id)
        .order_by(SensorData.timestamp.desc())
        .limit(20)
        .all()
    )

    # Get alerts for this farm
    alerts = (
        Alert.query.filter_by(farm_id=farm_id).order_by(Alert.created_at.desc()).all()
    )

    # Create a template for this in the next phase
    return render_template(
        "farm/view_farm.html",
        farm=farm,
        images=images,
        sensor_data=sensor_data,
        alerts=alerts,
        active_page="dashboard",
    )


@farm.route("/edit/<int:farm_id>", methods=["GET", "POST"])
@login_required
@require_farm_registration
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
        flash("Farm details updated successfully!", "success")
        return redirect(url_for("farm.view_farm", farm_id=farm.id))

    # Pre-populate form with existing data
    if request.method == "GET":
        form.name.data = farm.name
        form.location.data = farm.location
        form.size_acres.data = farm.size_acres
        form.crop_type.data = farm.crop_type
        form.description.data = farm.description

    # Create a template for this in the next phase
    return render_template(
        "farm/edit_farm.html", form=form, farm=farm, active_page="dashboard"
    )


@farm.route("/upload_image/<int:farm_id>", methods=["GET", "POST"])
@login_required
@require_farm_registration
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
            current_app.root_path, current_app.config["UPLOAD_FOLDER"], "images"
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
            user_id=current_user.id,
        )

        db.session.add(farm_image)
        db.session.commit()

        # Process image with ML model (asynchronously)
        process_farm_image(farm_image.id)

        flash("Image uploaded successfully! It will be analyzed shortly.", "success")
        return redirect(url_for("farm.view_farm", farm_id=farm.id))

    # Create a template for this in the next phase
    return render_template(
        "farm/upload_image.html", form=form, farm=farm, active_page="dashboard"
    )


@farm.route("/add_sensor_data/<int:farm_id>", methods=["GET", "POST"])
@login_required
@require_farm_registration
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
            user_id=current_user.id,
        )

        db.session.add(sensor_data)
        db.session.commit()

        flash("Sensor data added successfully!", "success")
        return redirect(url_for("farm.view_farm", farm_id=farm.id))

    # Create a template for this in the next phase
    return render_template(
        "farm/add_sensor_data.html", form=form, farm=farm, active_page="dashboard"
    )


@farm.route("/alerts")
@login_required
@require_farm_registration
def alerts():
    """View all alerts for user's farms"""
    # Get user's farms
    farm_ids = [farm.id for farm in Farm.query.filter_by(user_id=current_user.id).all()]

    # Get alerts for these farms
    alerts = (
        Alert.query.filter(Alert.farm_id.in_(farm_ids))
        .order_by(Alert.created_at.desc())
        .all()
    )

    # You could create a specialized alerts page or use the partials/alerts.html component
    return render_template("farm/alerts.html", alerts=alerts, active_page="dashboard")


@farm.route("/mark_alert_read/<int:alert_id>", methods=["POST"])
@login_required
def mark_alert_read(alert_id):
    """Mark an alert as read"""
    alert = Alert.query.get_or_404(alert_id)

    # Ensure user owns this alert's farm or is admin
    if alert.user_id != current_user.id and not current_user.is_admin():
        abort(403)  # Forbidden

    alert.is_read = True
    db.session.commit()

    return jsonify({"success": True})


# Personalized advisory
@farm.route('/advisory/<int:farm_id>')
@login_required
@require_farm_registration
def advisory(farm_id):
    """Generate farming advisory based on multiple data sources"""
    # Check if OpenAI API key is configured
    if not current_app.config.get('OPENAI_API_KEY'):
        flash("OpenAI API key not configured. Advisory service unavailable.", "warning")
        return redirect(url_for("farm.view_farm", farm_id=farm_id))
    
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
    - Crop health analysis: {latest_image.analysis_result if latest_image and hasattr(latest_image, 'analysis_result') else 'No recent image analysis'}
    - Soil moisture: {latest_sensor.value if latest_sensor else 'No recent sensor data'} {latest_sensor.unit if latest_sensor else ''}
    - Satellite vegetation index: {satellite_data.get('ndvi') if satellite_data else 'No satellite data'}
    - Weather forecast: {get_weather_forecast(farm.location) if farm.location else 'No location data'}
    
    Focus on practical recommendations for irrigation, fertilization, and pest control.
    """
    
    # Get AI-generated advisory
    advisory_text = generate_advisory(prompt)
    
    return render_template(
        'farm/advisory.html',
        farm=farm,
        advisory=advisory_text,
        image_data=latest_image,
        sensor_data=latest_sensor,
        satellite_data=satellite_data,
        active_page='dashboard'
    )


@farm.route('/api/advisory/<int:farm_id>', methods=['GET'])
@login_required
@require_farm_registration
def api_advisory(farm_id):
    """API endpoint to fetch advisory data"""
    farm = Farm.query.get_or_404(farm_id)
    # Ensure user owns the farm
    if farm.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    
    # Get latest data (simplified version of the advisory route)
    latest_image = FarmImage.query.filter_by(farm_id=farm_id).order_by(FarmImage.upload_date.desc()).first()
    latest_sensor = SensorData.query.filter_by(farm_id=farm_id).order_by(SensorData.timestamp.desc()).first()
    
    # Check if OpenAI API key is configured
    if not current_app.config.get('OPENAI_API_KEY'):
        return jsonify({
            "error": "Advisory service unavailable. API key not configured."
        }), 503
    
    # Initialize OpenAI
    openai.api_key = current_app.config['OPENAI_API_KEY']
    
    # Generate simplified prompt
    prompt = f"""
    Generate a concise farming advisory (under 100 words) for {farm.crop_type} crops based on available farm data.
    Focus on practical recommendations for irrigation, fertilization, and pest control.
    """
    
    advisory_text = generate_advisory(prompt)
    
    return jsonify({
        "advisory": advisory_text,
        "farm_id": farm_id,
        "farm_name": farm.name,
        "crop_type": farm.crop_type,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })


# Debug endpoint for internal use
@farm.route("/debug")
@login_required
def debug():
    """Debug endpoint to check farm configuration and routes"""
    debug_info = {
        "blueprint": "farm",
        "config": {
            "openweather_api_key_configured": bool(
                current_app.config.get("OPENWEATHER_API_KEY")
            ),
            "openai_api_key_configured": bool(
                current_app.config.get("OPENAI_API_KEY")
            )
        },
        "farm_count": Farm.query.filter_by(user_id=current_user.id).count(),
        "sensor_data_count": SensorData.query.filter_by(
            user_id=current_user.id
        ).count(),
        "alert_count": Alert.query.filter_by(user_id=current_user.id).count(),
    }
    return jsonify(debug_info)


@farm.route("/api/dashboard-data")
@login_required
def dashboard_data():
    """API endpoint that provides dashboard data in JSON format"""
    # Get the user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()