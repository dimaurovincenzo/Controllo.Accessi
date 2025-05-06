from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField
from wtforms.validators import Optional
from app.models import User, QRCode
from datetime import date, timedelta

class AccessSearchForm(FlaskForm):
    qr_id = SelectField('QR Code', coerce=int, validators=[Optional()])
    user_id = SelectField('Utente', coerce=int, validators=[Optional()])
    operator_id = SelectField('Operatore', coerce=int, validators=[Optional()])
    date_from = DateField('Data da', validators=[Optional()], default=date.today() - timedelta(days=30))
    date_to = DateField('Data a', validators=[Optional()], default=date.today())
    submit = SubmitField('Cerca')

    def __init__(self, *args, **kwargs):
        super(AccessSearchForm, self).__init__(*args, **kwargs)
        self.qr_id.choices = [(0, 'Tutti')] + [
            (qr.id, f"{qr.description} ({qr.uuid[:8]}...)") 
            for qr in QRCode.query.order_by(QRCode.description).all()
        ]
        self.user_id.choices = [(0, 'Tutti')] + [
            (user.id, f"{user.nome} {user.cognome}") 
            for user in User.query.filter_by(is_active=True).order_by(User.cognome).all()
        ]
        self.operator_id.choices = [(0, 'Tutti')] + [
            (user.id, f"{user.nome} {user.cognome}") 
            for user in User.query.filter(User.role.in_(['admin', 'operator'])).order_by(User.cognome).all()
        ] 