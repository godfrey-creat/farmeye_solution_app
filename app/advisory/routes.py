from flask import jsonify, current_app, render_template
from flask_login import login_required, current_user
import os
from datetime import datetime, timedelta
from . import advisory
from ..farm.models import (
    Farm, SensorData, WeatherData, CropHealth, PestControl, FarmStage, FarmImage
)
from app.feed.routes import detector   # Use the global YOLO detector instance
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_latest_farm_image(farm_id):
    return FarmImage.query.filter_by(farm_id=farm_id).order_by(FarmImage.upload_date.desc()).first()

def get_soil_health(farm_id):
    farm = Farm.query.get(farm_id)
    if not farm:
        return None
    return {
        "soil_type": farm.soil_type,
        "ph_level": farm.ph_level,
        "soil_notes": getattr(farm, "soil_notes", ""),
        "status": "Good" if farm.ph_level and 6.0 <= farm.ph_level <= 7.5 else "Check",
        "quality": 80 if farm.ph_level and 6.0 <= farm.ph_level <= 7.5 else 50,
        "nitrogen": getattr(farm, "nitrogen", None),
        "phosphorus": getattr(farm, "phosphorus", None),
    }

def get_moisture_data(farm_id):
    return SensorData.query.filter_by(farm_id=farm_id, sensor_type="soil_moisture").order_by(SensorData.timestamp.desc()).all()

def get_weather_data(farm_id):
    return WeatherData.query.filter_by(farm_id=farm_id).order_by(WeatherData.timestamp.desc()).all()

@advisory.route("/dashboard_data")
@login_required
def dashboard_data():
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    if not farm:
        return jsonify({"error": "No farm found for user"}), 404

    # --- Get farm state ---
    soil_health = get_soil_health(farm.id)
    moisture = get_moisture_data(farm.id)
    weather_data = get_weather_data(farm.id)
    current_stage_obj = FarmStage.query.filter_by(
        farm_id=farm.id, status="Active"
    ).order_by(FarmStage.start_date.desc()).first()
    current_stage = current_stage_obj.stage_name if current_stage_obj else "Unknown"
    active_pests = PestControl.query.filter_by(farm_id=farm.id, status="Active").all()

    # --- Sensor Data (latest values) ---
    soil_moisture = SensorData.query.filter_by(
        farm_id=farm.id, sensor_type="soil_moisture"
    ).order_by(SensorData.timestamp.desc()).first()
    nitrogen_sensor = SensorData.query.filter_by(
        farm_id=farm.id, sensor_type="nitrogen"
    ).order_by(SensorData.timestamp.desc()).first()
    phosphorus_sensor = SensorData.query.filter_by(
        farm_id=farm.id, sensor_type="phosphorus"
    ).order_by(SensorData.timestamp.desc()).first()
    ph_sensor = SensorData.query.filter_by(
        farm_id=farm.id, sensor_type="ph"
    ).order_by(SensorData.timestamp.desc()).first()

    # --- Use global YOLO detector on latest image ---
    latest_image = get_latest_farm_image(farm.id)
    yolo_detections = []
    if latest_image and os.path.exists(latest_image.file_path):
        try:
            image_pil = Image.open(latest_image.file_path)
            yolo_detections = detector.detect(image_pil)
        except Exception as e:
            current_app.logger.error(f"Error running YOLO on advisory image: {str(e)}")
            yolo_detections = []
    else:
        yolo_detections = []

    ai_input = {
        "current_conditions": {
            "soil_health": soil_health,
            "soil_moisture": [m.as_dict() if hasattr(m, "as_dict") else str(m) for m in moisture],
            "weather": [w.as_dict() if hasattr(w, "as_dict") else str(w) for w in weather_data]
        },
        "crop_status": {
            "current_stage": current_stage,
            "model_predictions": yolo_detections
        },
        "active_issues": {
            "pests": [
                {
                    "name": pest.pest_name or "Unknown Pest",
                    "severity": pest.severity or "Medium",
                    "location": pest.location_in_farm or "Unknown Location",
                    "detected_date": pest.detection_date.isoformat() if pest.detection_date else "Unknown Date",
                    "description": pest.description or "No description available"
                }
                for pest in active_pests
            ]
        },
        "sensor_data": {
            "soil_moisture": soil_moisture.value if soil_moisture else None,
            "nitrogen": nitrogen_sensor.value if nitrogen_sensor else None,
            "phosphorus": phosphorus_sensor.value if phosphorus_sensor else None,
            "ph": ph_sensor.value if ph_sensor else None,
        }
    }

    recommendations = generate_ai_recommendations(ai_input, farm)
    response_data = {
        "ai_input": ai_input,
        "recommendations": recommendations,
    }
    return jsonify(response_data)

@advisory.route("/dashboard")
@login_required
def dashboard():
    return render_template("advisory/advisory.html", active_page="advisory")

