from datetime import datetime
from app import db  # Import db from app package instead of creating a new instance


class Farm(db.Model):
    __tablename__ = "farms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    size = db.Column(db.Float, nullable=False)  # Size in acres/hectares
    size_acres = db.Column(db.Float)  # Size specifically in acres
    crop_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # New fields for enhanced farm registration
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    region = db.Column(db.String(100))
    soil_type = db.Column(db.String(50))
    ph_level = db.Column(db.Float)
    soil_notes = db.Column(db.Text)
    irrigation_type = db.Column(db.String(50))
    water_source = db.Column(db.String(50))

    # Relationships
    owner = db.relationship("User", backref="farms", lazy=True, foreign_keys=[user_id])
    sensors = db.relationship("Sensor", backref="farm", lazy=True)
    crop_health = db.relationship("CropHealth", backref="farm", lazy=True)
    weather_data = db.relationship("WeatherData", backref="farm", lazy=True)
    images = db.relationship("FarmImage", backref="farm", lazy=True)
    fields = db.relationship(
        "Field",
        backref=db.backref("farm_ref", lazy=True),
        lazy=True,
        cascade="all, delete-orphan",
    )
    team_members = db.relationship(
        "FarmTeamMember", backref="farm", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Farm {self.name}, Location: {self.location}>"


class Sensor(db.Model):
    __tablename__ = "sensors"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    sensor_type = db.Column(
        db.String(50), nullable=False
    )  # E.g., Humidity, Temperature, etc.
    location = db.Column(db.String(200), nullable=False)
    install_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_maintenance = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="Active")  # Active, Inactive, etc.

    sensor_data = db.relationship("SensorData", backref="sensor", lazy=True)

    def __repr__(self):
        return f"<Sensor {self.sensor_type} at {self.location}>"


class SensorData(db.Model):
    __tablename__ = "sensor_data"

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey("sensors.id"), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Valid")  # Valid, Invalid, etc.
    # Added fields from auth.models
    sensor_type = db.Column(db.String(50))  # e.g., 'soil_moisture', 'temperature'
    unit = db.Column(db.String(20))  # e.g., 'celsius', '%', 'pH'
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Use string reference for User
    user = db.relationship(
        "User", backref="sensor_data", lazy=True, foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"<SensorData Sensor: {self.sensor_id}, Value: {self.value}, Time: {self.timestamp}>"


class CropHealth(db.Model):
    __tablename__ = "crop_health"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # Healthy, Needs Attention, etc.
    notes = db.Column(db.Text, nullable=True)
    image_url = db.Column(
        db.String(200), nullable=True
    )  # Optional field for storing image URLs

    def __repr__(self):
        return f"<CropHealth Farm: {self.farm_id}, Status: {self.status}, Date: {self.assessment_date}>"


class WeatherData(db.Model):
    __tablename__ = "weather_data"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    rainfall = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    condition = db.Column(db.String(50), nullable=False)  # Sunny, Rainy, etc.

    def __repr__(self):
        return f"<WeatherData Farm: {self.farm_id}, Condition: {self.condition}, Time: {self.timestamp}>"


class FarmImage(db.Model):
    __tablename__ = "farm_images"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)  # URL or path to the image
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Added fields from auth.models
    filename = db.Column(db.String(255))
    path = db.Column(db.String(255))
    image_type = db.Column(db.String(50))  # e.g., 'soil', 'crop', 'pest'
    processed = db.Column(db.Boolean, default=False)
    processing_results = db.Column(db.Text)  # JSON or text results from ML model
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Use string reference for User
    user = db.relationship(
        "User", backref="farm_images", lazy=True, foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"<FarmImage Farm: {self.farm_id}, URL: {self.image_url}>"


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    alert_type = db.Column(
        db.String(50), nullable=False
    )  # E.g., 'Sensor Failure', 'Weather Alert', etc.
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Active")  # Active, Resolved, etc.
    # Added fields from auth.models
    severity = db.Column(db.String(20))  # e.g., 'low', 'medium', 'high'
    is_read = db.Column(db.Boolean, default=False)

    # Use string reference for User
    user = db.relationship("User", backref="alerts", lazy=True, foreign_keys=[user_id])

    def __repr__(self):
        return f"<Alert Type: {self.alert_type}, Status: {self.status}, Created At: {self.created_at}>"


# Pest Control Models
class PestControl(db.Model):
    __tablename__ = "pest_control"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    pest_name = db.Column(db.String(100), nullable=False)
    detection_date = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(20), default="Medium")  # Low, Medium, High
    location_in_farm = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="Active")  # Active, Treated, Resolved
    image_url = db.Column(db.String(200), nullable=True)
    detected_by = db.Column(
        db.String(50), default="Manual"
    )  # Manual, YOLO, Sensor, etc.

    # Relationship with Farm
    farm = db.relationship("Farm", backref="pest_detections", lazy=True)
    # Relationship with actions
    actions = db.relationship("PestAction", backref="pest_detection", lazy=True)

    def __repr__(self):
        return f"<PestControl {self.pest_name}, Farm: {self.farm_id}, Severity: {self.severity}>"


