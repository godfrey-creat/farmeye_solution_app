# app/api/routes.py
from flask import jsonify, current_app, request
from flask_login import login_required, current_user
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from app.utils.advisory import generate_ten_day_advisory
from . import api
from ..farm.models import (
    Farm,
    SensorData,
    Alert,
    FarmStage,
    PestControl,
    FarmTeamMember,
)
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key
client = OpenAI()
api_key=os.environ.get("OPENAI_API_KEY")


@api.route("/dashboard-data", methods=["GET"])
@login_required
def dashboard_data():
    """API endpoint that provides dashboard data in JSON format"""
    # Get time range from query params
    time_range = request.args.get("range", "30")
    try:
        time_range = int(time_range)
        # Enforce interval of 7 days up to a max of 31 days
        if time_range < 7:
            time_range = 7
        elif time_range > 31:
            time_range = 31
    except ValueError:
        time_range = 30

    # Get farms owned by user and farms where user is a team member
    farms = Farm.query.filter_by(user_id=current_user.id).all()
    farm_team_memberships = FarmTeamMember.query.filter_by(
        user_id=current_user.id
    ).all()
    team_farms = [membership.farm for membership in farm_team_memberships]
    all_farms = farms + team_farms

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

    # Get the selected field (for now, we'll use an empty field)
    field = []  

    # 1. Farm & Field Information
    farm_info = {
        "name": farm.name,
        "field": field,
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 2. Weather & Forecast - Using real API data
    weather_data = get_real_weather_data(farm)

    # 3. Soil & Field Health - Using real sensor data
    # Get the latest sensor data for various soil metrics
    soil_moisture = get_latest_sensor_data(farm.id, "soil_moisture")
    soil_nitrogen = get_latest_sensor_data(farm.id, "soil_nitrogen")
    soil_phosphorus = get_latest_sensor_data(farm.id, "soil_phosphorus")
    soil_ph = get_latest_sensor_data(farm.id, "soil_ph")
    soil_organic_matter = get_latest_sensor_data(farm.id, "soil_organic_matter")
    
    # Calculate soil health status based on actual readings
    soil_health_status = calculate_soil_health_status(
        soil_nitrogen, soil_phosphorus, soil_ph, soil_organic_matter
    )
    
    # Soil Health Card Data
    soil_health = {
        "status": soil_health_status["status"],
        "quality": soil_health_status["quality"],
        "nitrogen": soil_nitrogen.value if soil_nitrogen else None,
        "phosphorus": soil_phosphorus.value if soil_phosphorus else None,
        "ph_level": soil_ph.value if soil_ph else None,
        "organic_matter": soil_organic_matter.value if soil_organic_matter else None,
    }

    # Field Health Card Data from actual field sensors and satellite data
    field_health = get_field_health_data(farm.id)

    # Moisture Level Card Data - using actual sensor data and irrigation logs
    moisture = get_moisture_data(farm.id, soil_moisture)

    # 4. Crop Growth & Harvest
    # Get the current farm stage
    farm_stage = FarmStage.query.filter_by(farm_id=farm.id, status="Active").first()
    
    # Get actual crop growth data
    crop_growth = get_crop_growth_data(farm.id, farm_stage)

    # 5. Field Metrics Historical Data
    # Generate dates for the selected time range
    dates = [
        (datetime.now() - timedelta(days=i)).strftime("%b %d")
        for i in range(time_range)
    ]
    dates.reverse()

    # Get real historical data for the selected time range
    historical_data = get_historical_sensor_data(farm.id, time_range, dates)

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
                "title": alert.alert_type,
                "message": alert.message,
                "severity": alert.severity,
                "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    # 7. Get real-time recommendations using LLM
    # Prepare data for LLM processing
    soil_moisture_data = {
        "recent_readings": historical_data["moisture"] if "moisture" in historical_data else [],
        "current": moisture["current"] if "current" in moisture else None,
        "last_irrigation": moisture.get("last_irrigation", ""),
        "next_irrigation": moisture.get("next_irrigation", ""),
    }

    # Get satellite NDVI data
    satellite_data = get_satellite_ndvi_data(farm.id)
    
    # Get model prediction data
    model_prediction_data = get_model_prediction_data(farm.id)

    # Generate the advisory using external LLM
    advisory = generate_llm_advisory(
        soil_moisture=soil_moisture_data,
        weather=weather_data,
        satellite=satellite_data,
        model_prediction=model_prediction_data,
        soil_health=soil_health,
        field_health=field_health,
        crop_growth=crop_growth
    )

    # Get action recommendations from the advisory
    recommendations = extract_recommendations_from_advisory(advisory)

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
        "advisory": advisory,
    }

    return jsonify(response_data)


