# Secure File Vault
## Secure Web-Based File Encryption and Management System

## 1. Introduction

Secure File Vault is a web application developed for the ICS0027 Web Application Security course. The purpose of the application is to allow authenticated users to upload, store, download, and delete files while applying security controls against common web application vulnerabilities.

The application was designed with the assumption that uploaded files may contain sensitive information. Files are therefore encrypted before being stored on the server, and access to each file is restricted to its owner.

The main security goals of the project are:

- protect user accounts with secure authentication;
- protect uploaded files using authenticated encryption;
- prevent unauthorized access to files belonging to other users;
- protect state-changing requests against Cross-Site Request Forgery (CSRF);
- prevent Cross-Site Scripting (XSS);
- prevent SQL injection;
- validate uploaded files and restrict unsafe file types;
- provide secure error handling without exposing internal application information;
- log important security events without storing sensitive secrets.

The application is implemented using Python and Flask with SQLite as the database.

---

## 2. Implementation

### 2.1 Technology Stack

The application uses the following technologies:

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- SQLite
- Argon2
- Python `cryptography` library
- AES-GCM authenticated encryption
- HTML/Jinja templates

The project is structured so that authentication, forms, database models, encryption, and security logging are separated into different modules where appropriate.

---

### 2.2 User Authentication

Users can register with a username and password.

Passwords are never stored in plaintext. Passwords are hashed using Argon2 before being stored in the database.

Example:

```python
password_hash = password_hasher.hash(form.password.data)
```

During login, the submitted password is verified against the stored Argon2 password hash.

```python
password_hasher.verify(
    user.password_hash,
    form.password.data
)
```

If authentication fails, the application displays a generic message:

```text
Invalid username or password.
```

The application does not reveal whether the username or password was incorrect.

After successful login, the existing session is cleared before creating the authenticated session.

Session-related security settings include:

```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
```

The authenticated session also has a limited lifetime.

---

### 2.3 File Upload and Validation

Only authenticated users can upload files.

The application currently allows the following file extensions:

- `.txt`
- `.pdf`
- `.png`
- `.jpg`
- `.jpeg`

Unsupported file extensions are rejected.

Uploaded filenames are processed using:

```python
secure_filename()
```

This reduces risks caused by unsafe filenames and path manipulation.

Empty files are also rejected.

The application has a maximum request size of 10 MB:

```python
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
```

Files larger than this limit are rejected with HTTP status `413`.

Uploaded files are not stored using their original filename. Instead, a random UUID-based filename is generated:

```python
stored_filename = f"{uuid4().hex}.bin"
```

This prevents users from controlling the path or server-side filename used for encrypted storage.

---

### 2.4 File Encryption

Uploaded file contents are encrypted before being written to disk.

The application uses AES-GCM authenticated encryption with a 256-bit encryption key.

For every file, a new random 12-byte nonce is generated:

```python
nonce = os.urandom(12)
```

Encryption is performed using:

```python
aesgcm.encrypt(nonce, file_data, None)
```

Only encrypted file contents are stored in the `storage` directory.

The database stores metadata including:

- original filename;
- generated encrypted filename;
- AES-GCM nonce;
- owner ID.

The encryption key is stored outside the source code in an environment variable:

```text
ENCRYPTION_KEY
```

The real encryption key is stored in `.env`, which is excluded from Git.

`.env.example` contains only placeholder values.

---

### 2.5 File Download

When a user downloads a file, the application first verifies file ownership.

The database query includes both the file ID and the authenticated user's ID:

```python
StoredFile.query.filter_by(
    id=file_id,
    owner_id=current_user.id
).first()
```

If the requested file does not belong to the current user, the request is rejected with a `404` response.

If access is allowed, the encrypted data is read from disk and decrypted using AES-GCM.

The decrypted file is then returned to the authenticated user as a downloadable attachment.

Plaintext files are not permanently written back to the server's storage directory during download.

---

### 2.6 File Deletion

Deletion is implemented as a POST request and is protected by authentication and CSRF protection.

Before deleting a file, the application verifies that the requested file belongs to the authenticated user.

If ownership verification succeeds:

1. the encrypted file is deleted from server storage;
2. the corresponding database record is deleted.

If ownership verification fails, the request returns a generic `404` response.

---

### 2.7 CSRF Protection

The application uses Flask-WTF CSRF protection globally:

```python
csrf = CSRFProtect(app)
```

State-changing forms include hidden CSRF tokens using:

```html
{{ form.hidden_tag() }}
```

This protection is used for operations including:

- login;
- registration;
- upload;
- logout;
- file deletion.

Requests without a valid CSRF token are rejected.

A custom CSRF error handler returns a generic `400 Bad Request` response and records the rejected request in the security log.

---

### 2.8 XSS Protection and Security Headers

Jinja's default HTML escaping is used when displaying user-controlled information such as usernames and original filenames.

Templates do not intentionally mark user-controlled values as safe HTML.

The application also adds HTTP security headers to responses.

The configured Content Security Policy includes:

```text
default-src 'self'
script-src 'self'
style-src 'self' 'unsafe-inline'
img-src 'self' data:
object-src 'none'
base-uri 'self'
frame-ancestors 'none'
form-action 'self'
```

