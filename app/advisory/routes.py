# app/api/routes.py
from flask import jsonify, current_app
from flask_login import login_required, current_user
from flask import jsonify, current_app, render_template 
from ..feed.routes import detector
import requests
import os
import numpy as np
import base64
import json
from io import BytesIO
from PIL import Image
import traceback
import cv2
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from . import api
from app.advisory import advisory
from ..farm.models import (
    Farm, SensorData, Alert, FarmStage, PestControl, Field, FarmImage,
    CropHealth, WeatherData, LaborTask, PestAction
)
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def get_weather_data(location):
    return WeatherData.query.join(Farm).filter(Farm.location == location).order_by(WeatherData.timestamp.desc()).all()

def get_soil_health(farm_id):
    farm = Farm.query.get(farm_id)
    if not farm:
        return None
    return {
        "soil_type": farm.soil_type,
        "ph_level": farm.ph_level,
        "soil_notes": farm.soil_notes
    }

def get_field_health(farm_id):
    return CropHealth.query.filter_by(farm_id=farm_id).order_by(CropHealth.assessment_date.desc()).all()

def get_moisture_data(farm_id):
    return SensorData.query.filter_by(farm_id=farm_id, sensor_type="soil_moisture").order_by(SensorData.timestamp.desc()).all()

def get_crop_growth(farm_id):
    return CropHealth.query.filter_by(farm_id=farm_id).order_by(CropHealth.assessment_date.desc()).all()

def get_historical_data(farm_id):
    return {
        "weather": WeatherData.query.filter_by(farm_id=farm_id).order_by(WeatherData.timestamp.asc()).all(),
        "moisture": SensorData.query.filter_by(farm_id=farm_id, sensor_type="soil_moisture").order_by(SensorData.timestamp.asc()).all(),
        "crop_health": CropHealth.query.filter_by(farm_id=farm_id).order_by(CropHealth.assessment_date.asc()).all()
    }

def get_active_alerts(farm_id):
    return Alert.query.filter_by(farm_id=farm_id, status="Active").order_by(Alert.created_at.desc()).all()

def get_model_predictions(farm_id):
    return FarmImage.query.filter_by(farm_id=farm_id, image_type="pest", processed=True).order_by(FarmImage.upload_date.desc()).all()

@advisory.route("/dashboard")
@login_required
def dashboard():
    """Render the dashboard page"""
    return render_template("advisory/advisory.html", active_page="advisory")

@advisory.route("/dashboard_data")
@login_required
def dashboard_data():
    """Get comprehensive dashboard data including AI recommendations"""
    # Get the user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    if not farm:
        return jsonify({"error": "No farm found for user"}), 404

    # 1. Basic Farm Information
    farm_info = {
        "name": farm.name,
        "location": farm.location,
        "size": farm.size,
        "crop_type": farm.crop_type,
        "soil_type": farm.soil_type,
        "irrigation_type": farm.irrigation_type,
        "water_source": farm.water_source,
    }

    # 2. Weather Data
    weather_data = get_weather_data(farm.location)

    # 3. Soil Health Data
    soil_health = get_soil_health(farm.id)

    # 4. Field Health Data
    field_health = get_field_health(farm.id)

    # 5. Moisture Data
    moisture = get_moisture_data(farm.id)

    # 6. Crop Growth Data
    crop_growth = get_crop_growth(farm.id)

    # 7. Historical Data
    historical_data = get_historical_data(farm.id)

    # 8. Alerts
    alerts_data = get_active_alerts(farm.id)

    # 9. Model Predictions (from YOLO)
    model_predictions = get_model_predictions(farm.id)

    # 10. Sensor Data
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

    # 7. AI-Generated Smart Recommendations
    recommendations = generate_ai_recommendations(farm, {
        "soil_health": soil_health,
        "field_health": field_health,
        "moisture": moisture,
        "crop_growth": crop_growth,
        "weather": weather_data,
        "alerts": alerts_data,
        "historical_data": historical_data,
        "model_predictions": model_predictions,  # Updated with YOLO detections
        "sensors": {
            "soil_moisture": soil_moisture.value if soil_moisture else None,
            "nitrogen": nitrogen_sensor.value if nitrogen_sensor else None,
            "phosphorus": phosphorus_sensor.value if phosphorus_sensor else None,
            "ph": ph_sensor.value if ph_sensor else None,
        }
    })

    # Combine all data into a single response (add model predictions)
    response_data = {
        "farm_info": farm_info,
        "weather": weather_data,
        "soil_health": soil_health,
        "field_health": field_health,
        "moisture": moisture,
        "crop_growth": crop_growth,
        "historical_data": historical_data,
        "alerts": alerts_data,
        "model_predictions": model_predictions,  # Updated with YOLO detections
        "recommendations": recommendations,
    }

    return jsonify(response_data)
