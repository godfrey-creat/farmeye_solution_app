# app/api/routes.py
from flask import jsonify, current_app
from flask_login import login_required, current_user
import requests
from datetime import datetime, timedelta
from . import api
from ..farm.models import Farm, SensorData, Alert, FarmStage, PestControl
import os
from dotenv import load_dotenv
load_dotenv()


@api.route('/dashboard-data')
@login_required
def dashboard_data():
    """API endpoint that provides dashboard data in JSON format"""
    # Get the user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()

    if not farm:
        return jsonify({
            'error': 'No farm found. Please register a farm first.'
        }), 404

    # Get the selected field (for now, we'll use a mock field)
    field = "Field A-12"  # This would come from the database in a real application

    # 1. Farm & Field Information
    farm_info = {
        'name': farm.name,
        'field': field,
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 2. Weather & Forecast
    # Try to extract latitude and longitude from the farm location
    weather_data = {}
    try:
        # Check if location contains lat/long information
        if ',' in farm.location:
            lat, lon = map(float, farm.location.split(','))

            # Set up default weather data in case the API call fails
            weather_data = {
                'temperature': 24,
                'condition': 'Sunny',
                'icon': '01d',
                'forecast': 'Weather forecast unavailable'
            }

            # Try to get API key from config
            api_key = os.getenv('OPENWEATHER_API_KEY')
            if api_key:
                try:
                    weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={api_key}"
                    response = requests.get(weather_url)

                    if response.status_code == 200:
                        data = response.json()
                        current = data['current']

                        weather_data = {
                            'temperature': round(current['temp']),
                            'condition': current['weather'][0]['main'],
                            'icon': current['weather'][0]['icon'],
                            'forecast': 'Light rain expected in 36 hours' if 'rain' in data.get('daily', [{}])[1] else 'No precipitation expected'
                        }
                except Exception as e:
                    current_app.logger.error(f"OpenWeather API error: {str(e)}")
                    # Keep default weather data
            else:
                weather_data['forecast'] = 'Weather forecast unavailable (API key not configured)'
        else:
            weather_data = {
                'temperature': 24,  # Fallback data
                'condition': 'Sunny',
                'icon': '01d',
                'forecast': 'Set farm location for weather forecast'
            }
    except Exception as e:
        current_app.logger.error(f"Weather data processing error: {str(e)}")
        weather_data = {
            'temperature': 24,  # Fallback data
            'condition': 'Sunny',
            'icon': '01d',
            'forecast': 'Weather forecast unavailable'
        }

    # 3. Soil & Field Health
    # Get the latest sensor data
    soil_moisture = SensorData.query.filter_by(
        farm_id=farm.id,
        sensor_type='soil_moisture'
    ).order_by(SensorData.timestamp.desc()).first()

    # Soil Health Card Data
    soil_health = {
        'status': 'Good',  # Could be derived from sensor data
        'quality': 76,     # Overall soil health score
        'nitrogen': 42,    # ppm
        'phosphorus': 28,  # ppm
        'ph_level': 6.8,
        'organic_matter': 4.2  # percentage
    }

    # Field Health Card Data
    field_health = {
        'status': 'Excellent',
        'overall_health': 82,  # percentage
        'improvement': 2,      # percentage improvement
        'improvement_direction': 'up'  # 'up' or 'down'
    }

    # Moisture Level Card Data
    moisture = {
        'status': 'Normal',
        'current': soil_moisture.value if soil_moisture else 64,  # percentage
        'last_irrigation': '2 days ago',
        'next_irrigation': 'Tomorrow',
        'forecast': 'Light rain expected in 36 hours'
    }

    # 4. Crop Growth & Harvest
    # Get the current farm stage
    farm_stage = FarmStage.query.filter_by(
        farm_id=farm.id,
        status='Active'
    ).first()

    # Crop Growth Card Data
    crop_growth = {
        'status': 'On Track',
        'days': '28/62',
        'progress': 45,  # percentage
        'stage': farm_stage.stage_name if farm_stage else 'Vegetative',
        'next_stage': 'Flowering (in 14 days)',
        'harvest_date': 'August 15'
    }

    # 5. Field Metrics Historical Data
    # This would come from sensor history, but for now we'll use mock data
    historical_data = {
        'temperature': [22, 24, 26, 25, 27, 26, 24, 25, 26, 28, 29, 27, 26, 24, 23],
        'moisture': [68, 65, 62, 60, 58, 75, 72, 68, 65, 62, 59, 56, 53, 70, 68],
        'growth': [2.1, 2.3, 2.8, 3.0, 3.2, 3.1, 2.9, 2.7, 2.5, 2.4, 2.2, 2.0, 1.9, 1.8, 1.7],
        'soil_health': [76, 75, 74, 76, 78, 80, 78, 77, 76, 75, 74, 73, 75, 78, 77],
        'dates': ['May 1', 'May 3', 'May 5', 'May 7', 'May 9', 'May 11', 'May 13', 'May 15', 'May 17', 'May 19', 'May 21', 'May 23', 'May 25', 'May 27', 'May 29']
    }

    # 6. Alerts and Recommendations
    # Get recent alerts
    alerts = Alert.query.filter_by(
        farm_id=farm.id,
        is_read=False
    ).order_by(Alert.created_at.desc()).limit(3).all()

    alerts_data = []
    for alert in alerts:
        alerts_data.append({
            'id': alert.id,
            'title': alert.alert_type,  # Using alert_type as the title
            'message': alert.message,
            'severity': alert.severity,
            'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    # 7. Recommended Actions
    # These would come from an AI recommendation system or predefined rules
    # Using mock data for now
    recommendations = [
        {
            'action': 'Apply Fertilizer',
            'description': 'Nitrogen levels in sectors 2 and 3 are below optimal. Apply supplemental fertilizer within 48 hours.',
            'priority': 'High',
            'due': 'Tomorrow'
        },
        {
            'action': 'Pest Treatment',
            'description': 'Early signs of corn earworm detected in sector 4. Apply organic pesticide to prevent infestation.',
            'priority': 'Medium',
            'due': 'In 3 days'
        },
        {
            'action': 'Equipment Maintenance',
            'description': 'Irrigation system inspection recommended. Last maintenance was performed 45 days ago.',
            'priority': 'Info',
            'due': 'This week'
        }
    ]

    # Combine all data into a single response
    response_data = {
        'farm_info': farm_info,
        'weather': weather_data,
        'soil_health': soil_health,
        'field_health': field_health,
        'moisture': moisture,
        'crop_growth': crop_growth,
        'historical_data': historical_data,
        'alerts': alerts_data,
        'recommendations': recommendations
    }

    return jsonify(response_data)

@api.route('/debug')
@login_required
def api_debug():
    """Debug endpoint to check API configuration and routes"""
    # Check if OpenWeather API key is configured
    openweather_key = 'Not configured'
    if current_app.config.get('OPENWEATHER_API_KEY'):
        openweather_key = 'Configured (first 4 chars: ' + current_app.config.get('OPENWEATHER_API_KEY')[:4] + '...)'

    debug_info = {
        'blueprint': 'api',
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'authenticated': current_user.is_authenticated
        },
        'openweather_api_key': openweather_key,
        'farm_count': Farm.query.filter_by(user_id=current_user.id).count(),
        'sensor_data_count': SensorData.query.filter_by(farm_id=Farm.query.filter_by(user_id=current_user.id).first().id if Farm.query.filter_by(user_id=current_user.id).first() else 0).count(),
        'alert_count': Alert.query.filter_by(user_id=current_user.id).count(),
        'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

    return jsonify(debug_info)

@api.route('/user-profile')
@login_required
def user_profile():
    """Return current user profile information"""
    profile_data = {
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'full_name': f"{current_user.first_name} {current_user.last_name}",
        'initials': f"{current_user.first_name[0]}{current_user.last_name[0]}" if current_user.first_name and current_user.last_name else "?",
        'is_approved': current_user.is_approved
    }

    return jsonify(profile_data)