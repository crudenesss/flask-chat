"""main application file"""

import logging
from os import getenv
from datetime import timedelta
from bson import ObjectId
from flask import Flask, redirect, render_template
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required

# from forms import MessageForm
from utils.constants import MSG_LOAD_BATCH, MSG_LENGTH, SESSION_EXPIRY
from views import views_bp
from models import db, insert_message

# Define app
app = Flask(__name__)

# Define app configurations
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=SESSION_EXPIRY)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_CSRF_CHECK_FORM"] = True

app.register_blueprint(views_bp)

# Create socket handle
socket = SocketIO(app)
socket.init_app(app, cors_allowed_origins="*")

# Create jwt manager handler
jwt = JWTManager(app)
jwt.init_app(app)

logger = logging.getLogger("gunicorn.access")


# Custom exceptions for error responses
@jwt.unauthorized_loader
def unauthorized_loader_error(error):
    """Custom handler for abscence of jwt token when accessing an endpoint"""
    logger.debug(error)
    return redirect("/login")


@jwt.expired_token_loader
def expired_token_loader_error(token):
    """Custom handler for expired token provided when accesssing an endpoint"""
    token_type = token['type']
    logger.debug("The %s token has expired", token_type)
    return redirect("/login")


@jwt.invalid_token_loader
def invalid_token_loader_error(error):
    """Custom handler for invalid jwt token provided when accessing an endpoint"""
    logger.error(error)
    return redirect("/login")


@socket.on("message")
@jwt_required()
def handle_message(msg):
    """handle initial messages sent via websocket and saves them to database"""

    logger.debug("Message received")

    # If recevived message length is more than required
    if len(msg.get("message")) > MSG_LENGTH:
        logger.debug("Message length limit exceeded")
        socket.emit("message_too_long", {"msg_length": MSG_LENGTH})
        logger.debug("Event received")
        return

    # Getting the username of message sender
    username = db["users"].find_one({"_id": ObjectId(get_jwt_identity())}).get("username")
    logger.debug("Current user: %s", username)

    # Retrieve message
    message = msg.get("message")
    messages = db["messages"]

    # Append username info to pass through socket
    msg["username"] = username

    # Save to database
    result = insert_message(messages, username, message)
    if not result:
        logger.error("An error occured while handling message")
        return render_template("error.html")

    socket.emit("message", msg)


@socket.on("request_message")
@jwt_required()
def load_messages(cnt):
    """handle socket request to load bunch of messages from database"""

    logger.debug("Messages loaded: %s", cnt)

    # Validation piece: handles random other tampered values in global
    # counter variable than numbers
    try:
        int(cnt)
    except ValueError:
        logger.error(
            """Variale 'cnt' value is not expected: not convertable to int
            Current 'cnt' value - %s""",
            cnt,
        )
        return

    # if no messages to load remain sends event via socket
    if db["messages"].count_documents({}) <= int(cnt):
        socket.emit("loading_finished")
        return

    # retrieve 5 messages or whatever less that is remained
    messages = db["messages"].find(
        skip=(
            0
            if db["messages"].count_documents({}) < MSG_LOAD_BATCH + int(cnt)
            else db["messages"].count_documents({}) - MSG_LOAD_BATCH - int(cnt)
        ),
        limit=(
            db["messages"].count_documents({}) - int(cnt)
            if db["messages"].count_documents({}) <= MSG_LOAD_BATCH + int(cnt)
            else MSG_LOAD_BATCH
        ),
    )

    logger.debug(
        "%s messages retrieved from collection %s",
        messages.retrieved,
        messages.collection,
    )

    messages_listed = list(messages)

    # sort messages in reversed order by date to send via socket event one by one
    for msg in sorted(messages_listed, key=lambda x: x["_id"], reverse=True):
        message = {
            "username": msg["username"],
            "message": msg["message"],
            "timestamp": str(msg["timestamp"]),
        }
        socket.emit("load", message)
