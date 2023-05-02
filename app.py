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

@app.get("/")
def homepage():
    """Redirect to '/register'"""

    return redirect("/register")

@app.route("/register", methods=["GET", "POST"])
def register():
    """ Register user: produce registration form & handle form submission."""

    #TODO: if user logged in, redirect to user page

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

        # TODO: try and add user: works, cool // error: handle it
        # catch error

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id

        return redirect(f"/users/{user.username}")

    else:
        return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    """ Login user: produce login form & handle form submission. """

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        pwd = form.password.data

        user = User.verify(username, pwd)

        if user:
            session["user_id"] = user.id
            flash("Login successful!")
            return redirect(f"/users/{user.username}")

        else:
            form.username.errors = ["Invalid name/password"]

    return render_template("login.html", form=form)

@app.get("/users/<username>")
def user_details(username):
    """ Show user detail for specific user
        Make sure logged in user can see
    """
    if "user_id" not in session:
        flash("You must be logged in!")
        return redirect("/login")
    else:
        user = User.query.get(session["user_id"])
        if user.username == username:
            return render_template("user.html", user=user, form=CSRFProtectForm())
        else:
            #TODO: check demo code for flash msg
            flash("Unauthorized access")
            return redirect(f"/users/{user.username}")

@app.post("/logout")
def logout():
    """ Log user out and redirect to homepage """

    form = CSRFProtectForm()

    if form.validate_on_submit():
        session.pop("user_id", None)

    return redirect("/")