def get_real_weather_data(farm):
    """Get real weather data from OpenWeather API"""
    # Default in case API fails
    default_weather = {
        "temperature": None,
        "condition": "Unknown",
        "icon": "01d",
        "forecast": "Weather forecast unavailable",
    }
    
    try:
        # Check if location contains lat/long information
        if "," in farm.location:
            lat, lon = map(float, farm.location.split(","))
            
            # Get API key from environment
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if not api_key:
                current_app.logger.error("OpenWeather API key not configured")
                return default_weather
                
            weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={api_key}"
            response = requests.get(weather_url)
            
            if response.status_code == 200:
                data = response.json()
                current = data["current"]
                
                # Extract forecast data
                forecast_data = []
                for day in data.get("daily", [])[:5]:  # Get 5-day forecast
                    forecast_data.append({
                        "date": datetime.fromtimestamp(day["dt"]).strftime("%Y-%m-%d"),
                        "temp_min": round(day["temp"]["min"]),
                        "temp_max": round(day["temp"]["max"]),
                        "condition": day["weather"][0]["main"],
                        "icon": day["weather"][0]["icon"],
                        "precipitation": day.get("rain", 0) if "rain" in day else 0,
                    })
                
                return {
                    "temperature": round(current["temp"]),
                    "condition": current["weather"][0]["main"],
                    "icon": current["weather"][0]["icon"],
                    "humidity": current["humidity"],
                    "wind_speed": current["wind_speed"],
                    "forecast": forecast_data,
                }
            else:
                current_app.logger.error(f"OpenWeather API error: {response.status_code}")
                return default_weather
        else:
            return default_weather
    except Exception as e:
        current_app.logger.error(f"Weather data processing error: {str(e)}")
        return default_weather


def get_latest_sensor_data(farm_id, sensor_type):
    """Get the latest sensor data for a specific sensor type"""
    return (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type=sensor_type)
        .order_by(SensorData.timestamp.desc())
        .first()
    )


def calculate_soil_health_status(nitrogen, phosphorus, ph, organic_matter):
    """Calculate soil health status based on actual readings"""
    # Default status
    status = {
        "status": "Unknown",
        "quality": 0
    }
    
    # If we have all metrics, calculate a real status
    if nitrogen and phosphorus and ph and organic_matter:
        # Example logic - customize based on actual soil science
        n_score = 0
        if 30 <= nitrogen.value <= 60:
            n_score = 25
        elif 20 <= nitrogen.value < 30 or 60 < nitrogen.value <= 70:
            n_score = 15
        else:
            n_score = 5
            
        p_score = 0
        if 20 <= phosphorus.value <= 40:
            p_score = 25
        elif 15 <= phosphorus.value < 20 or 40 < phosphorus.value <= 50:
            p_score = 15
        else:
            p_score = 5
            
        ph_score = 0
        if 6.5 <= ph.value <= 7.0:
            ph_score = 25
        elif 6.0 <= ph.value < 6.5 or 7.0 < ph.value <= 7.5:
            ph_score = 15
        else:
            ph_score = 5
            
        om_score = 0
        if organic_matter.value >= 4.0:
            om_score = 25
        elif 3.0 <= organic_matter.value < 4.0:
            om_score = 15
        else:
            om_score = 5
            
        # Total score out of 100
        total = n_score + p_score + ph_score + om_score
        
        # Set status based on score
        if total >= 80:
            status["status"] = "Excellent"
        elif total >= 60:
            status["status"] = "Good"
        elif total >= 40:
            status["status"] = "Fair"
        else:
            status["status"] = "Poor"
            
        status["quality"] = total
    
    return status


