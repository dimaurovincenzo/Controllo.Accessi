import os
from app import create_app, db
from app.models import User, QRCode, Access, Log

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db, 
        User=User, 
        QRCode=QRCode, 
        Access=Access,
        Log=Log
    )

@app.cli.command("init-db")
def init_db():
    """Inizializza il database con l'utente admin."""
    db.create_all()
    if User.query.filter_by(email='admin@example.com').first() is None:
        User.create_admin('admin@example.com', 'admin123')
        print('Utente admin creato con successo.')
    else:
        print('Utente admin già esistente.')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)