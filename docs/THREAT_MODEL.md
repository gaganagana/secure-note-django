# SecureNote — Threat Model & Security Architecture (STRIDE)

This document provides a formal STRIDE threat modeling analysis of SecureNote, detailing potential attack vectors, threat actors, and engineering countermeasures.

```
+-------------------------------------------------------------------------+
|                              THREAT MODEL                               |
|                                                                         |
|  [ Attacker / Adversary ]                                               |
|           |                                                             |
|           v                                                             |
|   +---------------+     HTTPS / Session Token     +-----------------+   |
|   |  Web Browser  | ----------------------------> |  Django Backend |   |
|   |  / API Client | <---------------------------- |   (DRF Views)   |   |
|   +---------------+                               +-----------------+   |
|                                                           |             |
|                                            Fernet AES-128 | Decrypt on  |
|                                            (Application)  | Fetch       |
|                                                           v             |
|                                                   +-----------------+   |
|                                                   |  SQLite Storage |   |
|                                                   | (Ciphertext DB) |   |
|                                                   +-----------------+   |
+-------------------------------------------------------------------------+
```

---

## 1. STRIDE Analysis Matrix

| Threat Category | Potential Attack Vector | Impact | Mitigations Implemented in SecureNote |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Credential stuffing, session hijacking, brute-force login attempts | Unauthorized access to account notes | Django session authentication, PBKDF2 password hashing (with salt and SHA-256), `HttpOnly` session cookies. |
| **Tampering** | Modifying ciphertext directly inside the database or during transit | Data corruption or unauthorized note altering | Fernet HMAC-SHA256 signature verification. Any modified byte fails cryptographic authentication and prevents decryption. |
| **Repudiation** | User denies creating, editing, or deleting a specific note | Inability to audit unauthorized account actions | Database timestamps (`created_at`, `updated_at`) and Django user ownership auditing on all mutations. |
| **Information Disclosure** | Database file exfiltration, SQL injection, memory scraping | Plaintext leaks of private personal notes | Zero plaintext persistence in SQLite (Fernet encryption at application layer before SQL `INSERT`). |
| **Denial of Service** | Flooding note creation endpoints with excessively large payloads | Server CPU exhaustion or disk fill | Payload length validation on serializer fields; maximum character constraints in models and forms. |
| **Elevation of Privilege**| Manipulating note ID in REST API URL to access other users' notes (IDOR/BOLA) | Unauthorized read/write across tenants | Strict queryset filtering (`Note.objects.filter(user=request.user)`) enforced on every view and DRF ViewSet. |

---

## 2. Trust Boundaries & Data Flow

1. **User Space (Untrusted)**: Client browser inputs, form fields, and HTTP headers.
2. **Web / Application Tier (Trusted)**: Django framework handling authentication, session resolution, and input sanitization.
3. **Cryptographic Engine (Internal Core)**: Fernet symmetric encryption module holding the secret key loaded from `.env`.
4. **Data Persistence Tier (Semi-Trusted / Ciphertext Only)**: SQLite database. Even if compromised, plaintext notes cannot be extracted without the environment encryption key.
