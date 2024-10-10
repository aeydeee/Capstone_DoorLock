from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.simple import StringField, SubmitField, HiddenField
from wtforms.validators import Length, DataRequired
from wtforms.widgets.core import Select

from models import Subject, Faculty


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[Length(min=3)])
    submit = SubmitField('Go')


class CustomSelect(Select):
    def __call__(self, field, **kwargs):
        if 'name' in kwargs:
            kwargs['name'] = kwargs.pop('name')
        return super().__call__(field, **kwargs)


class AssignStudentForm(FlaskForm):
    subject = SelectMultipleField('Subjects', coerce=int)
    submit = SubmitField('Assign')

    def __init__(self, *args, **kwargs):
        super(AssignStudentForm, self).__init__(*args, **kwargs)
        self.subject.choices = [
            (subject.id, f"{subject.subject_name} - {', '.join(faculty.full_name for faculty in subject.faculties)}")
            # (subject.id, f"{subject.subject_name}")
            for subject in Subject.query.all()
        ]


class AssignFacultyForm(FlaskForm):
    faculty = SelectMultipleField('Faculties', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign')

    def __init__(self, *args, **kwargs):
        super(AssignFacultyForm, self).__init__(*args, **kwargs)
        self.faculty.choices = [
            (
                faculty.id,
                f"{faculty.faculty_number} - {faculty.full_name}"
            )
            for faculty in Faculty.query.all()
        ]
