from flask import Blueprint

bp = Blueprint('accesses', __name__)

from app.accesses import routes 