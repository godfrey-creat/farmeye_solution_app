# app/farm/routes.py
import os
import uuid
from datetime import datetime
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
    abort,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import db
from . import farm
from .forms import FarmForm, ImageUploadForm, SensorDataForm
from .models import Farm, FarmImage, SensorData, Alert, FarmTeamMember

# from ..decorators import permission_required
from ..ml.utils import process_farm_image
from flask import Blueprint, jsonify, current_app
import requests
from datetime import datetime, timedelta
from ..farm.models import Farm, SensorData, Alert, FarmStage, PestControl


@farm.route("/dashboard")
@login_required
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
def field_map():
    """Display field map view"""
    # You would add your field map logic here
    return render_template("dashboard/field_map.html", active_page="field_map")


@farm.route("/analytics")
@login_required
def analytics():
    """Display analytics view"""
    # You would add your analytics logic here
    return render_template("dashboard/analytics.html", active_page="analytics")


@farm.route("/irrigation")
@login_required
def irrigation():
    """Display irrigation management view"""
    # You would add your irrigation logic here
    return render_template("dashboard/irrigation.html", active_page="irrigation")


@farm.route("/weather")
@login_required
def weather():
    """Display weather forecast view"""
    # Redirect to the weather module
    return redirect(url_for("weather.dashboard"))


@farm.route("/pest_control")
@login_required
def pest_control():
    """Display pest control view"""
    # Redirect to the pest control module
    return redirect(url_for("pest.dashboard"))


@farm.route("/schedule")
@login_required
def schedule():
    """Display schedule view"""
    # You would add your schedule logic here
    return render_template("dashboard/schedule.html", active_page="schedule")


@farm.route("/register", methods=["GET", "POST"])
@login_required
def register_farm():
    """Register a new farm"""
    if not current_user.is_approved:
        if request.is_json:
            return (
                jsonify(
                    {
                        "error": "Your account must be approved before registering a farm."
                    }
                ),
                403,
            )
        flash("Your account must be approved before registering a farm.", "warning")
        return redirect(url_for("farm.dashboard"))

    if request.method == "POST":
        if request.is_json:
            try:
                data = request.get_json()

                # Basic validation
                required_fields = ["name", "size_acres", "crop_type"]
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({"error": f"{field} is required"}), 400

                # Create new farm with extended fields
                farm = Farm(
                    name=data["name"],
                    size=float(
                        data["size_acres"]
                    ),  # Keep size field for backwards compatibility
                    size_acres=float(data["size_acres"]),
                    crop_type=data["crop_type"],
                    description=data.get("description", ""),
                    user_id=current_user.id,
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    region=data.get("region"),
                    soil_type=data.get("soil_type"),
                    ph_level=data.get("ph_level"),
                    soil_notes=data.get("soil_notes"),
                    irrigation_type=data.get("irrigation_type"),
                    water_source=data.get("water_source"),
                )

                # Set location from coordinates if provided
                if data.get("latitude") and data.get("longitude"):
                    farm.location = f"({data['latitude']}, {data['longitude']})"
                else:
                    farm.location = data.get("region", "Unknown")

                db.session.add(farm)
                db.session.commit()

                # Process team members if provided
                if data.get("team_members"):
                    try:
                        from ..auth.models import User

                        for member in data["team_members"]:
                            user = User.query.filter_by(email=member["email"]).first()
                            if user:
                                team_member = FarmTeamMember(
                                    farm_id=farm.id,
                                    user_id=user.id,
                                    role=member["role"],
                                    added_by=current_user.id,
                                )
                                db.session.add(team_member)
                        db.session.commit()
                    except Exception as e:
                        current_app.logger.error(f"Error adding team members: {str(e)}")
                        # Don't fail the whole request if team member addition fails

                return (
                    jsonify(
                        {"message": "Farm registered successfully!", "farm_id": farm.id}
                    ),
                    201,
                )

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error registering farm: {str(e)}")
                return jsonify({"error": str(e)}), 500
        else:
            # Handle regular form submission
            form = FarmForm()
            if form.validate_on_submit():
                try:
                    farm = Farm(
                        name=form.name.data,
                        location=form.location.data,
                        size_acres=form.size_acres.data,
                        crop_type=form.crop_type.data,
                        description=form.description.data,
                        user_id=current_user.id,
                    )
                    db.session.add(farm)
                    db.session.commit()
                    flash("Farm registered successfully!", "success")
                    return redirect(url_for("farm.view_farm", farm_id=farm.id))
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error registering farm: {str(e)}")
                    flash("An error occurred while registering the farm.", "error")

    # GET request - show the registration form
    form = FarmForm()
    return render_template(
        "farm/register_farm.html", form=form, active_page="dashboard"
    )


@farm.route("/view/<int:farm_id>")
@login_required
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
            )
        },
        "farm_count": Farm.query.filter_by(user_id=current_user.id).count(),
        "sensor_data_count": SensorData.query.filter_by(
            user_id=current_user.id
        ).count(),
        "alert_count": Alert.query.filter_by(user_id=current_user.id).count(),
    }
    return jsonify(debug_info)


