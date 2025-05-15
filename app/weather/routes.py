# app/weather/routes.py
import requests
from datetime import datetime
from flask import render_template, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import weather
from ..farm.models import Farm
from ..decorators import require_farm_registration
from app import db

# Your OpenWeatherMap API key
OPENWEATHER_API_KEY = "9ec417826bab17ebcc02904f96c4f776"


@weather.route("/dashboard")
@login_required
@require_farm_registration
def dashboard():
    """Weather dashboard for farmer's location"""
    # Initialize template variables - ALWAYS pass these
    template_vars = {
        "has_location": False,
        "farm": None,
        "current": None,
        "hourly": [],
        "daily": [],
        "alerts": [],
        "rainfall": 0,
        "error": False,
        "active_page": "weather",
    }

    # Get user's first farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    template_vars["farm"] = farm

    if not farm:
        flash("Please register a farm first to view weather data.", "warning")
        return render_template("dashboard/weather.html", **template_vars)

    # Try to get lat/lon from farm
    lat, lon = None, None

    # Check if farm has direct latitude/longitude attributes
    if hasattr(farm, "latitude") and hasattr(farm, "longitude"):
        lat = farm.latitude
        lon = farm.longitude
    # Check if location is stored as "lat,lon" string
    elif farm.location and "," in farm.location:
        try:
            lat, lon = map(float, farm.location.split(","))
        except ValueError:
            pass

    if not lat or not lon:
        flash("Please update your farm location to view weather data.", "warning")
        return render_template("dashboard/weather.html", **template_vars)

    # We have location
    template_vars["has_location"] = True

    try:
        # Fetch weather data
        weather_data = fetch_weather_data(lat, lon)

        # Update template variables with actual data
        template_vars.update(
            {
                "current": weather_data["current"],
                "hourly": weather_data["hourly"],
                "daily": weather_data["daily"],
                "alerts": weather_data.get("alerts", []),
                "rainfall": weather_data["current"].get("rain", 0),
            }
        )

        return render_template("dashboard/weather.html", **template_vars)

    except Exception as e:
        current_app.logger.error(f"Error fetching weather data: {str(e)}")
        flash("Unable to retrieve weather data. Please try again later.", "danger")
        template_vars["error"] = True
        return render_template("dashboard/weather.html", **template_vars)


def fetch_weather_data(lat, lon):
    """Fetch weather data from OpenWeatherMap"""
    # Use One Call API
    url = f"https://api.openweathermap.org/data/2.5/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "exclude": "minutely",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Process the data to match template expectations
    weather_data = {
        "current": process_current_weather(data["current"]),
        "hourly": [process_hourly_weather(hour) for hour in data["hourly"][:24]],
        "daily": [process_daily_weather(day) for day in data["daily"][:7]],
        "alerts": data.get("alerts", []),
    }

    return weather_data


def process_current_weather(current):
    """Process current weather data to match template expectations"""
    return {
        "temp": round(current["temp"]),
        "feels_like": round(current["feels_like"]),
        "humidity": current["humidity"],
        "pressure": current["pressure"],
        "wind_speed": round(current["wind_speed"] * 3.6, 1),  # m/s to km/h
        "wind_deg": current["wind_deg"],
        "uvi": current["uvi"],
        "clouds": current["clouds"],
        "visibility": current.get("visibility", 10000) / 1000,  # m to km
        "dew_point": round(current["dew_point"]),
        "description": current["weather"][0]["description"],
        "icon": current["weather"][0]["icon"],
        "main": current["weather"][0]["main"],
        "condition": current["weather"][0]["main"],  # For template compatibility
        "time": datetime.fromtimestamp(current["dt"]),
        "dt": datetime.fromtimestamp(current["dt"]),  # Keep both for compatibility
        "sunrise": datetime.fromtimestamp(current["sunrise"]),
        "sunset": datetime.fromtimestamp(current["sunset"]),
        "rain": current.get("rain", {}).get("1h", 0),
    }


