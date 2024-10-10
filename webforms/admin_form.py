from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, EmailField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email, ValidationError

from webforms.faculty_form import current_year
from webforms.validators import contact_num_length


class AdminForm(FlaskForm):
    rfid_uid = StringField(
        'RFID UID',
        validators=[Length(max=100)],
        filters=[lambda x: x or ''],
        render_kw={"placeholder": "Leave blank if no RFID scanner"}
    )
    f_name = StringField('First Name', validators=[DataRequired(), Length(max=100)], filters=[lambda x: x or ''])
    l_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)], filters=[lambda x: x or ''])
    m_name = StringField('Middle Name', validators=[Optional(), Length(max=100)],
                         filters=[lambda x: x or ''])  # Made optional
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)], filters=[lambda x: x or ''])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])

    # Admin
    school_id = StringField('School ID', validators=[DataRequired(), Length(max=100)], filters=[lambda x: x or ''])

    submit = SubmitField('Register')

    # Custom validator for email domain

    def validate_email(self, field):
        if not field.data.endswith('@cspc.edu.ph'):
            raise ValidationError('Email must be an @cspc.edu.ph address.')
