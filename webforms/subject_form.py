from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import TimeField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    code = StringField('Subject Code', validators=[DataRequired()])
    units = IntegerField('Subject Units', validators=[DataRequired(), NumberRange(min=1)])
    faculty = SelectField('Faculty', validators=[DataRequired()])
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


class EditSubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    code = StringField('Subject Code', validators=[DataRequired()])
    units = IntegerField('Subject Units', validators=[DataRequired(), NumberRange(min=1)])
    faculty = SelectField('Faculty', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')
