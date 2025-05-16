<<<<<<< HEAD
# app/farm/forms.py
from flask_wtf import FlaskForm
from wtforms.validators import NumberRange, Optional, Email
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import FloatField, SelectMultipleField, BooleanField, RadioField
from wtforms import FloatField, SelectMultipleField, BooleanField, RadioField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class FarmForm(FlaskForm):
    farm_name = StringField('Farm Name', validators=[DataRequired(), Length(1, 100)])
    region = SelectField('Farm Region', choices=[
        ('central', 'Central'), ('coast', 'Coast'), ('eastern', 'Eastern'),
        ('nairobi', 'Nairobi'), ('north_eastern', 'North Eastern'),
        ('nyanza', 'Nyanza'), ('rift_valley', 'Rift Valley'), ('western', 'Western')
    ], validators=[DataRequired()])
    submit = SubmitField('Next: Add Field')

class FieldForm(FlaskForm):
    field_name = StringField('Field Name', validators=[DataRequired()])
    crop_type = StringField('Crop Type', validators=[DataRequired()])
    latitude = StringField('Latitude', validators=[Optional()])
    longitude = StringField('Longitude', validators=[Optional()])
    farming_method = SelectField('Farming Method', choices=[
        ('conventional', 'Conventional'), ('organic', 'Organic'),
        ('hydroponic', 'Hydroponic'), ('greenhouse', 'Greenhouse'),
        ('zero_grazing', 'Zero-grazing')
    ], validators=[DataRequired()])
    smart_devices = SelectMultipleField('Smart Devices', choices=[
        ('soil_moisture_sensor', 'Soil Moisture Sensors'),
        ('weather_station', 'Weather Station'),
        ('livestock_tracker', 'Livestock Trackers'),
        ('cctv', 'CCTV Cameras'),
        ('temp_humidity', 'Temperature/Humidity Sensors'),
        ('auto_feeder', 'Automated Feeders'),
        ('drone', 'Drone Surveillance')
    ])
    monitoring_goals = SelectMultipleField('Monitoring Goals', choices=[
        ('crop_health', 'Real-time Crop Health'),
        ('soil_moisture', 'Soil Moisture & Nutrients'),
        ('livestock_health', 'Livestock Movement/Health'),
        ('water_usage', 'Water Usage Efficiency'),
        ('pest_alerts', 'Pest/Disease Alerts'),
        ('yield_prediction', 'Yield Prediction'),
        ('weather_forecast', 'Weather Forecasting'),
        ('auto_irrigation', 'Automated Irrigation')
    ])
    consent = BooleanField('I consent to smart monitoring.', validators=[DataRequired()])
    add_another = SubmitField('Add Another Field')
    finish = SubmitField('Finish Registration')



