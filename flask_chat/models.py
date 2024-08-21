"""functions to work with database"""

import datetime
import logging
import os
from pymongo import MongoClient, errors

# Define constants
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOSTNAME = os.getenv("MONGO_HOSTNAME")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")

logger = logging.getLogger("gunicorn.access")

# Init database connection and get app database handle
try:
    client = MongoClient(f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOSTNAME}:27017/")
    db = client[MONGO_DATABASE]
    logger.info("Connection is to database is maintained")
except errors.PyMongoError as err:
    logger.error("An error occured while maintaining connection to database: %s", err)


def insert_user(collection, username, email, password):
    """add document with user info"""
    user_data = {"username": username, "email": email, "role": "user", "password": password}
    try:
        collection.insert_one(user_data)
        logger.debug("1 user inserted in a database")
        return True
    except errors.PyMongoError as e:
        logger.error("Failed to insert user in a database: %s", e)
        return False


def insert_message(collection, username, message_text):
    """add document with message data"""
    message_data = {
        "username": username,
        "message": message_text,
        "timestamp": datetime.datetime.now().timestamp(),
    }
    try:
        collection.insert_one(message_data)
        logger.debug("1 message inserted in a database")
        return True
    except errors.PyMongoError as e:
        logger.error("Failed to insert message in a database: %s", e)
        return False
