# app/api/routes.py
<<<<<<< HEAD
import openai
import os
from flask import jsonify, current_app, request
from sqlalchemy.orm import joinedload
from app import db
from sqlalchemy import func
from flask import abort
from datetime import datetime, timedelta
=======
from flask import jsonify, current_app, request
>>>>>>> origin/Dynamic-Parsing
from flask_login import login_required, current_user
import requests
from datetime import datetime, timedelta
from . import api
from ..farm.models import (
    Farm,
<<<<<<< HEAD
    Field,
    Sensor,
    SensorData,
    CropHealth,
    WeatherData,
    FarmImage,
    Alert,
    FarmStage,
    FarmTeamMember,
    LaborTask,
)

=======
    SensorData,
    Alert,
    FarmStage,
    PestControl,
    FarmTeamMember,
)
>>>>>>> origin/Dynamic-Parsing
import os
from dotenv import load_dotenv

load_dotenv()


@api.route("/dashboard-data", methods=["GET"])
@login_required
def dashboard_data():
    """API endpoint that provides dashboard data in JSON format"""
    # Get time range from query params
    time_range = request.args.get("range", "30")
    try:
        time_range = int(time_range)
    except ValueError:
        time_range = 30  # Get the user's farms
<<<<<<< HEAD
    farm = Farm.query.filter_by(user_id=current_user.id).all()
=======
    farms = Farm.query.filter_by(user_id=current_user.id).all()
>>>>>>> origin/Dynamic-Parsing
    farm_team_memberships = FarmTeamMember.query.filter_by(
        user_id=current_user.id
    ).all()
    team_farms = [membership.farm for membership in farm_team_memberships]
<<<<<<< HEAD
    all_farms = farm + team_farms
=======
    all_farms = farms + team_farms
>>>>>>> origin/Dynamic-Parsing

    if not all_farms:
        return jsonify(
            {
                "error": "No farm found. Please register a farm first.",
                "metrics": {},
                "recommendations": [],
                "alerts": [],
                "historical_data": None,
            }
        )

    # Use the first farm as the primary farm
    farm = all_farms[0]

<<<<<<< HEAD
def get_field_by_name(field_name, farm_id=None):
    """
    Retrieve a Field object by its name and optional farm_id.
    
    Args:
        field_name (str): The name of the field to look for.
        farm_id (int, optional): The ID of the farm (to disambiguate field names).

    Returns:
        Field: The matching Field object, or aborts with 404 if not found.
    """
    query = Field.query.filter_by(name=field_name)

    if farm_id is not None:
        query = query.filter_by(farm_id=farm_id)

    field = query.first()

    if not field:
        abort(404, description=f"Field '{field_name}' not found for farm_id {farm_id}.")

    return field    

# Enhanced version of your weather data API route
# Weather Data API Route - Provides the weather data for the dashboard
@api.route("/weather-data/<int:farm_id>", methods=["GET"])
def fetch_and_store_weather_data(farm_id):
    """
    Fetch and return the latest weather data for a given farm.
    If the farm's location is not set or an error occurs,
    return an appropriate error message.
    """
    weather_data = {
        "temperature": 24,
        "humidity": 50,
        "rainfall": 0.0,
        "wind_speed": 1.0,
        "condition": "Clear",  # Changed from "Unknown" to have a default icon
        "forecast": "Weather forecast unavailable"
    }
    
    try:
        # Retrieve the farm from the database
        farm = Farm.query.get(farm_id)
        if not farm:
            return jsonify({"error": "Farm not found"}), 404
        
        # Check if location has "lat,lon"
        if farm.location and "," in farm.location:
            lat, lon = map(float, farm.location.split(","))
            
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if not api_key:
                current_app.logger.warning("OPENWEATHER_API_KEY is not configured.")
                weather_data["forecast"] = "Weather forecast unavailable (API key missing)"
                return jsonify(weather_data)
            
            # OpenWeather One Call API
            weather_url = (
                f"https://api.openweathermap.org/data/2.5/onecall"
                f"?lat={lat}&lon={lon}&exclude=minutely,hourly,alerts&units=metric&appid={api_key}"
            )
            response = requests.get(weather_url, timeout=10)  # Added timeout
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            daily = data.get("daily", [{}])[1] if len(data.get("daily", [])) > 1 else {}
            
            # Get the main weather condition
            weather_condition = "Unknown"
            if current.get("weather") and len(current["weather"]) > 0:
                weather_condition = current["weather"][0].get("main", "Unknown")
            
            weather_data.update({
                "temperature": round(current.get("temp", 24)),
                "humidity": current.get("humidity", 50),
                "rainfall": daily.get("rain", 0.0) if isinstance(daily.get("rain"), (int, float)) else 0.0,
                "wind_speed": current.get("wind_speed", 1.0),
                "condition": weather_condition,
                "forecast": (
                    "Rain expected in 36 hours" if daily.get("rain") else "No rain expected"
                )
            })
            
            # Save to database
            weather_entry = WeatherData(
                farm_id=farm.id,
                timestamp=datetime.utcnow(),
                temperature=weather_data["temperature"],
                humidity=weather_data["humidity"],
                rainfall=weather_data["rainfall"],
                wind_speed=weather_data["wind_speed"],
                condition=weather_data["condition"]
            )
            
            db.session.add(weather_entry)
            db.session.commit()
        
        else:
            weather_data["forecast"] = "Set farm location for weather forecast"
    
    except requests.exceptions.RequestException as re:
        current_app.logger.error(f"Weather API request error: {str(re)}")
        weather_data["forecast"] = "Weather service unavailable"
    
    except Exception as e:
        current_app.logger.error(f"Weather data error: {str(e)}")
        weather_data["forecast"] = "Weather forecast unavailable"
    
    return jsonify(weather_data)

