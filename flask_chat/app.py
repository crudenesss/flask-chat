"""main application file"""

import logging
from os import getenv
from datetime import timedelta
from flask import Flask, redirect, render_template
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required

# from forms import MessageForm
from utils.constants import MSG_MAX_LENGTH, SESSION_EXPIRY
from services import UserService, MessageService
from views import views_bp

# Define app
app = Flask(__name__)
app.debug = True

# Define app configurations
# JWT
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=SESSION_EXPIRY)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_CSRF_CHECK_FORM"] = True

# Content validation
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

app.register_blueprint(views_bp)

# Create socket handle
socket = SocketIO(app)
socket.init_app(app, cors_allowed_origins="*")

# Create jwt manager handler
jwt = JWTManager(app)
jwt.init_app(app)

logger = logging.getLogger("gunicorn.access")

# Init custom services
user_service = UserService()
message_service = MessageService()


# Custom exceptions for error responses
@jwt.unauthorized_loader
def unauthorized_loader_error(error):
    """Custom handler for abscence of jwt token when accessing an endpoint"""
    logger.debug(error)
    return redirect("/login")


@jwt.expired_token_loader
def expired_token_loader_error(token):
    """Custom handler for expired token provided when accesssing an endpoint"""
    token_type = token["type"]
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

    # If recevived message length is more than required
    if len(msg.get("message")) > MSG_MAX_LENGTH:
        logger.debug("Message length limit exceeded")
        socket.emit("message_too_long", {"msg_length": MSG_MAX_LENGTH})
        return

    # Getting the username of message sender
    user_id = get_jwt_identity()

    # Retrieve message
    message = msg.get("message")
    logger.debug("Message received: %s", message)

    # Save to database
    result = message_service.insert_message(message, user_id)
    if not result:
        logger.error("An error occured while inserting message")
        return render_template(
            "error.html", message="An error occured while inserting message"
        )

    username = user_service.get_user_by_id(user_id).username
    logger.debug("Current user: %s", username)

    # Append username info to pass through socket
    msg["username"] = username
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
    if message_service.count() <= int(cnt):
        socket.emit("loading_finished")
        return

    # retrieve batch of messages or whatever less that is remained
    messages = message_service.retrieve_messages(
        initial_load=False, counter=int(cnt), jsonify=True
    )
    if not messages:
        logger.error("An error occured while loading messages.")
        return

    logger.debug("%s messages retrieved from collection.", len(messages))

    # sort messages in reversed order by date to send via socket event one by one
    for msg in sorted(messages, key=lambda x: x.message_timestamp, reverse=True):
        message = {
            "username": msg.username,
            "message": msg.message_content,
            "timestamp": str(msg.message_timestamp),
        }
        socket.emit("load", message)
