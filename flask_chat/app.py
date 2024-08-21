"""main application file"""

import logging
from os import getenv
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO

# from forms import MessageForm
from utils.constants import MSG_LOAD_BATCH
from views import views_bp
from models import db, insert_message

# Define app
app = Flask(__name__)

app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

app.register_blueprint(views_bp)

# Create socket handle
socket = SocketIO(app)
socket.init_app(app, cors_allowed_origins="*")

logger = logging.getLogger("gunicorn.access")


@socket.on("message")
def handle_message(msg):
    """handle initial messages sent via websocket and saves them to database"""

    logger.debug("Message received")

    # form = request.form(MessageForm)
    # TODO: validation

    username = msg.get("username")
    message = msg.get("message")

    messages = db["messages"]
    result = insert_message(messages, username, message)
    if not result:
        logger.error("An error occured while handling message")
        return render_template("error.html", session=session)
    socket.emit("message", msg)


@socket.on("request_message")
def load_messages(cnt):
    """handle socket request to load bunch of messages from database"""

    logger.debug("Messages loaded: %s", cnt)

    # Validation piece: handles random other tampered values in global
    # counter variable than numbers
    try:
        int(cnt)
    except ValueError:
        logger.error("""Variale 'cnt' value is not expected: not convertable to int
            Current 'cnt' value - %s""", cnt)
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
