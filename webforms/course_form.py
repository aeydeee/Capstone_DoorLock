from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField

from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from models import Program, Semester, YearLevel


class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired()])
    code = StringField('Course Code', validators=[DataRequired()])
    units = IntegerField('Course Units', validators=[DataRequired(), NumberRange(min=1)])

    submit = SubmitField('Submit')


class EditCourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired()])
    code = StringField('Course Code', validators=[DataRequired()])
    units = IntegerField('Course Units', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Submit')


class ProgramYearLevelSemesterCourseForm(FlaskForm):
    program = SelectField('Program', coerce=int, validators=[DataRequired()])
    year_level = SelectField('Year Level', coerce=int, validators=[DataRequired()])
    semester = SelectField('Semester', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Details')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.program.choices = self.get_choices(Program, 'program_name')
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
            elif model.__name__ == 'Section':
                choice = (item.id, item.section_name.name)  # Assuming `section_name` is an enum
            else:
                choice = (item.id, getattr(item, attribute))
            choices.append(choice)
        return choices
