from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Length, Optional
from app.models import User
from datetime import datetime, timedelta

class QRCodeForm(FlaskForm):
    description = StringField('Descrizione', validators=[
        DataRequired(), 
        Length(1, 200)
    ])
    user_id = SelectField('Assegna a Utente', coerce=int)
    expiry_date = DateTimeField('Data di Scadenza (opzionale)', 
                              format='%Y-%m-%dT%H:%M', 
                              validators=[Optional()],
                              default=(datetime.now() + timedelta(days=30)))
    submit = SubmitField('Genera QR Code')

    def __init__(self, *args, **kwargs):
        super(QRCodeForm, self).__init__(*args, **kwargs)
        self.user_id.choices = [(0, 'Nessun utente (QR generico)')] + [
            (user.id, f"{user.nome} {user.cognome} ({user.email})") 
            for user in User.query.filter_by(is_active=True).order_by(User.cognome).all()
        ]

class QRCodeSearchForm(FlaskForm):
    description = StringField('Descrizione', validators=[Optional()])
    user_id = SelectField('Utente', coerce=int, validators=[Optional()])
    is_active = SelectField('Stato', choices=[
        ('', 'Tutti'),
        ('1', 'Attivi'),
        ('0', 'Disattivati')
    ], validators=[Optional()])
    submit = SubmitField('Cerca')

    def __init__(self, *args, **kwargs):
        super(QRCodeSearchForm, self).__init__(*args, **kwargs)
        self.user_id.choices = [(0, 'Tutti')] + [
            (user.id, f"{user.nome} {user.cognome}") 
            for user in User.query.filter_by(is_active=True).order_by(User.cognome).all()
        ] 