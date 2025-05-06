from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.main import bp
from app import db
from datetime import datetime

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('main/dashboard.html', title='Dashboard')
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('main/dashboard.html', title='Dashboard') 