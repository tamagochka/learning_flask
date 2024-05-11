from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
from app import db
from app.models import User
from sqlalchemy import select


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    # WTForms методы составленные по шаблону validate_<field_name> считает пользовательскими валидаторами
    # и вызывает их в дополнение к стандартным
    def validate_username(self, username):  # проверка существует ли уже такой пользователь
        user = db.session.scalar(select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):  # проверка зарегистрирован ли уже такой email
        user = db.session.scalar(select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')
