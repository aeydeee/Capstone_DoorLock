from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length
from models import Program, YearLevel, Semester, Program, Section


class ProgramForm(FlaskForm):
    program_name = StringField('Program Name', validators=[DataRequired(), Length(max=255)])
    program_code = StringField('Program Code', validators=[Length(max=255)])
    submit = SubmitField('Submit')


class YearLevelForm(FlaskForm):
    level_name = StringField('Year Level', validators=[DataRequired(), Length(max=255)])
    level_code = IntegerField('Year Code', validators=[DataRequired()])
    submit = SubmitField('Add Year Level')


class SemesterForm(FlaskForm):
    semester_name = StringField('Semester Name', validators=[DataRequired(), Length(max=255)])
    semester_code = IntegerField('Semester Code', validators=[DataRequired()])
    submit = SubmitField('Add Semester')


class CourseForm(FlaskForm):
    course_code = StringField('Course Code', validators=[DataRequired(), Length(max=255)])
    course_name = StringField('Course Name', validators=[DataRequired(), Length(max=255)])
    course_units = StringField('Course Units', validators=[DataRequired(), Length(max=255)])
    course_description = StringField('Course Description', validators=[Length(max=255)])
    submit = SubmitField('Add Course')


class SectionForm(FlaskForm):
    section_range = StringField('Section Name or Range (e.g., A or A-F)', validators=[DataRequired()])
    submit = SubmitField('Add Section(s)')


class EditSectionForm(FlaskForm):
    section_name = StringField('Section Name', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Submit')
