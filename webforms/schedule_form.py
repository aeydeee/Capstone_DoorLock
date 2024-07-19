from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import TimeField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired


class ScheduleForm(FlaskForm):
    faculty = SelectField('Faculty', validators=[DataRequired()])
    subject = SelectField('Subject', validators=[DataRequired()])
    day = SelectField('Day', choices=[
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday')
    ], validators=[DataRequired()])
    schedule_from = TimeField('Time From', format='%H:%M', validators=[DataRequired()])
    schedule_to = TimeField('Time End', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditScheduleForm(FlaskForm):
    day = SelectField('Day', choices=[
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday')
    ], validators=[DataRequired()])
    schedule_from = TimeField('Time From', format='%H:%M', validators=[DataRequired()])
    schedule_to = TimeField('Time End', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Update Schedule')
