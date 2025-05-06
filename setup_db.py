"""
Script per inizializzare il database da zero.
Questo script elimina il database esistente se presente e crea tutte le tabelle
necessarie direttamente dai modelli.
"""
import os
import sys
import importlib.util

def setup_database():
    # Determina la directory dell'applicazione Flask
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Se lo script è eseguito dalla directory principale
    if os.path.basename(script_dir) == 'controllo-accessi-flask':
        app_dir = script_dir
    else:
        app_dir = os.path.join(script_dir, 'controllo-accessi-flask')
        if not os.path.exists(app_dir):
            print(f"ERRORE: Directory dell'applicazione Flask non trovata in {app_dir}")
            sys.exit(1)
    
    print(f"Cartella dell'applicazione identificata: {app_dir}")
    
    # Aggiungi la directory dell'app al percorso di ricerca dei moduli Python
    sys.path.insert(0, os.path.dirname(app_dir))
    
    # Importa i moduli necessari
    try:
        from app import create_app, db
        from app.models import User, QRCode, Access, Log
    except ImportError as e:
        print(f"ERRORE: Impossibile importare i moduli necessari: {e}")
        print("Assicurati di eseguire lo script dalla directory corretta")
        sys.exit(1)
    
    # Crea l'app
    app = create_app()
    with app.app_context():
        # Trova il percorso al file del database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Verifica se il database esiste e lo elimina
        if db_path.startswith('/'):  # Percorso assoluto
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    print(f"Database esistente eliminato: {db_path}")
                except Exception as e:
                    print(f"ERRORE: Impossibile eliminare il database: {e}")
                    sys.exit(1)
        else:  # Percorso relativo
            base_dir = os.path.abspath(os.path.dirname(app_dir))
            full_path = os.path.join(base_dir, db_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    print(f"Database esistente eliminato: {full_path}")
                except Exception as e:
                    print(f"ERRORE: Impossibile eliminare il database: {e}")
                    sys.exit(1)
        
        # Crea tutte le tabelle nel database
        try:
            db.create_all()
            print("Tabelle create con successo nel database.")
        except Exception as e:
            print(f"ERRORE: Impossibile creare le tabelle: {e}")
            sys.exit(1)
        
        # Crea l'utente admin se non esiste
        try:
            if User.query.filter_by(email='admin@example.com').first() is None:
                User.create_admin('admin@example.com', 'admin123')
                print("Utente admin creato con successo (email: admin@example.com, password: admin123)")
            else:
                print("Utente admin già presente nel database.")
            
            # Crea un utente super admin
            if User.query.filter_by(email='superadmin@example.com').first() is None:
                User.create_admin('superadmin@example.com', 'super123', super_admin=True)
                print("Utente super admin creato con successo (email: superadmin@example.com, password: super123)")
            else:
                print("Utente super admin già presente nel database.")
        except Exception as e:
            print(f"ERRORE: Impossibile creare gli utenti admin: {e}")
            sys.exit(1)
            
        print("\nIl database è stato inizializzato con successo!")
        print("È possibile accedere all'applicazione utilizzando:")
        print("Email admin: admin@example.com")
        print("Password admin: admin123")
        print("Email super admin: superadmin@example.com")
        print("Password super admin: super123")

if __name__ == '__main__':
    setup_database() 