#!/usr/bin/env python3
"""
FarmEye: Smart Farm Monitoring System
This is the main entry point for the FarmEye web application.
It initializes and runs the Flask application.
"""

import os
from app import create_app
from flask_migrate import Migrate
from app.auth.models import db, User, Role
from app.farm.models import Farm, Sensor, SensorData, CropHealth, WeatherData
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Create the application instance with the appropriate configuration
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """
    Configure Flask shell context to auto-import database models
    and other commonly used objects for easier debugging and testing.
    """
    return dict(
        db=db, 
        User=User, 
        Role=Role, 
        Farm=Farm, 
        Sensor=Sensor, 
        SensorData=SensorData,
        CropHealth=CropHealth,
        WeatherData=WeatherData
    )

@app.cli.command("init-db")
def init_db():
    """Initialize the database with initial roles and admin user."""
    from flask import current_app
    
    print("Creating database tables...")
    db.create_all()
    
    # Create roles if they don't exist
    roles = ['Admin', 'Farmer', 'Agricultural Officer', 'Researcher']
    for role_name in roles:
        role = Role.query.filter_by(name=role_name).first()
        if role is None:
            role = Role(name=role_name)
            db.session.add(role)
    
    # Create admin user if it doesn't exist
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@farmeye.com')
    admin = User.query.filter_by(email=admin_email).first()
    if admin is None:
        admin_role = Role.query.filter_by(name='Admin').first()
        admin_password = current_app.config.get('ADMIN_PASSWORD', 'admin123')  # Change in production
        admin = User(
            email=admin_email,
            username='admin',
            password=admin_password,
            firstname='Admin',
            lastname='User',
            role=admin_role,
            confirmed=True
        )
        db.session.add(admin)
    
    db.session.commit()
    print("Database initialized with roles and admin user.")

@app.cli.command("create-test-data")
def create_test_data():
    """Create test data for development and testing purposes."""
    from faker import Faker
    import random
    from datetime import datetime, timedelta
    
    fake = Faker()
    
    print("Creating test data...")
    
    # Create test farms
    for i in range(5):
        farm = Farm(
            name=f"Test Farm {i+1}",
            location=fake.city(),
            size=random.randint(1, 100),
            crop_type=random.choice(['Maize', 'Coffee', 'Tea', 'Wheat', 'Beans']),
            owner_id=1  # Assign to admin for simplicity
        )
        db.session.add(farm)
    
    db.session.commit()
    
    # Create test sensors for each farm
    farms = Farm.query.all()
    sensor_types = ['Soil Moisture', 'Temperature', 'Humidity', 'Light', 'pH']
    
    for farm in farms:
        for _ in range(3):  # 3 sensors per farm
            sensor = Sensor(
                farm_id=farm.id,
                sensor_type=random.choice(sensor_types),
                location=f"Field {random.randint(1, 5)}",
                install_date=datetime.now() - timedelta(days=random.randint(1, 90)),
                last_maintenance=datetime.now() - timedelta(days=random.randint(0, 30)),
                status='Active'
            )
            db.session.add(sensor)
    
    db.session.commit()
    
    # Create test sensor data
    sensors = Sensor.query.all()
    for sensor in sensors:
        # Generate data for the last 7 days
        for day in range(7):
            for hour in range(0, 24, 3):  # Data every 3 hours
                reading_time = datetime.now() - timedelta(days=day, hours=hour)
                
                # Generate appropriate values based on sensor type
                if sensor.sensor_type == 'Soil Moisture':
                    value = random.uniform(20.0, 80.0)
                elif sensor.sensor_type == 'Temperature':
                    value = random.uniform(15.0, 35.0)
                elif sensor.sensor_type == 'Humidity':
                    value = random.uniform(40.0, 95.0)
                elif sensor.sensor_type == 'Light':
                    value = random.uniform(0.0, 1000.0)
                else:  # pH
                    value = random.uniform(4.5, 8.5)
                
                data = SensorData(
                    sensor_id=sensor.id,
                    value=value,
                    timestamp=reading_time,
                    status='Valid'
                )
                db.session.add(data)
    
    # Create weather data for each farm
    weather_conditions = ['Sunny', 'Cloudy', 'Rainy', 'Windy', 'Overcast']
    for farm in farms:
        for day in range(7):
            data = WeatherData(
                farm_id=farm.id,
                timestamp=datetime.now() - timedelta(days=day),
                temperature=random.uniform(15.0, 30.0),
                humidity=random.uniform(40.0, 95.0),
                rainfall=random.uniform(0.0, 30.0),
                wind_speed=random.uniform(0.0, 15.0),
                condition=random.choice(weather_conditions)
            )
            db.session.add(data)
    
    # Create crop health assessments
    health_statuses = ['Healthy', 'Minor Issues', 'Needs Attention', 'Critical']
    for farm in farms:
        for _ in range(3):  # 3 assessments per farm
            assessment_date = datetime.now() - timedelta(days=random.randint(0, 30))
            health = CropHealth(
                farm_id=farm.id,
                assessment_date=assessment_date,
                status=random.choice(health_statuses),
                notes=fake.paragraph(nb_sentences=3),
                image_url=None  # No actual images in test data
            )
            db.session.add(health)
    
    db.session.commit()
    print("Test data created successfully.")


if __name__ == '__main__':
    # Use environment variables for host and port if available
    host = os.getenv('FARMEYE_HOST', '0.0.0.0')
    port = int(os.getenv('FARMEYE_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    app.run(host=host, port=port, debug=debug)