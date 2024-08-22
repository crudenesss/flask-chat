"""routes for app"""

import os
import logging
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
)

from models import db, insert_user
from decorators import login_required, privilege_required
from forms import RegForm, LogForm, EditProfileForm

from utils.constants import (
    PROFILE_PICTURE_STORAGE_PATH,
    DEFAULT_PROFILE_PICTURE_PATH,
    WEBSITE_NAME,
)
from utils.helpers import (
    password_hash,
    password_verify,
    random_strings_generator,
    log_request,
    verify_image,
)

# Blueprint initialization
views_bp = Blueprint("routes", __name__)

# Init root logger
logger = logging.getLogger("gunicorn.access")


@views_bp.route("/", methods=["GET"])
@login_required
def main():
    """Root page where the chat operates"""

    log_request()

    # Retrieve messages from database
    messages = db["messages"]
    message_data = messages.find(
        skip=(
            0 if messages.count_documents({}) < 5 else messages.count_documents({}) - 5
        )
    )
    logger.debug(
        "%s messages retrieved from collection '%s'.",
        message_data.retrieved,
        message_data.collection,
    )

    user_data = db["users"].find_one({"username": session.get("username")})
    logger.debug("Info about user retrieved successfully")

    message_data_listed = list(message_data)
    return render_template(
        "index.html",
        s=session,
        msg_data=message_data_listed,
        usr_data=user_data,
        web_name=WEBSITE_NAME,
    )


# Registration page route
@views_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registration page"""

    log_request()

    # Signup form handle
    form = RegForm(request.form)

    if request.method != "POST":
        return render_template("register.html", form=form, session=session)

    # Here goes validating of WTForm inputs
    if not form.validate():
        logger.debug("Validation of registration form's input failed")
        return render_template("register.html", form=form, session=session)

    # If everything's ok, retrieve inputs from form
    username = form.username.data
    email = form.email.data
    password = password_hash(form.password.data)

    # Get collection's handler where we store data about registered users
    users = db["users"]

    # Check whether user tries to register with used credentials
    if users.find_one({"username": username}):
        flash("This username is already in use.", category="username_error")
        return redirect(request.url)
    if users.find_one({"email": email}):
        flash("This email is already in use.", category="email_error")
        return redirect(request.url)

    # Make sure insertion is completed without errors
    result = insert_user(users, username, email, password)
    if not result:
        logger.debug("New user registration failed")
        return render_template("error.html", session=session)

    logger.info("New user registration is completed successfully")

    return render_template("verification.html", session=session)


# Login page route
@views_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""

    log_request()

    # Login form handle
    form = LogForm(request.form)

    if request.method != "POST":
        return render_template("login.html", form=form, session=session)

    if not form.validate():
        logger.debug("Validation of registration form's input failed")
        return render_template("login.html", form=form, session=session)

    username = form.username.data
    password = form.password.data

    users = db["users"]

    # Check whether user exists in the database
    if not users.find_one({"username": username}):
        flash("Invalid username or password.")
        return render_template("login.html", form=form, session=session)

    # Retrieve correct password hash
    password_db = users.find_one({"username": username}).get("password")

    # Here goes verifying password hashes
    if not password_verify(password_db, password):
        flash("Invalid username or password.")
        logger.info("Login failed")
        return render_template("login.html", form=form, session=session)

    # Adding username to session, considering it as successful login,
    # redirecting to main page
    session["username"] = username

    logger.info("Login successful.")

    return redirect("/")


@views_bp.route("/logout")
@login_required
def logout():
    """Logout function"""

    log_request()
    session.pop("username", None)
    logger.info("User logged out")

    return redirect("/login")


@views_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Display profile page"""

    log_request()

    # Login form handle
    form = EditProfileForm(request.form)

    # Retrieve info from database about current user
    users = db["users"]
    user_data = users.find_one({"username": session["username"]})
    logger.debug("Info about user retrieved successfully")

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
            web_name=WEBSITE_NAME,
        )

    # Check if request contains data about file uploaded
    if request.files["file"].read() != b"":
        content = request.files["file"]
        content.seek(0)
        content_clean = content.read()
        content.seek(0)

        logger.debug("file content: %s", content_clean)

        # Check if received file's content is empty or if file was not chosen
        if content_clean == b"":
            flash("Empty upload file provided.")
            return redirect(request.url)

        if not verify_image(content_clean):
            flash("The file is inappropriate or corrupted. Try again")
            return redirect(request.url)

        # Generate new random name for file that will be stored
        picture_name = random_strings_generator()

        # Saving file to it's defined path
        with open(
            os.path.join(PROFILE_PICTURE_STORAGE_PATH, picture_name), "wb"
        ) as file:
            content.save(file)

        # remove old picture to avoid trashing
        if user_data.get("pp_name") is not None:
            os.remove(
                os.path.join(PROFILE_PICTURE_STORAGE_PATH, user_data.get("pp_name"))
            )
            logger.debug("previous picture is removed")

        # Update profile picture filename in database
        update_string = {"$set": {"pp_name": picture_name}}

        result = users.update_one(user_data, update_string)
        if not result:
            logger.debug("Data update failed")
            return render_template("error.html", session=session)

        return render_template(
            "profile.html",
            form=form,
            session=session,
            data=user_data,
        )

    if not form.validate():
        logger.debug("Validation of profile edit form's input failed")
        return redirect(request.url)

    username = form.username.data
    email = form.email.data

    # Create dictionary for values that were changed
    newvalues = {}

    for key, data in (("username", username), ("email", email)):
        if data == user_data[key]:
            continue

        # Check whether user tries to replace info with used credentials
        if users.find_one({key: data}):
            flash(f"This {data} is already in use.")

            return render_template(
                "profile.html",
                form=form,
                session=session,
                data=user_data,
            )

        newvalues[key] = data

    # Check whether the values need to be updated
    if len(newvalues) > 0:
        logger.debug("Values to update: %s", len(newvalues))
        update_string = {"$set": newvalues}

        result = users.update_one(user_data, update_string)
        if not result:
            logger.debug("Data update failed")
            return render_template("error.html", session=session)

        logger.info("User info updated successfully")
        session["username"] = username
        user_data = users.find_one(result.upserted_id)

    return render_template(
        "profile.html",
        form=form,
        session=session,
        data=user_data,
        web_name=WEBSITE_NAME,
    )


@views_bp.route("/profile-picture", methods=["GET"])
@login_required
def profile_picture():
    """Retrieve users' profile pictures"""

    log_request()

    username = session.get("username")
    profile_picture_name = db["users"].find_one({"username": username}).get("pp_name")

    # Check if user has his profile picture set -
    # if not - return path with default picture
    if profile_picture_name is None:
        logger.debug("No picture to retrieve: set to default")
        return send_file(DEFAULT_PROFILE_PICTURE_PATH)
    else:
        return send_file(
            os.path.join(PROFILE_PICTURE_STORAGE_PATH, profile_picture_name)
        )


@views_bp.route("/manage")
@privilege_required
def manage_chat():
    """Page to handle chat settings"""

    log_request()

    return "Welcome to admin panel! Under maintainance. Stand by"
