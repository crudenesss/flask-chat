"""misc functions to use in application"""

import uuid
from argon2 import PasswordHasher, exceptions


def password_hash(plain):
    """hashes password with argon2 hash"""
    ph = PasswordHasher()
    hashed = ph.hash(plain)
    return hashed


def password_verify(hash_string, input_plain):
    """verify password hash"""
    ph = PasswordHasher()
    try:
        return ph.verify(hash_string, input_plain)
    except exceptions.Argon2Error:
        return False


def filename_generator():
    """generate random filenames"""
    newname = str(uuid.uuid4())
    return newname
