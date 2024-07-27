import uuid
from argon2 import PasswordHasher, exceptions


def password_hash(plain):
    ph = PasswordHasher()
    hashed = ph.hash(plain)
    return hashed


def password_verify(hash_string, input_plain):
    ph = PasswordHasher()
    try:
        return ph.verify(hash_string, input_plain)
    except exceptions.Argon2Error:
        return False


def filename_generator():
    newname = str(uuid.uuid4())
    return newname
