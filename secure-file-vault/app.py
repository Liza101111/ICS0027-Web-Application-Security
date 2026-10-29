import os
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from io import BytesIO

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, session, url_for, send_file
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect

from werkzeug.utils import secure_filename

from forms import LoginForm, LogoutForm, RegistrationForm, UploadForm, DeleteForm
from models import User, db, StoredFile
from crypto import encrypt_file, decrypt_file

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secure_file_vault.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

csrf = CSRFProtect(app) 

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

db.init_app(app)

password_hasher = PasswordHasher()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def home():
    logout_form = LogoutForm()
    return render_template("index.html", logout_form=logout_form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(
            username=form.username.data
        ).first()

        if existing_user:
            flash("Username already exists.")
            return render_template("register.html", form=form)

        password_hash = password_hasher.hash(form.password.data)

        user = User(
            username=form.username.data,
            password_hash=password_hash
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful.")
        return redirect(url_for("home"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data
        ).first()

        if user:
            try:
                password_hasher.verify(
                    user.password_hash,
                    form.password.data
                )

                session.clear()
                login_user(user)
                session.permanent = True

                flash("Login successful.")
                return redirect(url_for("home"))

            except VerifyMismatchError:
                pass

        flash("Invalid username or password.")

    return render_template("login.html", form=form)

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    form = LogoutForm()

    if form.validate_on_submit():
        logout_user()
        session.clear()
        flash("You have been logged out.")

    return redirect(url_for("home"))

@app.route("/files")
@login_required
def files():
    user_files = current_user.files
    delete_form = DeleteForm()

    return render_template(
        "files.html",
        files=user_files,
        delete_form=delete_form
    )

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        uploaded_file = form.file.data

        original_filename = secure_filename(uploaded_file.filename)

        if not original_filename:
            flash("Please select a valid file.")
            return render_template("upload.html", form=form)

        file_data = uploaded_file.read()

        encrypted_data, nonce = encrypt_file(file_data)

        stored_filename = f"{uuid4().hex}.bin"

        storage_folder = Path(app.root_path) / "storage"
        storage_folder.mkdir(exist_ok=True)

        file_path = storage_folder / stored_filename

        with open(file_path, "wb") as encrypted_file:
            encrypted_file.write(encrypted_data)

        stored_file = StoredFile(
            original_filename=original_filename,
            stored_filename=stored_filename,
            nonce=nonce,
            owner_id=current_user.id
        )

        db.session.add(stored_file)
        db.session.commit()

        flash("File uploaded and encrypted successfully.")

        return redirect(url_for("files"))

    return render_template("upload.html", form=form)

@app.route("/download/<int:file_id>")
@login_required
def download(file_id):
    stored_file = StoredFile.query.filter_by(
        id=file_id,
        owner_id=current_user.id
    ).first_or_404()

    storage_folder = Path(app.root_path) / "storage"
    file_path = storage_folder / stored_file.stored_filename

    with open(file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()

    decrypted_data = decrypt_file(
        encrypted_data,
        stored_file.nonce
    )

    return send_file(
        BytesIO(decrypted_data),
        as_attachment=True,
        download_name=stored_file.original_filename
    )

@app.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    form = DeleteForm()

    if form.validate_on_submit():
        stored_file = StoredFile.query.filter_by(
            id=file_id,
            owner_id=current_user.id
        ).first_or_404()

        storage_folder = Path(app.root_path) / "storage"
        file_path = storage_folder / stored_file.stored_filename

        if file_path.exists():
            file_path.unlink()

        db.session.delete(stored_file)
        db.session.commit()

        flash("File deleted successfully.")

    return redirect(url_for("files"))

if __name__ == '__main__':
    app.run(
        debug=True,
        ssl_context="adhoc"
    )