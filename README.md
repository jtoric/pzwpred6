# 🏫 UNIZD Oglasnik

Jednostavna web aplikacija za objavu i pregled oglasa napravljena u **Flasku**.  
Projekt je razvijen kao dio kolegija **Programiranje za Web (SIT UNIZD)**.

---

## ✨ Funkcionalnosti

### Autentikacija i autorizacija
- Autentikacija korisnika (registracija, prijava, odjava) preko **Flask-Login**
- Verifikacija email adrese (link s rokom od 1h, `itsdangerous.URLSafeTimedSerializer`)
- **Role-based access control** preko **Flask-Principal**
  - Korisničke uloge: `user` (default) i `admin`
  - Admin korisnici imaju pristup admin panelu
- **Rate limiting** preko **Flask-Limiter** (brute-force zaštita)
  - Login: 5 zahtjeva/minutu
  - Registracija: 3 zahtjeva/minutu
  - Resend verification: 2 zahtjeva/minutu

### Korisnički profil
- Korisnički profil: ime, prezime, broj mobitela, profilna slika (GridFS)
- Pregled i uređivanje profila
- Automatsko kreiranje admin korisnika pri pokretanju aplikacije

### Admin funkcionalnosti
- **Admin panel** (`/admin/users`) za upravljanje korisnicima
- **CRUD operacije** na korisnicima (Create, Read, Update, Delete)
  - Kreiranje novih korisnika
  - Pregled svih korisnika
  - Uređivanje korisnika (username, email, role, lozinka, email verificiran)
  - Brisanje korisnika (admin ne može obrisati samog sebe)
- Zaštita admin ruta s Flask-Principal permisijama

### Oglasi
- "Moji oglasi" (`/ads/my`) s pretragom, filtriranjem i paginacijom
- Dodavanje novog oglasa putem forme
- **Uređivanje postojećih oglasa** i **Brisanje oglasa**
  - Samo vlasnik oglasa ili admin mogu uređivati/brisati
  - Zaštita preko Flask-Principal permisija
- **Markdown editor (EasyMDE)** za opis oglasa
  - Live preview, toolbar, naslovi/liste/linkovi/citati
- Polja oglasa: naslov, opis, cijena, kategorija, lokacija, slika
  - Ime prodavača i broj mobitela automatski se preuzimaju iz profila korisnika
- Filtriranje po kategorijama (radi i u "Moji oglasi")

### Sigurnost
- **Session i Cookie sigurnost** (configurirano preko `config.py`)
  - `SESSION_COOKIE_HTTPONLY = True` (nema JS pristupa)
  - `SESSION_COOKIE_SAMESITE = 'Lax'` (CSRF zaštita)
  - `SESSION_COOKIE_SECURE` (True u production, False u development)
  - `REMEMBER_COOKIE_DURATION = 7 dana`
- **Sigurnosni HTTP headeri** (`@app.after_request`)
  - `X-Content-Type-Options: nosniff` (sprječava MIME sniffing)
  - `X-Frame-Options: DENY` (sprječava clickjacking)
  - `Referrer-Policy: strict-origin-when-cross-origin`
- **Sanitizacija HTML-a** (XSS zaštita) i CSRF zaštita (Flask-WTF)
- **Rate limiting** za zaštitu od brute-force napada

### Tehnički detalji
- Validacija unosa (obavezna polja, duljina…)
- Flash poruke, PRG (Post → Redirect → Get)
- Bootstrap 5 za izgled i layout
- Spremanje oglasa u **MongoDB**, slike u **GridFS**
- Konfiguracija preko `config.py` (Development/Production klase)

---

## ⚙️ Instalacija i pokretanje

### Preduslovi
- Python 3.8+
- MongoDB (instaliraj lokalno ili koristi Docker)

