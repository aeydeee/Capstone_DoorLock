from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField, SubmitField, HiddenField
from wtforms.validators import Length, DataRequired

from models import Subject


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[Length(min=3)])
    submit = SubmitField('Go')


class AssignStudentForm(FlaskForm):
    subject = SelectField('Subject', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Assign')

    def __init__(self, *args, **kwargs):
        super(AssignStudentForm, self).__init__(*args, **kwargs)
        self.subject.choices = [
            (subject.id, f"{subject.subject_name} - {', '.join(faculty.full_name for faculty in subject.faculties)}")
            for subject in Subject.query.all()
        ]
