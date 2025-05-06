from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.accesses import bp
from app.accesses.forms import AccessSearchForm
from app.models import Access, QRCode, User, Log
from app import db
from datetime import datetime, time, date, timedelta
from sqlalchemy import or_, and_
import requests
from flask import current_app

@bp.route('/')
@login_required
def index():
    search_form = AccessSearchForm(request.args, meta={'csrf': False}) if request.args else AccessSearchForm()
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Access.query.join(QRCode)
    
    # Filtraggio per QR code
    if search_form.qr_id.data and search_form.qr_id.data != 0:
        query = query.filter(Access.qr_id == search_form.qr_id.data)
    
    # Filtraggio per utente (proprietario del QR code)
    if search_form.user_id.data and search_form.user_id.data != 0:
        query = query.filter(QRCode.user_id == search_form.user_id.data)
    
    # Filtraggio per operatore (chi ha scansionato)
    if search_form.operator_id.data and search_form.operator_id.data != 0:
        query = query.filter(Access.operator_id == search_form.operator_id.data)
    
    # Filtraggio per data
    if search_form.date_from.data:
        start_date = datetime.combine(search_form.date_from.data, time.min)
        query = query.filter(Access.timestamp >= start_date)
    
    if search_form.date_to.data:
        end_date = datetime.combine(search_form.date_to.data, time.max)
        query = query.filter(Access.timestamp <= end_date)
    
    accesses = query.order_by(Access.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # Ottieni gli indirizzi per gli accessi che hanno coordinate geografiche
    access_addresses = {}
    for access in accesses.items:
        if access.latitude and access.longitude:
            # Verifica se abbiamo già l'indirizzo per queste coordinate (approssimative)
            # Per evitare troppe chiamate API, approssimiamo le coordinate a 3 decimali
            lat_key = round(access.latitude, 3)
            lng_key = round(access.longitude, 3)
            coord_key = f"{lat_key},{lng_key}"
            
            if coord_key not in access_addresses:
                address = reverse_geocode(access.latitude, access.longitude)
                access_addresses[coord_key] = address if address else None
    
    return render_template(
        'accesses/index.html', 
        title='Storico Accessi', 
        accesses=accesses.items,
        pagination=accesses,
        search_form=search_form,
        access_addresses=access_addresses
    )

@bp.route('/statistics')
@login_required
def statistics():
    # Periodo predefinito: ultimo mese
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    # Parametri opzionali dalla query string
    period = request.args.get('period', 'month')
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'year':
        start_date = end_date - timedelta(days=365)
    
    # Statistiche per giorno
    daily_stats = db.session.query(
        db.func.date(Access.timestamp).label('day'),
        db.func.count(Access.id).label('count')
    ).filter(
        Access.timestamp >= datetime.combine(start_date, time.min),
        Access.timestamp <= datetime.combine(end_date, time.max)
    ).group_by(
        db.func.date(Access.timestamp)
    ).order_by(
        db.func.date(Access.timestamp)
    ).all()
    
    # Statistiche per QR code
    qr_stats = db.session.query(
        QRCode.description,
        db.func.count(Access.id).label('count')
    ).join(
        Access, Access.qr_id == QRCode.id
    ).filter(
        Access.timestamp >= datetime.combine(start_date, time.min),
        Access.timestamp <= datetime.combine(end_date, time.max)
    ).group_by(
        QRCode.id
    ).order_by(
        db.func.count(Access.id).desc()
    ).limit(10).all()
    
    # Statistiche per operatore
    operator_stats = db.session.query(
        User.nome,
        User.cognome,
        db.func.count(Access.id).label('count')
    ).join(
        Access, Access.operator_id == User.id
    ).filter(
        Access.timestamp >= datetime.combine(start_date, time.min),
        Access.timestamp <= datetime.combine(end_date, time.max)
    ).group_by(
        User.id
    ).order_by(
        db.func.count(Access.id).desc()
    ).all()
    
    # Totale accessi nel periodo
    total_accesses = db.session.query(db.func.count(Access.id)).filter(
        Access.timestamp >= datetime.combine(start_date, time.min),
        Access.timestamp <= datetime.combine(end_date, time.max)
    ).scalar()
    
    # Preparazione dati per il grafico
    dates = [stat.day.strftime('%d/%m') for stat in daily_stats]
    counts = [stat.count for stat in daily_stats]
    
    return render_template(
        'accesses/statistics.html', 
        title='Statistiche Accessi',
        period=period,
        dates=dates,
        counts=counts,
        qr_stats=qr_stats,
        operator_stats=operator_stats,
        total_accesses=total_accesses
    )

@bp.route('/accesses')
@login_required
def list_accesses():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    
    # Query base
    query = Access.query.join(User).join(QRCode)
    
    # Aggiungi filtri di ricerca se presenti
    if search_query:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                QRCode.code.ilike(f'%{search_query}%')
            )
        )
    
    # Ordina per data di accesso decrescente
    query = query.order_by(Access.access_time.desc())
    
    # Paginazione
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    accesses = pagination.items
    
    return render_template('accesses/list.html', 
                         accesses=accesses,
                         pagination=pagination,
                         search_query=search_query)