### MongoDB instalacija
- **Windows/macOS/Linux**: [MongoDB Community Server](https://www.mongodb.com/try/download/community)

### Koraci instalacije

1. Kloniraj repozitorij:
   ```bash
   git clone https://github.com/jtoric/pzwpred2.git
   cd pzwpred2
   ```

2. Kreiraj virtualno okruženje i instaliraj pakete:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\Activate.ps1      # Windows PowerShell

   pip install -r requirements.txt
   ```

3. Kopiraj .env primjer i postavi varijable okruženja:
   ```bash
   cp .env.example .env   # Linux / macOS
   # Windows PowerShell
   Copy-Item .env.example .env
   ```

   Uredi `.env` i postavi vrijednosti (primjer):
   ```env
   # Flask
   SECRET_KEY=promijeni-ovo-u-sigurni-key

   # MongoDB
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DB=pzw

   # Email (Flask-Mail)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=tvoj-email@gmail.com
   MAIL_PASSWORD=tvoja-app-lozinka
   MAIL_DEFAULT_SENDER=noreply@unizd-oglasnik.hr

   # Admin korisnik (automatski se kreira pri pokretanju aplikacije)
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD_HASH=pbkdf2:sha256:600000$...  # Generiraj pomoću naredbe u nastavku
   ADMIN_EMAIL=admin@unizd-oglasnik.hr
   ```

4. Generiraj password hash za admin korisnika:
   ```bash
   # Generiraj password hash za admin lozinku
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('tvoja-admin-lozinka'))"
   ```
   
   Kopiraj generirani hash i zalijepi u `.env` datoteku kao vrijednost za `ADMIN_PASSWORD_HASH`.
   
   **Primjer:**
   ```bash
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('tvoja-admin-lozinka'))"
   ```
   Output će biti nešto poput:
   ```
   pbkdf2:sha256:600000$XxXxXxXx$...
   ```
   
   Zalijepi taj hash u `.env`:
   ```env
   ADMIN_PASSWORD_HASH=pbkdf2:sha256:600000$XxXxXxXx$...
   ```

5. Osiguraj da MongoDB radi:
   ```bash
   # Provjeri da li MongoDB radi na localhost:27017
   # Ako ne radi, pokreni MongoDB server
   ```

6. Pokreni aplikaciju:
   ```bash
   python app.py
   ```

7. Otvori u browseru:
   ```
   http://127.0.0.1:5000/
   ```

**Napomena:** Admin korisnik se automatski kreira pri prvom pokretanju aplikacije ako ne postoji. Možeš se prijaviti s `ADMIN_USERNAME` i lozinkom koju si koristio za generiranje hash-a.

### Sigurnosne postavke

Aplikacija koristi konfiguracijske klase (`config.py`) za različita okruženja:

- **Development**: `SESSION_COOKIE_SECURE = False` (radi na HTTP)
- **Production**: `SESSION_COOKIE_SECURE = True` (zahtijeva HTTPS)

Za pokretanje u production modu:
```bash
# U app.py ili kroz environment varijablu
app = create_app('production')
```

### Rate Limiting

Aplikacija koristi **Flask-Limiter** za zaštitu od brute-force napada:
- **Login**: 5 zahtjeva po minuti
- **Registracija**: 3 zahtjeva po minuti  
- **Resend verification**: 2 zahtjeva po minuti

Prekoračenje limita vraća 429 (Too Many Requests) error sa custom error stranicom.

### Admin Panel

Admin korisnici mogu pristupiti admin panelu kroz navigaciju:
- **Lista korisnika**: `/admin/users`
- **Kreiranje korisnika**: `/admin/users/new`
- **Uređivanje korisnika**: `/admin/users/<user_id>/edit`
- **Brisanje korisnika**: `/admin/users/<user_id>/delete` (POST)

Sve admin rute su zaštićene s Flask-Principal permisijama.

---

## ✍️ Markdown podrška

Aplikacija podržava **Markdown formatiranje** u opisu oglasa! Korisnici mogu koristiti:

### Dostupne Markdown značajke:
- **Podebljano**: `**tekst**` ili `__tekst__`
- *Kurziv*: `*tekst*` ili `_tekst_`
- Naslovi: `# H1`, `## H2`, `### H3`, itd.
- Liste:
  ```markdown
  - Stavka 1
  - Stavka 2
  
  1. Numerirana stavka
  2. Druga stavka
  ```
- Linkovi: `[tekst](https://url.com)`
- Citati: `> Ovo je citat`
- Kod: `` `inline kod` `` ili blokovi koda s ` ``` `

### Sigurnost:
- Svi HTML tagovi su **sanitizirani** pomoću `bleach` biblioteke
- Dozvoljeni samo sigurni tagovi (`<p>`, `<strong>`, `<em>`, `<ul>`, `<li>`, itd.)
- Zaštita od XSS napada

### EasyMDE Editor:
- Live preview Markdown formatiranja
- Toolbar s quick buttons
- Side-by-side prikaz (Markdown | Preview)
- Fullscreen mod
- Brojanje riječi i linija

---


## 👨‍🏫 Autor
mag.ing. Josip Torić  
Studij informacijskih tehnologija — Sveučilište u Zadru
