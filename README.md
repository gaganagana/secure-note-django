# SecureNote — Encrypted Personal Notes Web Application

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/Django%20REST%20Framework-3.14%2B-red.svg)](https://www.django-rest-framework.org/)
[![Security](https://img.shields.io/badge/Encryption-Fernet%20AES--128--CBC-orange.svg)](https://cryptography.io/)
[![Frontend](https://img.shields.io/badge/Frontend-Bootstrap%205%20%7C%20Vanilla%20JS-purple.svg)](https://getbootstrap.com/)

> **Portfolio & Interview Project**: SecureNote is an educational full-stack web application designed to demonstrate clean Django MVT architecture, strict ownership-based authorization, and application-level symmetric encryption using Python's `cryptography` library.

---

## 1. Project Overview

**SecureNote** allows authenticated users to create, view, edit, search, and manage personal notes while ensuring that the note body is encrypted **before** it is stored in the database.

When a note is saved, Django converts the plaintext into an authenticated ciphertext token via **Fernet** (AES-128-CBC + HMAC-SHA256). Even if the underlying SQLite database file is accessed or inspected directly, the contents remain encrypted ciphertext. When an authorized user requests their note, the backend decrypts the content on the fly and renders it.

### Target Use Cases
* Personal study notes and interview preparation logs
* Project architecture drafts and ideas
* Private daily reflections and journals
* Work-related scratch notes

> [!WARNING]
> **Educational Disclaimer**: SecureNote is an educational portfolio project built to demonstrate application-level cryptography and full-stack Django concepts. It is **not** a replacement for commercial password managers (e.g., 1Password, Bitwarden) or enterprise key-management systems. Users should never store banking credentials, master passwords, or production API secret keys in this application.

---

## 2. Problem Statement

In conventional CRUD web applications, user notes and comments are stored in the database as **raw plaintext**:

```text
[Browser Plaintext] ──> [Django View] ──> [Database Column: Plaintext]
```

This introduces notable security risks:
1. **Database Leaks & Backups**: If a database backup file (`.sqlite3` / `.sql`) is leaked or misconfigured, all private user notes are exposed in plain English.
2. **Internal Access**: Database administrators (DBAs) or server operators can inspect private records without restriction.
3. **SQL Injection**: If raw SQL is improperly handled, extracted rows yield immediate plaintext.

### The Solution: Application-Level Encryption
SecureNote implements **application-level symmetric encryption**:

```text
[Browser Plaintext] ──> [Django View] ──> [encrypt_text()] ──> [Database Column: Ciphertext]
```

The database stores only base64 ciphertext tokens (e.g., `gAAAAABm...`). Plaintext exists in memory only during the active request lifecycle and is never written to disk in unencrypted form.

---

## 3. Technology Stack & Justification

| Technology | Purpose in Project | Why This Was Selected |
| :--- | :--- | :--- |
| **Python 3** | Core backend language | Readable syntax, powerful standard library, industry standard for web development. |
| **Django (MVT)** | Full-stack web framework | Built-in authentication, robust ORM, automatic CSRF protection, secure session handling. |
| **Django ORM** | Object-Relational Mapping | Translates Python models into parameterized SQL queries, eliminating SQL injection risks. |
| **SQLite** | Relational database | Serverless, zero-configuration, lightweight file-based database ideal for demonstration and local development. |
| **Cryptography (Fernet)** | Note content encryption | Implements standard AES-128-CBC with PKCS7 padding and HMAC-SHA256 authentication. Prevents both reading and tampering. |
| **Django REST Framework (DRF)** | REST API | Demonstrates clean JSON serialization, HTTP status codes, and API authentication. |
| **Bootstrap 5** | Responsive UI styling | Modern SaaS cards, responsive grid, light/dark mode support, modal dialogs, and toast alerts. |
| **Vanilla JavaScript** | Client-side interactivity | Lightweight, zero-dependency DOM manipulation, modal handling, theme persistence, and asynchronous Fetch API calls. |

---

## 4. Key Distinction: Encryption vs. Hashing

A critical talking point in full-stack technical interviews is distinguishing between **reversible encryption** and **irreversible hashing**:

| Feature | Encryption (Fernet) | Hashing (PBKDF2 SHA-256) |
| :--- | :--- | :--- |
| **Mechanism** | Symmetric Cipher (AES-128-CBC + HMAC) | Cryptographic One-Way Function |
| **Reversibility** | **Two-Way** (Can be decrypted using the secret key) | **One-Way** (Cannot be decrypted back to original text) |
| **Use in SecureNote** | **Note Content**: Encrypted before DB insert; decrypted when owner views the note. | **User Passwords**: Hashed with a random salt by Django's auth system. Never decrypted. |
| **Verification** | `decrypt_text(ciphertext) == plaintext` | `check_password(input_password, stored_hash)` compares calculated hash. |
| **Why not the other?** | We cannot hash notes because the user needs to read their notes back later. | We cannot encrypt passwords because two-way decryption introduces unnecessary key exposure risk. |

---

## 5. System Architecture & Request Flows

### High-Level Architecture
```text
                          USER (Browser)
                                │
                        HTML5 / Bootstrap 5 / JS
                                │
                          Django URLs
                                │
                          Django Views
                         /            \
           Web Request  /              \  REST API Request
                       ▼                ▼
                 Django Forms       API Views (DRF)
                       │                │
                       └───────┬────────┘
                               ▼
                   Authentication & Authorization
                     (Ownership: owner == request.user)
                               │
                               ▼
                 Explicit Cryptography (utils.py)
                    ├── encrypt_text() [Writes]
                    └── decrypt_text() [Reads]
                               │
                               ▼
                          Django ORM
                     (Parameterized SQL Queries)
                               │
                               ▼
                         SQLite Database
                       (Ciphertext Storage)
```

---

### Create Note Flow (Writing Data)
```text
User enters title, category, and plaintext content in browser
                      ↓
HTTP POST request submitted with CSRF token
                      ↓
Django URL router dispatches to `note_create_view`
                      ↓
`@login_required` verifies user authentication
                      ↓
`form.is_valid()` validates inputs
                      ↓
`encrypt_text(form.cleaned_data['content'])` produces base64 ciphertext
                      ↓
Django ORM instantiates `Note(owner=request.user, encrypted_content=ciphertext)`
                      ↓
SQLite inserts row with encrypted ciphertext column
                      ↓
HTTP 302 Redirect to note detail view with success toast message
```

---

### View Note Flow (Reading Data)
```text
User navigates to `/notes/<id>/`
                      ↓
Django URL router dispatches to `note_detail_view` with `pk=<id>`
                      ↓
`@login_required` checks active session
                      ↓
ORM fetches note: `note = get_object_or_404(Note, pk=pk)`
                      ↓
AUTHORIZATION CHECK:
if note.owner != request.user:
    return HttpResponseForbidden (HTTP 403)
                      ↓
`decrypt_text(note.encrypted_content)` converts ciphertext back to plaintext
                      ↓
Django template engine renders `note_detail.html` with decrypted text
                      ↓
HTTP 200 response returned to user's browser
```

---

## 6. Directory Structure

```text
D:\securenote\
│
├── manage.py                   # Django CLI utility for tasks and server management
├── requirements.txt            # Python package dependencies
├── .env.example                # Template for environment variables (safe to commit)
├── .gitignore                  # Git rules preventing commit of secrets, DB, and venv
├── README.md                   # Comprehensive project documentation
├── INTERVIEW_PREPARATION.md    # Technical interview questions and answers
│
├── securenote/                 # Project configuration package
│   ├── __init__.py
│   ├── settings.py             # App settings, DB config, DRF settings, auth URLs
│   ├── urls.py                 # Top-level URL routing (delegates to notes.urls)
│   ├── asgi.py                 # ASGI entrypoint for asynchronous servers
│   └── wsgi.py                 # WSGI entrypoint for standard production servers
│
├── notes/                      # Core business logic app
│   ├── migrations/             # Database schema migrations
│   ├── __init__.py
│   ├── admin.py                # Django Admin with read-only encrypted content
│   ├── apps.py                 # Application configuration
│   ├── forms.py                # UserRegisterForm and NoteForm
│   ├── models.py               # Note model with owner ForeignKey & encrypted_content
│   ├── serializers.py          # DRF NoteSerializer (clean input/output validation)
│   ├── urls.py                 # URL patterns for web views & REST API endpoints
│   ├── views.py                # Web views (landing, auth, dashboard, note CRUD)
│   ├── api_views.py            # DRF API views with explicit encryption & ownership
│   ├── utils.py                # Fernet encrypt_text(), decrypt_text(), DecryptionError
│   └── tests.py                # 12 automated test cases covering auth, crypto & API
│
├── templates/                  # Server-side HTML templates
│   ├── base.html               # Base layout (Bootstrap 5, navbar, theme toggle, toasts, modal)
│   ├── landing.html            # Public SaaS landing page with crypto visual element
│   ├── dashboard.html          # Stats cards, recent notes, and Fetch API refresh button
│   ├── auth/
│   │   ├── login.html          # Clean sign-in card
│   │   └── register.html       # Clean sign-up card
│   └── notes/
│       ├── note_list.html      # Note cards, search bar, and category filter pills
│       ├── note_detail.html    # Decrypted note view, copy button, raw ciphertext inspector
│       └── note_form.html      # Create and edit note form with plaintext textarea
│
└── static/                     # Static assets
    ├── css/
    │   └── style.css           # Custom styling, category badge styles, card hover effects
    └── js/
        └── main.js             # Theme toggle, toast auto-init, delete modal, Fetch API
```

---

## 7. Step-by-Step Installation & Setup (Windows)

Follow these straightforward steps to run SecureNote locally on Windows.

### Prerequisites
* Python 3.10+ installed and added to `PATH`.

### Step 1: Open Terminal in Project Folder
```powershell
cd D:\securenote
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy restriction, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and re-run the activation script).*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Generate a Fernet Encryption Key
Run this Python command in your terminal to generate a 32-byte URL-safe base64 Fernet key:
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
*Example output:* `GWyQCk5Mryt-cKW2W4P6OBoAImgzAOqLI3CLzxUQLxk=`

### Step 6: Create Your `.env` File
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in your editor and paste the generated Fernet key:
```text
SECRET_KEY=django-insecure-local-demo-secret-key-12345
DEBUG=True
FERNET_KEY=your-generated-fernet-key-here
```

### Step 7: Apply Database Migrations
```powershell
python manage.py migrate
```

### Step 8: Run Automated Tests
Verify that all 12 unit and security tests pass:
```powershell
python manage.py test notes
```

### Step 9: Start the Development Server
```powershell
python manage.py runserver
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 8. REST API Endpoints

SecureNote includes a clean, lightweight REST API built with Django REST Framework. All endpoints require authentication (`SessionAuthentication` or `BasicAuthentication`).

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/notes/` | List all notes belonging to the authenticated user. Note content is decrypted in the response. | `200 OK`, `401 Unauthorized` |
| `POST` | `/api/notes/` | Create a new note. Plaintext `content` is encrypted before saving. | `201 Created`, `400 Bad Request`, `401 Unauthorized` |
| `GET` | `/api/notes/<id>/` | Retrieve a single note by ID. Ownership verified; returns decrypted content. | `200 OK`, `404 Not Found`, `401 Unauthorized` |
| `PUT` | `/api/notes/<id>/` | Update a note. Updated plaintext is re-encrypted before saving. | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/api/notes/<id>/` | Delete a note. Ownership verified. | `204 No Content`, `404 Not Found` |

### Sample API Request (`POST /api/notes/`)
```json
{
  "title": "Database Optimization Checklist",
  "category": "Work",
  "content": "Add indexes on frequently queried columns and avoid N+1 queries using select_related."
}
```

### Sample API Response (`201 Created`)
```json
{
  "id": 1,
  "owner": "alice",
  "title": "Database Optimization Checklist",
  "category": "Work",
  "content": "Add indexes on frequently queried columns and avoid N+1 queries using select_related.",
  "created_at": "2026-09-26T07:30:00Z",
  "updated_at": "2026-09-26T07:30:00Z"
}
```

---

## 9. Interactive UI Features

* **Dark / Light Mode**: Uses Bootstrap 5.3 `data-bs-theme` attribute toggled with Vanilla JavaScript and remembered across sessions via `localStorage`.
* **Toast Alerts**: Django flash messages (`messages.success`, `messages.error`) automatically render as floating Bootstrap toasts with icons and auto-dismiss after 5 seconds.
* **Delete Confirmation Modal**: Prevents accidental note deletion. JavaScript dynamically configures the delete form's target URL upon opening.
* **Real Fetch API Demonstration**: Clicking **"Refresh Notes"** on the Dashboard executes an asynchronous `fetch('/api/notes/')` request to the DRF API, dynamically re-rendering recent notes in the DOM without a page refresh.
* **One-Click Copy**: A dedicated button on the note detail page copies decrypted content directly to the user's clipboard.
* **Raw Ciphertext Inspector**: An expandable accordion on the note detail page demonstrates how the ciphertext is actually stored in SQLite, providing a great visual aid for interviews.

---

## 10. Automated Test Suite

Run the test suite using:
```powershell
python manage.py test notes
```

The 12 test cases systematically verify:
1. **Password Hashing**: Verifies that passwords are saved as salted PBKDF2 hashes, never plaintext.
2. **Ciphertext Storage**: Inspects SQLite records directly using the ORM to prove that `encrypted_content` does NOT contain the plaintext input and starts with the Fernet header `gAAAAA`.
3. **Decryption on Retrieval**: Verifies that the note owner receives HTTP 200 with correctly decrypted content rendered in the HTML.
4. **Ownership Authorization**: Verifies that User B receives HTTP 403 Forbidden when attempting to view, edit, or delete User A's note.
5. **Update & Re-encryption**: Verifies that updating a note properly re-encrypts the new content.
6. **Deletion**: Verifies that deleting a note removes it completely from SQLite.
7. **Decryption Error Handling**: Verifies that corrupted or tampered ciphertext triggers `DecryptionError`.
8. **API Authentication**: Verifies that unauthenticated requests to `/api/notes/` are rejected (401/403).
9. **API CRUD Operations**: Verifies creating and listing notes via DRF.
10. **API Ownership Enforcement**: Verifies that User B receives HTTP 404 when querying User A's note ID via the API.
11. **Missing Key Handling**: Verifies that a missing `FERNET_KEY` raises `ImproperlyConfigured` with actionable instructions.
12. **Invalid Key Handling**: Verifies that a malformed `FERNET_KEY` raises `ImproperlyConfigured`.

---

## 11. Security Limitations & Future Roadmap

To demonstrate engineering maturity in an interview, be prepared to discuss the intentional limitations of this portfolio project and how you would scale it in production:

1. **Application-Level Shared Key**:
   * *Current*: All notes are encrypted using a single environment-level `FERNET_KEY`.
   * *Future Improvement*: Derive a unique key per user from their password using PBKDF2 / Argon2, or use an external Key Management Service (AWS KMS, Google Cloud KMS, or HashiCorp Vault).
2. **Encrypted Content Searching**:
   * *Current*: Full-text search is applied only to note titles and categories. Ciphertext cannot be queried using SQL `LIKE` or `icontains` because ciphertext looks like random base64 bytes.
   * *Future Improvement*: Implement searchable symmetric encryption (SSE) or client-side index filtering.
3. **Key Rotation**:
   * *Future Improvement*: Add a `MultiFernet` utility to support zero-downtime key rotation where notes encrypted with old keys can be read and re-encrypted with a primary new key.
