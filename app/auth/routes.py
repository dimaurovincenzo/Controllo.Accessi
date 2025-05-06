from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm
from app.models import User, Log
from app import db
from datetime import datetime

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Email o password non valida.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Account disattivato. Contatta l\'amministratore.', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Registra il login nel log
        log = Log(
            user_id=user.id,
            action='login',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Accedi', form=form)

@bp.route('/logout')
@login_required
def logout():
    # Registra il logout nel log
    log = Log(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('Logout effettuato con successo.', 'success')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Solo gli amministratori possono registrare nuovi utenti
    if not current_user.is_admin():
        flash('Accesso negato.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            nome=form.nome.data,
            cognome=form.cognome.data,
            password=form.password.data,
            role='user'  # Default role
        )
        db.session.add(user)
        
        # Registra la creazione dell'utente nel log
        log = Log(
            user_id=current_user.id,
            action='create_user',
            details=f"Creato nuovo utente: {form.email.data}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Utente registrato con successo!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('auth/register.html', title='Registra Utente', form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.old_password.data):
            flash('Password attuale non corretta.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.password = form.password.data
        
        # Registra il cambio password nel log
        log = Log(
            user_id=current_user.id,
            action='change_password',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('La tua password è stata aggiornata.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html', title='Cambia Password', form=form) 