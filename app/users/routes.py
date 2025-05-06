from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.users import bp
from app.users.forms import UserForm, UserSearchForm
from app.models import User, Log
from app import db
from sqlalchemy import or_

@bp.route('/')
@login_required
def index():
    if not current_user.is_admin():
        flash('Accesso negato. Solo gli amministratori possono gestire gli utenti.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    search_form = UserSearchForm(request.args, meta={'csrf': False}) if request.args else UserSearchForm()
    
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    query = User.query
    
    # Ricerca per nome/cognome/email
    if search_form.search.data:
        search_term = f"%{search_form.search.data}%"
        query = query.filter(
            or_(
                User.nome.ilike(search_term),
                User.cognome.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    # Filtraggio per ruolo
    if search_form.role.data:
        query = query.filter(User.role == search_form.role.data)
    
    # Filtraggio per stato attivo/inattivo
    if search_form.is_active.data:
        is_active = search_form.is_active.data == '1'
        query = query.filter(User.is_active == is_active)
    
    users = query.order_by(User.cognome, User.nome).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'users/index.html', 
        title='Gestione Utenti', 
        users=users.items,
        pagination=users,
        search_form=search_form
    )

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_admin():
        flash('Accesso negato. Solo gli amministratori possono creare utenti.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            nome=form.nome.data,
            cognome=form.cognome.data,
            role=form.role.data,
            is_active=form.is_active.data
        )
        
        if form.password.data:
            user.password = form.password.data
        
        db.session.add(user)
        
        # Registra l'azione nel log
        log = Log(
            user_id=current_user.id,
            action='create_user',
            details=f"Creato utente: {form.email.data}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Utente creato con successo!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/edit.html', title='Crea Utente', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.is_admin():
        flash('Accesso negato. Solo gli amministratori possono modificare utenti.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(id)
    
    # Per evitare che venga segnalato errore di email duplicata quando si modifica l'utente
    form = UserForm()
    form.user_email = user.email
    
    if form.validate_on_submit():
        user.email = form.email.data
        user.nome = form.nome.data
        user.cognome = form.cognome.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.password = form.password.data
        
        # Registra l'azione nel log
        log = Log(
            user_id=current_user.id,
            action='edit_user',
            details=f"Modificato utente: {user.email}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Utente aggiornato con successo!', 'success')
        return redirect(url_for('users.index'))
    
    # Pre-popolamento del form
    form.email.data = user.email
    form.nome.data = user.nome
    form.cognome.data = user.cognome
    form.role.data = user.role
    form.is_active.data = user.is_active
    
    return render_template('users/edit.html', title='Modifica Utente', form=form, user=user)

@bp.route('/<int:id>/toggle_active')
@login_required
def toggle_active(id):
    if not current_user.is_admin():
        flash('Accesso negato. Solo gli amministratori possono modificare lo stato degli utenti.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(id)
    
    # Non permettere la disattivazione dell'account corrente
    if user.id == current_user.id:
        flash('Non puoi disattivare il tuo account.', 'danger')
        return redirect(url_for('users.index'))
    
    user.is_active = not user.is_active
    
    # Registra l'azione nel log
    log = Log(
        user_id=current_user.id,
        action='toggle_user_active',
        details=f"Modificato stato utente: {user.email} - {'Attivato' if user.is_active else 'Disattivato'}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f"Utente {'attivato' if user.is_active else 'disattivato'} con successo.", 'success')
    return redirect(url_for('users.index')) 