class PestAction(db.Model):
    __tablename__ = "pest_actions"

    id = db.Column(db.Integer, primary_key=True)
    pest_control_id = db.Column(
        db.Integer, db.ForeignKey("pest_control.id"), nullable=False
    )
    action_type = db.Column(
        db.String(50), nullable=False
    )  # Chemical, Biological, Mechanical, etc.
    action_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    application_date = db.Column(db.DateTime, nullable=True)
    scheduled_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.String(20), default="Scheduled"
    )  # Scheduled, Completed, Cancelled
    effectiveness = db.Column(
        db.String(20), nullable=True
    )  # Low, Medium, High (to be filled after evaluation)
    cost = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Use string reference for User
    user = db.relationship(
        "User", backref="pest_actions", lazy=True, foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"<PestAction {self.action_name}, Type: {self.action_type}, Status: {self.status}>"


class FarmStage(db.Model):
    __tablename__ = "farm_stages"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    stage_name = db.Column(
        db.String(50), nullable=False
    )  # Unprepared, Prepared, Germination, Growth, Flowering, Harvesting
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="Active")  # Active, Completed
    description = db.Column(db.Text)
    expected_duration = db.Column(db.Integer)  # Expected days in this stage
    recommended_tasks = db.Column(db.Text)

    recommended_tasks = db.Column(db.Text)  # JSON string of recommended task types

    def get_recommended_tasks(self):
        """Get recommended tasks for this growth stage"""
        if not self.recommended_tasks:
            return []

        try:
            import json

            return json.loads(self.recommended_tasks)
        except:
            return []

    # Relationship with Farm
    farm = db.relationship("Farm", backref="farm_stages", lazy=True)
    # Relationship with Labor tasks
    labor_tasks = db.relationship("LaborTask", backref="farm_stage", lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<FarmStage {self.stage_name}, Farm: {self.farm_id}, Status: {self.status}>"


class LaborTask(db.Model):
    __tablename__ = "labor_tasks"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey("farm_stages.id"), nullable=True)
    task_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.String(20), default="Pending"
    )  # Pending, In Progress, Completed, Cancelled
    priority = db.Column(db.String(20), default="Medium")  # Low, Medium, High
    labor_hours = db.Column(db.Float, nullable=True)
    cost = db.Column(db.Float, nullable=True)

    # Relationship with Farm
    farm = db.relationship("Farm", backref="labor_tasks", lazy=True)

    def __repr__(self):
        return (
            f"<LaborTask {self.task_name}, Farm: {self.farm_id}, Status: {self.status}>"
        )


class FarmTeamMember(db.Model):
    __tablename__ = "farm_team_members"

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # viewer, editor, admin
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="farm_memberships")
    added_by_user = db.relationship(
        "User", foreign_keys=[added_by], backref="added_farm_members"
    )

    def __repr__(self):
        return f"<FarmTeamMember user_id={self.user_id} farm_id={self.farm_id} role={self.role}>"


class Field(db.Model):
    """Field model representing a section of a farm"""

    __tablename__ = "fields"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to boundary markers
    boundaries = db.relationship(
        "BoundaryMarker", backref="field", lazy=True, cascade="all, delete-orphan"
    )


class BoundaryMarker(db.Model):
    """BoundaryMarker model representing GPS coordinates for field boundaries"""

    __tablename__ = "boundary_markers"

    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey("fields.id"), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
