# SecureNote — Technical Interview Preparation Guide

This comprehensive guide is designed for **Python Full Stack Developer interviews**. Every question and answer is grounded **strictly in the actual code and architecture implemented in SecureNote**.

---

## Table of Contents
1. [Project-Level Questions](#1-project-level-questions)
2. [Django Architecture & MVT](#2-django-architecture--mvt)
3. [Database & Data Modeling](#3-database--data-modeling)
4. [Authentication vs. Authorization](#4-authentication-vs-authorization)
5. [Cryptography & Security Concepts](#5-cryptography--security-concepts)
6. [Django REST Framework (DRF) & REST APIs](#6-django-rest-framework-drf--rest-apis)
7. [Frontend & JavaScript Integration](#7-frontend--javascript-integration)
8. [File-by-File Code Walkthrough](#8-file-by-file-code-walkthrough)
9. [End-to-End Request Tracing (The Interview Gold Standard)](#9-end-to-end-request-tracing-the-interview-gold-standard)

---

## 1. Project-Level Questions

### Q1: What is SecureNote?
**Answer**: SecureNote is an educational full-stack web application built using Python, Django, Django REST Framework, SQLite, Bootstrap 5, and Vanilla JavaScript. It allows authenticated users to create and manage personal notes while encrypting note content at the application layer using the Python `cryptography` library (Fernet) before the content is saved to SQLite.

### Q2: Why did you build this project?
**Answer**: To demonstrate how fundamental software engineering and security concepts—user authentication, ownership-based authorization, ORM database transactions, REST API design, and symmetric data encryption—integrate seamlessly into a clean, standard Django web application without unnecessary third-party abstractions.

### Q3: What problem does SecureNote solve?
**Answer**: In conventional CRUD applications, user notes are stored as plaintext in the database. If the database file is leaked, misconfigured, or accessed by unauthorized administrators, all private information is exposed in cleartext. SecureNote solves this by encrypting note content at the application layer before database insertion. Even with full access to the raw SQLite database file, an attacker only sees random base64-encoded ciphertext tokens.

### Q4: Why did you choose Django?
**Answer**: Django follows the "batteries-included" philosophy. It provides out-of-the-box:
* A hardened user authentication system (with PBKDF2 password hashing).
* Built-in CSRF (Cross-Site Request Forgery) protection.
* A secure Object-Relational Mapper (ORM) that prevents SQL injection via parameterized queries.
* Robust session management.
* A structured Model-View-Template (MVT) architecture that makes code easy to maintain and explain.

### Q5: Why did you choose SQLite?
**Answer**: SQLite is serverless, zero-configuration, and transactional (ACID compliant). For local development, portfolio evaluation, and automated testing, SQLite requires no external service installation. In production, Django makes it trivial to swap SQLite for PostgreSQL by simply updating the `DATABASES` dictionary in `settings.py` without modifying any Python application code.

### Q6: Why did you choose application-level encryption over database-level encryption?
**Answer**: Database-level encryption (Transparent Data Encryption or full-disk encryption) protects data at rest on disk, but data in transit between the application and database remains plaintext, and any database user or admin can query the plaintext. Application-level encryption ensures that data is encrypted *before* it leaves the Django application process. The database never sees or stores plaintext.

### Q7: What are the limitations of your project?
**Answer**:
1. **Shared Key**: All notes currently share a single environment-level `FERNET_KEY`. If that key is compromised, all notes can be decrypted.
2. **Encrypted Content Searching**: Because ciphertext looks like random bytes, we cannot use standard SQL `LIKE` queries to search inside the encrypted note bodies; search is applied to note titles and categories.
3. **Key Management**: In an enterprise system, encryption keys should be managed by a dedicated Hardware Security Module (HSM) or cloud Key Management Service (AWS KMS, Google Cloud KMS, HashiCorp Vault) with automated key rotation.

### Q8: What would you improve in the future?
**Answer**:
1. Implement per-user encryption keys derived from the user's password using PBKDF2 or Argon2.
2. Use `MultiFernet` to support zero-downtime key rotation.
3. Add rate limiting to authentication endpoints to prevent brute-force attacks.
4. Integrate with PostgreSQL for production deployments.

---

## 2. Django Architecture & MVT

### Q9: What is Django's MVT pattern?
**Answer**: MVT stands for **Model-View-Template**:
* **Model (`models.py`)**: Defines the data structure, relationships, and business rules. It interfaces with the database via the Django ORM.
* **View (`views.py`)**: The controller/handler. It receives HTTP requests, executes business logic (such as checking authentication, ownership, or calling encryption functions), queries models, and returns an HTTP response (HTML or JSON).
* **Template (`templates/`)**: The presentation layer. Contains HTML and Django Template Language (DTL) tags to render dynamic data into web pages for the browser.

### Q10: What is the difference between a Django Project and a Django App?
**Answer**:
* A **Project** (`securenote/`) represents the entire web site/configuration. It contains global settings (`settings.py`), root URL routing (`urls.py`), and deployment interfaces (`wsgi.py`, `asgi.py`).
* An **App** (`notes/`) is a modular, self-contained Python package that handles a specific domain of functionality (e.g., note models, views, forms, and tests). A project can contain multiple apps, and apps can theoretically be reused across projects.

### Q11: What is the role of `manage.py`?
**Answer**: `manage.py` is a command-line script created automatically by Django. It sets the `DJANGO_SETTINGS_MODULE` environment variable and delegates commands to `django.core.management` for actions such as `runserver`, `makemigrations`, `migrate`, `test`, and `createsuperuser`.

### Q12: What are migrations and how do they work?
**Answer**: Migrations are Django’s way of propagating changes made to Python models (`models.py`) into the database schema (`db.sqlite3`):
* `makemigrations`: Inspects `models.py`, compares it with the previous migration files, and writes a new migration Python script (e.g., `0001_initial.py`).
* `migrate`: Executes the unapplied migration scripts against the database, creating or altering SQL tables, columns, and foreign keys.

### Q13: What is Django ORM and why use it instead of raw SQL?
**Answer**: An ORM (Object-Relational Mapper) lets developers interact with relational databases using Python objects and methods (`Note.objects.filter(...)`) rather than writing raw SQL strings (`SELECT * FROM notes_note WHERE ...`).
* **Security**: The ORM uses **parameterized queries**, which automatically separates user input from SQL commands, effectively preventing SQL injection attacks.
* **Database Abstraction**: The same Python code runs seamlessly on SQLite, PostgreSQL, MySQL, or Oracle.
* **Productivity**: Eliminates boilerplate data mapping and type conversions.

---

## 3. Database & Data Modeling

### Q14: Explain the `Note` model in SecureNote.
**Answer**: In `notes/models.py`:
```python
class Note(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    encrypted_content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Personal')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```
* `owner`: A Foreign Key linking the note to Django's built-in `User` model.
* `title`: A non-sensitive title string used for indexing, filtering, and display.
* `encrypted_content`: A `TextField` storing the base64 Fernet ciphertext token.
* `category`: A choice field restricting categories to Personal, Study, Work, Ideas, and Journal.
* `created_at` / `updated_at`: Automated timestamps for auditability and ordering.

### Q15: What is a Primary Key and Foreign Key?
**Answer**:
* **Primary Key (`id`)**: A unique identifier for each row in a database table. In our `Note` model, Django automatically provisions an auto-incrementing integer `BigAutoField` named `id`.
* **Foreign Key (`owner_id`)**: A field in one table that references the primary key of another table (`auth_user.id`). This establishes a relationship between two tables.

### Q16: What does `on_delete=models.CASCADE` mean?
**Answer**: It defines referential integrity behavior. When a record in the parent table (`User`) is deleted, all associated child records in the `Note` table are automatically and permanently deleted by the database. This prevents orphaned notes from lingering in the database without an owner.

### Q17: What relationship exists between `User` and `Note`?
**Answer**: A **Many-to-One** (or One-to-Many) relationship:
* One `User` can create many `Notes`.
* Each `Note` belongs to exactly one `User`.

---

## 4. Authentication vs. Authorization

### Q18: What is the difference between Authentication and Authorization?
**Answer**:
* **Authentication ("Who are you?")**: The process of verifying a user’s identity. Example: A user entering their username and password on `/login/`.
* **Authorization ("What are you allowed to do?")**: The process of determining whether an authenticated user has permission to access a specific resource. Example: In `/notes/<id>/`, checking whether `note.owner == request.user`.

### Q19: How does Django handle user login and sessions?
**Answer**:
1. When a user submits credentials, Django's `authenticate()` verifies the username and password against the stored password hash.
2. If valid, `login(request, user)` creates a session:
   * Generates a cryptographically random `session_key`.
   * Stores the session data in the `django_session` database table.
   * Sends the `session_key` back to the user's browser in an HTTP-only cookie named `sessionid`.
3. On subsequent requests, the browser sends the `sessionid` cookie. Django’s `SessionMiddleware` and `AuthenticationMiddleware` read the cookie, look up the session in the database, and attach the authenticated user object to `request.user`.

### Q20: How are passwords stored in Django? Why aren't they encrypted?
**Answer**:
* Django stores passwords as **cryptographic one-way hashes** using the **PBKDF2** algorithm with a SHA-256 digest and thousands of iterations (configured in `AUTH_PASSWORD_VALIDATORS`).
* **Why not encrypted?**: Passwords must **never** be reversible. If an attacker steals the database and an encryption key, they could decrypt all user passwords. With hashing, the original password is never stored anywhere; when a user logs in, Django hashes their input with the stored salt and compares the calculated hash to the stored hash.

### Q21: How is Authorization (ownership checking) enforced in SecureNote?
**Answer**: We enforce authorization directly in the backend Python views, never relying solely on hiding buttons in the HTML:
* **Web Views (`notes/views.py`)**:
  ```python
  note = get_object_or_404(Note, pk=pk)
  if note.owner != request.user:
      return HttpResponseForbidden("You do not have permission to access this note.")
  ```
* **REST API Views (`notes/api_views.py`)**:
  ```python
  notes = Note.objects.filter(owner=request.user)
  # Or when looking up a specific note:
  note = Note.objects.filter(id=pk, owner=request.user).first()
  if not note:
      return Response({'detail': 'Note not found or access denied.'}, status=404)
  ```
If User B attempts to access `/notes/1/` owned by User A, the backend intercepts the request and returns HTTP 403 Forbidden (or HTTP 404 in the API).

---

## 5. Cryptography & Security Concepts

### Q22: What is Fernet and how does it work?
**Answer**: Fernet is an implementation of symmetric authenticated cryptography provided by the Python `cryptography` library:
* **Algorithm**: It uses **AES-128 in CBC mode** with PKCS7 padding for confidentiality.
* **Authentication**: It uses **HMAC-SHA256** to authenticate the ciphertext and prevent tampering.
* **Key Format**: A 32-byte URL-safe base64-encoded secret key.
* **Symmetric**: The exact same secret key is used to both encrypt and decrypt the text.

### Q23: Why can't we use hashing to protect note content?
**Answer**: Hashing is a **one-way function**; once data is hashed, it cannot be recovered. Because the user needs to view, edit, and read their note content later, the content must be **reversible**. Therefore, symmetric encryption (two-way) is mandatory for note content, whereas hashing (one-way) is mandatory for passwords.

### Q24: Where is the encryption key stored and why shouldn't it be committed to Git?
**Answer**:
* The encryption key is stored in the environment variable `FERNET_KEY`, which is loaded from a local `.env` file via `python-dotenv`.
* It must **never** be committed to Git because any person or bot with access to the source code repository would obtain the key and be able to decrypt all database contents.
* SecureNote includes a `.env.example` in version control and adds `.env` to `.gitignore`.

### Q25: What happens if the encryption key is lost?
**Answer**: Because Fernet uses standard AES encryption without backdoors, if the `FERNET_KEY` is lost or deleted, the ciphertext in the database **cannot be recovered**. Any attempt to decrypt with a new or different key will raise a `cryptography.fernet.InvalidToken` exception, which our application catches and raises as `DecryptionError`.

### Q26: Why can't you search encrypted note content using standard database SQL queries?
**Answer**:
* In normal databases, searching is done with queries like `WHERE content LIKE '%search_term%'`.
* Fernet ciphertext is non-deterministic (it uses a randomized 16-byte IV/timestamp for every encryption). Even the exact same word encrypted twice produces two completely different base64 ciphertext tokens.
* The SQLite database only sees random-looking characters (e.g., `gAAAAABm...`). Therefore, database-level pattern matching cannot search encrypted content.
* In SecureNote, we deliberately search by unencrypted metadata (`title` and `category`) to avoid misleading security claims.

### Q27: What is CSRF and how does Django protect against it?
**Answer**:
* **CSRF (Cross-Site Request Forgery)** is an attack where a malicious website tricks an authenticated user's browser into submitting an unauthorized request (such as deleting a note) to a web application where the user is currently logged in.
* **Django's Protection**: Django uses the **Synchronizer Token Pattern**:
  1. `CsrfViewMiddleware` generates a random CSRF secret and sets a cookie in the browser.
  2. In HTML forms, `{% csrf_token %}` outputs a hidden input field containing a masked token.
  3. When the form is submitted via POST, Django compares the token submitted in the form against the cookie. If they don't match or the token is missing, Django rejects the request with HTTP 403 Forbidden.

### Q28: What is SQL Injection and how does Django ORM prevent it?
**Answer**:
* **SQL Injection** occurs when untrusted user input is directly concatenated into a raw SQL query string, allowing an attacker to manipulate the query syntax (e.g., `' OR '1'='1`).
* **Django's Prevention**: The Django ORM does not concatenate raw strings. It uses **parameterized queries** (prepared statements). User inputs are passed as parameters separate from the SQL query structure. The database engine treats the parameter strictly as literal data, making it impossible for input to alter query logic.

---

## 6. Django REST Framework (DRF) & REST APIs

### Q29: What is a REST API?
**Answer**: REST (Representational State Transfer) is an architectural style for designing networked applications. It uses standard HTTP methods to perform CRUD operations on resources identified by URIs:
* `GET`: Retrieve resource(s)
* `POST`: Create a new resource
* `PUT`: Replace/update an entire existing resource
* `PATCH`: Partially update an existing resource
* `DELETE`: Remove a resource

### Q30: What is JSON and why is it used in REST APIs?
**Answer**: JSON (JavaScript Object Notation) is a lightweight, language-agnostic text format for data interchange. It is natively understood by JavaScript in web browsers and easily parsed/generated by Python via dictionaries and lists.

### Q31: What HTTP status codes are used in SecureNote's API?
**Answer**:
* `200 OK`: Request succeeded (e.g., retrieving notes via `GET /api/notes/` or updating via `PUT`).
* `201 Created`: Resource successfully created (e.g., `POST /api/notes/`).
* `204 No Content`: Resource successfully deleted (e.g., `DELETE /api/notes/<id>/`).
* `400 Bad Request`: Validation failure (e.g., missing required title or content).
* `401 Unauthorized`: Request lacks valid authentication credentials.
* `403 Forbidden`: Authenticated user lacks permission to perform the requested action.
* `404 Not Found`: Resource does not exist or does not belong to the user.

### Q32: Why did you use `APIView` in SecureNote?
**Answer**: We chose DRF’s `APIView` instead of complex ModelViewSets to keep the code **explicit, transparent, and easy to explain**:
* In `post()`, we explicitly validate data, call `encrypt_text()`, and create the model record.
* In `get()`, we query the user's notes, explicitly call `decrypt_text()`, and return serialized JSON.
* There are no hidden serializer hooks, custom ORM fields, or magic overrides.

---

## 7. Frontend & JavaScript Integration

### Q33: Why did you use Vanilla JavaScript instead of React or Vue?
**Answer**:
1. **Simplicity & Maintainability**: Vanilla JavaScript runs natively in every modern browser without requiring Node.js, npm packages, Webpack, Babel, or a complex build step.
2. **Architecture Focus**: The goal of this portfolio project is to demonstrate mastery of core Python, Django, database transactions, and security fundamentals. Vanilla JS keeps the frontend lightweight and responsive while leaving the core business logic in Python.

### Q34: What is the Fetch API and how is it used in SecureNote?
**Answer**: The **Fetch API** is a modern, native browser JavaScript interface for making asynchronous HTTP requests without reloading the page.
* In `static/js/main.js`, clicking the **"Refresh Notes"** button on the dashboard triggers:
  ```javascript
  const response = await fetch('/api/notes/', { method: 'GET' });
  const notes = await response.json();
  renderRecentNotes(notes);
  ```
* This asynchronously fetches the latest decrypted notes from the DRF backend and updates the DOM in real time, demonstrating frontend-to-backend API communication.

### Q35: What is the DOM?
**Answer**: The **Document Object Model (DOM)** is a tree-like object representation of the HTML document created by the browser. JavaScript uses the DOM API (`document.getElementById`, `innerHTML`, `classList`) to dynamically inspect, update, or manipulate page content and styles in response to user actions.

---

## 8. File-by-File Code Walkthrough

Be prepared to explain the exact responsibility of every file in the project:

### 1. `notes/utils.py`
* **Purpose**: Dedicated cryptographic utility module.
* **Key Components**:
  * `class DecryptionError(Exception)`: Custom exception raised when ciphertext is corrupted, tampered with, or cannot be decrypted with the key.
  * `get_fernet() -> Fernet`: Reads `FERNET_KEY` from `os.environ`. Raises `ImproperlyConfigured` if missing or malformed.
  * `encrypt_text(plain_text: str) -> str`: Converts UTF-8 string to bytes, calls `fernet.encrypt()`, and returns base64 ciphertext string.
  * `decrypt_text(cipher_text: str) -> str`: Converts base64 ciphertext string to bytes, calls `fernet.decrypt()`, and returns original UTF-8 plaintext string.

### 2. `notes/models.py`
* **Purpose**: Database schema definition.
* **Key Components**:
  * `class Note(models.Model)`: Fields include `owner` (ForeignKey to `User`), `title`, `encrypted_content`, `category`, and timestamps.
  * Explicitly names the field `encrypted_content` to make it clear to anyone inspecting the model that ciphertext is stored.

### 3. `notes/forms.py`
* **Purpose**: User input validation and HTML form generation.
* **Key Components**:
  * `UserRegisterForm`: Extends `UserCreationForm` to add an `email` field and apply Bootstrap CSS classes.
  * `NoteForm`: A clean form exposing `title`, `category`, and `content` (plaintext input textarea). Encryption happens in the view upon form submission.

### 4. `notes/views.py`
* **Purpose**: Web request handlers for HTML templates.
* **Key Components**:
  * `landing_view`: Public landing page.
  * `register_view` / `login_view` / `logout_view`: User authentication flows.
  * `dashboard_view`: Computes category metrics and fetches 5 recent notes for `request.user`.
  * `note_list_view`: Lists notes with category filtering and title search.
  * `note_detail_view`: Verifies `note.owner == request.user` (or returns 403), calls `decrypt_text()`, and passes decrypted content to the template.
  * `note_create_view`: Validates form, calls `encrypt_text(content)`, and creates the `Note` instance.
  * `note_update_view`: Verifies ownership, pre-populates form with `decrypt_text()`, and re-encrypts on save.
  * `note_delete_view`: Verifies ownership and permanently deletes the note on POST.

### 5. `notes/serializers.py`
* **Purpose**: REST API data validation and serialization.
* **Key Components**:
  * `class NoteSerializer(serializers.Serializer)`: Validates input fields (`title`, `category`, `content`) and formats output JSON. Contains no hidden hooks.

### 6. `notes/api_views.py`
* **Purpose**: REST API endpoints using DRF `APIView`.
* **Key Components**:
  * `NoteListCreateAPIView`: `get()` lists decrypted notes; `post()` explicitly encrypts and creates.
  * `NoteDetailAPIView`: `get()`, `put()`, and `delete()` enforcing strict `owner=request.user` filtering and explicit crypto calls.

### 7. `notes/admin.py`
* **Purpose**: Privacy-conscious Django Admin configuration.
* **Key Components**:
  * Displays `encrypted_content` as a read-only field. Does NOT decrypt user notes in the admin panel to respect user privacy and the principle of least privilege.

### 8. `notes/tests.py`
* **Purpose**: Automated test suite.
* **Key Components**:
  * 12 test cases verifying password hashing, raw database ciphertext storage, owner access, non-owner 403 rejection, API authentication, API 404 rejection, and error handling for missing/corrupted keys.

### 9. `static/js/main.js`
* **Purpose**: Client-side interactivity.
* **Key Components**:
  * `initTheme()`: Manages Dark/Light mode toggle and synchronizes with `localStorage`.
  * `initToasts()`: Auto-initializes Bootstrap toast alerts.
  * `initDeleteModal()`: Injects dynamic note title and form URL into the confirmation modal.
  * `initFetchApiRefresh()`: Executes asynchronous `fetch('/api/notes/')` call and updates the dashboard DOM live.

---

## 9. End-to-End Request Tracing (The Interview Gold Standard)

If asked: *"Trace what happens when a user creates a note in SecureNote"*:

```text
1. User enters "System Architecture Notes" and content in the browser and clicks "Save Note".
2. Browser sends an HTTP POST request to `/notes/create/` with the form payload and CSRF token.
3. Django's `CsrfViewMiddleware` verifies that the CSRF token matches the session cookie.
4. Django's URL resolver routes `/notes/create/` to `notes.views.note_create_view`.
5. The `@login_required` decorator checks `request.user.is_authenticated`. If not, redirects to `/login/`.
6. The view instantiates `form = NoteForm(request.POST)` and calls `form.is_valid()`.
7. The view extracts plaintext from `form.cleaned_data['content']`.
8. The view calls `encrypt_text(plain_content)` in `notes/utils.py`.
9. `encrypt_text()` retrieves `FERNET_KEY` from the environment, initializes `Fernet(key)`, encrypts the bytes via AES-128-CBC + HMAC-SHA256, and returns a base64 ciphertext token.
10. The view calls `Note.objects.create(owner=request.user, title=title, category=category, encrypted_content=ciphertext)`.
11. Django ORM translates this into a parameterized SQL `INSERT INTO notes_note (...) VALUES (?, ?, ?, ...)` statement.
12. SQLite executes the query and writes the row to `db.sqlite3`.
13. The view queues a success toast message using Django's `messages` framework.
14. The view returns an `HttpResponseRedirect` (HTTP 302) to `/notes/<id>/`.
15. The browser follows the redirect, where `note_detail_view` verifies ownership, decrypts the ciphertext on the fly, and renders the decrypted note in HTML.
```
