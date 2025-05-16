from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    FloatField,
    SelectField,
    DateTimeField,
    IntegerField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Optional, NumberRange


class IrrigationZoneForm(FlaskForm):
    name = StringField("Zone Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    area = FloatField(
        "Area (sq meters)", validators=[DataRequired(), NumberRange(min=0)]
    )
    crop_type = StringField("Crop Type", validators=[DataRequired()])
    target_moisture = FloatField(
        "Target Moisture %", validators=[DataRequired(), NumberRange(min=0, max=100)]
    )
    status = SelectField(
        "Status",
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("scheduled", "Scheduled"),
        ],
    )


class IrrigationScheduleForm(FlaskForm):
    zone_id = SelectField("Zone", coerce=int, validators=[DataRequired()])
    start_time = DateTimeField("Start Time", validators=[DataRequired()])
    duration = IntegerField(
        "Duration (minutes)", validators=[DataRequired(), NumberRange(min=1)]
    )
    water_amount = FloatField(
        "Water Amount (gallons)", validators=[DataRequired(), NumberRange(min=0)]
    )
    recurrence = SelectField(
        "Recurrence",
        choices=[
            ("once", "Once"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("custom", "Custom"),
        ],
    )


class IrrigationSensorForm(FlaskForm):
    zone_id = SelectField("Zone", coerce=int, validators=[DataRequired()])
    sensor_type = SelectField(
        "Sensor Type",
        choices=[("moisture", "Moisture"), ("flow", "Flow"), ("pressure", "Pressure")],
    )
    location = StringField("Location", validators=[DataRequired()])
    status = SelectField(
        "Status",
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("maintenance", "Maintenance"),
        ],
    )


class AlertSettingsForm(FlaskForm):
    moisture_threshold_low = FloatField(
        "Low Moisture Threshold %",
        validators=[DataRequired(), NumberRange(min=0, max=100)],
    )
    moisture_threshold_high = FloatField(
        "High Moisture Threshold %",
        validators=[DataRequired(), NumberRange(min=0, max=100)],
    )
    notification_email = StringField("Notification Email", validators=[Optional()])
    alert_frequency = SelectField(
        "Alert Frequency",
        choices=[("realtime", "Real-time"), ("hourly", "Hourly"), ("daily", "Daily")],
    )
