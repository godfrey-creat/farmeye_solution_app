from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length

class AdvisoryRecommendationForm(FlaskForm):
    farm_id = HiddenField("Farm ID", validators=[DataRequired()])
    action = StringField("Action", validators=[DataRequired(), Length(max=128)])
    description = TextAreaField("Description", validators=[DataRequired()])
    priority = SelectField(
        "Priority",
        choices=[("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
        default="Medium"
    )
    due = StringField("Due (timeframe)", validators=[Length(max=64)])
    reasoning = TextAreaField("Reasoning")