from flask import Flask, render_template, abort
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, current_user
from flask_principal import Principal, Identity, AnonymousIdentity, RoleNeed, UserNeed, Permission
from flask_principal import identity_loaded, identity_changed
from flask_mail import Mail
from pymongo import MongoClient
from dotenv import load_dotenv
import gridfs
import os
from .main import bp as main_bp
from .ads import bp as ads_bp
from .auth import bp as auth_bp
from .admin import bp as admin_bp
from .ads.routes import get_image
from .utils import markdown_to_html
from .auth.models import User

def create_app(config_name='development'):
    """App Factory pattern za kreiranje Flask aplikacije"""
    # Učitaj varijable iz .env datoteke
    load_dotenv()
    
    app = Flask(__name__, template_folder='templates')
    
    # Konfiguracija iz .env datoteke (s fallback vrijednostima)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'jako-jak-random-key')
    
    # Inicijalizacija ekstenzija
    bootstrap = Bootstrap5(app)
    
    # Inicijalizacija Flask-Mail (učitaj iz .env)
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', None)
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', None)
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@unizd-oglasnik.hr')
    
    mail = Mail(app)
    
    # Inicijalizacija Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Molimo prijavite se za pristup ovoj stranici.'
    login_manager.login_message_category = 'info'
    
    # User loader callback za Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)
    
    # Inicijalizacija Flask-Principal
    principal = Principal(app)
    
    # Definiranje permission-a
    admin_permission = Permission(RoleNeed('admin'))
    
    # Postavljanje identity-ja kada korisnik ulazi
    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        """Postavlja identity kada korisnik ulazi u aplikaciju"""
        if current_user.is_authenticated:
            identity.user = current_user
            identity.provides.add(UserNeed(current_user.id))
            
            if current_user.role == 'admin':
                identity.provides.add(RoleNeed('admin'))
    
    # MongoDB konekcija
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    db = client[os.getenv('MONGODB_DB', 'pzw')]
    app.config['DB'] = db
    app.config['ADS_COLLECTION'] = db['ads']
    app.config['USERS_COLLECTION'] = db['users']
    app.config['GRIDFS'] = gridfs.GridFS(db)
    
    # Kreiranje admin korisnika ako ne postoji
    with app.app_context():
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password_hash = os.getenv('ADMIN_PASSWORD_HASH')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@unizd-oglasnik.hr')
        
        if admin_username and admin_password_hash:
            users_collection = app.config['USERS_COLLECTION']
            existing_admin = users_collection.find_one({'username': admin_username})
            
            if not existing_admin:
                user_data = {
                    'username': admin_username,
                    'email': admin_email,
                    'password_hash': admin_password_hash,  # Direktno upisujemo hash iz .env
                    'email_verified': True,  # Admin email je automatski verificiran
                    'role': 'admin',
                    'first_name': '',
                    'last_name': '',
                    'phone': '',
                    'profile_image_id': None
                }
                users_collection.insert_one(user_data)
                print(f'Admin korisnik "{admin_username}" kreiran.')
    
    # Registracija blueprint-a
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ads_bp, url_prefix='/ads')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Dodaj route za slike na root level (bez /ads/ prefiksa)
    app.add_url_rule('/image/<image_id>', 'get_image', get_image)
    
    # Registracija Jinja2 filtera
    app.jinja_env.filters['markdown'] = markdown_to_html
    
    # Test route za 500 grešku (samo u development modu)
    if config_name == 'development':
        @app.route('/test-500')
        def test_500():
            raise Exception("Test 500 greška")

     # Test route za 403 grešku (samo u development modu)
    if config_name == 'development':
        @app.route('/test-403')
        def test_403():
            abort(403)
    
    # Error handleri
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    return app