def generate_ai_recommendations(farm, dashboard_data):
    """Generate AI-powered recommendations using OpenAI"""
    try:
        # Check if OpenAI API key is configured
        if not os.getenv("OPENAI_API_KEY"):
            current_app.logger.warning("OpenAI API key not configured, using fallback recommendations")
            return get_fallback_recommendations(farm, dashboard_data)
        
        # Prepare the farm context data
        farm_context = prepare_farm_data_for_ai(farm, dashboard_data)
        
        # Create the prompt for the LLM
        prompt = create_recommendation_prompt(farm_context)
        
        # Call the OpenAI API using the client
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
        
        # Extract the response content
        recommendations_text = response.choices[0].message.content
        
        # Parse the AI response into structured recommendations
        recommendations = parse_ai_recommendations(recommendations_text)
        
        # Ensure we have at least some recommendations
        if not recommendations:
            recommendations = get_fallback_recommendations(farm, dashboard_data)
        
        return recommendations
        
    except Exception as e:
        current_app.logger.error(f"Error generating AI recommendations: {str(e)}")
        return get_fallback_recommendations(farm, dashboard_data)
    
# generate_ai_recommendations, prepare_farm_data_for_ai, create_recommendation_prompt, 
# parse_ai_recommendations, parse_text_recommendations, get_fallback_recommendations, etc.
def prepare_farm_data_for_ai(farm, dashboard_data):
    """Prepare comprehensive farm data for AI analysis"""
    
    # Get additional database information
    active_pests = PestControl.query.filter_by(farm_id=farm.id, status="Active").all()
    pending_tasks = LaborTask.query.filter_by(farm_id=farm.id, status="Pending").all()
    recent_alerts = Alert.query.filter_by(farm_id=farm.id, is_read=False).limit(5).all()
    
    # Get sensor trends (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_sensors = SensorData.query.filter(
        SensorData.farm_id == farm.id,
        SensorData.timestamp >= week_ago
    ).order_by(SensorData.timestamp.desc()).all()
    
    # Get current farm stage
    current_stage = FarmStage.query.filter_by(
        farm_id=farm.id, status="Active"
    ).order_by(FarmStage.start_date.desc()).first()
    
    # Get latest crop health assessment
    latest_crop_health = CropHealth.query.filter_by(
        farm_id=farm.id
    ).order_by(CropHealth.assessment_date.desc()).first()
    
    # Safe handling of model predictions and detections
    model_predictions = dashboard_data.get("model_predictions", {})
    detections = model_predictions.get("detections", [])
    
    # Calculate detection summary with null safety
    maize_count = 0
    weed_count = 0
    avg_confidence = 0.0
    
    if detections and isinstance(detections, list):
        maize_count = sum(1 for d in detections if isinstance(d, dict) and d.get('class') == 'maize')
        weed_count = sum(1 for d in detections if isinstance(d, dict) and d.get('class') == 'weed')
        
        # Calculate average confidence with null safety
        confidence_values = [d.get('confidence', 0) for d in detections if isinstance(d, dict) and d.get('confidence') is not None]
        if confidence_values:
            avg_confidence = sum(confidence_values) / len(confidence_values)
    
    farm_context = {
        "farm_info": {
            "name": farm.name or "Unknown Farm",
            "location": farm.location or "Unknown Location",
            "size": farm.size or 0,
            "crop_type": farm.crop_type or "Unknown Crop",
            "soil_type": farm.soil_type or "Unknown Soil",
            "irrigation_type": farm.irrigation_type or "Unknown Irrigation",
            "water_source": farm.water_source or "Unknown Water Source",
        },
        "current_conditions": {
            "soil_health": dashboard_data.get("soil_health", {}),
            "field_health": dashboard_data.get("field_health", {}),
            "moisture_levels": dashboard_data.get("moisture", {}),
            "weather": dashboard_data.get("weather", {}),
        },
        "crop_status": {
            "current_stage": current_stage.stage_name if current_stage else "Unknown",
            "days_in_stage": (datetime.utcnow() - current_stage.start_date).days if current_stage else 0,
            "growth_progress": dashboard_data.get("crop_growth", {}),
            "model_predictions": model_predictions,
            "detection_summary": {
                "maize_count": maize_count,
                "weed_count": weed_count,
                "avg_confidence": avg_confidence
            },
            "health_assessment": {
                "status": latest_crop_health.status if latest_crop_health else "Unknown",
                "notes": latest_crop_health.notes if latest_crop_health else "No recent assessment",
                "date": latest_crop_health.assessment_date.isoformat() if latest_crop_health else None
            }
        },
        "sensor_data": {
            "current_readings": dashboard_data.get("sensors", {}),
            "historical_trends": dashboard_data.get("historical_data", {}),
            "recent_readings": [
                {
                    "type": sensor.sensor_type,
                    "value": sensor.value,
                    "timestamp": sensor.timestamp.isoformat(),
                    "unit": sensor.unit or ""
                }
                for sensor in recent_sensors[:10]  # Last 10 readings
            ]
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
            ],
            "alerts": [
                {
                    "type": alert.alert_type or "Unknown Alert",
                    "message": alert.message or "No message",
                    "severity": alert.severity or "Medium",
                    "created_at": alert.created_at.isoformat() if alert.created_at else "Unknown Date"
                }
                for alert in recent_alerts
            ],
            "pending_tasks": [
                {
                    "name": task.task_name or "Unknown Task",
                    "description": task.description or "No description",
                    "priority": task.priority or "Medium",
                    "due_date": task.end_date.isoformat() if task.end_date else None
                }
                for task in pending_tasks
            ]
        }
    }
    
    return farm_context

