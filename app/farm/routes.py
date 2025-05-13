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
from .forms import FarmForm, ImageUploadForm, SensorDataForm, FarmRegistrationForm
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
)
from ..auth.models import User  # Add this import
from ..decorators import require_farm_registration
import requests
from datetime import datetime, timedelta
from ..farm.models import Farm, SensorData, Alert, FarmStage, PestControl


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
    """Display field map view"""
    # You would add your field map logic here
    return render_template("dashboard/field_map.html", active_page="field_map")


@farm.route("/analytics")
@login_required
@require_farm_registration
def analytics():
    """Display analytics view"""
    # You would add your analytics logic here
    return render_template("dashboard/analytics.html", active_page="analytics")


@farm.route("/irrigation")
@login_required
@require_farm_registration
def irrigation():
    """Display irrigation management view"""
    # You would add your irrigation logic here
    return render_template("dashboard/irrigation.html", active_page="irrigation")


@farm.route("/weather")
@login_required
@require_farm_registration
def weather():
    """Display weather forecast view"""
    # Redirect to the weather module
    return redirect(url_for("weather.dashboard"))


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
                    farm = Farm(
                        name=farm_data["name"],
                        region=farm_data["region"],
                        user_id=current_user.id,
                        created_at=datetime.utcnow(),
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
                )  # For GET requests, render the registration page with CSRF protection
    form = FarmRegistrationForm()
    return render_template(
        "farm/farm_registration_standalone.html",
        form=form,
        current_user=current_user,  # Add current_user to template context
    )


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


@farm.route("/api/dashboard-data")
@login_required
def dashboard_data():
    """API endpoint that provides dashboard data in JSON format"""
    # Get the user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()

    if not farm:
        return jsonify({"error": "No farm found. Please register a farm first."}), 404

    # Get the selected field
    field = Field.query.filter_by(farm_id=farm.id).first()
    field_name = field.name if field else "No fields available"

    # Farm & Field Information
    farm_info = {
        "name": farm.name,
        "field": field_name,
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Get recent sensor data
    sensors = (
        SensorData.query.filter_by(farm_id=farm.id)
        .order_by(SensorData.timestamp.desc())
        .limit(5)
        .all()
    )
    sensor_data = [
        {
            "type": s.sensor_type,
            "value": s.value,
            "unit": s.unit,
            "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for s in sensors
    ]

    return jsonify(
        {"success": True, "data": {"farm_info": farm_info, "sensor_data": sensor_data}}
    )
