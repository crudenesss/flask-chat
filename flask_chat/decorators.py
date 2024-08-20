"""Decorators used within application"""

from functools import wraps
from flask import redirect, session, abort
from models import db


def login_required(f):
    """Checks if the user is logged in"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session.keys():
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def privilege_required(f):
    """Forbid access for users with no privileges for resource"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = db.users.find_one({"username": session.get("username")}).get("role")
        if role == "user":
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function
