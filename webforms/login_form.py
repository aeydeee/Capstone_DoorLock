from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    # role = SelectField('Role', choices=[('student', 'Student'), ('faculty', 'Faculty'), ('admin', 'Admin')],
    #                    validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')
