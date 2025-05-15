from app import db
from datetime import datetime
from app.farm.models import Farm


class IrrigationZone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    area = db.Column(db.Float)  # in square meters
    crop_type = db.Column(db.String(50))
    target_moisture = db.Column(db.Float)  # target soil moisture percentage
    status = db.Column(db.String(20))  # active, inactive, scheduled
    farm_id = db.Column(db.Integer, db.ForeignKey("farms.id"), nullable=False)
    farm = db.relationship("Farm", backref=db.backref("irrigation_zones", lazy=True))

    # Relationships
    schedules = db.relationship("IrrigationSchedule", backref="zone", lazy=True)
    sensors = db.relationship("IrrigationSensor", backref="zone", lazy=True)
    water_logs = db.relationship("WaterUsageLog", backref="zone", lazy=True)


class IrrigationSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("irrigation_zone.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer)  # duration in minutes
    water_amount = db.Column(db.Float)  # in gallons
    recurrence = db.Column(db.String(20))  # daily, weekly, custom
    status = db.Column(db.String(20))  # scheduled, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class IrrigationSensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("irrigation_zone.id"), nullable=False)
    sensor_type = db.Column(db.String(50))  # moisture, flow, pressure
    location = db.Column(db.String(100))
    last_reading = db.Column(db.Float)
    last_reading_time = db.Column(db.DateTime)
    status = db.Column(db.String(20))  # active, inactive, maintenance


class WaterUsageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("irrigation_zone.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    water_amount = db.Column(db.Float)  # in gallons
    duration = db.Column(db.Integer)  # in minutes
    cost = db.Column(db.Float)
    efficiency_rating = db.Column(db.Float)  # percentage


class IrrigationAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("irrigation_zone.id"), nullable=False)
    alert_type = db.Column(
        db.String(50)
    )  # low_moisture, system_failure, schedule_conflict
    message = db.Column(db.Text)
    severity = db.Column(db.String(20))  # info, warning, critical
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