# 3. Soil & Field Health
def get_latest_soil_moisture(farm_id):
    # Check for an active soil moisture sensor for the given farm
    soil_sensors = Sensor.query.filter_by(
        farm_id=farm_id,
        sensor_type="soil_moisture",
        status="Active"
    ).all()

    if not soil_sensors:
        abort(404, description="No active soil moisture sensors found for this farm.")

    # Get sensor IDs
    sensor_ids = [sensor.id for sensor in soil_sensors]

    # Get the latest sensor data from those sensors
    latest_data = (
        SensorData.query
        .filter(
            SensorData.sensor_id.in_(sensor_ids),
            SensorData.status == "Valid",
            SensorData.sensor_type == "soil_moisture"
        )
=======
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

            # Set up default weather data in case the API call fails
            weather_data = {
                "temperature": 24,
                "condition": "Sunny",
                "icon": "01d",
                "forecast": "Weather forecast unavailable",
            }

            # Try to get API key from config
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if api_key:
                try:
                    weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={api_key}"
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
                                if "rain" in data.get("daily", [{}])[1]
                                else "No precipitation expected"
                            ),
                        }
                except Exception as e:
                    current_app.logger.error(f"OpenWeather API error: {str(e)}")
                    # Keep default weather data
            else:
                weather_data["forecast"] = (
                    "Weather forecast unavailable (API key not configured)"
                )
        else:
            weather_data = {
                "temperature": 24,  # Fallback data
                "condition": "Sunny",
                "icon": "01d",
                "forecast": "Set farm location for weather forecast",
            }
    except Exception as e:
        current_app.logger.error(f"Weather data processing error: {str(e)}")
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
>>>>>>> origin/Dynamic-Parsing
        .order_by(SensorData.timestamp.desc())
        .first()
    )

<<<<<<< HEAD
    if not latest_data:
        abort(404, description="No valid soil moisture data found.")

    return {
        "value": latest_data.value,
        "unit": latest_data.unit,
        "timestamp": latest_data.timestamp,
        "location": {
            "latitude": latest_data.latitude,
            "longitude": latest_data.longitude
        },
        "sensor_id": latest_data.sensor_id
    }
