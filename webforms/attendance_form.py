from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired

from models import Schedule, Subject


class SelectScheduleForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    schedule_id = SelectField('Schedule', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def set_choices(self):
        self.subject_id.choices = [(subject.id, subject.subject_name) for subject in Subject.query.all()]
        self.schedule_id.choices = []

    def set_schedule_choices(self, subject_id):
        schedules = Schedule.query.filter_by(subject_id=subject_id).all()
        self.schedule_id.choices = [(schedule.id, f"{schedule.day.name} {schedule.start_time} - {schedule.end_time}")
                                    for schedule in schedules]
