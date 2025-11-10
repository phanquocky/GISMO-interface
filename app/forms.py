from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed

class InputForm(FlaskForm):
    file = FileField('Upload File')
    content = TextAreaField('Or paste content')
    submit = SubmitField('Run Gismo')