def get_recent_alerts(farm_id, limit=3):
    # Query recent unread alerts
    alerts = (
        Alert.query
        .filter_by(farm_id=farm_id, is_read=False)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )

    if not alerts:
        return []  # or return a default message

    alerts_data = []
    for alert in alerts:
        alerts_data.append({
            "id": alert.id,
            "title": alert.alert_type,
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status,
            "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return alerts_data
   

# Soil Health Card Data
soil_health = {
    "status": "Good",  # Could be derived from sensor data
    "quality": 76,  # Overall soil health score
    "nitrogen": 42,  # ppm
    "phosphorus": 28,  # ppm
    "ph_level": 6.8,
    "organic_matter": 4.2,  # percentage
}

def calculate_field_health(farm_id):
    from ..farm.models import SensorData, Alert, FarmStage
    from datetime import datetime, timedelta

    # --- 1. Fetch latest soil moisture data ---
    latest_soil_moisture = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="soil_moisture")
        .order_by(SensorData.timestamp.desc())
        .first()
    )
    
    soil_score = 0
    if latest_soil_moisture:
        moisture_value = latest_soil_moisture.value
        # Example thresholds — adjust based on agronomic needs
        if 30 <= moisture_value <= 60:
            soil_score = 30  # Healthy range
        elif 20 <= moisture_value < 30 or 60 < moisture_value <= 70:
            soil_score = 20  # Slightly off
        else:
            soil_score = 10  # Poor

    # --- 2. Count recent active alerts (last 7 days) and their severity ---
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_alerts = Alert.query.filter_by(farm_id=farm_id, is_read=False).filter(Alert.created_at >= week_ago).all()

    alert_score = 30
    if active_alerts:
        high_severity_count = sum(1 for a in active_alerts if a.severity == "high")
        medium_severity_count = sum(1 for a in active_alerts if a.severity == "medium")
        
        deductions = (high_severity_count * 10) + (medium_severity_count * 5)
        alert_score = max(0, 30 - deductions)

    # --- 3. Crop growth progress score ---
    farm_stage = FarmStage.query.filter_by(farm_id=farm_id, status="Active").first()
    progress_score = 0
    if farm_stage and farm_stage.start_date and farm_stage.end_date:
        total_days = (farm_stage.end_date - farm_stage.start_date).days
        elapsed_days = (datetime.utcnow() - farm_stage.start_date).days
        progress = int((elapsed_days / total_days) * 100) if total_days > 0 else 0
        progress_score = min(30, int(progress * 0.3))  # Scale to 30

    # --- 4. Final health score ---
    total_score = soil_score + alert_score + progress_score

    # --- 5. Compare to last week's score for improvement ---
    # Placeholder: you’d store previous week score in DB or session/log
    previous_score = 80
    improvement = total_score - previous_score
    direction = "up" if improvement >= 0 else "down"

    field_health = {
        "status": "Excellent" if total_score >= 75 else "Good" if total_score >= 50 else "Poor",
        "overall_health": total_score,
        "improvement": abs(improvement),
        "improvement_direction": direction,
    }

    return field_health    

# 4. Crop Growth & Harvest
# Get the current farm stage
def get_crop_growth_data(farm_id):
    # Get the active farm stage
    farm_stage = FarmStage.query.filter_by(farm_id=farm_id, status="Active").first()

    # If stage exists, calculate progress
    if farm_stage and farm_stage.start_date and farm_stage.end_date:
        total_days = (farm_stage.end_date - farm_stage.start_date).days
        days_elapsed = (datetime.utcnow() - farm_stage.start_date).days
        progress = int((days_elapsed / total_days) * 100) if total_days > 0 else 0
        days_display = f"{min(days_elapsed, total_days)}/{total_days}"

        # Estimate next stage (optional logic based on business rules)
        next_stage = "Harvesting" if farm_stage.stage_name == "Flowering" else "Flowering (in 14 days)"
        harvest_date = farm_stage.end_date.strftime("%B %d")
    else:
        # Defaults if no active stage found
        progress = 0
        days_display = "0/0"
        next_stage = "Unknown"
        harvest_date = "TBD"

    crop_growth = {
        "status": "On Track" if progress > 25 else "Delayed",
        "days": days_display,
        "progress": progress,
        "stage": farm_stage.stage_name if farm_stage else "Vegetative",
        "next_stage": next_stage,
        "harvest_date": harvest_date
    }

    return crop_growth    
def get_real_time_field_health(field_id, time_range_days=7):
    """
    Generate real-time field health data based on sensor inputs and crop health reports.
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=time_range_days)

    # Get the field object (to get farm_id)
    field = Field.query.get(field_id)
    if not field:
        return {"error": "Field not found."}

    farm_id = field.farm_id

    # Filter sensor data by type and time
    def get_avg_sensor_value(sensor_type):
        return db.session.query(func.avg(SensorData.value)).filter(
            SensorData.sensor_type == sensor_type,
            SensorData.farm_id == farm_id,
            SensorData.timestamp.between(start_time, end_time),
            SensorData.status == 'Valid'
        ).scalar()

    temperature_avg = get_avg_sensor_value('temperature') or 0
    moisture_avg = get_avg_sensor_value('soil_moisture') or 0
    soil_health_avg = get_avg_sensor_value('soil_health') or 0
    growth_avg = get_avg_sensor_value('growth') or 0  # custom sensor, if any

    # Health status from crop health reports
    latest_crop_health = CropHealth.query.filter_by(farm_id=farm_id).order_by(CropHealth.assessment_date.desc()).first()
    status = latest_crop_health.status if latest_crop_health else "Unknown"

    # Calculate overall health
    def normalize(value, min_val, max_val):
        return max(0, min(100, int(((value - min_val) / (max_val - min_val)) * 100)))

    temperature_score = normalize(temperature_avg, 10, 35)
    moisture_score = normalize(moisture_avg, 30, 80)
    soil_health_score = normalize(soil_health_avg, 60, 100)
    growth_score = normalize(growth_avg, 1, 5)

    overall_health = int((temperature_score + moisture_score + soil_health_score + growth_score) / 4)

    # Calculate improvement percentage (You may need a historical comparison here)
    # For now, let's assume a dummy 2% improvement
    improvement = 2
    improvement_direction = "up"

    # Return real-time health card data
    field_health = {
        "status": status,
        "overall_health": overall_health,
        "improvement": improvement,
        "improvement_direction": improvement_direction,
    }

    return field_health

# 7. Recommended Actions
# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_recommendations_from_llm(crop_status, soil_moisture, satellite_data):
    # Compose a detailed but concise prompt for GPT-3.5
    prompt = f"""