def get_field_health_data(farm_id):
    """Get field health data from sensors and satellite imagery"""
    # Query for field health metrics from the database
    # This would include NDVI, pest presence, disease indicators, etc.
    
    # For now, use a placeholder until real data integration
    field_health = {
        "status": "Unknown",
        "overall_health": 0,
        "improvement": 0,
        "improvement_direction": "neutral",
    }
    
    # Example: Get field health score from a recent database record
    field_health_record = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="field_health_score")
        .order_by(SensorData.timestamp.desc())
        .first()
    )
    
    if field_health_record:
        field_health["overall_health"] = field_health_record.value
        
        # Get previous reading to calculate improvement
        prev_record = (
            SensorData.query.filter_by(farm_id=farm_id, sensor_type="field_health_score")
            .order_by(SensorData.timestamp.desc())
            .offset(1)
            .first()
        )
        
        if prev_record:
            improvement = field_health_record.value - prev_record.value
            field_health["improvement"] = abs(improvement)
            field_health["improvement_direction"] = "up" if improvement > 0 else "down"
        
        # Set status based on score
        if field_health["overall_health"] >= 80:
            field_health["status"] = "Excellent"
        elif field_health["overall_health"] >= 60:
            field_health["status"] = "Good"
        elif field_health["overall_health"] >= 40:
            field_health["status"] = "Fair"
        else:
            field_health["status"] = "Poor"
    
    return field_health


def get_moisture_data(farm_id, soil_moisture):
    """Get moisture data from sensors and irrigation logs"""
    moisture = {
        "status": "Unknown",
        "current": soil_moisture.value if soil_moisture else None,
        "last_irrigation": None,
        "next_irrigation": None,
    }
    
    # Get the last irrigation record
    last_irrigation = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="irrigation_event")
        .order_by(SensorData.timestamp.desc())
        .first()
    )
    
    if last_irrigation:
        days_since = (datetime.now() - last_irrigation.timestamp).days
        if days_since == 0:
            moisture["last_irrigation"] = "Today"
        elif days_since == 1:
            moisture["last_irrigation"] = "Yesterday"
        else:
            moisture["last_irrigation"] = f"{days_since} days ago"
    
    # Determine moisture status based on current reading
    if soil_moisture:
        if soil_moisture.value >= 70:
            moisture["status"] = "High"
            moisture["next_irrigation"] = "Not needed"
        elif soil_moisture.value >= 50:
            moisture["status"] = "Normal"
            moisture["next_irrigation"] = "In 3 days"
        elif soil_moisture.value >= 30:
            moisture["status"] = "Low"
            moisture["next_irrigation"] = "Tomorrow"
        else:
            moisture["status"] = "Critical"
            moisture["next_irrigation"] = "Immediately"
    
    return moisture


