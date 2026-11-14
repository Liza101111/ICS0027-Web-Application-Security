# Secure File Vault

Secure Web-Based File Encryption and Management System developed for the ICS0027 Web Application Security course at TalTech.

## Features

The current application supports:

- User registration
- Argon2 password hashing
- Login and logout
- Secure session management
- CSRF protection
- Uploading files
- AES-GCM server-side file encryption
- Viewing the logged-in user's files
- Secure file download and decryption
- File deletion
- File ownership checks
- HTTPS/TLS in the development setup
- File type validation and 10 MB upload limit
- XSS defenses and HTTP security headers
- Custom secure error handling
- Structured security logging
- Security testing for CSRF, SQL injection, XSS, IDOR, upload validation, and error handling

Files are encrypted before they are written to `storage/`.

When a user downloads a file, the application checks that the file belongs to the logged-in user, decrypts it in memory, and returns it over HTTPS.

## Technology Stack

- Python 3.13
- Flask
- Flask-SQLAlchemy
- SQLite
- Flask-Login
- Flask-WTF
- Argon2
- Python `cryptography` library
- AES-GCM

## Project Structure

```text
secure-file-vault/
├── app.py
├── models.py
├── forms.py
├── crypto.py
├── security_logging.py
├── init_db.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── templates/
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── files.html
│   ├── upload.html
│   └── error.html
│
├── logs/
│   └── .gitkeep
│
├── storage/
│   └── .gitkeep
│
└── docs/
    ├── architecture.png
    ├── design.md
    ├── progress.md
    ├── security-tests.md
    └── report-draft.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Liza101111/ICS0027-Web-Application-Security.git
```

Enter the project directory:

```bash
cd ICS0027-Web-Application-Security/secure-file-vault
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation temporarily, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

and activate the environment again.

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Create the environment configuration

Create a `.env` file in the project directory.

Generate a Flask secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Generate a 32-byte AES encryption key:

```bash
python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
```

Add both generated values to `.env`:

```env
SECRET_KEY=your-generated-secret-key
ENCRYPTION_KEY=your-generated-encryption-key
```

Do not commit `.env` to Git.

`.env.example` contains only placeholder variable names.

### 5. Initialize the database

```bash
python init_db.py
```

This creates the local SQLite database.

### 6. Run the application

```bash
python app.py
```

The development server runs over HTTPS:

```text
https://127.0.0.1:5000
```

The application uses a temporary self-signed development certificate, so the browser may display a certificate warning.

For local development, choose **Advanced** and continue to `127.0.0.1`.

## Basic Usage

1. Register a user.
2. Log in.
3. Open **My Files**.
4. Upload a file.
5. The file is encrypted using AES-GCM before being written to `storage/`.
6. Downloading a file decrypts it in memory after an ownership check.
7. Files can also be deleted by their owner.
8. Log out when finished.

## Security Notes

- Passwords are stored using Argon2 hashes.
- Uploaded files are stored only in encrypted form.
- AES-GCM uses a unique random nonce for each encrypted file.
- The encryption key is loaded from an environment variable.
- File ownership is checked server-side before download or deletion.
- CSRF protection is enabled for state-changing requests.
- Session cookies use `HttpOnly`, `Secure`, and `SameSite=Lax`.
- Sessions expire after approximately 30 minutes of inactivity.
- File uploads are limited to 10 MB.
- Allowed upload extensions are `.txt`, `.pdf`, `.png`, `.jpg`, and `.jpeg`.
- Empty files and unsupported file types are rejected.
- Jinja auto-escaping and Content Security Policy are used as XSS defenses.
- Security headers include `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy`.
- Custom handlers provide generic responses for 400, 404, 413, and 500 errors.
- Security events are written as structured JSON to `logs/security.log`.
- Real security logs are excluded from Git.
- SQLAlchemy ORM is used instead of string-concatenated SQL.
- The application is served over HTTPS during development.
- Flask debug mode is disabled in the current security-testing configuration.

## Security Testing

Checkpoint 3 testing includes:

- Allowed and disallowed file upload tests
- Empty file validation
- Oversized upload / HTTP 413 test
- XSS payload tests
- CSRF request without a token
- SQL injection payload tests
- Cross-user download and delete (IDOR) tests
- Secure 404 and 413 error handling tests
- Structured security logging verification

Detailed results are available in:

```text
docs/security-tests.md
```

## Checkpoint Documentation

Checkpoint 1 design documentation:

```text
docs/design.md
```

System architecture diagram:

```text
docs/architecture.png
```

Checkpoint 2 progress note:

```text
docs/progress.md
```

Checkpoint 3 security test results:

```text
docs/security-tests.md
```

Checkpoint 3 draft report:

```text
docs/report-draft.md
```