def create_recommendation_prompt(farm_context):
    """Create a comprehensive prompt for AI recommendation generation"""
    
    # Get values with safe defaults
    farm_info = farm_context.get('farm_info', {})
    current_conditions = farm_context.get('current_conditions', {})
    crop_status = farm_context.get('crop_status', {})
    active_issues = farm_context.get('active_issues', {})
    
    # Safe access to nested dictionaries
    soil_health = current_conditions.get('soil_health', {})
    moisture_levels = current_conditions.get('moisture_levels', {})
    field_health = current_conditions.get('field_health', {})
    weather = current_conditions.get('weather', {})
    growth_progress = crop_status.get('growth_progress', {})
    detection_summary = crop_status.get('detection_summary', {})
    
    prompt = f"""
Based on the following comprehensive farm data, provide 3-5 specific, actionable recommendations for optimal farm management:

FARM INFORMATION:
- Name: {farm_info.get('name', 'Unknown')}
- Crop Type: {farm_info.get('crop_type', 'Unknown')}
- Size: {farm_info.get('size', 0)} acres
- Soil Type: {farm_info.get('soil_type', 'Unknown')}
- Irrigation: {farm_info.get('irrigation_type', 'Unknown')}
- Location: {farm_info.get('location', 'Unknown')}

CURRENT CONDITIONS:
- Soil Health: {soil_health.get('status', 'Unknown')} (Quality: {soil_health.get('quality', 0)}%)
- Nitrogen: {soil_health.get('nitrogen', 0)} ppm
- Phosphorus: {soil_health.get('phosphorus', 0)} ppm
- pH Level: {soil_health.get('ph_level', 0)}
- Soil Moisture: {moisture_levels.get('current', 0)}% ({moisture_levels.get('status', 'Unknown')})
- Field Health: {field_health.get('status', 'Unknown')} ({field_health.get('overall_health', 0)}%)
- Weather: {weather.get('temperature', 0)}°C, {weather.get('condition', 'Unknown')}

CROP STATUS:
- Current Stage: {crop_status.get('current_stage', 'Unknown')}
- Days in Stage: {crop_status.get('days_in_stage', 0)}
- Growth Status: {growth_progress.get('status', 'Unknown')}
- Progress: {growth_progress.get('progress', 0)}%

ACTIVE ISSUES:
- Active Pests: {len(active_issues.get('pests', []))} detected
- Unread Alerts: {len(active_issues.get('alerts', []))}
- Pending Tasks: {len(active_issues.get('pending_tasks', []))}

SPECIFIC ISSUES DETECTED:
"""
    
    # Add model predictions to the prompt
    model_predictions = crop_status.get('model_predictions', {})
    if model_predictions:
        prompt += f"""
MODEL PREDICTIONS:
- Crop Type: {model_predictions.get('crop_type', 'Unknown')}
- Health Status: {model_predictions.get('health_status', 'Unknown')}
- Disease Class: {model_predictions.get('disease_class', 'None detected')}
- Confidence: {(model_predictions.get('confidence') or 0) * 100:.1f}%
- Last Analyzed: {model_predictions.get('last_analyzed', 'Unknown')}

DETECTION RESULTS:
- Maize Plants Detected: {detection_summary.get('maize_count', 0)}
- Weeds Detected: {detection_summary.get('weed_count', 0)}
- Average Detection Confidence: {detection_summary.get('avg_confidence', 0) * 100:.1f}%
"""
    
    # Add specific pest information
    pests = active_issues.get('pests', [])
    if pests:
        prompt += "\nPEST ISSUES:\n"
        for pest in pests:
            prompt += f"- {pest.get('name', 'Unknown')} ({pest.get('severity', 'Unknown')} severity) in {pest.get('location', 'Unknown')}: {pest.get('description', 'No description')}\n"
    
    # Add specific alerts
    alerts = active_issues.get('alerts', [])
    if alerts:
        prompt += "\nRECENT ALERTS:\n"
        for alert in alerts[:3]:  # Top 3 alerts
            prompt += f"- {alert.get('type', 'Unknown')}: {alert.get('message', 'No message')} (Severity: {alert.get('severity', 'Unknown')})\n"
    
    # Add pending tasks
    tasks = active_issues.get('pending_tasks', [])
    if tasks:
        prompt += "\nPENDING TASKS:\n"
        for task in tasks[:3]:  # Top 3 tasks
            prompt += f"- {task.get('name', 'Unknown')} (Priority: {task.get('priority', 'Unknown')}): {task.get('description', 'No description')}\n"
    
    prompt += """

Please provide 3-5 specific recommendations in the following JSON format:
[
    {
        "action": "Brief action title",
        "description": "Detailed explanation of what to do and why",
        "priority": "High/Medium/Low",
        "due": "Timeframe for action",
        "reasoning": "Why this recommendation is important based on the data"
    }
]

Focus on:
1. Immediate critical issues that need attention
2. Preventive measures based on current conditions
3. Optimization opportunities for better yields
4. Seasonal/stage-appropriate recommendations
5. Resource efficiency improvements

Ensure recommendations are specific to the crop type, current growth stage, and detected conditions.
"""
    
    return prompt

