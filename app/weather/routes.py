from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from . import weather
from ..farm.models import Farm
from .forms import FarmLocationForm
import requests
from datetime import datetime
import json

# OpenWeather API config
OPENWEATHER_API_KEY = "9ec417826bab17ebcc02904f96c4f776"
OPENWEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/onecall"

@weather.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Weather dashboard page - displays current weather and forecasts"""
    # Get the user's farm
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    
    if not farm:
        # If no farm is found, render the template with a message
        return render_template('dashboard/weather.html', 
                              has_location=False,
                              active_page='weather')
    
    # Try to extract latitude and longitude from the farm location
    # Farm location is stored as "latitude,longitude" 
    try:
        # Check if location contains lat/long information
        if ',' in farm.location:
            lat, lon = map(float, farm.location.split(','))
        else:
            # If location doesn't have coordinates, show the update form
            return render_template('dashboard/weather.html', 
                                  has_location=False,
                                  active_page='weather')
        
        # Build OpenWeather API URL
        weather_url = f"{OPENWEATHER_ENDPOINT}?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={OPENWEATHER_API_KEY}"
        
        # Call the OpenWeather API
        response = requests.get(weather_url)
        
        if response.status_code == 200:
            weather_data = response.json()
            
            # Format the current weather data
            current = weather_data['current']
            current_weather = {
                'temp': round(current['temp']),
                'feels_like': round(current['feels_like']),
                'humidity': current['humidity'],
                'uvi': current['uvi'],
                'wind_speed': current['wind_speed'],
                'condition': current['weather'][0]['main'],
                'description': current['weather'][0]['description'],
                'icon': current['weather'][0]['icon'],
                'time': datetime.fromtimestamp(current['dt'])
            }
            
            # Format hourly forecast (next 24 hours)
            hourly = []
            for hour in weather_data['hourly'][:24]:
                hourly.append({
                    'temp': round(hour['temp']),
                    'time': datetime.fromtimestamp(hour['dt']),
                    'condition': hour['weather'][0]['main'],
                    'icon': hour['weather'][0]['icon'],
                    'pop': round(hour['pop'] * 100)  # Probability of precipitation
                })
            
            # Format daily forecast (7 days)
            daily = []
            for day in weather_data['daily'][:7]:
                daily.append({
                    'day': datetime.fromtimestamp(day['dt']),
                    'temp_max': round(day['temp']['max']),
                    'temp_min': round(day['temp']['min']),
                    'condition': day['weather'][0]['main'],
                    'icon': day['weather'][0]['icon'],
                    'pop': round(day['pop'] * 100),  # Probability of precipitation
                    'humidity': day['humidity'],
                    'uvi': day['uvi']
                })
            
            # Check for rainfall data
            rainfall = 0
            if 'rain' in current:
                rainfall = current['rain'].get('1h', 0)  # Past hour rainfall in mm
            
            # Save weather data to database (optional)
            # This can be implemented to store historical weather data
            # save_weather_data(farm.id, current_weather, daily[0])
            
            return render_template('dashboard/weather.html',
                                  has_location=True,
                                  farm=farm,
                                  current=current_weather,
                                  hourly=hourly,
                                  daily=daily,
                                  rainfall=rainfall,
                                  active_page='weather')
        else:
            # API call failed
            current_app.logger.error(f"Weather API error: {response.status_code} - {response.text}")
            flash('Unable to retrieve weather data. Please try again later.', 'warning')
            return render_template('dashboard/weather.html',
                                  has_location=True,
                                  error=True,
                                  active_page='weather')
            
    except Exception as e:
        # If any error occurs, show the error in the template
        current_app.logger.error(f"Weather API error: {str(e)}")
        flash('There was an error retrieving weather data. Please try again later.', 'danger')
        return render_template('dashboard/weather.html',
                              has_location=False,
                              error=True,
                              active_page='weather')

@weather.route('/update-location', methods=['GET', 'POST'])
@login_required
def update_location():
    """Update farm location page - displays form and handles submission"""
    farm = Farm.query.filter_by(user_id=current_user.id).first()
    form = FarmLocationForm()
    
    # Pre-populate the form if farm location exists
    if farm and ',' in farm.location and request.method == 'GET':
        lat, lon = farm.location.split(',')
        form.latitude.data = float(lat)
        form.longitude.data = float(lon)
    
    if form.validate_on_submit():
        try:
            # Get form data
            latitude = form.latitude.data
            longitude = form.longitude.data
            
            # Update the farm location
            if farm:
                # Store location as "latitude,longitude" string
                farm.location = f"{latitude},{longitude}"
                
                # Save to database
                from app import db
                db.session.commit()
                
                # Update weather data for the new location (optional)
                # This could refresh weather data after location change
                
                flash('Farm location updated successfully!', 'success')
            else:
                flash('Farm not found. Please create a farm first.', 'warning')
            
            # Redirect to the weather dashboard
            return redirect(url_for('weather.dashboard'))
            
        except Exception as e:
            current_app.logger.error(f"Error updating location: {str(e)}")
            flash(f'Error updating location: {str(e)}', 'danger')
    
    return render_template('dashboard/update_location.html', 
                          form=form,
                          farm=farm,
                          active_page='weather')

def save_weather_data(farm_id, current_weather, daily_forecast):
    """Save weather data to the database for historical records"""
    # This is an optional function to save weather data to the database
    # Can be implemented to store historical weather data in the weather_data table
    # and forecast data in the forecast_data table
    from app import db
    from ..farm.models import WeatherData
    
    # Create new WeatherData record
    weather_data = WeatherData(
        farm_id=farm_id,
        timestamp=current_weather['time'],
        temperature=current_weather['temp'],
        humidity=current_weather['humidity'],
        rainfall=0,  # Can be updated if you have rainfall data
        wind_speed=current_weather['wind_speed'],
        condition=current_weather['condition']
    )
    
    # Save to database
    db.session.add(weather_data)
    db.session.commit()
    
    # You could also save forecast data to a forecast_data table
    # if you wanted to track prediction accuracy 