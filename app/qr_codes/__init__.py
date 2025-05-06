from flask import Blueprint

bp = Blueprint('qr_codes', __name__)

from app.qr_codes import routes 