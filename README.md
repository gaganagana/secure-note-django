# SecureNote – Encrypted Personal Notes App

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-green.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/REST%20Framework-3.14%2B-red.svg)](https://www.django-rest-framework.org/)
[![Security](https://img.shields.io/badge/Cryptography-Fernet%20AES--128-orange.svg)](#how-encryption-works)

I built SecureNote as a Python full-stack project to understand how application security and cryptography work in Django. It allows users to write private notes that are automatically encrypted using Python's Fernet library before being saved to SQLite, ensuring the database never stores plaintext notes.

---

## Why I Made It

In typical web applications, user notes or messages are stored directly in plain text in the database. If a database backup is misplaced or an unauthorized user gets direct access to the database file, all private text can be read immediately.

I wanted to build a working project where note text is encrypted at the application level before being saved to the database. Even if someone opens the SQLite database file directly, they will only see encrypted ciphertext tokens. Only the logged-in owner can decrypt and view their notes.

---

## What I Worked On

* **User Authentication:** Built registration, login, and logout views using Django's built-in authentication system with secure password hashing.
* **Symmetric Encryption:** Used Python's `cryptography.fernet` library to encrypt note contents with AES-128 in CBC mode and HMAC-SHA256 authentication before saving them to SQLite.
* **Ownership Access Control:** Added strict checks in Django views so users can only view, edit, or delete notes that belong to their own account.
* **REST API & Fetch:** Created API endpoints using Django REST Framework and connected them with vanilla JavaScript `fetch()` so the dashboard updates dynamically without full page reloads.
* **Automated Unit Tests:** Wrote 12 unit tests using Django's `TestCase` covering user registration, login, note encryption, decryption, and access restrictions. All 12 tests pass.

---

## Technologies Used

* **Backend:** Python 3, Django, Django REST Framework
* **Cryptography:** `cryptography` library (Fernet / AES-128)
* **Database:** SQLite
* **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript (Fetch API)
* **Testing:** Django TestCase

---

## How Encryption Works in This Project

When you save a note, the Django view encrypts the content before writing it to the database:

```text
User enters note: "Meeting notes for Friday"
          │
          ▼
Django View calls encrypt_text(content)
          │  (Fernet symmetric key loaded from environment variable)
          ▼
Stored in SQLite: "gAAAAABn7Q8...X9_kLz4" (Ciphertext Token)
          │
          ▼
When the owner views the note:
Django View calls decrypt_text(ciphertext) -> "Meeting notes for Friday"
```

If another user tries to access the note using its ID, Django blocks the request with an HTTP 403 / 404 response.

---

## How to Run It Locally

### 1. Clone the repository
```bash
git clone https://github.com/gaganagana/secure-note-django.git
cd secure-note-django
```

### 2. Set up virtual environment & install dependencies
```bash
python -m venv venv
venv\Scripts\activate      # On Windows
# source venv/bin/activate  # On Linux/macOS

pip install -r requirements.txt
```

### 3. Set up environment variables & database
```bash
cp .env.example .env
python manage.py migrate
```

### 4. Run tests & start the server
```bash
python manage.py test
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

---

## What I Learned

* The difference between one-way password hashing (Argon2 / PBKDF2) and two-way symmetric encryption (Fernet / AES).
* How to write Django unit tests that check models, views, and authentication permissions.
* Passing CSRF tokens safely with JavaScript fetch calls in Django templates.
* Managing secret keys and credentials using `.env` files and `.gitignore`.