def parse_text_recommendations(text_response):
    """Parse text-based AI response into structured recommendations"""
    recommendations = []
    lines = text_response.split('\n')
    
    current_rec = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for numbered recommendations or bullet points
        if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '•']):
            if current_rec:
                recommendations.append(current_rec)
            
            # Extract action from the line
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
            # Add to description if we have a current recommendation
            current_rec["description"] += " " + line
    
    # Add the last recommendation
    if current_rec:
        recommendations.append(current_rec)
    
    return recommendations[:5]  # Limit to 5 recommendations


def get_fallback_recommendations(farm, dashboard_data):
    """Generate fallback recommendations when AI is unavailable"""
    recommendations = []
    
    # Get database-based recommendations as fallback
    active_pests = PestControl.query.filter_by(farm_id=farm.id, status="Active").all()
    pending_tasks = LaborTask.query.filter_by(farm_id=farm.id, status="Pending").limit(2).all()
    
    # Pest control recommendations
    for pest in active_pests:
        recommendations.append({
            "action": "Pest Treatment",
            "description": f"{pest.pest_name} detected in {pest.location_in_farm or 'farm'}. {pest.description or 'Immediate attention required.'}",
            "priority": pest.severity or "Medium",
            "due": "ASAP" if pest.severity == "High" else "This week",
            "reasoning": "Active pest detection requires immediate intervention"
        })
    
    # Labor task recommendations
    for task in pending_tasks:
        due_date = task.end_date.strftime("%b %d") if task.end_date else "This week"
        recommendations.append({
            "action": task.task_name,
            "description": task.description or f"Complete {task.task_name} task",
            "priority": task.priority or "Medium",
            "due": due_date,
            "reasoning": "Scheduled farm maintenance task"
        })
    
    # Sensor-based recommendations
    sensors = dashboard_data.get("sensors", {})
    
    if sensors.get("nitrogen") and sensors["nitrogen"] < 40:
        recommendations.append({
            "action": "Apply Nitrogen Fertilizer",
            "description": f"Nitrogen levels are at {sensors['nitrogen']} ppm, below optimal range. Apply nitrogen-rich fertilizer to improve crop growth.",
            "priority": "High",
            "due": "Within 48 hours",
            "reasoning": "Low nitrogen levels can significantly impact crop yield"
        })
    
    if sensors.get("soil_moisture") and sensors["soil_moisture"] < 40:
        recommendations.append({
            "action": "Irrigation Needed",
            "description": f"Soil moisture is at {sensors['soil_moisture']}%, below optimal range. Schedule irrigation to prevent crop stress.",
            "priority": "High",
            "due": "Today",
            "reasoning": "Low soil moisture can cause immediate crop stress"
        })
    
    # Default recommendation if none found
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
    """Parse AI response into structured recommendation format"""
    try:
        # Try to extract JSON from the response
        # The AI might include text before/after the JSON, so we need to find it
        start_idx = ai_response.find('[')
        end_idx = ai_response.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            # If no JSON found, try to parse as text and create structured recommendations
            return parse_text_recommendations(ai_response)
        
        json_str = ai_response[start_idx:end_idx]
        recommendations = json.loads(json_str)
        
        # Validate and clean recommendations
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
        
    except json.JSONDecodeError:
        current_app.logger.warning("Failed to parse AI response as JSON, attempting text parsing")
        return parse_text_recommendations(ai_response)
    except Exception as e:
        current_app.logger.error(f"Error parsing AI recommendations: {str(e)}")
        return []


