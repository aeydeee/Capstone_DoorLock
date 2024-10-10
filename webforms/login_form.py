from flask_wtf import FlaskForm

from wtforms.fields.simple import PasswordField, SubmitField, StringField, EmailField
from wtforms.validators import DataRequired, Length

from webforms.validators import strong_password, totp_length


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Length(1, 64)])
    # password = PasswordField('Password', validators=[DataRequired(), strong_password])
    totp_code = StringField('TOTP Code ', validators=[DataRequired(), totp_length])
    submit = SubmitField('Login')
