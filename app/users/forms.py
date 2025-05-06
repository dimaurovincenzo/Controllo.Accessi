from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, Optional
from wtforms import ValidationError
from app.models import User

class UserForm(FlaskForm):
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
    role = SelectField('Ruolo', choices=[
        ('user', 'Utente'), 
        ('operator', 'Operatore'),
        ('admin', 'Amministratore'),
        ('super_admin', 'Super Amministratore')
    ])
    is_active = BooleanField('Attivo', default=True)
    password = PasswordField('Password', validators=[Optional()])
    password2 = PasswordField('Conferma password', validators=[
        EqualTo('password', message='Le password devono corrispondere.')
    ])
    submit = SubmitField('Salva')

    def validate_email(self, field):
        if self.email.data != getattr(self, 'user_email', None) and \
           User.query.filter_by(email=field.data).first():
            raise ValidationError('Email già registrata.')

class UserSearchForm(FlaskForm):
    search = StringField('Cerca', validators=[Optional()])
    role = SelectField('Ruolo', choices=[
        ('', 'Tutti'), 
        ('user', 'Utenti'), 
        ('operator', 'Operatori'),
        ('admin', 'Amministratori'),
        ('super_admin', 'Super Amministratori')
    ], validators=[Optional()])
    is_active = SelectField('Stato', choices=[
        ('', 'Tutti'),
        ('1', 'Attivi'),
        ('0', 'Disattivati')
    ], validators=[Optional()])
    submit = SubmitField('Cerca')