@advisory.route("/debug")
@login_required
def api_debug():
    """Debug endpoint to check API configuration and routes"""
    print("\n" + "="*80)
    print("DEBUG ENDPOINT CALLED")
    print("="*80)
    
    # Check if OpenWeather API key is configured
    openweather_key = "Not configured"
    if os.getenv("OPENWEATHER_API_KEY"):
        openweather_key = (
            "Configured (first 4 chars: "
            + os.getenv("OPENWEATHER_API_KEY")[:4]
            + "...)"
        )
    
    # Check OpenAI API key
    openai_key = "Not configured"
    if os.getenv("OPENAI_API_KEY"):
        openai_key = (
            "Configured (first 4 chars: "
            + os.getenv("OPENAI_API_KEY")[:4]
            + "...)"
        )
    
    print(f"OpenWeather API Key: {openweather_key}")
    print(f"OpenAI API Key: {openai_key}")

    # Get user's farm for more detailed debug info
    user_farm = Farm.query.filter_by(user_id=current_user.id).first()
    
    if not user_farm:
        print("❌ No farm found for user")
        debug_info = {
            "blueprint": "api",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "authenticated": current_user.is_authenticated,
            },
            "error": "No farm found for user",
            "openweather_api_key": openweather_key,
            "openai_api_key": openai_key,
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return jsonify(debug_info)
    
    print(f"✅ Farm found: {user_farm.name} (ID: {user_farm.id})")
    
    # Get counts for debug info
    sensor_count = SensorData.query.filter_by(farm_id=user_farm.id).count()
    alert_count = Alert.query.filter_by(farm_id=user_farm.id).count()
    pest_count = PestControl.query.filter_by(farm_id=user_farm.id).count()
    stage_count = FarmStage.query.filter_by(farm_id=user_farm.id).count()
    task_count = LaborTask.query.filter_by(farm_id=user_farm.id).count()
    field_count = Field.query.filter_by(farm_id=user_farm.id).count()
    
    print(f"📊 Data counts:")
    print(f"   - Sensor Data: {sensor_count}")
    print(f"   - Alerts: {alert_count}")
    print(f"   - Pest Controls: {pest_count}")
    print(f"   - Farm Stages: {stage_count}")
    print(f"   - Labor Tasks: {task_count}")
    print(f"   - Fields: {field_count}")
    
    # Test AI Recommendations Generation
    print("\n" + "-"*60)
    print("TESTING AI RECOMMENDATIONS GENERATION")
    print("-"*60)
    
    try:
        # Get basic dashboard data for AI recommendations
        print("🔄 Gathering dashboard data...")
        
        # Create minimal dashboard data for testing
        test_dashboard_data = {
            "soil_health": {
                "status": "Good",
                "quality": 76,
                "nitrogen": 42,
                "phosphorus": 28,
                "ph_level": 6.8,
            },
            "field_health": {
                "status": "Good",
                "overall_health": 76,
            },
            "moisture": {
                "status": "Normal",
                "current": 64,
            },
            "crop_growth": {
                "status": "On Track",
                "progress": 65,
                "stage": "Growth",
            },
            "weather": {
                "temperature": 24,
                "condition": "Sunny",
            },
            "model_predictions": {
                "crop_type": "Maize",
                "health_status": "Healthy",
                "confidence": 0.85,
                "detections": [
                    {"class": "maize", "confidence": 0.9},
                    {"class": "maize", "confidence": 0.8},
                ]
            },
            "sensors": {
                "soil_moisture": 64,
                "nitrogen": 42,
                "phosphorus": 28,
                "ph": 6.8,
            },
            "historical_data": {
                "temperature": [22, 24, 26, 25, 27],
                "moisture": [68, 65, 62, 60, 58],
            },
            "alerts": []
        }
        
        print("🤖 Generating AI recommendations...")
        
        # Generate AI recommendations
        recommendations = generate_ai_recommendations(user_farm, test_dashboard_data)
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        print("\n📋 AI RECOMMENDATIONS:")
        print("-" * 40)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.get('action', 'Unknown Action')}")
            print(f"   Priority: {rec.get('priority', 'Unknown')}")
            print(f"   Due: {rec.get('due', 'Unknown')}")
            print(f"   Description: {rec.get('description', 'No description')}")
            if rec.get('reasoning'):
                print(f"   Reasoning: {rec.get('reasoning')}")
        
        # Test the farm context preparation
        print("\n" + "-"*40)
        print("FARM CONTEXT DATA:")
        print("-"*40)
        
        farm_context = prepare_farm_data_for_ai(user_farm, test_dashboard_data)
        
        print(f"Farm Info: {farm_context['farm_info']['name']}")
        print(f"Crop Type: {farm_context['farm_info']['crop_type']}")
        print(f"Current Stage: {farm_context['crop_status']['current_stage']}")
        print(f"Detection Summary:")
        print(f"   - Maize Count: {farm_context['crop_status']['detection_summary']['maize_count']}")
        print(f"   - Weed Count: {farm_context['crop_status']['detection_summary']['weed_count']}")
        print(f"   - Avg Confidence: {farm_context['crop_status']['detection_summary']['avg_confidence']:.2f}")
        print(f"Active Issues:")
        print(f"   - Pests: {len(farm_context['active_issues']['pests'])}")
        print(f"   - Alerts: {len(farm_context['active_issues']['alerts'])}")
        print(f"   - Tasks: {len(farm_context['active_issues']['pending_tasks'])}")
        
        ai_status = "✅ AI Recommendations Working"
        
    except Exception as e:
        print(f"❌ Error generating AI recommendations: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        
        recommendations = []
        ai_status = f"❌ AI Error: {str(e)}"
    
    print("\n" + "="*80)
    print("DEBUG ENDPOINT COMPLETED")
    print("="*80 + "\n")
    
    # Prepare debug info response
    debug_info = {
        "blueprint": "api",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "authenticated": current_user.is_authenticated,
        },
        "api_keys": {
            "openweather": openweather_key,
            "openai": openai_key,
        },
        "farm_info": {
            "id": user_farm.id,
            "name": user_farm.name,
            "crop_type": user_farm.crop_type,
            "location": user_farm.location,
            "size": user_farm.size,
        },
        "data_counts": {
            "farms": Farm.query.filter_by(user_id=current_user.id).count(),
            "sensor_data": sensor_count,
            "alerts": alert_count,
            "pest_controls": pest_count,
            "farm_stages": stage_count,
            "labor_tasks": task_count,
            "fields": field_count,
        },
        "ai_recommendations": {
            "status": ai_status,
            "count": len(recommendations),
            "recommendations": recommendations,
        },
        "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return jsonify(debug_info)

@advisory.route("/advisory")
@login_required
def advisory():
    """Render the advisory page with AI recommendations"""
    try:
        # Get the dashboard data (this will include AI recommendations)
        response = dashboard_data()
        
        # Check if the response is successful
        if isinstance(response, tuple):  # Error response
            return response
            
        # Extract data from the JSON response
        dashboard_json = response.get_json()
        
        # Pass the data to the template
        return render_template('advisory.html', 
                             farm_info=dashboard_json.get('farm_info', {}),
                             weather=dashboard_json.get('weather', {}),
                             soil_health=dashboard_json.get('soil_health', {}),
                             field_health=dashboard_json.get('field_health', {}),
                             moisture=dashboard_json.get('moisture', {}),
                             crop_growth=dashboard_json.get('crop_growth', {}),
                             historical_data=dashboard_json.get('historical_data', {}),
                             alerts=dashboard_json.get('alerts', []),
                             model_predictions=dashboard_json.get('model_predictions', {}),
                             recommendations=dashboard_json.get('recommendations', []))
                             
    except Exception as e:
        current_app.logger.error(f"Error loading advisory page: {str(e)}")
        return render_template('advisory.html', 
                             error="Unable to load advisory data. Please try again later.",
                             farm_info={}, weather={}, soil_health={}, field_health={}, 
                             moisture={}, crop_growth={}, historical_data={}, 
                             alerts=[], model_predictions={}, recommendations=[])