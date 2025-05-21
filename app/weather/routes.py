# Updated routes.py with city name in URL path

import requests
import json
import math
import platform
from datetime import datetime, timedelta
from flask import (
    render_template,
    jsonify,
    redirect,
    url_for,
    flash,
    current_app,
    request,
)
from flask_login import login_required, current_user
from . import weather
from ..farm.models import Farm
from ..decorators import require_farm_registration
from app import db

import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Your OpenWeatherMap API key
OPENWEATHER_API_KEY = (
    "073c86bb08ab26b37ab8a79c850ec27d"  # Replace with your actual API key
)


def format_hour(dt):
    """Format hour without leading zero in a cross-platform way"""
    hour_str = dt.strftime("%I %p")
    # Strip leading zero but keep spaces
    if hour_str.startswith("0"):
        hour_str = hour_str[1:]
    return hour_str


# Redirect from dashboard to the default location
@weather.route("/dashboard")
@login_required
@require_farm_registration
def dashboard():
    """Redirect to the user's farm location"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()

    if not farm or not farm.location:
        flash("Please update your farm location to view weather data.", "warning")
        return render_template(
            "dashboard/weather.html",
            has_location=False,
            farm=farm,
            error=False,
            active_page="weather",
        )

    # Extract location name (first word) from farm.location
    location_name = farm.location.split()[0]

    # Redirect to the location-specific URL
    return redirect(url_for("weather.location_weather", location=location_name))


# Simplified location_weather function to ensure mock data works
@weather.route("/<location>")
@login_required
@require_farm_registration
def location_weather(location):
    """Weather dashboard for specific location"""
    # Initialize template variables
    template_vars = {
        "has_location": True,
        "farm": None,
        "current": None,
        "hourly": [],
        "daily": [],
        "alerts": [],
        "rainfall": 0,
        "error": False,
        "active_page": "weather",
        "format_hour": format_hour,
        "running_on_windows": platform.system() == "Windows",
        "location_name": location,  # Add location name from URL
    }

    # Get user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    template_vars["farm"] = farm

    if not farm:
        flash("Please register a farm first to view weather data.", "warning")
        template_vars["has_location"] = False
        return render_template("dashboard/weather.html", **template_vars)

    try:
        # First try to get real weather data
        current_app.logger.info(f"Fetching real weather for location: {location}")

        # Try API call with a short timeout to fail fast if network issues
        real_weather = None
        try:
            real_weather = fetch_weather_data(location)
        except Exception as e:
            current_app.logger.error(f"Error fetching real weather: {str(e)}")
            real_weather = None

        # If real weather data is not available, use mock data
        if not real_weather:
            current_app.logger.warning("Using mock data because API call failed")
            weather_data = get_mock_weather_data()
            flash("Using simulated weather data due to connectivity issues.", "info")
        else:
            weather_data = real_weather

        # Prepare chart data as JSON
        try:
            # Simple, safe chart data preparation
            chart_data = {
                "hour_labels": [],
                "hour_temps": [],
                "day_labels": [],
                "day_pops": [],
            }

            # Add hourly data
            if weather_data.get("hourly"):
                for hour in weather_data["hourly"][:24]:
                    # Format hour safely
                    hour_str = "Unknown"
                    if isinstance(hour.get("dt"), datetime):
                        hour_dt = hour.get("dt")
                        hour_str = format_hour(hour_dt)
                    chart_data["hour_labels"].append(hour_str)
                    chart_data["hour_temps"].append(hour.get("temp", 0))

            # Add daily data
            if weather_data.get("daily"):
                for day in weather_data["daily"]:
                    day_str = "Unknown"
                    if isinstance(day.get("dt"), datetime):
                        day_dt = day.get("dt")
                        day_str = day_dt.strftime("%a")
                    chart_data["day_labels"].append(day_str)
                    chart_data["day_pops"].append(day.get("pop", 0))

            template_vars["chart_data"] = chart_data
            template_vars["chart_data_json"] = json.dumps(chart_data)
        except Exception as chart_err:
            current_app.logger.error(f"Error preparing chart data: {str(chart_err)}")
            # Provide empty chart data as fallback
            template_vars["chart_data"] = {
                "hour_labels": [],
                "hour_temps": [],
                "day_labels": [],
                "day_pops": [],
            }
            template_vars["chart_data_json"] = (
                '{"hour_labels": [], "hour_temps": [], "day_labels": [], "day_pops": []}'
            )

        # Update template variables with weather data
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
        current_app.logger.error(f"Error in location_weather view: {str(e)}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")

        # Last resort - try to use mock data even if something else failed
        try:
            weather_data = get_mock_weather_data()
            template_vars.update(
                {
                    "current": weather_data["current"],
                    "hourly": weather_data["hourly"],
                    "daily": weather_data["daily"],
                    "alerts": [],
                    "rainfall": 0,
                    "chart_data_json": '{"hour_labels": [], "hour_temps": [], "day_labels": [], "day_pops": []}',
                }
            )
            flash("Using simulated weather data due to technical issues.", "info")
            return render_template("dashboard/weather.html", **template_vars)
        except:
            # If all else fails, show error UI
            flash("Unable to retrieve weather data. Please try again later.", "danger")
            template_vars["error"] = True
            return render_template("dashboard/weather.html", **template_vars)


def fetch_weather_data(location):
    """Fetch weather data from OpenWeatherMap using location name"""
    current_app.logger.info(f"Fetching weather for location: {location}")

    try:
        # Current Weather API call (accepts city names directly)
        current_url = "https://api.openweathermap.org/data/2.5/weather"
        current_params = {
            "q": location,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        }

        current_app.logger.info(f"Requesting current weather from {current_url}")
        current_response = requests.get(current_url, params=current_params)
        current_app.logger.info(
            f"Current weather API status: {current_response.status_code}"
        )

        if current_response.status_code != 200:
            current_app.logger.error(f"API Error: {current_response.text}")
            return None

        current_data = current_response.json()

        # Forecast API call (accepts city names directly)
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        forecast_params = {
            "q": location,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        }

        current_app.logger.info(f"Requesting forecast from {forecast_url}")
        forecast_response = requests.get(forecast_url, params=forecast_params)
        current_app.logger.info(f"Forecast API status: {forecast_response.status_code}")

        if forecast_response.status_code != 200:
            current_app.logger.error(f"API Error: {forecast_response.text}")
            return None

        forecast_data = forecast_response.json()

        # Process data for template
        weather_data = {
            "current": process_current_weather_alternative(current_data),
            "hourly": process_forecast_hourly(forecast_data),
            "daily": process_forecast_daily(forecast_data),
            "alerts": [],  # Not available in the regular API
        }

        current_app.logger.info("Weather data processed successfully")
        return weather_data

    except requests.RequestException as e:
        current_app.logger.error(f"API request error: {str(e)}")
        return None
    except KeyError as e:
        current_app.logger.error(f"Data parsing error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return None


def process_current_weather_alternative(data):
    """Process current weather data from regular Weather API"""
    return {
        "temp": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "humidity": round(data["main"]["humidity"]),
        "pressure": round(data["main"]["pressure"]),
        "wind_speed": round(data["wind"]["speed"] * 3.6, 1),  # m/s to km/h
        "wind_deg": round(data["wind"]["deg"]),
        "uvi": 0,  # Not available in regular API
        "clouds": data["clouds"]["all"],
        "visibility": data.get("visibility", 10000) / 1000,  # m to km
        "dew_point": 0,  # Not available in regular API
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "main": data["weather"][0]["main"],
        "condition": data["weather"][0]["main"],
        "time": datetime.fromtimestamp(data["dt"]),
        "dt": datetime.fromtimestamp(data["dt"]),
        "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]),
        "sunset": datetime.fromtimestamp(data["sys"]["sunset"]),
        "rain": round(data.get("rain", {}).get("1h", 0), 2),
    }


def process_forecast_hourly(data):
    """Process hourly forecast data from regular Forecast API"""
    hourly_list = []

    # Get next 24 hours (forecast is in 3-hour intervals)
    for i, item in enumerate(data["list"]):
        if i >= 8:  # Limit to 8 entries (24 hours)
            break

        hourly_list.append(
            {
                "temp": round(item["main"]["temp"]),
                "feels_like": round(item["main"]["feels_like"]),
                "humidity": item["main"]["humidity"],
                "wind_speed": round(item["wind"]["speed"] * 3.6, 1),
                "pop": int(item.get("pop", 0) * 100),  # Probability of precipitation
                "rain": round(
                    item.get("rain", {}).get("3h", 0) / 3, 2
                ),  # Convert 3h rain to 1h
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"],
                "main": item["weather"][0]["main"],
                "condition": item["weather"][0]["main"],
                "time": datetime.fromtimestamp(item["dt"]),
                "dt": datetime.fromtimestamp(item["dt"]),
            }
        )

    return hourly_list


def process_forecast_daily(data):
    """Process daily forecast data from regular Forecast API"""
    # Group forecast by day
    daily_data = {}

    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        day_key = dt.strftime("%Y-%m-%d")

        if day_key not in daily_data:
            daily_data[day_key] = {
                "dt": dt,
                "temp_min": item["main"]["temp_min"],
                "temp_max": item["main"]["temp_max"],
                "humidity": [],
                "pop": [],
                "rain": 0,
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"],
                "main": item["weather"][0]["main"],
                "wind_speed": [],
            }
        else:
            daily_data[day_key]["temp_min"] = min(
                daily_data[day_key]["temp_min"], item["main"]["temp_min"]
            )
            daily_data[day_key]["temp_max"] = max(
                daily_data[day_key]["temp_max"], item["main"]["temp_max"]
            )

        # Collect values for averaging
        daily_data[day_key]["humidity"].append(item["main"]["humidity"])
        daily_data[day_key]["pop"].append(item.get("pop", 0))
        daily_data[day_key]["rain"] += item.get("rain", {}).get("3h", 0)
        daily_data[day_key]["wind_speed"].append(item["wind"]["speed"])

    # Process daily data
    daily_list = []

    for day_key in sorted(daily_data.keys()):
        day = daily_data[day_key]

        # Calculate average values
        avg_humidity = (
            round(sum(day["humidity"]) / len(day["humidity"]), 2)
            if day["humidity"]
            else 0
        )
        avg_wind_speed = (
            round(sum(day["wind_speed"]) / len(day["wind_speed"]) * 3.6, 2)
            if day["wind_speed"]
            else 0
        )
        avg_pop = round(max(day["pop"]) * 100, 2) if day["pop"] else 0

        # Create a data structure compatible with the template
        day_weather = {
            "dt": day["dt"],
            "day": day["dt"],
            "temp_min": round(day["temp_min"], 2),
            "temp_max": round(day["temp_max"], 2),
            "temp_day": round(day["temp_max"], 2),
            "temp_night": round(day["temp_min"], 2),
            "temp": {
                "min": round(day["temp_min"], 2),
                "max": round(day["temp_max"], 2),
                "day": round(day["temp_max"], 2),
                "night": round(day["temp_min"], 2),
            },
            "humidity": avg_humidity,
            "wind_speed": avg_wind_speed,
            "pop": avg_pop,
            "rain": round(day["rain"], 2),
            "description": day["description"],
            "icon": day["icon"],
            "main": day["main"],
            "condition": day["main"],
            "sunrise": day["dt"].replace(hour=6, minute=0, second=0),  # Approximation
            "sunset": day["dt"].replace(hour=18, minute=0, second=0),  # Approximation
            "uvi": 0,  # Not available in regular API
        }

        daily_list.append(day_weather)

        # Limit to 7 days
        if len(daily_list) >= 7:
            break

    return daily_list


# Fixed mock data function - renaming the pop attribute to probability
def get_mock_weather_data():
    """Return mock weather data for development when API is unavailable"""
    current_app.logger.info("Using mock weather data for development")

    # Current time and date
    now = datetime.now()

    # Mock current weather
    current = {
        "temp": 25,
        "feels_like": 26,
        "humidity": 65,
        "pressure": 1013,
        "wind_speed": 12.5,
        "wind_deg": 180,
        "uvi": 4.5,
        "clouds": 40,
        "visibility": 10,
        "dew_point": 18,
        "description": "scattered clouds",
        "icon": "03d",
        "main": "Clouds",
        "condition": "Clouds",
        "time": now,
        "dt": now,
        "sunrise": now.replace(hour=6, minute=30, second=0),
        "sunset": now.replace(hour=18, minute=45, second=0),
        "rain": 0,
    }

    # Mock hourly forecast
    hourly = []
    for i in range(24):
        hour_time = now + timedelta(hours=i)
        hour_temp = 25 + 5 * math.sin(i * math.pi / 12)  # Temperature curve
        hourly.append(
            {
                "temp": round(hour_temp),
                "feels_like": round(hour_temp + 1),
                "humidity": 65,
                "wind_speed": 12.5,
                "probability": (
                    20 if i % 4 == 0 else 10
                ),  # Changed from pop to probability
                "rain": 0.5 if i % 4 == 0 else 0,
                "description": "scattered clouds",
                "icon": "03d",
                "main": "Clouds",
                "condition": "Clouds",
                "time": hour_time,
                "dt": hour_time,
            }
        )

    # Mock daily forecast
    daily = []
    for i in range(7):
        day_time = now + timedelta(days=i)
        daily.append(
            {
                "temp_min": 20,
                "temp_max": 30,
                "temp_day": 28,
                "temp_night": 22,
                "temp": {
                    "min": 20,
                    "max": 30,
                    "day": 28,
                    "night": 22,
                },
                "humidity": 65,
                "wind_speed": 12.5,
                "probability": (
                    30 if i % 2 == 0 else 10
                ),  # Changed from pop to probability
                "rain": 2 if i % 2 == 0 else 0,
                "description": "scattered clouds",
                "icon": "03d",
                "main": "Clouds",
                "condition": "Clouds",
                "day": day_time,
                "dt": day_time,
                "sunrise": day_time.replace(hour=6, minute=30, second=0),
                "sunset": day_time.replace(hour=18, minute=45, second=0),
                "uvi": 4.5,
            }
        )

    return {
        "current": current,
        "hourly": hourly,
        "daily": daily,
        "alerts": [],
    }


# API endpoints with location-based routes
@weather.route("/api/current/<location>")
@login_required
@require_farm_registration
def api_current_weather(location):
    """API endpoint for current weather for specific location"""
    try:
        weather_data = fetch_weather_data(location)
        if not weather_data:
            return jsonify({"error": "Failed to retrieve weather data"}), 500

        return jsonify(weather_data["current"])
    except Exception as e:
        current_app.logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@weather.route("/api/forecast/<location>")
@login_required
@require_farm_registration
def api_forecast(location):
    """API endpoint for weather forecast for specific location"""
    try:
        weather_data = fetch_weather_data(location)
        if not weather_data:
            return jsonify({"error": "Failed to retrieve weather data"}), 500

        return jsonify(
            {"hourly": weather_data["hourly"], "daily": weather_data["daily"]}
        )
    except Exception as e:
        current_app.logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Add this route for testing
@weather.route("/test")
@login_required
def test_weather():
    """Test route that always works with hardcoded data"""
    template_vars = {
        "has_location": True,
        "farm": None,
        "error": False,
        "active_page": "weather",
        "format_hour": format_hour,
        "running_on_windows": platform.system() == "Windows",
        "location_name": "Test Location",
    }

    # Get user's farm but still work if not found
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    template_vars["farm"] = farm

    # Always use mock data
    weather_data = get_mock_weather_data()

    # Simple chart data
    chart_data = {
        "hour_labels": [
            "1 AM",
            "2 AM",
            "3 AM",
            "4 AM",
            "5 AM",
            "6 AM",
            "7 AM",
            "8 AM",
            "9 AM",
            "10 AM",
            "11 AM",
            "12 PM",
            "1 PM",
            "2 PM",
            "3 PM",
            "4 PM",
            "5 PM",
            "6 PM",
            "7 PM",
            "8 PM",
            "9 PM",
            "10 PM",
            "11 PM",
            "12 AM",
        ],
        "hour_temps": [
            22,
            21,
            20,
            19,
            18,
            19,
            20,
            22,
            24,
            26,
            27,
            28,
            29,
            30,
            29,
            28,
            26,
            25,
            24,
            23,
            22,
            21,
            20,
            19,
        ],
        "day_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "day_pops": [20, 10, 30, 10, 30, 10, 30],
    }

    template_vars["chart_data"] = chart_data
    template_vars["chart_data_json"] = json.dumps(chart_data)

    # Update template variables
    template_vars.update(
        {
            "current": weather_data["current"],
            "hourly": weather_data["hourly"],
            "daily": weather_data["daily"],
            "alerts": [],
            "rainfall": 0,
        }
    )

    flash("This is test data for debugging purposes.", "info")
    return render_template("dashboard/weather.html", **template_vars)
