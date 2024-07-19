from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField, SubmitField, HiddenField
from wtforms.validators import Length, DataRequired


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[Length(min=3)])
    submit = SubmitField('Go')


class AssignStudentsForm(FlaskForm):
    instructor = SelectField('Instructor', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Assign Students')
