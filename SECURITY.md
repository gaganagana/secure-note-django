# Security Policy & Cryptographic Specifications

## 1. Security Philosophy
SecureNote was architected with a **Defense-in-Depth** and **Zero Plaintext Persistence** mindset. While traditional web applications rely on perimeter security or transparent database-at-rest encryption, SecureNote implements application-layer cryptographic isolation to safeguard personal data even in the event of an unauthorized database dump or local file disclosure.

---

## 2. Cryptographic Specifications
- **Primitive**: Symmetric Authenticated Encryption via Python `cryptography.fernet`.
- **Underlying Cipher**: AES-128 in Cipher Block Chaining (CBC) mode with PKCS7 padding.
- **Message Integrity**: HMAC using SHA-256 for authenticated encryption (Encrypt-then-MAC).
- **IV Generation**: 128-bit Cryptographically Secure Pseudorandom Number Generator (CSPRNG) initialization vector generated uniquely per encryption operation.
- **Key Derivation & Storage**: The 256-bit Fernet key (128-bit AES encryption key + 128-bit HMAC signing key) is ingested strictly through environment variables (`ENCRYPTION_KEY`) and is never committed to source control or logged.

---

## 3. Vulnerability Mitigations
- **Broken Object Level Authorization (BOLA / IDOR)**:
  - All database queries for note retrieval, modification, or deletion are strictly scoped to the authenticated session user:
    ```python
    Note.objects.filter(user=request.user)
    ```
  - Direct object access by ID without ownership validation is rejected with HTTP 404/403.
- **Cross-Site Scripting (XSS)**:
  - Django automatic context-aware HTML escaping is enforced across all template renders.
  - REST API responses serialize plaintext solely on-demand to authorized clients via JSON.
- **Cross-Site Request Forgery (CSRF)**:
  - Strict CSRF token validation on all mutating state operations (`POST`, `PUT`, `DELETE`).
- **SQL Injection (SQLi)**:
  - Zero raw SQL query interpolation; 100% parameterized Django ORM abstraction.

---

## 4. Reporting a Vulnerability
If you discover a potential security vulnerability within this project, please report it responsibly:
1. Open a private security advisory or contact: `gaganacp2002@gmail.com`.
2. Provide detailed steps to reproduce the vulnerability, including PoC payloads or HTTP requests.
3. Allow a reasonable window for remediation prior to public disclosure.
