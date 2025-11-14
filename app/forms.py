from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, IntegerField
from wtforms import validators
from flask_wtf.file import FileField, FileAllowed

class InputForm(FlaskForm):
    file = FileField('Upload File')
    content = TextAreaField('Or paste content')
    k = IntegerField('k (maximum identifiable set size)', default=1, validators=[validators.NumberRange(min=1)])
    submit = SubmitField('Run Gismo')
