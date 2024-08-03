from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import TimeField
from wtforms.fields.simple import SubmitField, StringField
from wtforms.validators import DataRequired, ValidationError

from models import Faculty, Subject, Course, YearLevel, Semester, Section, DayOfWeek, YearLevelEnum


class ScheduleForm(FlaskForm):
    faculty = SelectField('Faculty', validators=[DataRequired()])
    subject = SelectField('Subject', validators=[DataRequired()])
    schedule_day = SelectField('Day', choices=[
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday')
    ], validators=[DataRequired()])
    schedule_time_from = TimeField('Time From', format='%H:%M', validators=[DataRequired()])
    schedule_time_to = TimeField('Time End', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditScheduleForm(FlaskForm):
    schedule_day = SelectField('Day', choices=[
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday')
    ], validators=[DataRequired()])
    schedule_time_from = TimeField('Time From', format='%H:%M', validators=[DataRequired()])
    schedule_time_to = TimeField('Time End', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit')


class NewScheduleForm(FlaskForm):
    day = SelectField('Day of the Week', choices=[(day.name, day.value) for day in DayOfWeek],
                      validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    section_id = SelectField('Section', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Schedule')

    def __init__(self, *args, **kwargs):
        super(NewScheduleForm, self).__init__(*args, **kwargs)
        self.section_id.choices = [(section.id, section.section_name) for section in Section.query.all()]

    def validate_end_time(form, field):
        if field.data <= form.start_time.data:
            raise ValidationError('End time must be after start time.')
