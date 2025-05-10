# app/farm/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, FloatField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class FarmForm(FlaskForm):
    """Form for creating or updating farm information"""
    name = StringField('Farm Name', validators=[
        DataRequired(), 
        Length(1, 100)
    ])
    location = StringField('Location', validators=[
        DataRequired(), 
        Length(1, 200)
    ])
    size_acres = FloatField('Size (acres)', validators=[
        DataRequired(),
        NumberRange(min=0.1, message='Farm size must be greater than 0.1 acres')
    ])
    crop_type = StringField('Primary Crop Type', validators=[
        DataRequired(), 
        Length(1, 100)
    ])
    description = TextAreaField('Description', validators=[
        Optional()
    ])
    submit = SubmitField('Save Farm')

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

