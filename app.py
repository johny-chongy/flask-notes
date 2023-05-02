import os

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension

from models import connect_db, db, User
from forms import RegisterForm, LoginForm, CSRFProtectForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql:///notes")
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

@app.get('/')
def homepage():
    """Redirect to '/register'"""

    return redirect('/register')

@app.route('/register', methods=["GET", "POST"])
def register():
    """ Register user: produce form & handle form submission."""

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username,
                             password,
                             email,
                             first_name,
                             last_name)

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id

        return redirect(f"/users/{user.username}")

    else:
        return render_template("register.html", form=form)