def generate_ai_recommendations(ai_input, farm):
    """Generate AI-powered recommendations using OpenAI"""
    try:
        if not os.getenv("OPENAI_API_KEY"):
            current_app.logger.warning("OpenAI API key not configured, using fallback recommendations")
            return get_fallback_recommendations(ai_input, farm)
        prompt = create_recommendation_prompt(ai_input)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert agricultural consultant with deep knowledge of crop management, soil health, pest control, and farming best practices. Provide actionable, specific recommendations based on the farm data provided."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        recommendations_text = response.choices[0].message.content
        recommendations = parse_ai_recommendations(recommendations_text)
        if not recommendations:
            recommendations = get_fallback_recommendations(ai_input, farm)
        return recommendations
    except Exception as e:
        current_app.logger.error(f"Error generating AI recommendations: {str(e)}")
        return get_fallback_recommendations(ai_input, farm)

def create_recommendation_prompt(ai_input):
    current_conditions = ai_input.get("current_conditions", {})
    crop_status = ai_input.get("crop_status", {})
    active_issues = ai_input.get("active_issues", {})
    sensor_data = ai_input.get("sensor_data", {})

    prompt = f"""
Based on the following farm data, provide 3-5 actionable recommendations.

CURRENT CONDITIONS:
- Soil Health: {current_conditions.get('soil_health')}
- Soil Moisture: {current_conditions.get('soil_moisture')}
- Weather: {current_conditions.get('weather')}

CROP STATUS:
- Current Stage: {crop_status.get('current_stage')}
- Model Predictions (YOLO): {crop_status.get('model_predictions')}

ACTIVE ISSUES:
- Active Pests: {active_issues.get('pests')}

SENSOR DATA:
- Current Readings: {sensor_data}

Please reply with 3-5 specific recommendations in this JSON format:
[
    {{
        "action": "Brief action title",
        "description": "Detailed explanation",
        "priority": "High/Medium/Low",
        "due": "Timeframe for action",
        "reasoning": "Why this is important"
    }}
]
"""
    return prompt

def parse_text_recommendations(text_response):
    recommendations = []
    lines = text_response.split('\n')
    current_rec = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '•']):
            if current_rec:
                recommendations.append(current_rec)
            action = line
            for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '•']:
                action = action.replace(prefix, '').strip()
            current_rec = {
                "action": action[:50] + "..." if len(action) > 50 else action,
                "description": action,
                "priority": "Medium",
                "due": "This week",
                "reasoning": ""
            }
        elif current_rec:
            current_rec["description"] += " " + line
    if current_rec:
        recommendations.append(current_rec)
    return recommendations[:5]

def get_fallback_recommendations(ai_input, farm):
    recommendations = []
    pests = ai_input.get("active_issues", {}).get("pests", [])
    for pest in pests:
        recommendations.append({
            "action": "Pest Treatment",
            "description": f"{pest.get('name', 'Unknown Pest')} detected in {pest.get('location', 'farm')}. {pest.get('description', 'Immediate attention required.')}",
            "priority": pest.get('severity', 'Medium'),
            "due": "ASAP" if pest.get('severity') == "High" else "This week",
            "reasoning": "Active pest detection requires immediate intervention"
        })
    sensors = ai_input.get("sensor_data", {})
    if sensors.get("nitrogen") and sensors["nitrogen"] < 40:
        recommendations.append({
            "action": "Apply Nitrogen Fertilizer",
            "description": f"Nitrogen levels are at {sensors['nitrogen']} ppm, below optimal range. Apply nitrogen-rich fertilizer to improve crop growth.",
            "priority": "High",
            "due": "Within 48 hours",
            "reasoning": "Low nitrogen levels can impact crop yield"
        })
    if sensors.get("soil_moisture") and sensors["soil_moisture"] < 40:
        recommendations.append({
            "action": "Irrigation Needed",
            "description": f"Soil moisture is at {sensors['soil_moisture']}%, below optimal range. Schedule irrigation to prevent crop stress.",
            "priority": "High",
            "due": "Today",
            "reasoning": "Low soil moisture can cause immediate crop stress"
        })
    if not recommendations:
        recommendations.append({
            "action": "Regular Monitoring",
            "description": "Continue monitoring sensor data and crop health. All systems appear normal. Consider routine maintenance tasks.",
            "priority": "Info",
            "due": "Ongoing",
            "reasoning": "Preventive monitoring ensures optimal farm performance"
        })
    return recommendations

def parse_ai_recommendations(ai_response):
    try:
        start_idx = ai_response.find('[')
        end_idx = ai_response.rfind(']') + 1
        if start_idx == -1 or end_idx == 0:
            return parse_text_recommendations(ai_response)
        json_str = ai_response[start_idx:end_idx]
        import json
        recommendations = json.loads(json_str)
        validated_recommendations = []
        for rec in recommendations:
            if isinstance(rec, dict) and 'action' in rec and 'description' in rec:
                validated_recommendations.append({
                    "action": rec.get('action', 'Unknown Action'),
                    "description": rec.get('description', 'No description provided'),
                    "priority": rec.get('priority', 'Medium'),
                    "due": rec.get('due', 'This week'),
                    "reasoning": rec.get('reasoning', '')
                })
        return validated_recommendations
    except Exception as e:
        current_app.logger.error(f"Error parsing AI recommendations: {str(e)}")
        return parse_text_recommendations(ai_response)