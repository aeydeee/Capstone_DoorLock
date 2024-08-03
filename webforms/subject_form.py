from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.datetime import TimeField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from models import Course, Semester, YearLevel


class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    code = StringField('Subject Code', validators=[DataRequired()])
    units = IntegerField('Subject Units', validators=[DataRequired(), NumberRange(min=1)])
    faculty = SelectMultipleField('Faculty', validators=[DataRequired()])
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

    course = SelectField('Course', validators=[DataRequired()])
    year_level = SelectField('Year Level', validators=[DataRequired()])
    section = SelectField('Section', validators=[DataRequired()], coerce=int)
    semester = SelectField('Semester', validators=[DataRequired()])

    submit = SubmitField('Submit')


class EditSubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    code = StringField('Subject Code', validators=[DataRequired()])
    units = IntegerField('Subject Units', validators=[DataRequired(), NumberRange(min=1)])
    faculty = SelectField('Faculty', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')


class CourseYearLevelSemesterSubjectForm(FlaskForm):
    course = SelectField('Course', coerce=int, validators=[DataRequired()])
    year_level = SelectField('Year Level', coerce=int, validators=[DataRequired()])
    semester = SelectField('Semester', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Details')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course.choices = self.get_choices(Course, 'course_name')
        self.year_level.choices = self.get_choices(YearLevel, 'level_name')
        self.semester.choices = self.get_choices(Semester, 'semester_name')

    @staticmethod
    def get_choices(model, attribute):
        choices = []
        for item in model.query.all():
            if model.__name__ == 'YearLevel':
                choice = (item.id, item.level_name.name)  # Assuming `level_name` is an enum
            elif model.__name__ == 'Semester':
                choice = (item.id, item.semester_name.name)  # Assuming `semester_name` is an enum
            else:
                choice = (item.id, getattr(item, attribute))
            choices.append(choice)
        return choices