You are an expert agronomist AI. Based on the following real-time farm data, provide 3 brief and actionable recommendations in under 100 words total. Each recommendation should include the action, a short reason, and a time frame. Prioritize urgent issues. Format as a JSON list of dictionaries with 'action', 'description', 'priority', and 'due'.

Crop Status:
{crop_status}

Soil Moisture:
{soil_moisture}

Satellite Imagery:
{satellite_data}
"""

    # Call OpenAI GPT-3.5 API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a smart farm assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=300
    )

    # Extract content from response
    reply = response['choices'][0]['message']['content']
    
    # Optionally, evaluate the response format if needed (JSON loading)
    try:
        import json
        recommendations = json.loads(reply)
    except Exception as e:
        print("Failed to parse GPT response:", e)
        recommendations = []

    return recommendations

# Sample dynamic input data
crop_status = """
Maize: 3 sectors healthy, 2 sectors show leaf blight, 1 sector stunted growth.
Beans: 2 sectors healthy, 1 sector showing rust, 1 sector anthracnose infection.
"""

soil_moisture = """
Sector 2 and 4 soil moisture below 30%, Sector 1 optimal, others borderline low.
"""

satellite_data = """
Signs of drought stress in eastern plots. Reduced NDVI in maize plots.
"""

# Call the function to get real-time LLM-based recommendations
recommendations = generate_recommendations_from_llm(crop_status, soil_moisture, satellite_data)

# Output or use the recommendations in your app
for r in recommendations:
    print(r)    

    
=======
    # Soil Health Card Data
    soil_health = {
        "status": "Good",  # Could be derived from sensor data
        "quality": 76,  # Overall soil health score
        "nitrogen": 42,  # ppm
        "phosphorus": 28,  # ppm
        "ph_level": 6.8,
        "organic_matter": 4.2,  # percentage
    }

    # Field Health Card Data
    field_health = {
        "status": "Excellent",
        "overall_health": 82,  # percentage
        "improvement": 2,  # percentage improvement
        "improvement_direction": "up",  # 'up' or 'down'
    }

    # Moisture Level Card Data
    moisture = {
        "status": "Normal",
        "current": soil_moisture.value if soil_moisture else 64,  # percentage
        "last_irrigation": "2 days ago",
        "next_irrigation": "Tomorrow",
        "forecast": "Light rain expected in 36 hours",
    }

    # 4. Crop Growth & Harvest
    # Get the current farm stage
    farm_stage = FarmStage.query.filter_by(farm_id=farm.id, status="Active").first()

    # Crop Growth Card Data
    crop_growth = {
        "status": "On Track",
        "days": "28/62",
        "progress": 45,  # percentage
        "stage": farm_stage.stage_name if farm_stage else "Vegetative",
        "next_stage": "Flowering (in 14 days)",
        "harvest_date": "August 15",
    }  # 5. Field Metrics Historical Data
    # Generate dates for the selected time range
    dates = [
        (datetime.now() - timedelta(days=i)).strftime("%b %d")
        for i in range(time_range)
    ]
    dates.reverse()

    # Generate mock data for the selected time range
    historical_data = {
        "temperature": generate_mock_data(time_range, 20, 30),
        "moisture": generate_mock_data(time_range, 50, 80),
        "growth": generate_mock_data(time_range, 1.5, 3.5, 1),
        "soil_health": generate_mock_data(time_range, 70, 85),
        "dates": dates,
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
        "field_health": field_health,
        "moisture": moisture,
        "crop_growth": crop_growth,
        "historical_data": historical_data,
        "alerts": alerts_data,
        "recommendations": recommendations,
    }

    return jsonify(response_data)


>>>>>>> origin/Dynamic-Parsing
@api.route("/debug")
@login_required
def api_debug():
    """Debug endpoint to check API configuration and routes"""
    # Check if OpenWeather API key is configured
    openweather_key = "Not configured"
    if current_app.config.get("OPENWEATHER_API_KEY"):
        openweather_key = (
            "Configured (first 4 chars: "
            + current_app.config.get("OPENWEATHER_API_KEY")[:4]
            + "...)"
        )

    debug_info = {
        "blueprint": "api",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "authenticated": current_user.is_authenticated,
        },
        "openweather_api_key": openweather_key,
        "farm_count": Farm.query.filter_by(user_id=current_user.id).count(),
        "sensor_data_count": SensorData.query.filter_by(
            farm_id=(
                Farm.query.filter_by(user_id=current_user.id).first().id
                if Farm.query.filter_by(user_id=current_user.id).first()
                else 0
            )
        ).count(),
        "alert_count": Alert.query.filter_by(user_id=current_user.id).count(),
        "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return jsonify(debug_info)


@api.route("/user-profile")
@login_required
def user_profile():
    """Return current user profile information"""
    profile_data = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "full_name": f"{current_user.first_name} {current_user.last_name}",
        "initials": (
            f"{current_user.first_name[0]}{current_user.last_name[0]}"
            if current_user.first_name and current_user.last_name
            else "?"
        ),
        "is_approved": current_user.is_approved,
    }

    return jsonify(profile_data)


@api.route("/metric-data", methods=["GET"])
@login_required
def metric_data():
    """API endpoint that provides metric-specific data for charts"""
    metric = request.args.get("metric", "").lower()
    time_range = int(request.args.get("range", "30"))

    # Get the user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    if not farm:
        return jsonify({"error": "No farm found. Please register a farm first."}), 404

    # Generate dates for the time range
    dates = [
        (datetime.now() - timedelta(days=i)).strftime("%b %d")
        for i in range(time_range)
    ]
    dates.reverse()

    # Get historical data based on metric type
    if metric == "temperature":
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Temperature (°C)",
                    "data": generate_mock_data(
                        time_range, 20, 30
                    ),  # Mock data between 20-30°C
                    "borderColor": "#F1C40F",
                    "backgroundColor": "rgba(241, 196, 15, 0.1)",
                    "borderWidth": 3,
                    "pointRadius": 4,
                    "pointBackgroundColor": "#F1C40F",
                    "tension": 0.3,
                    "fill": True,
                }
            ],
        }
    elif metric == "moisture":
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Soil Moisture (%)",
                    "data": generate_mock_data(
                        time_range, 50, 80
                    ),  # Mock data between 50-80%
                    "borderColor": "#3498DB",
                    "backgroundColor": "rgba(52, 152, 219, 0.1)",
                    "borderWidth": 3,
                    "pointRadius": 4,
                    "pointBackgroundColor": "#3498DB",
                    "tension": 0.3,
                    "fill": True,
                }
            ],
        }
    elif metric == "growth":
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Growth Rate (cm/day)",
                    "data": generate_mock_data(
                        time_range, 1.5, 3.5, 1
                    ),  # Mock data between 1.5-3.5 cm/day
                    "borderColor": "#2ECC71",
                    "backgroundColor": "rgba(46, 204, 113, 0.1)",
                    "borderWidth": 3,
                    "pointRadius": 4,
                    "pointBackgroundColor": "#2ECC71",
                    "tension": 0.3,
                    "fill": True,
                }
            ],
        }
    elif metric == "soil health":
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Soil Health Score",
                    "data": generate_mock_data(
                        time_range, 70, 85
                    ),  # Mock data between 70-85
                    "borderColor": "#6E2C00",
                    "backgroundColor": "rgba(110, 44, 0, 0.1)",
                    "borderWidth": 3,
                    "pointRadius": 4,
                    "pointBackgroundColor": "#6E2C00",
                    "tension": 0.3,
                    "fill": True,
                }
            ],
        }
    else:
        return jsonify({"error": "Invalid metric specified"}), 400

    return jsonify(data)


def generate_mock_data(count, min_val, max_val, decimals=0):
    """Generate mock data points with some realistic variation"""
    import random

    data = []
    value = random.uniform(min_val, max_val)

    for _ in range(count):
        # Add some random variation while staying within bounds
        change = random.uniform(-2, 2)
        value = max(min_val, min(max_val, value + change))
        data.append(round(value, decimals))

<<<<<<< HEAD
    return data
=======
    return data
>>>>>>> origin/Dynamic-Parsing
