import os
import sys

# Pokušaj relativni import (radi kao paket)
try:
    from . import create_app
except ImportError:
    # Ako relativni import ne radi, koristi dinamički import
    # Postavi PYTHONPATH da uključuje trenutni direktorij
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dodaj trenutni direktorij u sys.path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Dinamički učitaj __init__.py
    import importlib.util
    
    init_path = os.path.join(current_dir, "__init__.py")
    
    # Odredi ime paketa (koristi ime direktorija)
    # Na Renderu će biti 'src', ali pokušajmo dinamički
    package_name = os.path.basename(current_dir) or 'pred2start'
    
    # Kreiraj spec s submodule_search_locations
    spec = importlib.util.spec_from_file_location(
        f"{package_name}", 
        init_path,
        submodule_search_locations=[current_dir]
    )
    
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {init_path}")
    
    # Kreiraj modul
    app_init = importlib.util.module_from_spec(spec)
    
    # Postavi __package__ i __name__ PRIJE exec_module
    # Ovo je ključno da relativni importi u __init__.py rade
    app_init.__package__ = package_name
    app_init.__name__ = package_name
    app_init.__file__ = init_path
    
    # Postavi sys.modules da modul bude dostupan
    sys.modules[package_name] = app_init
    sys.modules[f"{package_name}.__init__"] = app_init
    
    # Učitaj modul
    spec.loader.exec_module(app_init)
    
    create_app = app_init.create_app

# Koristi 'production' ako je RENDER environment postavljen, inače 'development'
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name=config_name)

if __name__ == '__main__':
    app.run(debug=True)