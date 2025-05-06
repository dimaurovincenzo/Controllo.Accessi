from app import db, login_manager
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
import os
import qrcode
from PIL import Image

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(64), nullable=False)
    cognome = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # admin, operator, user, super_admin
    is_active = db.Column(db.Boolean, default=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    qr_codes = db.relationship('QRCode', backref='owner', lazy='dynamic')
    
    @property
    def password(self):
        raise AttributeError('La password non è un attributo leggibile')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.nome} {self.cognome}"
    
    def is_admin(self):
        return self.role == 'admin' or self.role == 'super_admin'
    
    def is_operator(self):
        return self.role == 'operator' or self.role == 'admin' or self.role == 'super_admin'
    
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    @staticmethod
    def create_admin(email, password, super_admin=False):
        admin = User(
            email=email, 
            nome='Admin', 
            cognome='Sistema', 
            password=password, 
            role='super_admin' if super_admin else 'admin'
        )
        db.session.add(admin)
        db.session.commit()
        return admin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class QRCode(db.Model):
    __tablename__ = 'qrcodes'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    description = db.Column(db.String(200))
    file_path = db.Column(db.String(255))
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    accesses = db.relationship('Access', backref='qr_code', lazy='dynamic')
    
    def generate_qr_image(self):
        """Genera l'immagine QR code e salva il percorso del file"""
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
            
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(self.uuid)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Assicurati che la directory esista
        if not os.path.exists(current_app.config['QR_CODE_DIR']):
            os.makedirs(current_app.config['QR_CODE_DIR'])
        
        filename = f"{self.uuid}.png"
        file_path = os.path.join(current_app.config['QR_CODE_DIR'], filename)
        img.save(file_path)
        
        self.file_path = f"qrcodes/{filename}"
        return self.file_path

class Access(db.Model):
    __tablename__ = 'accesses'
    id = db.Column(db.Integer, primary_key=True)
    qr_id = db.Column(db.Integer, db.ForeignKey('qrcodes.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    operator = db.relationship('User', foreign_keys=[operator_id])
    note = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 può essere lungo
    
    user = db.relationship('User', backref='logs')