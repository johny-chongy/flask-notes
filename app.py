import os

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension

from models import connect_db, db, User, Note
from forms import RegisterForm, LoginForm, CSRFProtectForm, NewNoteForm

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

    if check_authorization():
        current_user = User.query.get(session["user_id"])
        return redirect(f"/users/{current_user.username}")
    else:

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

    # user = User.query.filter_by(username=username).one()
    check_user = User.query.filter_by(username=username).one_or_none()

    if not check_authorization() or session["user_id"] != check_user.id:
        flash("Unauthorized Access")
        return redirect("/")
    else:
       return render_template("user.html", user=check_user, form=CSRFProtectForm())

@app.post("/logout")
def logout():
    """ Log user out and redirect to homepage """

    form = CSRFProtectForm()

    if form.validate_on_submit():
        session.pop("user_id", None)

    return redirect("/")


@app.route("/users/<username>/notes/add", methods=["GET", "POST"])
def add_note(username):
    """Display form to add a new note
    Handle submission and redirect to user page"""

    user = User.query.get(session["user_id"])
    check_user = User.query.filter_by(username=username).one()

    if not check_authorization() or session["user_id"] != check_user.id:
        flash("Unauthorized Access")
        return redirect("/")
    else:
       form=NewNoteForm()

       if form.validate_on_submit():
           title = form.title.data
           content = form.content.data

           new_note = Note(title=title,
                           content=content,
                           owner_id=user.id)

           db.session.add(new_note)
           db.session.commit()

           return redirect(f"/users/{user.username}")
       else:
           return render_template("new-note.html", user=user, form=form)


@app.post("/users/<username>/delete")
def delete_user(username):
    """ Delete user from database, log out and redirect to / """

    user = User.query.get(session["user_id"])
    check_user = User.query.filter_by(username=username).one()

    if not check_authorization() or session["user_id"] != check_user.id:
        flash("Unauthorized Access")
        return redirect("/")
    else:
    #    for note in user.notes:
    #        db.session.delete(note)
       Note.query.filter_by(owner_id=user.id).delete()
       db.session.delete(user)
       db.session.commit()

       session.pop("user_id", None)

       return redirect("/")

@app.route("/notes/<int:note_id>/update", methods=["GET", "POST"])
def update_note(note_id):
    """ Show page to update note and handle note update
        redirect /users/<username>
    """

    note = Note.query.get_or_404(note_id)
    form = NewNoteForm(obj=note)

    if not check_authorization() or session["user_id"] != note.owner_id:
        flash("Unauthorized Access")
        return redirect("/")
    else:
       if form.validate_on_submit():
           note.title = form.title.data
           note.content = form.content.data

           db.session.commit()

           return redirect(f"/users/{note.user.username}")
       else:
           return render_template("edit-note.html",
                                  form=form,
                                  note=note)


@app.post("/notes/<int:note_id>/delete")
def delete_note(note_id):
    """ Delete note from database and redirect to
        /users/<username>
    """
    note = Note.query.get_or_404(note_id)

    if not check_authorization() or session["user_id"] != note.owner_id:
        flash("Unauthorized Access")
        return redirect("/")
    else:
        username = note.user.username

        db.session.delete(note)
        db.session.commit()

        return redirect(f"/users/{username}")






def check_authorization():
    """Check if logged in user has authorization to route"""

    return "user_id" in session