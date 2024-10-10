from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired


class UploadForm(FlaskForm):
    file = FileField('Upload Files here (Drag & Drop or Choose File)', validators=[
        DataRequired(),
        FileAllowed(['csv', 'xlsx'], 'CSV and Excel files only!')
    ])
    submit = SubmitField('Upload')
