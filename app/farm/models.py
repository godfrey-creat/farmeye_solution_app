from datetime import datetime
from app import db  # Import db from app package instead of creating a new instance

class Farm(db.Model):
    __tablename__ = 'farms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    size = db.Column(db.Float, nullable=False)  # Size in acres/hectares
    size_acres = db.Column(db.Float)  # Added from auth models
    crop_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)  # Added from auth models
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Use string reference instead of direct class reference
    # This breaks the circular dependency
    owner = db.relationship('User', backref='farms', lazy=True, foreign_keys=[user_id])
    sensors = db.relationship('Sensor', backref='farm', lazy=True)
    crop_health = db.relationship('CropHealth', backref='farm', lazy=True)
    weather_data = db.relationship('WeatherData', backref='farm', lazy=True)
    images = db.relationship('FarmImage', backref='farm', lazy=True)

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
    # Added fields from auth.models
    sensor_type = db.Column(db.String(50))  # e.g., 'soil_moisture', 'temperature'
    unit = db.Column(db.String(20))  # e.g., 'celsius', '%', 'pH'
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Use string reference for User
    user = db.relationship('User', backref='sensor_data', lazy=True, foreign_keys=[user_id])

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
    # Added fields from auth.models
    filename = db.Column(db.String(255))
    path = db.Column(db.String(255))
    image_type = db.Column(db.String(50))  # e.g., 'soil', 'crop', 'pest'
    processed = db.Column(db.Boolean, default=False)
    processing_results = db.Column(db.Text)  # JSON or text results from ML model
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Use string reference for User
    user = db.relationship('User', backref='farm_images', lazy=True, foreign_keys=[user_id])

    def __repr__(self):
        return f"<FarmImage Farm: {self.farm_id}, URL: {self.image_url}>"
    
class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    alert_type = db.Column(db.String(50), nullable=False)  # E.g., 'Sensor Failure', 'Weather Alert', etc.
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Active')  # Active, Resolved, etc.
    # Added fields from auth.models
    severity = db.Column(db.String(20))  # e.g., 'low', 'medium', 'high'
    is_read = db.Column(db.Boolean, default=False)
    
    # Use string reference for User
    user = db.relationship('User', backref='alerts', lazy=True, foreign_keys=[user_id])

    def __repr__(self):
        return f"<Alert Type: {self.alert_type}, Status: {self.status}, Created At: {self.created_at}>"