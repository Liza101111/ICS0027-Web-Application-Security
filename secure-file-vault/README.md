# Secure File Vault

Secure Web-Based File Encryption and Management System developed for the
ICS0027 Web Application Security course at TalTech.

## Project Scope

Secure File Vault is a web application that allows registered users to securely
upload, store, download, and delete personal files.

Uploaded files are encrypted by the Flask application before they are written to
file storage. Files are stored only in encrypted form.

When a user downloads a file, the application first checks that the user is
authenticated and owns the requested file. The server then decrypts the file and
sends it to the user's browser over HTTPS.

The application uses server-side encryption with a server-managed encryption key.

## Planned Features

- User registration
- User login and logout
- Secure session management
- Upload personal files
- Encrypt files before storage
- View a list of the logged-in user's files
- Download and decrypt owned files
- Delete owned files
- Server-side authorization checks
- Input validation
- CSRF protection
- HTTPS/TLS for deployed communication

## Planned Routes

| Method | Route | Description |
|---|---|---|
| GET | `/` | Home page |
| GET, POST | `/register` | Register a new user |
| GET, POST | `/login` | Log in |
| POST | `/logout` | Log out |
| GET | `/files` | View the logged-in user's files |
| POST | `/upload` | Upload and encrypt a file |
| GET | `/download/<id>` | Download and decrypt an owned file |
| POST | `/delete/<id>` | Delete an owned file |

## Technology Stack

- Python 3.13
- Flask
- SQLite
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Python `cryptography` library
- AES-GCM for file encryption
- HTML and Jinja2 templates

## Encryption Model

The application uses server-side encryption.

When a file is uploaded:

1. The user is authenticated.
2. The Flask application receives the file.
3. The application encrypts the file using AES-GCM.
4. Only the encrypted file is written to file storage.
5. File metadata is stored in the database.

When a file is downloaded:

1. The user must be logged in.
2. The application verifies that the requested file belongs to that user.
3. The encrypted file is loaded from storage.
4. The application decrypts the file in memory.
5. The plaintext file is sent to the browser over HTTPS.

Decryption is part of the download operation and is not a separate user action.

The encryption key will be stored separately from the database and encrypted file
storage.

## Project Structure

```text
secure-file-vault/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── templates/
│   └── index.html
│
├── static/
├── storage/
│
└── docs/
    ├── architecture.png
    └── design.md