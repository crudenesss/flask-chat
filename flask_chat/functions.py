"""misc functions to use in application"""

import uuid
import logging
from argon2 import PasswordHasher, exceptions
from flask import current_app, request

logger = logging.getLogger("gunicorn.access")


# Functions to use in working with hashes of user's passwords in app
def password_hash(plain):
    """hashes account's password with argon2 hash"""
    ph = PasswordHasher()
    hashed = ph.hash(plain)
    return hashed


def password_verify(hash_string, input_plain):
    """verify account's password hash"""
    ph = PasswordHasher()
    try:
        return ph.verify(hash_string, input_plain)
    except exceptions.Argon2Error:
        logger.error("Password hash verification failed")
        return False


# To mitigate security risks, all the received files from client side
# will be renamed to some random uuid
def filename_generator():
    """generate random filenames for uploaded files"""
    newname = str(uuid.uuid4())
    return newname


# Function to send custom log messages for each instances
def log_request():
    """Debug-level log to dump useful info about received requests"""
    with current_app.app_context():
        data = {
            "access_route": request.access_route,
            "args": request.args,
            "base_url": request.base_url,
            "content_encoding": request.content_encoding,
            "endpoint": request.endpoint,
            "files": request.files,
            "headers": request.headers,
            "method": request.method,
        }

    logger.debug("The request has reached the server with parameters: %s", data)
