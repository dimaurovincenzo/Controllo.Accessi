from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os
import logging
from logging.handlers import RotatingFileHandler
import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # Assicurarsi che la directory per QR code esista
    if not os.path.exists(app.config['QR_CODE_DIR']):
        os.makedirs(app.config['QR_CODE_DIR'])
    
    # Configurazione del logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Avvio applicazione QR Code')
    
    # Aggiungi context processor per la variabile 'now'
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}
    
    # Registrazione dei blueprint
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.qr_codes import bp as qr_bp
    app.register_blueprint(qr_bp, url_prefix='/qr')
    
    from app.accesses import bp as access_bp
    app.register_blueprint(access_bp, url_prefix='/accesses')
    
    from app.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/users')
    
    # Blueprint principale
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app

from app import models 