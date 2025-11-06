import os
from datetime import timedelta

class Config:
    """Bazna konfiguracija"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'jako-jak-random-key')
    
    # Session i Cookie sigurnost
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_HTTPONLY = True
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB = os.getenv('MONGODB_DB', 'pzw')
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', None)
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', None)
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@unizd-oglasnik.hr')
    
    # Admin korisnik
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', None)
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', None)
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@unizd-oglasnik.hr')

class DevelopmentConfig(Config):
    """Development konfiguracija"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False  # HTTP radi na localhost
    
class ProductionConfig(Config):
    """Production konfiguracija"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # HTTPS-only
    REMEMBER_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

