# import json
from os import getenv
from flask import Flask, render_template, session
from flask_socketio import SocketIO

from views import views_bp
from models import db, insert_message

# Define app
app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY")
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.register_blueprint(views_bp)

# Create socket handle
socket = SocketIO(app)
socket.init_app(app, cors_allowed_origins="*")


@socket.on("message")
def handle_message(msg):
    print("Message:", msg)
    messages = db["messages"]
    result = insert_message(messages, msg["username"], msg["message"])
    if not result:
        return render_template("error.html", session=session)
    socket.emit("message", msg)


@socket.on("request_message")
def load_messages(cnt):

    if db["messages"].count_documents({}) <= int(cnt):
        socket.emit("loading_finished")
        return

    messages = list(
        db["messages"].find(
            skip=(
                0
                if db["messages"].count_documents({}) < 5 + int(cnt)
                else db["messages"].count_documents({}) - 5 - int(cnt)
            ),
            limit=(
                db["messages"].count_documents({}) - int(cnt)
                if db["messages"].count_documents({}) <= 5 + int(cnt)
                else 5
            )
        )
    )
    for msg in sorted(messages, key=lambda x: x['_id'], reverse=True):
        message = {
            "username": msg["username"],
            "message": msg["message"],
            "timestamp": str(msg["timestamp"]),
        }
        socket.emit("load", message)


# if __name__ == "__main__":
#     socket.run(app, host="0.0.0.0", port=5000, debug=True)
