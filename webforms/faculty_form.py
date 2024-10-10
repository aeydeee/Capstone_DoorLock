import json
import re
from datetime import datetime

from flask import current_app
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, SubmitField, PasswordField, EmailField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, EqualTo, Length, Email, Optional, ValidationError, NumberRange

from webforms.validators import contact_num_length, strong_password

current_year = datetime.now().year


class OptionalPasswordIfAbsent:
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if not current_user.faculty_details.password_hash and not field.data:
            raise ValidationError(self.message)


class FacultyForm(FlaskForm):
    rfid_uid = StringField(
        'RFID UID',
        validators=[Length(max=100)],
        filters=[lambda x: x or ''],
        render_kw={"placeholder": "Leave blank if no RFID scanner"}
    )
    f_name = StringField('First Name', validators=[DataRequired(), Length(max=100)], filters=[lambda x: x or ''])
    l_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)], filters=[lambda x: x or ''])
    m_name = StringField('Middle Name', validators=[Optional(), Length(max=100)],
                         filters=[lambda x: x or ''])  # Optional field
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)], filters=[lambda x: x or ''])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()],
                         filters=[lambda x: x or ''])

    # Faculty Information
    school_id = StringField('School ID', validators=[DataRequired(), Length(max=100)], filters=[lambda x: x or ''])
    department = StringField('Department', validators=[DataRequired(), Length(max=255)], filters=[lambda x: x or ''])
    designation = StringField('Designation', validators=[DataRequired(), Length(max=255)], filters=[lambda x: x or ''])

    submit = SubmitField('Submit')

    # Custom validator for email domain
    def validate_email(self, field):
        if not field.data.endswith('@cspc.edu.ph'):
            raise ValidationError('Email must be an @cspc.edu.ph address.')
