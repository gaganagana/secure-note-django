# SecureNote — Encrypted Personal Notes & DevSecOps Showcase

[![Security CI](https://github.com/gaganagana/secure-note-django/actions/workflows/security-ci.yml/badge.svg)](https://github.com/gaganagana/secure-note-django/actions)
[![Bandit SAST](https://img.shields.io/badge/Bandit%20SAST-Verified%20Clean-brightgreen.svg)](#security-and-devsecops)
[![OWASP Protection](https://img.shields.io/badge/OWASP-BOLA%20%2F%20IDOR%20Hardened-blue.svg)](docs/THREAT_MODEL.md)
[![Cryptography](https://img.shields.io/badge/Cryptography-Fernet%20AES--128-orange.svg)](#how-encryption-works)
[![Django](https://img.shields.io/badge/Django-5.0%2B-green.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/REST%20Framework-3.14%2B-red.svg)](https://www.django-rest-framework.org/)

SecureNote is a security-focused full-stack web application designed to demonstrate **application-layer cryptographic defense-in-depth**, **API security (BOLA/IDOR prevention)**, and **DevSecOps automation in CI/CD pipelines**. It eliminates plaintext persistence in the database by encrypting note payloads at the application boundary prior to SQL execution.

---

## Key Highlights & Architectural Defense

- **Zero Plaintext Persistence:** Even if `db.sqlite3` is extracted or dumped via physical or logical compromise, all note contents are stored strictly as encrypted Base64 Fernet tokens.
- **Symmetric Authenticated Cryptography:** Leverages Python's `cryptography` engine (`Fernet` specification: AES-128 in CBC mode with PKCS7 padding and HMAC-SHA256 authenticated integrity verification).
- **Strict BOLA / IDOR Elimination:** Every database interaction is scoped to the authenticated session context (`Note.objects.filter(user=request.user)`), guaranteeing isolation between tenant records.
- **Automated DevSecOps Pipeline:** Continuous Integration via GitHub Actions running automated unit testing, Bandit SAST analysis, Semgrep security scans, and secret sanitization checks on every commit.

---

## Threat Model & Access Control

For full architectural threat analysis based on the STRIDE framework, refer to:
- [Threat Model & Security Architecture Document](docs/THREAT_MODEL.md)
- [Security Policy & Cryptographic Specifications](SECURITY.md)

### Cryptographic Workflow

```text
User Input: "Financial Notes & Passwords"
          │
          ▼
Django View / DRF Serializer
          │  (Fernet symmetric key loaded securely from environment)
          ▼
encrypt_text(content) -> "gAAAAABn7Q8...X9_kLz4" (Ciphertext Token)
          │
          ▼
Saved to SQLite Database (Zero Plaintext Exposure)
          │
          ▼
Decryption on retrieval (Authenticated Owner ONLY):
decrypt_text(token) -> "Financial Notes & Passwords"
```

---

## Security and DevSecOps

The repository includes pre-configured security tooling to shift security left into development workflows:

1. **GitHub Actions CI/CD (`.github/workflows/security-ci.yml`)**:
   - Executes 12 automated unit tests covering cryptographic integrity, authentication, and multi-tenant isolation.
   - Runs **Bandit SAST** across all backend code to detect high-severity Python vulnerabilities.
   - Runs **Semgrep** rulesets for Django security anti-patterns.
2. **Local Security Profiles**:
   - `.bandit` configuration profile tailoring rule confidence and severities.
   - `.pre-commit-config.yaml` to prevent committing secrets or private keys.

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
pip install bandit flake8
```

### 3. Configure environment variables & database
```bash
cp .env.example .env
python manage.py migrate
```

### 4. Run automated tests & security scanner
```bash
# Execute unit test suite (12 tests)
python manage.py test

# Run Bandit SAST security scan
bandit -r notes/ securenote/ -ll
```

### 5. Launch the application
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your browser.

---

## Author & Project Link
- **Author:** Gagana C P
- **LinkedIn:** [linkedin.com/in/gaganacp](https://www.linkedin.com/in/gaganacp/)
- **Repository:** [github.com/gaganagana/secure-note-django](https://github.com/gaganagana/secure-note-django)
