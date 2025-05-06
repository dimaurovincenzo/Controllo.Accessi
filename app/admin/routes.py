from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Access, QRCode, Log, User
from app.admin import bp
from datetime import datetime
import os

# PIN di accesso (da configurare in modo sicuro in produzione)
SUPER_ADMIN_PIN = os.environ.get('SUPER_ADMIN_PIN', '1234')

@bp.route('/super', methods=['GET', 'POST'])
@login_required
def super_admin():
    # Verifica se l'utente è un super admin
    if not current_user.is_super_admin() and not request.form.get('pin') == SUPER_ADMIN_PIN:
        authenticated = False
        pin = None
        
        if request.method == 'POST':
            pin = request.form.get('pin')
            if pin == SUPER_ADMIN_PIN:
                authenticated = True
            else:
                flash('PIN non valido o accesso non autorizzato', 'danger')
    else:
        # L'utente è un super admin o ha fornito il PIN corretto
        authenticated = True
        pin = SUPER_ADMIN_PIN
    
    return render_template('admin/super.html', 
                         authenticated=authenticated,
                         pin=pin)

@bp.route('/super/clear-database', methods=['POST'])
@login_required
def clear_database():
    # Verifica se l'utente è un super admin o ha il PIN
    pin = request.form.get('pin')
    if not current_user.is_super_admin() and pin != SUPER_ADMIN_PIN:
        flash('Accesso negato', 'danger')
        return redirect(url_for('admin.super_admin'))
    
    try:
        # Azzera i log
        Log.query.delete()
        
        # Azzera gli accessi
        Access.query.delete()
        
        # Azzera i QR code
        QRCode.query.delete()
        
        # Commit delle modifiche
        db.session.commit()
        
        # Registra l'azione nel log
        log = Log(
            user_id=current_user.id,
            action='clear_database',
            details="Database azzerato dal super admin",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Database azzerato con successo!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'azzeramento del database: {str(e)}', 'danger')
    
    return redirect(url_for('admin.super_admin'))

@bp.route('/super/search', methods=['GET'])
@login_required
def search_access():
    # Verifica se l'utente è un super admin o ha il PIN
    pin = request.args.get('pin')
    if not current_user.is_super_admin() and pin != SUPER_ADMIN_PIN:
        flash('Accesso negato', 'danger')
        return redirect(url_for('admin.super_admin'))
    
    search_query = request.args.get('search', '')
    search_results = []
    
    if search_query:
        try:
            # Cerca per ID accesso
            if search_query.isdigit():
                access = Access.query.get(int(search_query))
                if access:
                    search_results = [access]
            else:
                # Cerca per nome o email utente
                users = User.query.filter(
                    (User.nome.ilike(f'%{search_query}%')) | 
                    (User.cognome.ilike(f'%{search_query}%')) |
                    (User.email.ilike(f'%{search_query}%'))
                ).all()
                
                if users:
                    user_ids = [user.id for user in users]
                    # Cerca accessi degli utenti proprietari di QR code
                    qr_accesses = Access.query.join(QRCode).filter(QRCode.user_id.in_(user_ids)).all()
                    # Cerca accessi effettuati dagli utenti come operatori
                    op_accesses = Access.query.filter(Access.operator_id.in_(user_ids)).all()
                    
                    # Unisci i risultati senza duplicati
                    search_results = list(set(qr_accesses + op_accesses))
        except Exception as e:
            flash(f'Errore durante la ricerca: {str(e)}', 'danger')
    
    return render_template('admin/super.html',
                         authenticated=True,
                         pin=pin,
                         search_results=search_results)

@bp.route('/super/access/<int:access_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_access(access_id):
    # Verifica se l'utente è un super admin o ha il PIN
    pin = request.args.get('pin')
    if not current_user.is_super_admin() and pin != SUPER_ADMIN_PIN:
        flash('Accesso negato', 'danger')
        return redirect(url_for('admin.super_admin'))
    
    access = Access.query.get_or_404(access_id)
    
    if request.method == 'POST':
        try:
            # Aggiorna i dati dell'accesso
            if 'timestamp' in request.form:
                try:
                    access.timestamp = datetime.strptime(request.form['timestamp'], '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash('Formato data/ora non valido', 'danger')
                    return render_template('admin/edit_access.html', access=access, pin=pin)
            
            if 'latitude' in request.form and request.form['latitude']:
                try:
                    access.latitude = float(request.form['latitude'])
                except ValueError:
                    flash('Valore latitudine non valido', 'danger')
                    return render_template('admin/edit_access.html', access=access, pin=pin)
            
            if 'longitude' in request.form and request.form['longitude']:
                try:
                    access.longitude = float(request.form['longitude'])
                except ValueError:
                    flash('Valore longitudine non valido', 'danger')
                    return render_template('admin/edit_access.html', access=access, pin=pin)
            
            if 'note' in request.form:
                access.note = request.form['note']
            
            # Registra l'azione nel log
            log = Log(
                user_id=current_user.id,
                action='edit_access_super',
                details=f"Modificato accesso #{access.id} tramite pannello super admin",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Accesso modificato con successo!', 'success')
            return redirect(url_for('admin.super_admin', pin=pin))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la modifica dell\'accesso: {str(e)}', 'danger')
    
    return render_template('admin/edit_access.html',
                         access=access,
                         pin=pin) 