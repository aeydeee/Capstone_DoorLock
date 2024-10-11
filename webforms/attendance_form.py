from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired

from models import Schedule, Course


class SelectScheduleForm(FlaskForm):
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    schedule_id = SelectField('Schedule', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def set_choices(self):
        self.course_id.choices = [(course.id, course.course_name) for course in Course.query.all()]
        self.schedule_id.choices = []

    def set_schedule_choices(self, course_id):
        schedules = Schedule.query.filter_by(course_id=course_id).all()
        self.schedule_id.choices = [(schedule.id, f"{schedule.day.name} {schedule.start_time} - {schedule.end_time}")
                                    for schedule in schedules]
