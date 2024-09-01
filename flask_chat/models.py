"""functions to work with database"""

import datetime
import logging
import os
from bson import ObjectId
from pymongo import MongoClient, errors

from utils.constants import MSG_LOAD_BATCH

# Define constants
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOSTNAME = os.getenv("MONGO_HOSTNAME")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")

logger = logging.getLogger("gunicorn.access")

# Init database connection and get app database handle
try:
    client = MongoClient(
        f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOSTNAME}:27017/"
    )
    db = client[MONGO_DATABASE]
    logger.info("Connection is to database is maintained")
except errors.PyMongoError as err:
    logger.error("An error occured while maintaining connection to database: %s", err)


def insert_user(collection, username, email, password):
    """add document with user info"""
    user_data = {
        "username": username,
        "email": email,
        "role": "user",
        "password": password,
    }
    try:
        collection.insert_one(user_data)
        logger.debug("1 user inserted in a database")
        return True
    except errors.PyMongoError as e:
        logger.error("Failed to insert user in a database: %s", e)
        return False


def insert_message(collection, user_id, message_text):
    """add document with message data"""
    message_data = {
        "fk_user_id": ObjectId(user_id),
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


def retrieve_messages_readable(collection, initial_load=True, counter=None):
    """Retrieve messages from database ready to be rendered on page

    Args:
        collection (Collection): instance of MongoDB collection
        initial_load (bool, optional): _True_ is for when application is accessing collection
            initially i.e. when it is needed to load only newest batch of messages. 
            Defaults to _True_.
        counter (int, optional): Counter of already loaded messages. Applies only if `inital_load`
            is set to _False_. Defaults to _None_.

    Returns:
        CommandCursor: retrieved messages with easily rendered parameters
    """
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "fk_user_id",
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        {
            "$project": {
                "_id": 1,
                "fk_user_id": 1,
                "username": "$user_info.username",
                "message": 1,
                "timestamp": 1,
            }
        },
        { "$unwind": "$username" }
    ]

    if initial_load:
        if collection.count_documents({}) > MSG_LOAD_BATCH:
            pipeline.append(
                {"$skip": collection.count_documents({}) - MSG_LOAD_BATCH}
            )
    else:
        # Set documents to skip value
        if collection.count_documents({}) > MSG_LOAD_BATCH + counter:
            pipeline.append(
                {"$skip": collection.count_documents({}) - MSG_LOAD_BATCH - counter}
            )
        # Set documents output to limit
        if collection.count_documents({}) <= MSG_LOAD_BATCH + counter:
            pipeline.append(
                {"$limit": collection.count_documents({}) - counter}
            )
        else:
            pipeline.append(
                {"$limit": MSG_LOAD_BATCH}
            )

    results = collection.aggregate(pipeline)
    return list(results)
