from datetime import datetime
from app import db  # Import db from app package instead of creating a new instance

class Farm(db.Model):
    __tablename__ = 'farm'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    fields = db.relationship('Field', backref='farm', cascade="all, delete-orphan")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f"<Farm {self.name} in {self.region}>"

class Field(db.Model):
    __tablename__ = 'fields'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.String(50), nullable=True)
    longitude = db.Column(db.String(50), nullable=True)
    farming_method = db.Column(db.String(50), nullable=False)
    smart_devices = db.Column(db.String(200))  # comma-separated list
    monitoring_goals = db.Column(db.String(200))  # comma-separated list
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    
    def __repr__(self):
        return f"<Field {self.name} in {self.farm.name}>"

class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
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
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Use string reference for User
    user = db.relationship('User', backref='sensor_data', lazy=True, foreign_keys=[user_id])

    def __repr__(self):
        return f"<SensorData Sensor: {self.sensor_id}, Value: {self.value}, Time: {self.timestamp}>"

class CropHealth(db.Model):
    __tablename__ = 'crop_health'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # Healthy, Needs Attention, etc.
    notes = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)  # Optional field for storing image URLs

    def __repr__(self):
        return f"<CropHealth Farm: {self.farm_id}, Status: {self.status}, Date: {self.assessment_date}>"

class WeatherData(db.Model):
    __tablename__ = 'weather_data'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
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
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
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
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
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
    
class FarmStage(db.Model):
    __tablename__ = 'farm_stages'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    stage_name = db.Column(db.String(50), nullable=False)  # Unprepared, Prepared, Germination, Growth, Flowering, Harvesting
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Active')  # Active, Completed
    description = db.Column(db.Text)
    
    # Relationship with Farm
    farm = db.relationship('Farm', backref='farm_stages', lazy=True)
    # Relationship with Labor tasks
    labor_tasks = db.relationship('LaborTask', backref='farm_stage', lazy=True)

    def __repr__(self):
        return f"<FarmStage {self.stage_name}, Farm: {self.farm_id}, Status: {self.status}>"

class LaborTask(db.Model):
    __tablename__ = 'labor_tasks'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('farm_stages.id'), nullable=True)
    task_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Pending')  # Pending, In Progress, Completed, Cancelled
    priority = db.Column(db.String(20), default='Medium')  # Low, Medium, High
    labor_hours = db.Column(db.Float, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    
    # Relationship with Farm
    farm = db.relationship('Farm', backref='labor_tasks', lazy=True)

    def __repr__(self):
        return f"<LaborTask {self.task_name}, Farm: {self.farm_id}, Status: {self.status}>"