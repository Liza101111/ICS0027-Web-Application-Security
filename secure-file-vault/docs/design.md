# Secure File Vault — Design Document (Checkpoint 1)

ICS0027 Web Application Security — Threat Model and Architecture (Week 4)

## 1. System Architecture

```text
[ Browser ]  --HTTPS-->  [ Flask App ]  --encrypt/write-->  [ Storage ]
(untrusted)     <--HTTPS--   (trusted)   <--decrypt/read--   (encrypted files)
                                  |
                                  |--read/write metadata--> [ Database ]
                                                           (users, file metadata)
```

See `architecture.png` for the full diagram.

- **Trust boundary:** drawn between the Browser and the Flask App. Everything on the browser side (form input, uploaded file names, cookies, any client-side JavaScript) is treated as untrusted and is re-validated server-side. Everything on the Flask App side — routing, auth checks, encryption/decryption, database access — is trusted.
- **Where encryption happens:** entirely server-side, inside the Flask App. On upload, the app encrypts the file with AES-GCM before it is written to `storage/`. On download, the app reads the encrypted file, decrypts it in memory, and streams the plaintext to the browser over HTTPS. The file is never written to disk unencrypted, and the plaintext is never persisted — only ever held in memory for the duration of a single request.
- **What the database stores:** user accounts (username, password hash) and file metadata (filename, owner user ID, storage path, per-file IV/nonce). The database never stores plaintext file contents or the encryption key.
- **Where the encryption key lives:** a single server-managed key, loaded at runtime from an environment variable (see `.env.example`), never committed to source control and never sent to or derived from the browser.

## 2. Threat Model

Mapped to the OWASP Top 10 and the attack classes covered in Weeks 1–4.

| # | Threat | Where it applies | Mitigation |
|---|---|---|---|
| 1 | Injection (SQL injection) | Login, registration, file metadata queries | All queries go through the SQLAlchemy ORM with parameter binding; no raw/string-concatenated SQL |
| 2 | Identification and Authentication Failures (broken authentication) | Login, session handling | Passwords hashed with Argon2; failed-login rate limiting; sessions managed by Flask-Login |
| 3 | Broken access control (IDOR) | `/download/<id>`, `/delete/<id>` | Every file route checks `file.owner_id == current_user.id` server-side before acting, regardless of what ID the client supplies |
| 4 | HTML / JavaScript injection (XSS) | Any user-supplied text rendered back (e.g. filenames, usernames) | Jinja2 auto-escaping is kept enabled; untrusted content is never rendered using `|safe`; Content-Security-Policy can also be used |
| 5 | Input tampering | Upload form (filename, size, content-type), form fields in general | Server-side validation of file size, extension/type, and all form fields; client-side checks treated only as UX, never trusted |
| 6 | Client-side control bypass | Any UI restriction (disabled buttons, hidden fields, JS-only checks) | Every restriction is enforced server-side as well (e.g. max file size, ownership, allowed actions), so disabling JS or editing the DOM changes nothing |
| 7 | Cryptographic Failures (sensitive data exposure) | Files at rest, credentials, network traffic | AES-GCM encryption at rest for files; Argon2 password hashing; TLS for all traffic (see §3) |
| 8 | Security misconfiguration | Flask app configuration | Debug mode disabled outside local development; secrets loaded from environment variables, not hardcoded; default Flask secret key never used |
| 9 | Cross-Site Request Forgery (CSRF) | Upload, delete, logout, and other state-changing POST routes | Flask-WTF CSRF tokens required on all forms/state-changing requests |
| 10 | Key compromise exposes all files | Server holds a single master encryption key | Key stored only in an environment variable outside the codebase; file permissions restricted; this is an accepted trade-off of the server-side key model, documented here explicitly |
| 11 | Database-only breach (DB stolen, key not) | Database storing ciphertext + metadata | AES-GCM with a unique random IV/nonce per file, so ciphertext alone (without the key) does not reveal file contents |

## 3. Technology Stack

| Component | Choice | Justification |
|---|---|---|
| Framework | Flask | Lightweight; does not hide security-relevant decisions (sessions, cookies, CSRF) behind heavy defaults, so they can be implemented and explained explicitly |
| Database | SQLite via SQLAlchemy | Sufficient for course-scale data; SQLAlchemy's parameterized queries remove the main SQL injection risk |
| Auth/session | Flask-Login | Well-maintained and handles session lifecycle without reinventing cookie/session handling from scratch |
| Forms/CSRF | Flask-WTF | Provides CSRF tokens for forms |
| Crypto | Python `cryptography` library, AES-GCM | Widely used implementation; AES-GCM provides authenticated encryption, so tampering with ciphertext is detected |
| Password hashing | Argon2 (`argon2-cffi`) | Modern, memory-hard password hashing algorithm resistant to GPU-based brute-force attacks |

**TLS plan:** locally, the app can be run with a development HTTPS certificate for testing. For a real deployment, the app would sit behind a reverse proxy (for example, nginx) terminating TLS with a valid certificate, with HSTS enabled so browsers use HTTPS.

## 4. Authentication and Session Model

- **Password storage:** hashed with Argon2; plaintext passwords are never logged or stored.
- **Cookie flags:** session cookies are set with `HttpOnly`, `Secure`, and `SameSite=Lax`. Flask-WTF CSRF tokens are used on state-changing routes.
- **Session lifetime:** sessions expire after a fixed idle period (e.g. 30 minutes of inactivity), after which the user must log in again.
- **Session fixation prevention:** before establishing an authenticated session, existing pre-login session state is cleared. After successful authentication, fresh authenticated session state is created. The application does not trust authentication-related values supplied before login.
- **Multi-factor authentication:** not planned for the initial scope; noted as a possible future extension.

## 5. Summary of Design Decisions

- Encryption is **server-side**, using a **server-managed key** (not derived from the user's password), so the server can decrypt files on behalf of an authenticated owner without requiring the user to hold or re-enter a separate decryption key on every request.
- Decryption happens **inline as part of** **`/download/<id>`**, not as a separate user-facing action.
- This model trades off a stronger "zero-knowledge" guarantee (where even a full server compromise couldn't expose file contents) for simplicity of implementation and use. This trade-off is explicitly captured as threats #10 and #11 above, with corresponding mitigations.
