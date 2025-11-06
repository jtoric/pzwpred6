from flask import Flask, render_template, abort
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, current_user
from flask_principal import Principal, Identity, AnonymousIdentity, RoleNeed, UserNeed, Permission
from flask_principal import identity_loaded, identity_changed
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from dotenv import load_dotenv
import gridfs
import os
from .config import config
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
    
    # Učitaj konfiguraciju iz config.py
    app.config.from_object(config[config_name])
    
    # Inicijalizacija ekstenzija
    bootstrap = Bootstrap5(app)
    
    # Inicijalizacija Flask-Mail
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
    
    # MongoDB konekcija (koristi config postavke)
    # MongoDB Atlas zahtijeva SSL/TLS - mongodb+srv:// automatski koristi SSL
    mongodb_uri = app.config['MONGODB_URI']
    
    # Za mongodb+srv://, NE postavljamo tls=True eksplicitno jer to uzrokuje probleme
    # SRV format automatski koristi SSL/TLS
    # Dodajemo samo timeout opcije za bolju pouzdanost
    client = MongoClient(
        mongodb_uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        retryWrites=True
    )
    
    db = client[app.config['MONGODB_DB']]
    app.config['DB'] = db
    app.config['ADS_COLLECTION'] = db['ads']
    app.config['USERS_COLLECTION'] = db['users']
    app.config['GRIDFS'] = gridfs.GridFS(db)
    
    # Inicijalizacija Flask-Limiter s in-memory storage-om (deferred)
    # Memory storage je jednostavniji i dovoljan za većinu slučajeva
    # Koristimo deferred initialization da možemo primijeniti limite na blueprint rute
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["20000 per day", "5000 per hour"],
        strategy="fixed-window"
    )
    limiter.init_app(app)
    app.config['LIMITER'] = limiter
    app.limiter = limiter  # Također postavi kao atribut app objekta za lakši pristup
    
    # Kreiranje admin korisnika ako ne postoji
    with app.app_context():
        admin_username = app.config.get('ADMIN_USERNAME')
        admin_password_hash = app.config.get('ADMIN_PASSWORD_HASH')
        admin_email = app.config.get('ADMIN_EMAIL')
        
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
    
    # Primjeni rate limiting na auth rute nakon registracije blueprinta
    # Flask-Limiter automatski mapira limite na view funkcije preko endpoint imena
    if limiter:
        # Dohvati view funkcije iz app contexta i primjeni limite
        with app.app_context():
            # Primjeni limite direktno na view funkcije kroz app.view_functions
            if 'auth.login' in app.view_functions:
                app.view_functions['auth.login'] = limiter.limit("10 per minute")(app.view_functions['auth.login'])
            if 'auth.register' in app.view_functions:
                app.view_functions['auth.register'] = limiter.limit("10 per minute")(app.view_functions['auth.register'])
            if 'auth.resend_verification' in app.view_functions:
                app.view_functions['auth.resend_verification'] = limiter.limit("10 per minute")(app.view_functions['auth.resend_verification'])

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
    
    # Sigurnosni HTTP headeri
    @app.after_request
    def add_security_headers(response):
        """Dodaje sigurnosne HTTP headere na sve response-ove"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
    
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
    
    @app.errorhandler(429)
    def ratelimit_error(e):
        """Handler za rate limit greške (Too Many Requests)"""
        return render_template('errors/429.html'), 429
    
    return app

