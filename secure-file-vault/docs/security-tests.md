# Security Test Results

This document records the security tests performed on the Secure File Vault application.

## 1. File Upload Validation

### Test: Allowed File Type

**Input:** Valid `.txt`, `.pdf`, `.jpg`, `.jpeg`, or `.png` file.

**Expected result:** File is accepted, encrypted, and stored.

**Actual result:** Allowed file types were uploaded successfully.

**Result:** PASS

### Test: Disallowed File Type

**Input:** File with an unsupported extension such as `.exe` or `.php`.

**Expected result:** Upload is rejected.

**Actual result:** The application rejected the unsupported file type.

**Result:** PASS

### Test: Empty File

**Input:** Empty file.

**Expected result:** Upload is rejected.

**Actual result:** The application rejected the empty file.

**Result:** PASS

---

## 2. Security Headers and XSS Protection

### Test: Security Headers

The application response was inspected using Chrome Developer Tools.

The following headers were present:

- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

**Expected result:** Security headers are included in HTTP responses.

**Actual result:** All configured security headers were present.

**Result:** PASS

### Test: Cross-Site Scripting (XSS)

**Payload:**

```text
<script>alert(1)</script>
```

A second payload was also considered:

```text
<img src=x onerror=alert(1)>
```

**Expected result:** JavaScript must not execute.

**Actual result:** No JavaScript alert was executed. Jinja template escaping and the Content Security Policy prevent injected script execution.

**Result:** PASS

---

## 3. CSRF Protection

### Test: POST Request Without CSRF Token

A forged POST request was sent directly to the login endpoint without a CSRF token.

Example request:

```text
POST /login
username=testuser
password=FakePassword123
```

No CSRF token was included.

**Expected result:** The server rejects the request.

**Actual result:** The server returned:

```text
HTTP 400 Bad Request
```

The security log also recorded the rejected CSRF validation attempt.

**Result:** PASS

Normal requests submitted through the application's forms include a valid CSRF token and continue to work correctly.

---

## 4. SQL Injection Protection

### Test: Login SQL Injection

The following values were entered into the username field:

```text
' OR 1=1 --
```

```text
admin' --
```

```text
'
```

**Expected result:** Input is treated as data rather than SQL syntax. Authentication must not be bypassed.

**Actual result:** Login was rejected with an invalid username/password response. No SQL errors, database information, or stack traces were displayed.

**Result:** PASS

The application uses SQLAlchemy ORM queries rather than constructing SQL commands by concatenating user input.

Example:

```python
User.query.filter_by(username=form.username.data).first()
```

---

## 5. Broken Access Control / IDOR

Two separate user accounts were used for this test.

### Test: Download Another User's File

1. User A uploaded a file.
2. User A logged out.
3. User B logged in.
4. User B manually requested User A's file ID using:

```text
GET /download/<file_id>
```

**Expected result:** User B must not receive User A's file.

**Actual result:** The application returned the custom `404 Not Found` page and the file was not downloaded.

The security log recorded the access attempt as denied.

**Result:** PASS

### Test: Delete Another User's File

1. User B remained logged in.
2. A valid delete form belonging to User B was used so that a valid CSRF token was present.
3. The form action was changed to target User A's file ID.
4. The modified delete request was submitted.

Example:

```text
POST /delete/<user_a_file_id>
```

**Expected result:** User B must not be able to delete User A's file.

**Actual result:** The application returned `404 Not Found`. User A's file remained available.

The security log recorded the delete attempt as denied.

**Result:** PASS

---

## 6. Secure Error Handling

### Test: Nonexistent Resource

A nonexistent URL was requested.

**Expected result:** A generic error page is displayed without exposing application internals.

**Actual result:** The custom `404` page was displayed.

**Result:** PASS

### Test: Oversized Upload

A file larger than the configured 10 MB maximum upload size was submitted.

**Expected result:** Upload is rejected with a controlled error response.

**Actual result:** The application returned the custom `413` error page.

**Result:** PASS

The application also has generic handlers for HTTP `400` and `500` errors. Debug mode is disabled so internal stack traces are not exposed to users.

---

## 7. Structured Security Logging

Security-relevant actions are written to:

```text
logs/security.log
```

Logs use structured JSON records containing fields such as:

```json
{
  "timestamp": "2026-11-14T08:50:14+00:00",
  "event": "login",
  "user_id": 2,
  "source_ip": "127.0.0.1",
  "outcome": "success"
}
```

Recorded events include:

- successful and failed logins
- logout
- file upload
- file download
- file deletion
- denied file access
- CSRF validation failures

Passwords, encryption keys, CSRF tokens, session cookies, and file contents are not written to the security log.

**Result:** PASS

---

## Summary

| Security Test | Result |
|---|---|
| Allowed file upload | PASS |
| Invalid file type rejected | PASS |
| Empty file rejected | PASS |
| Security headers | PASS |
| XSS protection | PASS |
| CSRF protection | PASS |
| SQL injection protection | PASS |
| Cross-user download / IDOR | PASS |
| Cross-user delete / IDOR | PASS |
| Secure error handling | PASS |
| Structured security logging | PASS |

The implemented controls successfully blocked the tested attack vectors without exposing sensitive application or database information.