from flask_wtf import FlaskForm
from wtforms import SelectField, HiddenField, SubmitField
from wtforms.validators import DataRequired


class AttendanceStatusForm(FlaskForm):
    status = SelectField('Status', choices=[('', '--- Select Status ---'), ('present', 'Present'), ('late', 'Late'),
                                            ('absent', 'Absent')], validators=[DataRequired()])