Additional headers include:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
```

These headers provide additional protection against XSS, MIME sniffing, clickjacking, and information leakage through referrer data.

---

### 2.9 SQL Injection Protection

Database access is implemented using SQLAlchemy ORM.

For example:

```python
User.query.filter_by(
    username=form.username.data
).first()
```

and:

```python
StoredFile.query.filter_by(
    id=file_id,
    owner_id=current_user.id
).first()
```

The application does not build SQL queries by concatenating user-controlled strings.

SQLAlchemy therefore treats user input as parameter values rather than executable SQL syntax.

---

### 2.10 Secure Error Handling

The application provides custom handlers for common errors including:

- `400 Bad Request`
- `404 Not Found`
- `413 Request Entity Too Large`
- `500 Internal Server Error`

Error pages display generic messages rather than internal exception details.

For example:

```text
The requested resource was not found.
```

The application does not expose database errors, Python stack traces, encryption information, or filesystem paths to users.

Debug mode is disabled for security testing.

The `500` handler also performs:

```python
db.session.rollback()
```

to return the SQLAlchemy session to a usable state following a database-related failure.

---

### 2.11 Structured Security Logging

The application writes security-related events to:

```text
logs/security.log
```

Events are stored as structured JSON.

Example:

```json
{
  "timestamp": "2026-11-14T08:50:14+00:00",
  "event": "login",
  "user_id": 2,
  "source_ip": "127.0.0.1",
  "outcome": "success"
}
```

Logged events include:

- successful login;
- failed login;
- logout;
- file upload;
- file download;
- file deletion;
- denied file access;
- rejected CSRF requests.

The application deliberately avoids logging sensitive values such as:

- passwords;
- password hashes;
- encryption keys;
- session cookies;
- CSRF tokens;
- plaintext file contents.

Security log files are excluded from Git.

---

## 3. Security Analysis

### 3.1 Threat Model

The main threats considered during development include:

- SQL injection;
- Cross-Site Scripting;
- Cross-Site Request Forgery;
- broken authentication;
- insecure session handling;
- broken access control;
- Insecure Direct Object Reference attacks;
- malicious file uploads;
- path traversal;
- cryptographic failures;
- encryption-key exposure;
- information leakage through errors;
- insecure logging;
- clickjacking;
- security misconfiguration.

The server-side Flask application is treated as a trusted component, while browser input is considered untrusted.

The encryption key must remain separate from the database and encrypted file storage. This means that obtaining only the database or encrypted storage files should not directly provide plaintext file contents.

---

### 3.2 File Upload Security Testing

Valid file types including TXT, PDF, JPG, JPEG, and PNG were accepted.

Unsupported extensions such as `.exe` and `.php` were rejected.

Empty files were rejected.

A test file larger than 10 MB was uploaded and correctly rejected with the custom `413` error response.

Result: **PASS**

---

### 3.3 XSS Testing

XSS-style payloads were tested against user-controlled input.

Example:

```text
<script>alert(1)</script>
```

The payload did not execute as JavaScript.

Jinja escaping and the configured Content Security Policy provide multiple layers of protection.

The configured security headers were also verified using Chrome Developer Tools.

Result: **PASS**

---

### 3.4 CSRF Testing

A POST request was deliberately sent without a CSRF token.

Example target:

```text
POST /login
```

The server rejected the request with:

```text
HTTP 400 Bad Request
```

The rejection was also recorded in the structured security log.

Normal browser forms containing valid CSRF tokens continued to work.

Result: **PASS**

---

### 3.5 SQL Injection Testing

Several SQL injection payloads were tested in the login form.

Examples:

```text
' OR 1=1 --
```

```text
admin' --
```

```text
'
```

The application did not authenticate the attacker and did not display SQL errors or database information.

The values were treated as normal input by SQLAlchemy rather than executable SQL syntax.

Result: **PASS**

---

### 3.6 Broken Access Control / IDOR Testing

Two different user accounts were used.

User A uploaded a file.

User B then manually requested User A's file ID through the download route.

Example:

```text
GET /download/<user_a_file_id>
```

The request returned `404`, and User B did not receive the file.

A second test targeted file deletion.

User B submitted a valid CSRF-protected delete form while changing the destination file ID to User A's file ID.

Example:

```text
POST /delete/<user_a_file_id>
```

The request was rejected with `404`.

User A's file remained available and was not deleted.

The denied access attempts were also recorded in the structured security log.

Result: **PASS**

---

### 3.7 Error Handling Testing

A nonexistent application route was requested.

The application displayed the custom `404` error page and did not expose internal information.

A file larger than 10 MB was uploaded.

The application displayed the custom `413` error page.

A CSRF failure also produced the controlled `400` response.

Result: **PASS**

---

### 3.8 Security Logging Testing

Security events were generated by performing:

- failed login;
- successful login;
- upload;
- download;
- delete;
- unauthorized file access;
- CSRF failure;
- logout.

The resulting `security.log` entries contained structured fields including:

- timestamp;
- event;
- user ID;
- source IP;
- outcome.

Sensitive secrets were not present in the log.

Result: **PASS**

---

## 4. Conclusion

The Secure File Vault application implements the main functional and security requirements defined for the project.

Authenticated users can register, log in, upload files, download their own files, and delete their own files.

Uploaded files are encrypted using AES-GCM before being stored. Passwords are protected using Argon2 hashing, and encryption keys and application secrets are stored outside the source code.

The application implements multiple web security controls including CSRF protection, XSS defenses, Content Security Policy, secure session settings, SQLAlchemy parameterized database access, file validation, per-user authorization checks, secure error handling, and structured security logging.

Security testing demonstrated that attempted CSRF, SQL injection, XSS, oversized uploads, and cross-user file access were blocked by the implemented controls.

The current application therefore provides a secure foundation for the Secure File Vault project. Further improvements could include stronger deployment configuration, automated security tests, stricter Content Security Policy rules, rate limiting for authentication attempts, and additional monitoring for suspicious activity.