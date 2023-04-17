from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Regexp
import re

class SignUpForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    email = StringField('Email',validators=[DataRequired()])
    first_name = StringField('First Name',validators=[DataRequired()])
    last_name = StringField('Last Name',validators=[DataRequired()])
    password = PasswordField('Password',validators=[DataRequired()])
    confirm_password = PasswordField('Email',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField()

class LogInForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    password = PasswordField('Password',validators=[DataRequired()])
    submit = SubmitField()

class UpdateProfileForm(FlaskForm):
    username = StringField('Username')
    email = StringField('Email')
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    password = PasswordField('Password')
    confirm_password = PasswordField('Email',validators=[EqualTo('password')])
    submit = SubmitField()
