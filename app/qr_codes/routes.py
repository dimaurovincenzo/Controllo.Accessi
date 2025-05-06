from flask import render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from app.qr_codes import bp
from app.qr_codes.forms import QRCodeForm, QRCodeSearchForm
from app.models import QRCode, User, Log
from app import db
from datetime import datetime
import uuid
import os

@bp.route('/')
@login_required
def index():
    search_form = QRCodeSearchForm(request.args, meta={'csrf': False}) if request.args else QRCodeSearchForm()
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = QRCode.query
    
    if search_form.description.data:
        query = query.filter(QRCode.description.contains(search_form.description.data))
    
    if search_form.user_id.data and search_form.user_id.data != 0:
        query = query.filter(QRCode.user_id == search_form.user_id.data)
    
    if search_form.is_active.data:
        is_active = search_form.is_active.data == '1'
        query = query.filter(QRCode.is_active == is_active)
    
    qr_codes = query.order_by(QRCode.creation_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'qr_codes/index.html', 
        title='QR Codes', 
        qr_codes=qr_codes.items,
        pagination=qr_codes,
        search_form=search_form
    )

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_operator():
        flash('Solo gli operatori possono generare QR code.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = QRCodeForm()
    if form.validate_on_submit():
        qr_code = QRCode(
            description=form.description.data,
            user_id=form.user_id.data if form.user_id.data != 0 else None,
            expiry_date=form.expiry_date.data
        )
        
        # Genera l'immagine QR code
        qr_code.generate_qr_image()
        
        db.session.add(qr_code)
        
        # Registra l'azione nel log
        log = Log(
            user_id=current_user.id,
            action='create_qr_code',
            details=f"Creato QR code: {form.description.data}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('QR code generato con successo!', 'success')
        return redirect(url_for('qr_codes.view', id=qr_code.id))
    
    return render_template('qr_codes/create.html', title='Genera QR Code', form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    qr_code = QRCode.query.get_or_404(id)
    return render_template('qr_codes/view.html', title='Dettagli QR Code', qr_code=qr_code)

@bp.route('/<int:id>/toggle_active')
@login_required
def toggle_active(id):
    if not current_user.is_operator():
        flash('Solo gli operatori possono modificare i QR code.', 'danger')
        return redirect(url_for('qr_codes.index'))
    
    qr_code = QRCode.query.get_or_404(id)
    qr_code.is_active = not qr_code.is_active
    
    # Registra l'azione nel log
    log = Log(
        user_id=current_user.id,
        action='toggle_qr_code',
        details=f"Modificato stato QR code: {qr_code.description} - {'Attivato' if qr_code.is_active else 'Disattivato'}",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f"QR code {'attivato' if qr_code.is_active else 'disattivato'} con successo.", 'success')
    return redirect(url_for('qr_codes.view', id=qr_code.id))

@bp.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    # Tutti gli utenti autenticati possono scansionare QR code
    
    if request.method == 'POST':
        qr_uuid = request.form.get('qr_uuid', '')
        if not qr_uuid:
            return jsonify({'success': False, 'message': 'Nessun QR code fornito'})
        
        qr_code = QRCode.query.filter_by(uuid=qr_uuid).first()
        if not qr_code:
            return jsonify({'success': False, 'message': 'QR code non trovato'})
        
        if not qr_code.is_active:
            return jsonify({'success': False, 'message': 'QR code disattivato'})
        
        if qr_code.expiry_date and qr_code.expiry_date < datetime.utcnow():
            return jsonify({'success': False, 'message': 'QR code scaduto'})
        
        # Ottieni le coordinate geografiche dalla richiesta
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Registra un nuovo accesso
        from app.models import Access
        access = Access(
            qr_id=qr_code.id,
            operator_id=current_user.id,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None
        )
        db.session.add(access)
        
        # Prova a ottenere l'indirizzo dalle coordinate
        address = None
        if latitude and longitude:
            from app.accesses.routes import reverse_geocode
            try:
                address = reverse_geocode(float(latitude), float(longitude))
            except Exception as e:
                current_app.logger.error(f"Errore nella geocodifica durante la scansione: {str(e)}")
        
        location_info = ""
        if latitude and longitude:
            location_info = f" (Posizione: {latitude}, {longitude}"
            if address:
                location_info += f", {address}"
            location_info += ")"
        
        # Registra l'azione nel log
        log = Log(
            user_id=current_user.id,
            action='qr_scan',
            details=f"Scansione QR code: {qr_code.description}{location_info}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        # Costruisci informazioni utente se il QR è associato a un utente
        user_info = {}
        if qr_code.user_id:
            user = qr_code.owner
            user_info = {
                'nome': user.nome,
                'cognome': user.cognome,
                'email': user.email
            }
        
        response_data = {
            'success': True, 
            'message': 'Accesso registrato con successo',
            'qr_info': {
                'id': qr_code.id,
                'description': qr_code.description,
                'creation_date': qr_code.creation_date.strftime('%d/%m/%Y %H:%M'),
                'user': user_info
            }
        }
        
        # Aggiungi informazioni sulla posizione alla risposta
        if latitude and longitude:
            response_data['location'] = {
                'latitude': float(latitude),
                'longitude': float(longitude),
                'address': address
            }
        
        return jsonify(response_data)
    
    return render_template('qr_codes/scan.html', title='Scansiona QR Code')