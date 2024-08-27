"""initial script for database setup"""

import logging
from logging.config import dictConfig
import os
import time
import sys
from pymongo import MongoClient, errors

from utils.helpers import password_hash
from logging_config import logconfig_dict

# Load logger
logger = logging.getLogger("setup")

# Load environment variables
mongo_hostname = os.getenv("MONGO_HOSTNAME")
mongo_database = os.getenv("MONGO_DATABASE")

mongo_username = os.getenv("MONGO_USERNAME")
mongo_password = os.getenv("MONGO_PASSWORD")

root_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
root_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

username = os.getenv("APP_ADMINUSER")
email = os.getenv("APP_ADMINEMAIL")
password = os.getenv("APP_ADMINPASSWORD")

# Define roles for new user
roles = [{"role": "readWrite", "db": mongo_database}]


# Trying to connect to db given 3 attempts
def maintain_connection(usr, pwd, hst):
    """initiates connection with database"""
    for att in range(1, 4):
        try:
            conn = MongoClient(f"mongodb://{usr}:{pwd}@{hst}:27017/")
            logger.info("ATTEMPT %s: The connection is maintained!", att)
            return conn
        except errors.PyMongoError:
            logger.error("ERROR AT ATTEMPT %s", att)
            time.sleep(5)

    logger.error("Failed to establish connection after maximum attempts.")
    sys.exit()


# Insert user with Argon2-encrypted password into a "users" collection
def insert_user(conn, usr, eml, pwd):
    """inserts initial in-app user"""
    hashed_password = password_hash(pwd)
    if hashed_password:
        conn.users.insert_one(
            {
                "username": usr,
                "email": eml,
                "password": hashed_password,
                "role": "admin",
            }
        )
        logger.info("Admin user inserted successfully")
    else:
        logger.info("Failed to insert user due to password hashing error")


# Find whether our special user exists
def find_user(db, usr):
    """search system user by name"""
    listing = db.command({"usersInfo": usr})
    return listing["users"]


# Add another non-privileged user to system
def add_system_user(db, usr, pwd):
    """create system non-root user within database"""
    db.command("createUser", usr, pwd=pwd, roles=roles)
    logger.info("Non-privileged user is added")


if __name__ == "__main__":

    dictConfig(logconfig_dict)

    client = maintain_connection(root_username, root_password, mongo_hostname)
    admin_db = client.admin
    if not find_user(admin_db, mongo_username):
        logger.info("No additional user found, adding non-root")
        add_system_user(admin_db, mongo_username, mongo_password)

    client.close()

    # Insert a user with the desired credentials
    client = maintain_connection(mongo_username, mongo_password, mongo_hostname)
    mongo_database = client[mongo_database]

    users = mongo_database.users.find_one({"role": "admin"})
    if not users:
        insert_user(mongo_database, username, email, password)
        logger.info("No in-app user found in database, added admin successfully!")
