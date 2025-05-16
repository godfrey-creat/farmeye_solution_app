# app/main/routes.py
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from . import main
from ..auth.models import User
from ..farm.models import Farm, Alert
from ..decorators import require_farm_registration


@main.route("/")
def index():
    """Home page"""
    if current_user.is_authenticated:
        # Check if user has registered a farm
        has_farm = Farm.query.filter_by(user_id=current_user.id).first() is not None
        if not has_farm:
            return redirect(url_for("farm.register_farm"))

        farms = Farm.query.filter_by(user_id=current_user.id).all()

        # Get recent alerts for notification count
        alerts = (
            Alert.query.filter_by(user_id=current_user.id, is_read=False)
            .order_by(Alert.created_at.desc())
            .all()
        )

        # Count unread alerts for notification badge
        unread_count = len(alerts)

        # Field health data
        field_health = {
            "status": "Excellent",
            "overall_health": 82,
            "improvement": 2,
            "improvement_direction": "up",
        }

        # Soil health data
        soil_health = {
            "status": "Good",
            "quality": 76,
            "nitrogen": 42,  # ppm
            "phosphorus": 28,  # ppm
            "ph_level": 6.8,
            "organic_matter": 4.2,  # percentage
        }

        # Moisture data
        moisture = {
            "status": "Normal",
            "current_level": 64,  # percentage
            "optimal_range": "60-80%",
            "last_reading": "Today at 10:35 AM",
            "last_irrigation": "2 days ago",
            "next_irrigation": "Tomorrow",
        }

        # Growth stage data
        growth = {
            "status": "On Track",
            "stage": "Vegetative",
            "progress": 45,  # percentage completion of current stage
            "days": "28/62",  # days in current growth cycle
            "next_stage": "Flowering (in 14 days)",
            "harvest_date": "August 15",
        }

        return render_template(
            "dashboard/index.html",
            farms=farms,
            alerts=alerts,
            unread_count=unread_count,
            field_health=field_health,
            soil_health=soil_health,
            moisture=moisture,
            growth=growth,
            active_page="dashboard",
        )
    return redirect(url_for("auth.login"))


@main.route("/weather")
@login_required
def weather_redirect():
    """Redirect to the weather dashboard in the weather module"""
    return redirect(url_for("weather.dashboard"))


@main.route("/update_farm_location")
@login_required
def update_farm_location_redirect():
    """Redirect to the update location page in the weather module"""
    return redirect(url_for("weather.update_location"))


@main.route("/pest_control")
@login_required
def pest_control_redirect():
    """Redirect to the pest control dashboard in the pest module"""
    return redirect(url_for("pest.dashboard"))


# @main.route('/about')
# def about():
#    """About page"""
#    return render_template('about.html')

# @main.route('/contact')
# def contact():
#    """Contact page"""
#    return render_template('contact.html')