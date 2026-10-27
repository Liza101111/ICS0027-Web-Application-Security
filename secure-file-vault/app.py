import os 

from dotenv import load_dotenv
from flask import Flask, render_template, flash, redirect, url_for
from argon2 import PasswordHasher

from forms import RegistrationForm
from models import User, db

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secure_file_vault.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
password_hasher = PasswordHasher()

@app.route('/')
def home():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)