def get_crop_growth_data(farm_id, farm_stage):
    """
    Calculate crop growth data based on the farm stage and its start date.
    Uses the stage_name to determine typical duration.
    """
    if not farm_stage:
        return {
            "days_elapsed": 0,
            "progress_percentage": 0,
            "estimated_days_remaining": 0,
            "estimated_harvest_date": None
        }
    
    # Map stage names to typical durations (in days)
    stage_duration_map = {
        "unprepared": 10,
        "prepared": 15,
        "germination": 14,
        "growth": 30,
        "flowering": 25,
        "harvesting": 20
    }
    
    # Get default duration based on stage name (case-insensitive), default to 30 days if stage name not found
    stage_name_lower = farm_stage.stage_name.lower() if farm_stage.stage_name else ""
    default_duration = stage_duration_map.get(stage_name_lower, 30)
    
    # Get the start date of the stage
    start_date = farm_stage.start_date
    if not start_date:
        return {
            "days_elapsed": 0,
            "progress_percentage": 0,
            "estimated_days_remaining": default_duration,
            "estimated_harvest_date": None
        }
    
    # If end_date is set, use it for calculations
    end_date = farm_stage.end_date
    
    # Calculate days elapsed since stage start
    today = datetime.utcnow().date()
    start_date = start_date.date() if hasattr(start_date, 'date') else start_date
    days_elapsed = (today - start_date).days
    
    # Ensure days_elapsed is not negative
    days_elapsed = max(0, days_elapsed)
    
    # Calculate progress as a percentage
    progress_percentage = 0
    estimated_days_remaining = 0
    estimated_harvest_date = None
    
    if farm_stage.status.lower() == "completed" and end_date:
        # If stage is completed, progress is 100%
        progress_percentage = 100
        estimated_days_remaining = 0
        estimated_harvest_date = end_date
    else:
        # Calculate based on elapsed time vs expected duration
        progress_percentage = min(100, (days_elapsed / default_duration) * 100) if default_duration > 0 else 0
        estimated_days_remaining = max(0, default_duration - days_elapsed)
        estimated_harvest_date = start_date + timedelta(days=default_duration)
    
    return {
        "days_elapsed": days_elapsed,
        "progress_percentage": round(progress_percentage, 1),
        "estimated_days_remaining": estimated_days_remaining,
        "estimated_harvest_date": estimated_harvest_date.strftime('%Y-%m-%d') if estimated_harvest_date else None
    }