@login_required
def dashboard_data():
    """API endpoint that provides dashboard data in JSON format"""
    # Get the user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()

    if not farm:
        return jsonify({"error": "No farm found. Please register a farm first."}), 404

    # Get the selected field (for now, we'll use a mock field)
    field = "Field A-12"  # This would come from the database in a real application

    # 1. Farm & Field Information
    farm_info = {
        "name": farm.name,
        "field": field,
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 2. Weather & Forecast
    # Try to extract latitude and longitude from the farm location
    weather_data = {}
    try:
        # Check if location contains lat/long information
        if "," in farm.location:
            lat, lon = map(float, farm.location.split(","))

            # Call OpenWeather API (if configured)
            if (
                hasattr(current_app.config, "OPENWEATHER_API_KEY")
                and current_app.config["OPENWEATHER_API_KEY"]
            ):
                weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={current_app.config['OPENWEATHER_API_KEY']}"
                response = requests.get(weather_url)

                if response.status_code == 200:
                    data = response.json()
                    current = data["current"]

                    weather_data = {
                        "temperature": round(current["temp"]),
                        "condition": current["weather"][0]["main"],
                        "icon": current["weather"][0]["icon"],
                        "forecast": (
                            "Light rain expected in 36 hours"
                            if "rain" in data["daily"][1]
                            else "No precipitation expected"
                        ),
                    }
            else:
                # Fallback if OpenWeather not configured
                weather_data = {
                    "temperature": 24,  # Fallback data
                    "condition": "Sunny",
                    "icon": "01d",
                    "forecast": "Weather forecast unavailable (API not configured)",
                }
        else:
            # Fallback if no location set
            weather_data = {
                "temperature": 24,  # Fallback data
                "condition": "Sunny",
                "icon": "01d",
                "forecast": "Set farm location for weather forecast",
            }
    except Exception as e:
        current_app.logger.error(f"Weather API error: {str(e)}")
        weather_data = {
            "temperature": 24,  # Fallback data
            "condition": "Sunny",
            "icon": "01d",
            "forecast": "Weather forecast unavailable",
        }

    # 3. Soil & Field Health
    # Get the latest sensor data
    soil_moisture = (
        SensorData.query.filter_by(farm_id=farm.id, sensor_type="soil_moisture")
        .order_by(SensorData.timestamp.desc())
        .first()
    )

    # Mock data for now - would come from actual sensor readings
    soil_health = {
        "overall_health": 82,  # Mock percentage
        "improvement": 2,  # Mock percentage improvement
        "quality": 76,
        "nitrogen": 42,  # ppm
        "phosphorus": 28,  # ppm
        "ph_level": 6.8,
        "organic_matter": 4.2,  # percentage
        "moisture": soil_moisture.value if soil_moisture else 64,  # percentage
        "last_irrigation": "2 days ago",
        "next_irrigation": "Tomorrow",
    }

    # 4. Crop Growth & Harvest
    # Get the current farm stage
    farm_stage = FarmStage.query.filter_by(farm_id=farm.id, status="Active").first()

    crop_growth = {
        "stage": farm_stage.stage_name if farm_stage else "Vegetative",
        "progress": 45,  # percentage completion of current stage
        "days": "28/62",  # days in current growth cycle
        "next_stage": "Flowering (in 14 days)",
        "harvest_date": "August 15",
    }

    # 5. Field Metrics Historical Data
    # This would come from sensor history, but for now we'll use mock data
    historical_data = {
        "temperature": [22, 24, 26, 25, 27, 26, 24, 25, 26, 28, 29, 27, 26, 24, 23],
        "moisture": [68, 65, 62, 60, 58, 75, 72, 68, 65, 62, 59, 56, 53, 70, 68],
        "growth": [
            2.1,
            2.3,
            2.8,
            3.0,
            3.2,
            3.1,
            2.9,
            2.7,
            2.5,
            2.4,
            2.2,
            2.0,
            1.9,
            1.8,
            1.7,
        ],
        "soil_health": [76, 75, 74, 76, 78, 80, 78, 77, 76, 75, 74, 73, 75, 78, 77],
        "dates": [
            "May 1",
            "May 3",
            "May 5",
            "May 7",
            "May 9",
            "May 11",
            "May 13",
            "May 15",
            "May 17",
            "May 19",
            "May 21",
            "May 23",
            "May 25",
            "May 27",
            "May 29",
        ],
    }

    # 6. Alerts and Recommendations
    # Get recent alerts
    alerts = (
        Alert.query.filter_by(farm_id=farm.id, is_read=False)
        .order_by(Alert.created_at.desc())
        .limit(3)
        .all()
    )

    alerts_data = []
    for alert in alerts:
        alerts_data.append(
            {
                "id": alert.id,
                "title": alert.alert_type,  # Using alert_type as the title
                "message": alert.message,
                "severity": alert.severity,
                "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    # 7. Recommended Actions
    # These would come from an AI recommendation system or predefined rules
    # Using mock data for now
    recommendations = [
        {
            "action": "Apply Fertilizer",
            "description": "Nitrogen levels in sectors 2 and 3 are below optimal. Apply supplemental fertilizer within 48 hours.",
            "priority": "High",
            "due": "Tomorrow",
        },
        {
            "action": "Pest Treatment",
            "description": "Early signs of corn earworm detected in sector 4. Apply organic pesticide to prevent infestation.",
            "priority": "Medium",
            "due": "In 3 days",
        },
        {
            "action": "Equipment Maintenance",
            "description": "Irrigation system inspection recommended. Last maintenance was performed 45 days ago.",
            "priority": "Info",
            "due": "This week",
        },
    ]

    # Combine all data into a single response
    response_data = {
        "farm_info": farm_info,
        "weather": weather_data,
        "soil_health": soil_health,
        "crop_growth": crop_growth,
        "historical_data": historical_data,
        "alerts": alerts_data,
        "recommendations": recommendations,
    }

    return jsonify(response_data)
