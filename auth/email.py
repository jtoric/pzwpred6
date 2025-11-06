from flask import render_template, url_for, current_app
from flask_mail import Message
from threading import Thread

def send_async_email(app, msg):
    """Šalje email asinkrono u novom threadu"""
    with app.app_context():
        mail = current_app.extensions.get('mail')
        if not mail:
            app.logger.warning("Mail extension not found, email not sent")
            return
        
        try:
            mail.send(msg)
            app.logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            app.logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            # Ne re-raise exception da ne blokira aplikaciju

def send_verification_email(user):
    """Šalje email za verifikaciju email adrese"""
    app = current_app._get_current_object()
    mail = current_app.extensions.get('mail')
    
    # Generiraj verifikacijski token (traje 1 sat)
    token = user.generate_verification_token()
    
    if not mail:
        # Ako mail nije konfiguriran, samo loguj (za development)
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        print(f"Email verifikacijski link (development): {verify_url}")
        return
    
    # Kreiraj verifikacijski link
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    # Kreiraj email
    # Template je u glavnom templates folderu
    msg = Message(
        subject='Potvrdite vašu email adresu - UNIZD Oglasnik',
        recipients=[user.email],
        html=render_template('email/verify_email.html', 
                           username=user.username, 
                           verify_url=verify_url)
    )
    
    # Pošalji email asinkrono
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    
    return thr

