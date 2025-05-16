from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, FloatField
from wtforms.validators import DataRequired, ValidationError
import re

class FarmLocationForm(FlaskForm):
    """Form for updating a farm's location coordinates"""
    latitude = FloatField('Latitude', validators=[DataRequired()])
    longitude = FloatField('Longitude', validators=[DataRequired()])
    submit = SubmitField('Save Location')
    
    def validate_latitude(self, field):
        """Validate the latitude value is within valid range"""
        if field.data < -90 or field.data > 90:
            raise ValidationError('Latitude must be between -90 and 90 degrees')
    
    def validate_longitude(self, field):
        """Validate the longitude value is within valid range"""
        if field.data < -180 or field.data > 180:
            raise ValidationError('Longitude must be between -180 and 180 degrees') 