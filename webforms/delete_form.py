from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField


class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')
