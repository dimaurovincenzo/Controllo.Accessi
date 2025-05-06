from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricordami')
    submit = SubmitField('Accedi')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), 
        Length(1, 64), 
        Email()
    ])
    nome = StringField('Nome', validators=[
        DataRequired(), 
        Length(1, 64)
    ])
    cognome = StringField('Cognome', validators=[
        DataRequired(), 
        Length(1, 64)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        EqualTo('password2', message='Le password devono corrispondere.')
    ])
    password2 = PasswordField('Conferma password', validators=[DataRequired()])
    submit = SubmitField('Registra')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email già registrata.')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Vecchia password', validators=[DataRequired()])
    password = PasswordField('Nuova password', validators=[
        DataRequired(), 
        EqualTo('password2', message='Le password devono corrispondere.')
    ])
    password2 = PasswordField('Conferma nuova password', validators=[DataRequired()])
    submit = SubmitField('Aggiorna Password')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField('Reimposta Password')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nuova password', validators=[
        DataRequired(), 
        EqualTo('password2', message='Le password devono corrispondere.')
    ])
    password2 = PasswordField('Conferma password', validators=[DataRequired()])
    submit = SubmitField('Reimposta Password') 