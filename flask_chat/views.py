"""routes for app"""

import os
from functools import wraps
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
)

from constants import PROFILE_PICTURE_STORAGE_PATH, DEFAULT_PROFILE_PICTURE_PATH
from forms import RegForm, LogForm, EditProfileForm, SettingsEditProfileForm
from functions import password_hash, password_verify, filename_generator
from models import db, insert_user

# TODO: logging (debug, info, error)
# TODO: add comments
# TODO: add image validation
# TODO: check mongod.conf

# Blueprint initialization
views_bp = Blueprint("routes", __name__)


def login_required(f):
    """Checks if the user is logged in"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session.keys():
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@views_bp.route("/", methods=["GET"])
@login_required
def main():
    """Root page where the chat operates"""

    # Retrieve messages from database
    messages = db["messages"]
    message_data = list(
        messages.find(
            skip=(
                0
                if messages.count_documents({}) < 5
                else messages.count_documents({}) - 5
            )
        )
    )

    user_data = db["users"].find_one({"username": session.get("username")})

    return render_template(
        "index.html", s=session, msg_data=message_data, usr_data=user_data
    )


# Registration page route
@views_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registration page"""

    # Signup form handle
    form = RegForm(request.form)

    if request.method != "POST":
        return render_template("register.html", form=form, session=session)

    # Here goes validating of WTForm inputs
    if not form.validate():
        return render_template("register.html", form=form, session=session)

    # If everything's ok, retrieve inputs from form
    username = form.username.data
    email = form.email.data
    password = password_hash(form.password.data)

    # Get collection's handler where we store data about registered users
    users = db["users"]

    # Check whether user tries to register with used credentials
    if users.find_one({"username": session.get("username")}):
        flash("This username is already in use.", category="username_error")
        return render_template("register.html", form=form, session=session)
    if users.find_one({"email": session.get("email")}):
        flash("This email is already in use.", category="email_error")
        return render_template("register.html", form=form, session=session)

    # Make sure insertion is completed without errors
    result = insert_user(users, username, email, password)
    if not result:
        return render_template("error.html", session=session)

    return render_template("verification.html", session=session)


# Login page route
@views_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""

    # Login form handle
    form = LogForm(request.form)

    if request.method != "POST":
        return render_template("login.html", form=form, session=session)

    if not form.validate():
        return render_template("login.html", form=form, session=session)

    username = form.username.data
    password = form.password.data

    users = db["users"]

    # Check whether user exists in the database
    if not users.find_one({"username": session.get("username")}):
        flash("Invalid login or password.", category="login_error")
        return render_template("login.html", form=form, session=session)

    # Retrieve correct password hash
    password_db = users.find_one({"username": username}).get("password")

    # Here goes verifying password hashes
    if not password_verify(password_db, password):
        flash("Invalid login or password.", category="login_error")
        return render_template("login.html", form=form, session=session)

    # Adding username to session, considering it as successful login,
    # redirecting to main page
    session["username"] = username
    return redirect("/")


@views_bp.route("/logout")
@login_required
def logout():
    """Logout function"""

    session.pop("username", None)
    return redirect("/login")


