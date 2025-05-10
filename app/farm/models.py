from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Farm(db.Model):
    __tablename__ = 'farms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    size = db.Column(db.Float, nullable=False)  # Size in acres/hectares
    crop_type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # Foreign key to User table (if applicable)

    sensors = db.relationship('Sensor', backref='farm', lazy=True)
    crop_health = db.relationship('CropHealth', backref='farm', lazy=True)
    weather_data = db.relationship('WeatherData', backref='farm', lazy=True)

    def __repr__(self):
        return f"<Farm {self.name}, Location: {self.location}>"

class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)  # E.g., Humidity, Temperature, etc.
    location = db.Column(db.String(200), nullable=False)
    install_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_maintenance = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, etc.

    sensor_data = db.relationship('SensorData', backref='sensor', lazy=True)

    def __repr__(self):
        return f"<Sensor {self.sensor_type} at {self.location}>"

class SensorData(db.Model):
    __tablename__ = 'sensor_data'

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Valid')  # Valid, Invalid, etc.

    def __repr__(self):
        return f"<SensorData Sensor: {self.sensor_id}, Value: {self.value}, Time: {self.timestamp}>"

class CropHealth(db.Model):
    __tablename__ = 'crop_health'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # Healthy, Needs Attention, etc.
    notes = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)  # Optional field for storing image URLs

    def __repr__(self):
        return f"<CropHealth Farm: {self.farm_id}, Status: {self.status}, Date: {self.assessment_date}>"

class WeatherData(db.Model):
    __tablename__ = 'weather_data'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    rainfall = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    condition = db.Column(db.String(50), nullable=False)  # Sunny, Rainy, etc.

    def __repr__(self):
        return f"<WeatherData Farm: {self.farm_id}, Condition: {self.condition}, Time: {self.timestamp}>"
    
class FarmImage(db.Model):
    __tablename__ = 'farm_images'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)  # URL or path to the image
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FarmImage Farm: {self.farm_id}, URL: {self.image_url}>"
    
class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    alert_type = db.Column(db.String(50), nullable=False)  # E.g., 'Sensor Failure', 'Weather Alert', etc.
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Active')  # Active, Resolved, etc.

    def __repr__(self):
        return f"<Alert Type: {self.alert_type}, Status: {self.status}, Created At: {self.created_at}>"