from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_principal import Permission, RoleNeed
from . import bp
from .forms import UserForm
from ..auth.models import User
from werkzeug.security import generate_password_hash
from bson import ObjectId

# Admin permission za zaštitu ruta
admin_permission = Permission(RoleNeed('admin'))

@bp.route('/users')
@login_required
@admin_permission.require(http_exception=403)
def users():
    """Prikaz liste svih korisnika"""
    all_users = User.get_all()
    return render_template('users.html', users=all_users)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def new_user():
    """Kreiranje novog korisnika"""
    form = UserForm()
    
    if form.validate_on_submit():
        try:
            # Provjeri je li lozinka unesena (obavezna pri kreiranju)
            if not form.password.data:
                flash('Lozinka je obavezna pri kreiranju korisnika', 'danger')
                return render_template('user_form.html', form=form, title='Novi korisnik')
            
            # Kreiraj korisnika
            user = User.create(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            
            # Ažuriraj role i email_verified ako je potrebno
            if form.role.data != 'user':
                user.update_role(form.role.data)
            
            if form.email_verified.data:
                from flask import current_app
                users_collection = current_app.config['USERS_COLLECTION']
                users_collection.update_one(
                    {'_id': ObjectId(user.id)},
                    {'$set': {'email_verified': True}}
                )
            
            flash(f'Korisnik {user.username} je uspješno kreiran.', 'success')
            return redirect(url_for('admin.users'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('user_form.html', form=form, title='Novi korisnik')

@bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def edit_user(user_id):
    """Uređivanje korisnika"""
    user = User.get_by_id(user_id)
    if not user:
        flash('Korisnik nije pronađen', 'danger')
        return redirect(url_for('admin.users'))
    
    form = UserForm()
    
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.email_verified.data = user.email_verified
    
    if form.validate_on_submit():
        try:
            from flask import current_app
            users_collection = current_app.config['USERS_COLLECTION']
            
            # Provjeri jedinstvenost username-a i email-a
            existing_user = users_collection.find_one({
                '_id': {'$ne': ObjectId(user_id)},
                '$or': [
                    {'username': form.username.data},
                    {'email': form.email.data}
                ]
            })
            
            if existing_user:
                if existing_user['username'] == form.username.data:
                    flash('Korisničko ime već postoji', 'danger')
                    return render_template('user_form.html', form=form, title='Uredi korisnika', user=user)
                if existing_user['email'] == form.email.data:
                    flash('Email adresa već postoji', 'danger')
                    return render_template('user_form.html', form=form, title='Uredi korisnika', user=user)
            
            # Ažuriraj osnovne podatke
            update_data = {
                'username': form.username.data,
                'email': form.email.data,
                'role': form.role.data,
                'email_verified': form.email_verified.data
            }
            
            # Ažuriraj lozinku samo ako je unesena
            if form.password.data:
                update_data['password_hash'] = generate_password_hash(form.password.data)
            
            users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            
            flash(f'Korisnik {form.username.data} je uspješno ažuriran.', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            flash(f'Greška pri ažuriranju korisnika: {str(e)}', 'danger')
    
    return render_template('user_form.html', form=form, title='Uredi korisnika', user=user)

@bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_permission.require(http_exception=403)
def delete_user(user_id):
    """Brisanje korisnika"""
    user = User.get_by_id(user_id)
    if not user:
        flash('Korisnik nije pronađen', 'danger')
        return redirect(url_for('admin.users'))
    
    # Ne dozvoli brisanje samog sebe
    if user.id == current_user.id:
        flash('Ne možete obrisati vlastiti račun', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    user.delete()
    flash(f'Korisnik {username} je uspješno obrisan.', 'success')
    return redirect(url_for('admin.users'))

