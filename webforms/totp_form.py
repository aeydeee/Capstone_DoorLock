from flask_wtf import FlaskForm

from wtforms.fields.simple import SubmitField, StringField
from wtforms.validators import DataRequired

from webforms.validators import totp_length


class TOTPForm(FlaskForm):
    totp = StringField('Enter the TOTP code:', validators=[DataRequired(), totp_length])
    submit = SubmitField('Verify')


class RequestTOTPResetForm(FlaskForm):
    submit = SubmitField('Reset TOTP Secret Key')
