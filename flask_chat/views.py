"""routes for app"""

import os
import logging
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
)
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from bson import ObjectId

from models import db, insert_user, retrieve_messages_readable
from decorators import privilege_required
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
@jwt_required()
def main():
    """Root page where the chat operates"""

    log_request()

    user_id = get_jwt_identity()
    logger.debug("Current user: %s", user_id)

    # Retrieve messages from database
    message_data = retrieve_messages_readable(db["messages"])

    logger.debug(
        "%s messages retrieved from collection 'messages'.",
        len(message_data)
    )

    user_data = db["users"].find_one({"_id": ObjectId(user_id)})
    logger.debug("Info about user retrieved successfully: %s", user_data)

    return render_template(
        "index.html",
        msg_data=message_data,
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
        return render_template("register.html", form=form)

    # Here goes validating of WTForm inputs
    if not form.validate():
        logger.debug("Validation of registration form's input failed")
        return render_template("register.html", form=form)

    # If everything's ok, retrieve inputs from form
    username = form.username.data
    email = form.email.data
    password = password_hash(form.password.data)

    # Get collection's handler where we store data about registered users
    users = db["users"]

    # Check whether user tries to register with used credentials
    if users.find_one({"username": username}) or users.find_one({"email": email}):
        flash("These credentials are already in use.")
        return redirect(request.url)

    # Make sure insertion is completed without errors
    result = insert_user(users, username, email, password)
    if not result:
        logger.debug("New user registration failed")
        return render_template("error.html")

    logger.info("New user registration is completed successfully")

    return redirect("/login")


# Login page route
@views_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""

    log_request()

    # Login form handle
    form = LogForm(request.form)

    if request.method != "POST":
        return render_template("login.html", form=form)

    if not form.validate():
        logger.debug("Validation of registration form's input failed")
        return render_template("login.html", form=form)

    username = form.username.data
    password = form.password.data

    users = db["users"]

    # Check whether user exists in the database
    if not users.find_one({"username": username}):
        flash("Invalid username or password.")
        return render_template("login.html", form=form)

    # Retrieve correct password hash
    user_data = users.find_one({"username": username})

    # Here goes verifying password hashes
    if not password_verify(user_data.get("password"), password):
        flash("Invalid username or password.")
        logger.info("Login failed")
        return render_template("login.html", form=form)

    # Creating session token for user, considering it as successful login,
    # redirecting to main page
    response = redirect("/")
    access_token = create_access_token(identity=str(user_data.get("_id")))
    set_access_cookies(response, access_token)

    logger.info("Login successful.")

    return response


@views_bp.route("/logout")
@jwt_required()
def logout():
    """Logout function"""

    log_request()
    response = redirect("/login")
    unset_jwt_cookies(response)

    logger.info("User logged out")

    return response


@views_bp.route("/profile/<user>", methods=["GET", "POST"])
@jwt_required()
def profile(user):
    """Display profile page"""

    log_request()

    users = db["users"]

    user_id = get_jwt_identity()
    current_user = users.find_one({"_id": ObjectId(user_id)}).get("username")
    csrf_token = request.cookies.get("csrf_access_token")

    logger.debug("Current user: %s", current_user)

    # Login form handle
    form = EditProfileForm(request.form)

    # Retrieve info from database about user

    if not users.find_one({"username": user}):
        return abort(404)

    logger.debug("Info about user retrieved successfully")
    user_data = users.find_one({"username": user})

    if request.method != "POST":

        # Placeholder values from database to display in profile
        for field in form:
            if field.name == "csrf_token":
                logger.debug("CSRF token is set")
                field.data = csrf_token
            elif user_data.get(field.name):
                field.data = user_data.get(field.name)
            # If the field from user's document is empty
            else:
                field.data = ""

        return render_template(
            "profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
            web_name=WEBSITE_NAME,
        )

    # Check if request contains data about file uploaded
    if request.files["file"].read() != b"":
        content = request.files["file"]
        content.seek(0)
        content_clean = content.read()
        content.seek(0)

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
            return render_template("error.html")

        return render_template(
            "profile.html",
            form=form,
            current_user=current_user,
            csrf_token=csrf_token,
            data=user_data,
        )

    if not form.validate():
        logger.debug("Validation of profile edit form's input failed")
        return redirect(request.url)

    username = form.username.data

    # Create dictionary for values that were changed
    newvalues = {}

    for field in form:

        # Exclude hidden csrf_token field from cycle
        if field.name == "csrf_token":
            continue

        # Check fields that may be repeatable
        if field.name not in ["username", "email"]:
            newvalues[field.name] = field.data
            continue

        # Check if provided data is the same as previous
        if field.data == user_data[field.name]:
            continue

        # Check whether user tries to replace username/email with used credentials
        if users.find_one({field.name: field.data}):
            flash("These credentials are already in use.")

            return render_template(
                "profile.html",
                form=form,
                current_user=current_user,
                csrf_token=csrf_token,
                data=user_data,
            )

        newvalues[field.name] = field.data

    # Check whether the values need to be updated
    if len(newvalues) > 0:
        logger.debug("Values to update: %s", len(newvalues))
        update_string = {"$set": newvalues}

        result = users.update_one(user_data, update_string)
        if not result:
            logger.debug("Data update failed")
            return render_template("error.html")

        logger.info("User info updated successfully")
        user_data = users.find_one(result.upserted_id)

    return redirect(f"/profile/{username}")


@views_bp.route("/profile-picture/<user>", methods=["GET"])
@jwt_required()
def profile_picture(user):
    """Retrieve users' profile pictures"""

    log_request()

    profile_picture_name = db["users"].find_one({"username": user}).get("pp_name")

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