class ImageUploadForm(FlaskForm):
    """Form for uploading farm images"""
    image = FileField('Farm Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    image_type = SelectField('Image Type', choices=[
        ('crop', 'Crop Image'),
        ('soil', 'Soil Image'),
        ('pest', 'Pest/Disease Image'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Upload Image')

class SensorDataForm(FlaskForm):
    """Form for manually entering sensor data"""
    sensor_type = SelectField('Sensor Type', choices=[
        ('soil_moisture', 'Soil Moisture'),
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
        ('light', 'Light Intensity'),
        ('rainfall', 'Rainfall'),
        ('ph', 'Soil pH'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    value = FloatField('Value', validators=[DataRequired()])
    unit = StringField('Unit', validators=[DataRequired(), Length(1, 20)])
    latitude = FloatField('Latitude (optional)', validators=[Optional()])
    longitude = FloatField('Longitude (optional)', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Sensor Data')
class FarmRegistrationForm(FlaskForm):
    """Form for standalone farm registration page - used for CSRF protection only.
    All form data is handled via JavaScript and submitted as JSON."""

    def __init__(self, *args, **kwargs):
        super(FarmRegistrationForm, self).__init__(*args, **kwargs)
        # No fields needed as this is just for CSRF protection
        # The actual form data is handled via JavaScript in farm_registration.js


class TeamMemberForm(FlaskForm):
    """Form for adding team members to a farm"""

    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    role = SelectField(
        "Role",
        choices=[
            ("owner", "Owner"),
            ("manager", "Manager"),
            ("worker", "Worker"),
            ("consultant", "Consultant"),
        ],
        validators=[DataRequired()],
    )


class BoundaryMarkerForm(FlaskForm):
    """Form for field boundary markers"""

    latitude = FloatField("Latitude", validators=[DataRequired()])
    longitude = FloatField("Longitude", validators=[DataRequired()])
=======
# app/farm/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField,
    FloatField,
    TextAreaField,
    SelectField,
    SubmitField,
    FieldList,
    FormField,
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email


class FarmRegistrationForm(FlaskForm):
    """Form for standalone farm registration page - used for CSRF protection only.
    All form data is handled via JavaScript and submitted as JSON."""

    def __init__(self, *args, **kwargs):
        super(FarmRegistrationForm, self).__init__(*args, **kwargs)
        # No fields needed as this is just for CSRF protection
        # The actual form data is handled via JavaScript in farm_registration.js


class TeamMemberForm(FlaskForm):
    """Form for adding team members to a farm"""

    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    role = SelectField(
        "Role",
        choices=[
            ("owner", "Owner"),
            ("manager", "Manager"),
            ("worker", "Worker"),
            ("consultant", "Consultant"),
        ],
        validators=[DataRequired()],
    )


class BoundaryMarkerForm(FlaskForm):
    """Form for field boundary markers"""

    latitude = FloatField("Latitude", validators=[DataRequired()])
    longitude = FloatField("Longitude", validators=[DataRequired()])


class FieldForm(FlaskForm):
    """Form for farm fields"""

    name = StringField("Field Name", validators=[DataRequired()])
    boundaries = FieldList(FormField(BoundaryMarkerForm), min_entries=3)


class FarmForm(FlaskForm):
    """Form for creating or updating farm information"""

    name = StringField("Farm Name", validators=[DataRequired(), Length(1, 100)])
    location = StringField("Location", validators=[DataRequired(), Length(1, 200)])
    size_acres = FloatField(
        "Size (acres)",
        validators=[
            DataRequired(),
            NumberRange(min=0.1, message="Farm size must be greater than 0.1 acres"),
        ],
    )
    crop_type = StringField(
        "Primary Crop Type", validators=[DataRequired(), Length(1, 100)]
    )
    description = TextAreaField("Description", validators=[Optional()])
    fields = FieldList(FormField(FieldForm), min_entries=1)
    team_members = FieldList(FormField(TeamMemberForm), min_entries=0)
    submit = SubmitField("Save Farm")


class ImageUploadForm(FlaskForm):
    """Form for uploading farm images"""

    image = FileField(
        "Farm Image",
        validators=[
            FileRequired(),
            FileAllowed(["jpg", "jpeg", "png"], "Images only!"),
        ],
    )
    image_type = SelectField(
        "Image Type",
        choices=[
            ("crop", "Crop Image"),
            ("soil", "Soil Image"),
            ("pest", "Pest/Disease Image"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Upload Image")


class SensorDataForm(FlaskForm):
    """Form for manually entering sensor data"""

    sensor_type = SelectField(
        "Sensor Type",
        choices=[
            ("soil_moisture", "Soil Moisture"),
            ("temperature", "Temperature"),
            ("humidity", "Humidity"),
            ("light", "Light Intensity"),
            ("rainfall", "Rainfall"),
            ("ph", "Soil pH"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    value = FloatField("Value", validators=[DataRequired()])
    unit = StringField("Unit", validators=[DataRequired(), Length(1, 20)])
    latitude = FloatField("Latitude (optional)", validators=[Optional()])
    longitude = FloatField("Longitude (optional)", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Add Sensor Data")
>>>>>>> origin/Dynamic-Parsing