@bp.route('/accesses/<int:access_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_access(access_id):
    if not current_user.is_admin:
        flash('Accesso negato. Solo gli amministratori possono modificare gli accessi.', 'danger')
        return redirect(url_for('accesses.list_accesses'))
    
    access = Access.query.get_or_404(access_id)
    
    if request.method == 'POST':
        try:
            # Aggiorna i dati dell'accesso
            access.access_time = datetime.strptime(request.form['access_time'], '%Y-%m-%dT%H:%M')
            access.direction = request.form['direction']
            access.status = request.form['status']
            
            db.session.commit()
            flash('Accesso modificato con successo!', 'success')
            return redirect(url_for('accesses.list_accesses'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la modifica dell\'accesso: {str(e)}', 'danger')
    
    return render_template('accesses/edit.html', access=access)

@bp.route('/map')
@login_required
def map_view():
    """
    Visualizza una mappa con tutti gli accessi geolocalizzati
    """
    # Parametri opzionali dalla query string per il filtraggio
    qr_id = request.args.get('qr_id', type=int)
    user_id = request.args.get('user_id', type=int)
    operator_id = request.args.get('operator_id', type=int)
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    
    # Costruzione della query base
    query = Access.query.join(QRCode)
    
    # Applicazione dei filtri
    if qr_id:
        query = query.filter(Access.qr_id == qr_id)
    if user_id:
        query = query.filter(QRCode.user_id == user_id)
    if operator_id:
        query = query.filter(Access.operator_id == operator_id)
    
    # Filtraggio per data
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            query = query.filter(Access.timestamp >= datetime.combine(date_from, time.min))
        except ValueError:
            pass
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            query = query.filter(Access.timestamp <= datetime.combine(date_to, time.max))
        except ValueError:
            pass
    
    # Filtra solo gli accessi con coordinate geografiche valide
    query = query.filter(Access.latitude.isnot(None), Access.longitude.isnot(None))
    
    # Esegui la query
    accesses = query.order_by(Access.timestamp.desc()).all()
    
    # Prepara i dati per la visualizzazione sulla mappa
    markers = []
    for access in accesses:
        # Informazioni sul QR code
        qr_info = {
            'description': access.qr_code.description,
            'id': access.qr_code.id
        }
        
        # Informazioni sull'utente proprietario del QR code, se presente
        user_info = None
        if access.qr_code.owner:
            user_info = {
                'name': access.qr_code.owner.get_full_name(),
                'email': access.qr_code.owner.email
            }
        
        # Informazioni sull'operatore che ha effettuato la scansione
        operator_info = {
            'name': access.operator.get_full_name(),
            'email': access.operator.email
        }
        
        # Crea marker per la mappa
        markers.append({
            'id': access.id,
            'lat': access.latitude,
            'lng': access.longitude,
            'timestamp': access.timestamp.strftime('%d/%m/%Y %H:%M'),
            'qr': qr_info,
            'user': user_info,
            'operator': operator_info
        })
    
    # Ottieni l'elenco di QR code, utenti e operatori per i filtri
    qr_codes = QRCode.query.all()
    users = User.query.order_by(User.cognome, User.nome).all()
    operators = User.query.filter(User.role.in_(['admin', 'operator'])).order_by(User.cognome, User.nome).all()
    
    return render_template(
        'accesses/map.html', 
        title='Mappa Accessi',
        markers=markers,
        qr_codes=qr_codes,
        users=users,
        operators=operators,
        selected_qr_id=qr_id,
        selected_user_id=user_id,
        selected_operator_id=operator_id,
        date_from=date_from_str,
        date_to=date_to_str
    )

def reverse_geocode(lat, lng):
    """
    Converte coordinate geografiche in un indirizzo leggibile
    Utilizza OpenStreetMap/Nominatim come provider di default
    """
    provider = current_app.config['GEOCODING_PROVIDER']
    api_key = current_app.config['GEOCODING_API_KEY']
    
    if provider == 'nominatim':
        # OpenStreetMap Nominatim (non richiede API key)
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&addressdetails=1"
        headers = {
            'User-Agent': 'FlaskControlloAccessi/1.0'  # Nominatim richiede uno User-Agent personalizzato
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'display_name' in data:
                    return data['display_name']
        except Exception as e:
            current_app.logger.error(f"Errore nella geocodifica inversa: {e}")
    
    # In caso di errore o provider non supportato
    return None 

@bp.route('/api/geocode', methods=['GET'])
@login_required
def api_geocode():
    """
    API endpoint che converte coordinate in indirizzi
    """
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    
    if not lat or not lng:
        return jsonify({
            'success': False,
            'message': 'Parametri mancanti (lat, lng)'
        }), 400
    
    address = reverse_geocode(lat, lng)
    
    return jsonify({
        'success': True,
        'lat': lat,
        'lng': lng,
        'address': address or 'Indirizzo non trovato'
    }) 