"""functions to work with database"""
import datetime
import os
from pymongo import MongoClient

# Define constants
USER = os.getenv("MONGO_USERNAME")
PASSWORD = os.getenv("MONGO_PASSWORD")
HOST = os.getenv("HOST")
DB = os.getenv("DB")

# Init database connection and get app database handle
client = MongoClient(f"mongodb://{USER}:{PASSWORD}@{HOST}:27017/")
db = client[DB]


# def return_user(collection, user):
#     return collection.find_one({"username": user})


# def return_email(collection, email):
#     return collection.find_one({"email": email})


def insert_user(collection, username, email, password):
    """add document with user info"""
    user_data = {"username": username, "email": email, "password": password}
    result = collection.insert_one(user_data)
    return result


def insert_message(collection, username, message_text):
    """add document with message data"""
    message_data = {
        "username": username,
        "message": message_text,
        "timestamp": datetime.datetime.now().timestamp(),
    }
    result = collection.insert_one(message_data)
    return result
