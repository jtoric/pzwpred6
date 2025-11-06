from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional

class UserForm(FlaskForm):
    """Forma za kreiranje i uređivanje korisnika"""
    username = StringField(
        'Korisničko ime',
        validators=[
            DataRequired(message='Korisničko ime je obavezno'),
            Length(min=3, max=20, message='Korisničko ime mora imati između 3 i 20 znakova')
        ],
        render_kw={'placeholder': 'Unesite korisničko ime'}
    )
    
    email = StringField(
        'Email adresa',
        validators=[
            DataRequired(message='Email adresa je obavezna'),
            Email(message='Unesite ispravnu email adresu'),
            Length(max=120, message='Email adresa je predugačka')
        ],
        render_kw={'placeholder': 'Unesite email adresu'}
    )
    
    password = PasswordField(
        'Lozinka',
        validators=[
            Optional(),
            Length(min=6, message='Lozinka mora imati najmanje 6 znakova')
        ],
        render_kw={'placeholder': 'Ostavite prazno ako ne želite promijeniti lozinku'}
    )
    
    role = SelectField(
        'Uloga',
        choices=[('user', 'Korisnik'), ('admin', 'Administrator')],
        validators=[DataRequired()]
    )
    
    email_verified = BooleanField('Email verificiran', default=False)
    
    submit = SubmitField('Spremi')

