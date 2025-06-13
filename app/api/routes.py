# app/api/routes.py
from flask import jsonify, current_app
from flask_login import login_required, current_user
import requests
from datetime import datetime, timedelta
from . import api
from ..farm.models import (
    Farm, 
    SensorData, 
    Alert, 
    FarmStage, 
    PestControl,
    Field,
    Sensor,
    CropHealth,
    WeatherData,
    LaborTask,
    PestAction
)
import os
from dotenv import load_dotenv
from sqlalchemy import func, desc

load_dotenv()


@api.route("/dashboard-data")
@login_required
def dashboard_data():
    """API endpoint that provides dashboard data in JSON format"""
    # Get the user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()

    if not farm:
        return jsonify({"error": "No farm found. Please register a farm first."}), 404

    # Get the first field (or None if no fields exist)
    field = Field.query.filter_by(farm_id=farm.id).first()
    field_name = field.name if field else "No field"

    # 1. Farm & Field Information
    farm_info = {
        "name": farm.name,
        "location": farm.location,
        "field": field_name,
        "crop_type": farm.crop_type,
        "size": farm.size,
        "last_updated": farm.updated_at.strftime("%Y-%m-%d %H:%M:%S") if farm.updated_at else "Never",
    }

    # 2. Weather & Forecast
    weather_data = {}
    if farm.latitude and farm.longitude:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if api_key:
            try:
                weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={farm.latitude}&lon={farm.longitude}&exclude=minutely&units=metric&appid={api_key}"
                response = requests.get(weather_url)

                if response.status_code == 200:
                    data = response.json()
                    current = data["current"]
                    daily = data["daily"][0] if "daily" in data and len(data["daily"]) > 0 else {}

                    weather_data = {
                        "temperature": round(current["temp"]),
                        "humidity": current["humidity"],
                        "condition": current["weather"][0]["main"],
                        "icon": current["weather"][0]["icon"],
                        "wind_speed": current.get("wind_speed", 0),
                        "forecast": daily.get("summary", "No forecast available"),
                        "rain_probability": daily.get("pop", 0) * 100 if "pop" in daily else 0,
                    }
            except Exception as e:
                current_app.logger.error(f"OpenWeather API error: {str(e)}")
                weather_data["error"] = "Weather service temporarily unavailable"
    
    # Fallback to database weather data if API fails or not configured
    if not weather_data:
        latest_weather = WeatherData.query.filter_by(farm_id=farm.id).order_by(WeatherData.timestamp.desc()).first()
        if latest_weather:
            weather_data = {
                "temperature": latest_weather.temperature,
                "humidity": latest_weather.humidity,
                "condition": latest_weather.condition,
                "icon": "01d",  # Default sunny icon
                "wind_speed": latest_weather.wind_speed or 0,
                "forecast": f"Current conditions: {latest_weather.condition}",
                "rain_probability": 0,
            }

    # 3. Soil & Field Health
    # Get latest soil moisture reading
    soil_moisture = (
        SensorData.query.filter_by(farm_id=farm.id, sensor_type="soil_moisture")
        .order_by(SensorData.timestamp.desc())
        .first()
    )
    
    # Get latest pH reading
    soil_ph = (
        SensorData.query.filter_by(farm_id=farm.id, sensor_type="ph_level")
        .order_by(SensorData.timestamp.desc())
        .first()
    )
    
    # Get latest crop health assessment
    crop_health = (
        CropHealth.query.filter_by(farm_id=farm.id)
        .order_by(CropHealth.assessment_date.desc())
        .first()
    )

    # Soil Health Data
    soil_health = {
        "status": farm.soil_type or "Unknown",
        "ph_level": farm.ph_level or (soil_ph.value if soil_ph else None),
        "moisture": soil_moisture.value if soil_moisture else None,
        "irrigation_type": farm.irrigation_type or "Unknown",
        "water_source": farm.water_source or "Unknown",
        "notes": farm.soil_notes or "",
    }

    # Field Health Data
    field_health = {
        "status": crop_health.status if crop_health else "Unknown",
        "notes": crop_health.notes if crop_health else "",
        "last_assessment": crop_health.assessment_date.strftime("%Y-%m-%d") if crop_health else "Never",
        "image_url": crop_health.image_url if crop_health else None,
    }

    # 4. Crop Growth & Harvest
    # Get current farm stage
    farm_stage = FarmStage.query.filter_by(farm_id=farm.id, status="Active").first()
    
    # Get active labor tasks
    active_tasks = LaborTask.query.filter_by(
        farm_id=farm.id, 
        status="In Progress"
    ).count()

    # Crop Growth Data
    crop_growth = {
        "stage": farm_stage.stage_name if farm_stage else "Not specified",
        "start_date": farm_stage.start_date.strftime("%Y-%m-%d") if farm_stage and farm_stage.start_date else "Not started",
        "active_tasks": active_tasks,
        "crop_type": farm.crop_type,
    }

    # 5. Field Metrics Historical Data
    # Get sensor data from last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Temperature data
    temp_data = (
        SensorData.query.filter(
            SensorData.farm_id == farm.id,
            SensorData.sensor_type == "temperature",
            SensorData.timestamp >= seven_days_ago
        )
        .order_by(SensorData.timestamp)
        .all()
    )
    
    # Moisture data
    moisture_data = (
        SensorData.query.filter(
            SensorData.farm_id == farm.id,
            SensorData.sensor_type == "soil_moisture",
            SensorData.timestamp >= seven_days_ago
        )
        .order_by(SensorData.timestamp)
        .all()
    )

    historical_data = {
        "temperature": [{"x": d.timestamp.isoformat(), "y": d.value} for d in temp_data],
        "moisture": [{"x": d.timestamp.isoformat(), "y": d.value} for d in moisture_data],
    }

    # 6. Alerts and Recommendations
    # Get recent unread alerts
    alerts = (
        Alert.query.filter_by(farm_id=farm.id, is_read=False)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    alerts_data = [
        {
            "id": alert.id,
            "title": alert.alert_type,
            "message": alert.message,
            "severity": alert.severity,
            "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for alert in alerts
    ]

    # 7. Recommended Actions
    # Get pending pest actions
    pest_actions = (
        PestAction.query.join(PestControl)
        .filter(
            PestControl.farm_id == farm.id,
            PestAction.status == "Scheduled"
        )
        .order_by(PestAction.scheduled_date)
        .limit(3)
        .all()
    )
    
    # Get pending labor tasks
    pending_tasks = (
        LaborTask.query.filter_by(
            farm_id=farm.id,
            status="Pending"
        )
        .order_by(LaborTask.start_date)
        .limit(3)
        .all()
    )

    recommendations = []
    
    for action in pest_actions:
        recommendations.append({
            "action": f"Pest Control: {action.action_name}",
            "description": f"Scheduled pest control for {action.pest_detection.pest_name}",
            "priority": "High" if action.pest_detection.severity == "High" else "Medium",
            "due": action.scheduled_date.strftime("%Y-%m-%d") if action.scheduled_date else "ASAP",
        })
    
    for task in pending_tasks:
        recommendations.append({
            "action": f"Task: {task.task_name}",
            "description": task.description or "No description",
            "priority": task.priority,
            "due": task.start_date.strftime("%Y-%m-%d") if task.start_date else "ASAP",
        })

    # Combine all data into a single response
    response_data = {
        "farm_info": farm_info,
        "weather": weather_data,
        "soil_health": soil_health,
        "field_health": field_health,
        "crop_growth": crop_growth,
        "historical_data": historical_data,
        "alerts": alerts_data,
        "recommendations": recommendations,
    }

    return jsonify(response_data)


@api.route("/debug")
@login_required
def api_debug():
    """Debug endpoint to check API configuration and routes"""
    debug_info = {
        "blueprint": "api",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "authenticated": current_user.is_authenticated,
        },
        "openweather_api_key": "Configured" if os.getenv("OPENWEATHER_API_KEY") else "Not configured",
        "farm_count": Farm.query.filter_by(user_id=current_user.id).count(),
        "sensor_count": Sensor.query.join(Farm).filter(Farm.user_id == current_user.id).count(),
        "sensor_data_count": SensorData.query.join(Farm).filter(Farm.user_id == current_user.id).count(),
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