def process_hourly_weather(hour):
    """Process hourly weather data to match template expectations"""
    return {
        "temp": round(hour["temp"]),
        "feels_like": round(hour["feels_like"]),
        "humidity": hour["humidity"],
        "wind_speed": round(hour["wind_speed"] * 3.6, 1),
        "pop": int(hour["pop"] * 100),  # Probability of precipitation
        "rain": hour.get("rain", {}).get("1h", 0),
        "description": hour["weather"][0]["description"],
        "icon": hour["weather"][0]["icon"],
        "main": hour["weather"][0]["main"],
        "condition": hour["weather"][0]["main"],  # For template compatibility
        "time": datetime.fromtimestamp(hour["dt"]),
        "dt": datetime.fromtimestamp(hour["dt"]),  # Keep both for compatibility
    }


def process_daily_weather(day):
    """Process daily weather data to match template expectations"""
    return {
        "temp_min": round(day["temp"]["min"]),
        "temp_max": round(day["temp"]["max"]),
        "temp_day": round(day["temp"]["day"]),
        "temp_night": round(day["temp"]["night"]),
        "temp": day["temp"],  # Include full temp object
        "humidity": day["humidity"],
        "wind_speed": round(day["wind_speed"] * 3.6, 1),
        "pop": int(day["pop"] * 100),
        "rain": day.get("rain", 0),
        "description": day["weather"][0]["description"],
        "icon": day["weather"][0]["icon"],
        "main": day["weather"][0]["main"],
        "condition": day["weather"][0]["main"],  # For template compatibility
        "day": datetime.fromtimestamp(day["dt"]),  # For template compatibility
        "dt": datetime.fromtimestamp(day["dt"]),
        "sunrise": datetime.fromtimestamp(day["sunrise"]),
        "sunset": datetime.fromtimestamp(day["sunset"]),
        "uvi": day.get("uvi", 0),
    }


@weather.route("/update-location", methods=["GET", "POST"])
@login_required
@require_farm_registration
def update_location():
    """Update farm location page"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()

    if not farm:
        flash("Please register a farm first.", "warning")
        return redirect(url_for("farm.dashboard"))

    if request.method == "POST":
        # Handle form submission
        try:
            latitude = request.form.get("latitude")
            longitude = request.form.get("longitude")

            if not latitude or not longitude:
                flash("Please provide both latitude and longitude.", "danger")
                return render_template(
                    "dashboard/update_location.html", farm=farm, active_page="weather"
                )

            # Update farm location
            if hasattr(farm, "latitude") and hasattr(farm, "longitude"):
                farm.latitude = float(latitude)
                farm.longitude = float(longitude)
            else:
                farm.location = f"{latitude},{longitude}"

            db.session.commit()

            flash("Farm location updated successfully!", "success")
            return redirect(url_for("weather.dashboard"))

        except Exception as e:
            current_app.logger.error(f"Error updating location: {str(e)}")
            flash(f"Error updating location: {str(e)}", "danger")

    # GET request - show form
    return render_template(
        "dashboard/update_location.html", farm=farm, active_page="weather"
    )


@weather.route("/api/current")
@login_required
@require_farm_registration
def api_current_weather():
    """API endpoint for current weather"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()

    if not farm:
        return jsonify({"error": "No farm found"}), 400

    # Get lat/lon
    lat, lon = None, None
    if hasattr(farm, "latitude") and hasattr(farm, "longitude"):
        lat = farm.latitude
        lon = farm.longitude
    elif farm.location and "," in farm.location:
        try:
            lat, lon = map(float, farm.location.split(","))
        except ValueError:
            pass

    if not lat or not lon:
        return jsonify({"error": "No location data"}), 400

    try:
        weather_data = fetch_weather_data(lat, lon)
        return jsonify(weather_data["current"])
    except Exception as e:
        current_app.logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@weather.route("/api/forecast")
@login_required
@require_farm_registration
def api_forecast():
    """API endpoint for weather forecast"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()

    if not farm:
        return jsonify({"error": "No farm found"}), 400

    # Get lat/lon
    lat, lon = None, None
    if hasattr(farm, "latitude") and hasattr(farm, "longitude"):
        lat = farm.latitude
        lon = farm.longitude
    elif farm.location and "," in farm.location:
        try:
            lat, lon = map(float, farm.location.split(","))
        except ValueError:
            pass

    if not lat or not lon:
        return jsonify({"error": "No location data"}), 400

    try:
        weather_data = fetch_weather_data(lat, lon)
        return jsonify(
            {"hourly": weather_data["hourly"], "daily": weather_data["daily"]}
        )
    except Exception as e:
        current_app.logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500
