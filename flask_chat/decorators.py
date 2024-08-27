"""Decorators used within application"""

from functools import wraps
from bson import ObjectId
from flask import abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db


def privilege_required(f):
    """Forbid access for users with no privileges for resource"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        role = db.users.find_one({"_id": ObjectId(get_jwt_identity())}).get("role")
        if role not in ["admin", "mod"]:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function