@views_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Display profile page"""

    # Login form handle
    form = EditProfileForm(request.form)

    # Retrieve info from database about current user
    users = db["users"]
    user_data = users.find_one({"username": session["username"]})

    if request.method != "POST":

        # Placeholder values from database to display in profile
        for field in form:
            if user_data.get(field.name):
                field.data = user_data.get(field.name)
            else:
                field.data = ""

        return render_template(
            "profile.html",
            form=form,
            session=session,
            data=user_data,
        )

    if not form.validate():

        return render_template(
            "profile.html",
            form=form,
            session=session,
            data=user_data,
        )

    username = form.username.data
    email = form.email.data

    # Create dictionary for values that were changed
    newvalues = dict()

    if username != user_data["username"]:
        # Check whether user tries to replace info with used username
        if users.find_one({"username": username}):
            flash("This username is already in use.", category="username_error")

            return render_template(
                "profile.html",
                form=form,
                session=session,
                data=user_data,
            )
        else:
            newvalues["username"] = username

    if email != user_data["email"]:
        # Same with email
        if users.find_one({"email": email}):
            flash("This email is already in use.", category="email_error")

            return render_template(
                "profile.html",
                form=form,
                session=session,
                data=user_data,
            )
        else:
            newvalues["email"] = email

    # Check whether the values need to be updated
    if len(newvalues) > 0:

        update_string = {"$set": newvalues}

        result = users.update_one(user_data, update_string)
        if not result:
            return render_template("error.html", session=session)

        session["username"] = username
        user_data = users.find_one(result.upserted_id)

    return render_template("profile.html", form=form, session=session, data=user_data)


@views_bp.route("/profile-picture", methods=["GET"])
@login_required
def profile_picture():
    """Retrieve users' profile pictures"""

    username = session.get("username")
    profile_picture_name = db["users"].find_one({"username": username}).get("pp_name")

    # Check if user has his profile picture set -
    # if not - return path with default picture
    if profile_picture_name is None:
        return send_file(DEFAULT_PROFILE_PICTURE_PATH)
    else:
        return send_file(
            os.path.join(PROFILE_PICTURE_STORAGE_PATH, profile_picture_name)
        )


@views_bp.route("/settings/profile", methods=["GET", "POST"])
@login_required
def settings_profile():
    """Page to change profile data"""

    # Login form handle
    form = SettingsEditProfileForm(request.form)

    # Retrieve info from database about current user
    users = db["users"]
    user_data = users.find_one({"username": session["username"]})

    if request.method != "POST":

        # Placeholder values from database to display in profile
        for field in form:
            try:
                field.data = user_data[field.name]
            except KeyError:
                field.data = ""

        return render_template(
            "settings_profile.html",
            form=form,
            session=session,
            data=user_data,
        )

    # Check if request contains data about file uploaded
    if "file" in request.files:
        content = request.files["file"]

        # Check if received file's content is empty or if file was not chosen
        if content == "":
            flash("No upload file provided.")
            return redirect(request.url)

        # Generate new random name for file that will be stored
        picture_name = filename_generator()

        # Saving file to it's defined path
        with open(
            os.path.join(PROFILE_PICTURE_STORAGE_PATH, picture_name), "wb"
        ) as file:
            content.save(file)

        # Update profile picture filename in database
        update_string = {"$set": {"pp_name": picture_name}}

        result = users.update_one(user_data, update_string)
        if not result:
            return render_template("error.html", session=session)

        return render_template(
            "settings_profile.html",
            form=form,
            session=session,
            data=user_data,
        )

    if not form.validate():

        return render_template(
            "settings_profile.html",
            form=form,
            session=session,
            data=user_data,
        )

    username = form.username.data
    email = form.email.data

    # Create dictionary for values that were changed
    newvalues = dict()

    if username != user_data["username"]:
        # Check whether user tries to replace info with used username
        if users.find_one({"username": username}):
            flash("This username is already in use.", category="username_error")

            return render_template(
                "settings_profile.html",
                form=form,
                session=session,
                data=user_data,
            )
        else:
            newvalues["username"] = username

    if email != user_data["email"]:
        # Same with email
        if users.find_one({"email": email}):
            flash("This email is already in use.", category="email_error")

            return render_template(
                "settings_profile.html",
                form=form,
                session=session,
                data=user_data,
            )
        else:
            newvalues["email"] = email

    # Check whether the values need to be updated
    if len(newvalues) > 0:

        update_string = {"$set": newvalues}

        result = users.update_one(user_data, update_string)
        if not result:
            return render_template("error.html", session=session)

        session["username"] = username
        user_data = users.find_one(result.upserted_id)

    return render_template(
        "settings_profile.html",
        form=form,
        session=session,
        data=user_data,
    )