def get_historical_sensor_data(farm_id, time_range, dates):
    """Get historical sensor data for charts"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=time_range)
    
    # Query historical sensor data for different metrics
    temperature_data = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="temperature")
        .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
        .order_by(SensorData.timestamp.asc())
        .all()
    )
    
    moisture_data = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="soil_moisture")
        .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
        .order_by(SensorData.timestamp.asc())
        .all()
    )
    
    growth_data = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="growth_rate")
        .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
        .order_by(SensorData.timestamp.asc())
        .all()
    )
    
    soil_health_data = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="soil_health_score")
        .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
        .order_by(SensorData.timestamp.asc())
        .all()
    )
    
    # Initialize arrays for each data type
    temperature_values = []
    moisture_values = []
    growth_values = []
    soil_health_values = []
    
    # For each date in our range, find the corresponding data points
    for i in range(time_range):
        date = end_date - timedelta(days=time_range - 1 - i)
        date_start = datetime(date.year, date.month, date.day, 0, 0, 0)
        date_end = datetime(date.year, date.month, date.day, 23, 59, 59)
        
        # Find temperature data for this day
        temp_point = next(
            (d for d in temperature_data if date_start <= d.timestamp <= date_end), 
            None
        )
        temperature_values.append(temp_point.value if temp_point else None)
        
        # Find moisture data for this day
        moisture_point = next(
            (d for d in moisture_data if date_start <= d.timestamp <= date_end), 
            None
        )
        moisture_values.append(moisture_point.value if moisture_point else None)
        
        # Find growth data for this day
        growth_point = next(
            (d for d in growth_data if date_start <= d.timestamp <= date_end), 
            None
        )
        growth_values.append(growth_point.value if growth_point else None)
        
        # Find soil health data for this day
        soil_health_point = next(
            (d for d in soil_health_data if date_start <= d.timestamp <= date_end), 
            None
        )
        soil_health_values.append(soil_health_point.value if soil_health_point else None)
    
    # Return the compiled historical data
    return {
        "temperature": temperature_values,
        "moisture": moisture_values,
        "growth": growth_values,
        "soil_health": soil_health_values,
        "dates": dates,
    }


def get_satellite_ndvi_data(farm_id):
    """Get satellite NDVI data for the farm"""
    # Query the database for the latest satellite NDVI readings
    ndvi_readings = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="ndvi")
        .order_by(SensorData.timestamp.desc())
        .limit(5)
        .all()
    )
    
    if not ndvi_readings:
        return {
            "ndvi": [],
            "analysis": "No NDVI data available"
        }
    
    # Extract NDVI values
    ndvi_values = [reading.value for reading in ndvi_readings]
    
    # Calculate average NDVI
    avg_ndvi = sum(ndvi_values) / len(ndvi_values)
    
    # Provide analysis based on NDVI values
    if avg_ndvi >= 0.7:
        analysis = "Excellent vegetation vigor"
    elif avg_ndvi >= 0.5:
        analysis = "Good vegetation vigor"
    elif avg_ndvi >= 0.3:
        analysis = "Moderate vegetation vigor"
    else:
        analysis = "Poor vegetation vigor, possible stress"
    
    return {
        "ndvi": ndvi_values,
        "analysis": analysis
    }


def get_model_prediction_data(farm_id):
    """Get model prediction data for the farm"""
    # Query the database for the latest model predictions
    yield_prediction = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="yield_prediction")
        .order_by(SensorData.timestamp.desc())
        .first()
    )
    
    pest_risk = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="pest_risk")
        .order_by(SensorData.timestamp.desc())
        .first()
    )
    
    disease_risk = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="disease_risk")
        .order_by(SensorData.timestamp.desc())
        .first()
    )
    
    # Return the prediction data
    return {
        "yield_forecast": f"Expected yield is {yield_prediction.value}% of maximum" if yield_prediction else "No yield forecast available",
        "pest_risk": get_risk_level(pest_risk.value if pest_risk else None),
        "disease_risk": get_risk_level(disease_risk.value if disease_risk else None)
    }


def get_risk_level(risk_value):
    """Convert numerical risk value to descriptive risk level"""
    if risk_value is None:
        return "Unknown risk level"
    
    if risk_value >= 75:
        return "High risk"
    elif risk_value >= 50:
        return "Medium risk"
    elif risk_value >= 25:
        return "Low risk"
    else:
        return "Minimal risk"


def generate_llm_advisory(soil_moisture, weather, satellite, model_prediction, soil_health, field_health, crop_growth):
    """Generate farm advisory using external LLM (GPT-3.5)"""
    try:
        # Prepare data for the LLM
        farm_data = {
            "soil_moisture": soil_moisture,
            "weather": weather,
            "satellite_ndvi": satellite,
            "model_prediction": model_prediction,
            "soil_health": soil_health,
            "field_health": field_health,
            "crop_growth": crop_growth,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Convert data to JSON for LLM consumption
        farm_data_json = json.dumps(farm_data)
        
        # Prepare the prompt for the LLM
        prompt = f"""
        You are an expert agricultural advisor. Based on the following real-time farm data, provide a comprehensive 10-day advisory for the farm.
        
        Farm Data:
        {farm_data_json}
        
        Please include:
        1. Overall assessment of farm health
        2. Specific recommendations for irrigation, fertilization, and pest management
        3. Weather impact analysis
        4. Crop growth projections
        5. Actionable steps with priorities (High, Medium, Low) and timelines
        
        Format your response as JSON with the following structure:
        {{
            "advisory_summary": "Brief summary of overall farm status",
            "irrigation_advisory": "Detailed irrigation recommendation",
            "fertilization_advisory": "Detailed fertilization recommendation",
            "pest_management_advisory": "Detailed pest management recommendation",
            "weather_impact": "Analysis of upcoming weather impact",
            "crop_projection": "Projection for crop growth",
            "recommendations": [
                {{
                    "action": "Specific action to take",
                    "description": "Detailed description of the action",
                    "priority": "High/Medium/Low",
                    "due": "Timeline for action"
                }}
            ]
        }}
        """
        
        # Call the OpenAI API
        response = client.responses.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert agricultural advisor providing data-driven farm management recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Lower temperature for more consistent advice
            max_tokens=1000
        )
        
        # Extract the advisory from the response
        advisory_text = response.choices[0].message.content
        
        # Parse the advisory as JSON
        try:
            advisory_json = json.loads(advisory_text)
            return advisory_json
        except json.JSONDecodeError:
            # If parsing fails, return the raw text
            current_app.logger.error("Failed to parse LLM advisory as JSON")
            return {"advisory_text": advisory_text}
            
    except Exception as e:
        current_app.logger.error(f"LLM advisory generation error: {str(e)}")
        return {
            "advisory_summary": "Error generating advisory. Please try again later.",
            "recommendations": []
        }


def extract_recommendations_from_advisory(advisory):
    """Extract recommendations from the LLM advisory"""
    if not advisory:
        return []
    
    # Get recommendations from the advisory
    if "recommendations" in advisory and isinstance(advisory["recommendations"], list):
        return advisory["recommendations"]
    
    # If no recommendations found, create a default one
    return [{
        "action": "Check Farm Sensors",
        "description": "Some sensors might not be reporting correctly. Please check the farm monitoring system.",
        "priority": "High",
        "due": "Today"
    }]


@api.route("/debug")
@login_required
def api_debug():
    """Debug endpoint to check API configuration and routes"""
    # Check if OpenWeather API key is configured
    openweather_key = "Not configured"
    if os.getenv("OPENWEATHER_API_KEY"):
        openweather_key = (
            "Configured (first 4 chars: "
            + os.getenv("OPENWEATHER_API_KEY")[:4]
            + "...)"
        )
    
    # Check if OpenAI API key is configured
    openai_key = "Not configured"
    if os.getenv("OPENAI_API_KEY"):
        openai_key = (
            "Configured (first 4 chars: "
            + os.getenv("OPENAI_API_KEY")[:4]
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
        "openai_api_key": openai_key,
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
    end_date = datetime.now()
    start_date = end_date - timedelta(days=time_range)
    dates = [
        (end_date - timedelta(days=i)).strftime("%b %d")
        for i in range(time_range)
    ]
    dates.reverse()

    # Get historical data based on metric type
    if metric == "temperature":
        sensor_data = (
            SensorData.query.filter_by(farm_id=farm.id, sensor_type="temperature")
            .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
            .order_by(SensorData.timestamp.asc())
            .all()
        )
        
        values = get_daily_sensor_values(sensor_data, start_date, time_range)
        
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Temperature (°C)",
                    "data": values,
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
        sensor_data = (
            SensorData.query.filter_by(farm_id=farm.id, sensor_type="soil_moisture")
            .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
            .order_by(SensorData.timestamp.asc())
            .all()
        )
        
        values = get_daily_sensor_values(sensor_data, start_date, time_range)
        
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Soil Moisture (%)",
                    "data": values,
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
        sensor_data = (
            SensorData.query.filter_by(farm_id=farm.id, sensor_type="growth_rate")
            .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
            .order_by(SensorData.timestamp.asc())
            .all()
        )
        
        values = get_daily_sensor_values(sensor_data, start_date, time_range)
        
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Growth Rate (cm/day)",
                    "data": values,
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
        sensor_data = (
            SensorData.query.filter_by(farm_id=farm.id, sensor_type="soil_health_score")
            .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
            .order_by(SensorData.timestamp.asc())
            .all()
        )
        
        values = get_daily_sensor_values(sensor_data, start_date, time_range)
        
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Soil Health Score",
                    "data": values,
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
    elif metric == "ndvi":
        sensor_data = (
            SensorData.query.filter_by(farm_id=farm.id, sensor_type="ndvi")
            .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
            .order_by(SensorData.timestamp.asc())
            .all()
        )
        
        values = get_daily_sensor_values(sensor_data, start_date, time_range)
        
        data = {
            "labels": dates,
            "datasets": [
                {
                    "label": "NDVI Score",
                    "data": values,
                    "borderColor": "#27AE60",
                    "backgroundColor": "rgba(39, 174, 96, 0.1)",
                    "borderWidth": 3,
                    "pointRadius": 4,
                    "pointBackgroundColor": "#27AE60",
                    "tension": 0.3,
                    "fill": True,
                }
            ],
        }
    else:
        return jsonify({"error": "Invalid metric specified"}), 400

    return jsonify(data)


def get_daily_sensor_values(sensor_data, start_date, time_range):
    """Extract daily sensor values from a collection of sensor readings"""
    values = []
    
    for i in range(time_range):
        day = start_date + timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day, 0, 0, 0)
        day_end = datetime(day.year, day.month, day.day, 23, 59, 59)
        
        # Find data for this day
        day_reading = next(
            (d for d in sensor_data if day_start <= d.timestamp <= day_end),
            None
        )
        
        values.append(day_reading.value if day_reading else None)
    
    return values

@api.route("/crop-health-report", methods=["GET"])
@login_required
def crop_health_report():
    """Generate a comprehensive crop health report using LLM analysis of sensor data"""
    farm_id = request.args.get("farm_id")
    
    # If no farm_id provided, use the user's primary farm
    if not farm_id:
        farm = Farm.query.filter_by(user_id=current_user.id).first()
        if not farm:
            return jsonify({"error": "No farm found. Please register a farm first."}), 404
        farm_id = farm.id
    
    # Collect all relevant data for the report
    soil_data = get_all_soil_data(farm_id)
    weather_data = get_real_weather_data(farm)
    growth_data = get_crop_growth_data(farm_id, FarmStage.query.filter_by(farm_id=farm_id, status="Active").first())
    satellite_data = get_satellite_ndvi_data(farm_id)
    pest_data = get_pest_data(farm_id)
    
    # Generate the report using external LLM
    try:
        # Prepare data for the LLM
        report_data = {
            "soil_data": soil_data,
            "weather_data": weather_data,
            "growth_data": growth_data,
            "satellite_data": satellite_data,
            "pest_data": pest_data,
            "farm_name": farm.name,
            "crop_type": farm.crop_type,
            "farm_location": farm.location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Convert data to JSON for LLM consumption
        report_data_json = json.dumps(report_data)
        
        # Prepare the prompt for the LLM
        prompt = f"""
        You are an expert agricultural scientist specialized in crop health assessment. 
        Based on the following real-time farm data, provide a comprehensive crop health report.
        
        Farm Data:
        {report_data_json}
        
        The report should include:
        1. Executive summary of overall crop health (100 words)
        2. Detailed soil analysis with trends and recommendations
        3. Growth stage analysis and comparison to expected benchmarks
        4. Pest and disease risk assessment
        5. Weather impact analysis (recent and forecast)
        6. NDVI and satellite imagery interpretation
        7. Key recommendations with clear priorities
        
        Format your response as JSON with the following structure:
        {{
            "report_title": "Crop Health Report for [Farm Name]",
            "executive_summary": "Brief summary of overall crop health",
            "soil_analysis": {{
                "status": "Current soil status",
                "trends": "Observed trends in soil health",
                "recommendations": "Soil management recommendations"
            }},
            "growth_analysis": {{
                "current_stage": "Current growth stage assessment",
                "comparison": "Comparison to benchmarks",
                "projection": "Growth projection"
            }},
            "pest_disease_assessment": {{
                "current_status": "Current pest/disease status",
                "risk_areas": "Identified risk areas",
                "recommended_actions": "Recommended mitigation actions"
            }},
            "weather_impact": {{
                "recent_impact": "Impact of recent weather",
                "forecast_implications": "Implications of weather forecast"
            }},
            "satellite_assessment": {{
                "ndvi_interpretation": "Interpretation of NDVI values",
                "field_variability": "Analysis of field variability",
                "hotspots": "Identified areas of concern"
            }},
            "key_recommendations": [
                {{
                    "action": "Specific action to take",
                    "description": "Detailed description of the action",
                    "priority": "High/Medium/Low",
                    "timeline": "When to implement"
                }}
            ]
        }}
        """
        
        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert agricultural scientist providing data-driven crop health assessments."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=1500
        )
        
        # Extract the report from the response
        report_text = response.choices[0].message.content
        
        # Parse the report as JSON
        try:
            report_json = json.loads(report_text)
            return jsonify(report_json)
        except json.JSONDecodeError:
            # If parsing fails, return the raw text
            current_app.logger.error("Failed to parse LLM report as JSON")
            return jsonify({"error": "Report format error", "raw_report": report_text})
            
    except Exception as e:
        current_app.logger.error(f"LLM report generation error: {str(e)}")
        return jsonify({
            "error": "Failed to generate crop health report",
            "message": str(e)
        }), 500


def get_all_soil_data(farm_id):
    """Collect all soil-related data for the farm"""
    # Get all soil-related sensor data
    soil_moisture = get_latest_sensor_data(farm_id, "soil_moisture")
    soil_nitrogen = get_latest_sensor_data(farm_id, "soil_nitrogen")
    soil_phosphorus = get_latest_sensor_data(farm_id, "soil_phosphorus")
    soil_potassium = get_latest_sensor_data(farm_id, "soil_potassium")
    soil_ph = get_latest_sensor_data(farm_id, "soil_ph")
    soil_organic_matter = get_latest_sensor_data(farm_id, "soil_organic_matter")
    soil_temperature = get_latest_sensor_data(farm_id, "soil_temperature")
    soil_ec = get_latest_sensor_data(farm_id, "soil_ec")  # Electrical conductivity
    
    # Collect historical soil moisture data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    historical_moisture = (
        SensorData.query.filter_by(farm_id=farm_id, sensor_type="soil_moisture")
        .filter(SensorData.timestamp >= start_date, SensorData.timestamp <= end_date)
        .order_by(SensorData.timestamp.asc())
        .all()
    )
    
    moisture_trend = []
    for reading in historical_moisture:
        moisture_trend.append({
            "date": reading.timestamp.strftime("%Y-%m-%d"),
            "value": reading.value
        })
    
    # Compile soil data
    soil_data = {
        "current": {
            "moisture": soil_moisture.value if soil_moisture else None,
            "nitrogen": soil_nitrogen.value if soil_nitrogen else None,
            "phosphorus": soil_phosphorus.value if soil_phosphorus else None,
            "potassium": soil_potassium.value if soil_potassium else None,
            "ph": soil_ph.value if soil_ph else None,
            "organic_matter": soil_organic_matter.value if soil_organic_matter else None,
            "temperature": soil_temperature.value if soil_temperature else None,
            "electrical_conductivity": soil_ec.value if soil_ec else None
        },
        "moisture_trend": moisture_trend,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return soil_data


def get_pest_data(farm_id):
    """Get pest related data for the farm"""
    # Query for pest detections and controls
    pest_controls = PestControl.query.filter_by(farm_id=farm_id).order_by(PestControl.applied_date.desc()).limit(5).all()
    
    # Get pest risk sensor data
    pest_risk = get_latest_sensor_data(farm_id, "pest_risk")
    disease_risk = get_latest_sensor_data(farm_id, "disease_risk")
    
    # Compile pest control history
    controls = []
    for control in pest_controls:
        controls.append({
            "date": control.applied_date.strftime("%Y-%m-%d"),
            "pest_type": control.pest_type,
            "control_method": control.control_method,
            "effectiveness": control.effectiveness
        })
    
    # Compile pest data
    pest_data = {
        "recent_controls": controls,
        "current_risk": {
            "pest": pest_risk.value if pest_risk else None,
            "disease": disease_risk.value if disease_risk else None
        },
        "detected_pests": ["aphids", "corn earworm", "spider mites"]  # This would come from image recognition or field reports
    }
    
    return pest_data