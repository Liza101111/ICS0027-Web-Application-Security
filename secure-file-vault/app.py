import os
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, session, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from forms import LoginForm, LogoutForm, RegistrationForm
from models import User, db

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secure_file_vault.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

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
    return render_template("files.html", files=user_files)

if __name__ == '__main__':
    app.run(debug=True)