"""initial script for database setup"""

import os
import time
import sys
from argon2 import PasswordHasher, exceptions
from pymongo import MongoClient, errors

# Load environment variables
host = os.getenv("HOST")

mongo_username = os.getenv("MONGO_USERNAME")
mongo_password = os.getenv("MONGO_PASSWORD")

root_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
root_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

username = os.getenv("APP_ADMINUSER")
email = os.getenv("APP_ADMINEMAIL")
password = os.getenv("APP_ADMINPASSWORD")

# Define roles for new user
roles = [{"role": "readWrite", "db": "chat_db"}]


# Trying to connect to db given 3 attempts
def maintain_connection(usr, pwd, hst):
    """initiates connection with database"""
    for att in range(1, 4):
        try:
            conn = MongoClient(f"mongodb://{usr}:{pwd}@{hst}:27017/")
            print(f"ATTEMPT {att}: The connection is maintained!")
            return conn
        except errors.PyMongoError as e:
            print(f"ERROR AT ATTEMPT {att}: {e}")
            time.sleep(5)

    print("Failed to establish connection after maximum attempts.")
    sys.exit()


# Hash the password using argon2
def hash_password(pwd):
    """hash password"""
    try:
        ph = PasswordHasher()
        return ph.hash(pwd)
    except exceptions.Argon2Error:
        print("Error hashing password")
        return None


# Insert user with Argon2-encrypted password into a "users" collection
def insert_user(conn, usr, eml, pwd):
    """inserts initial in-app user"""
    hashed_password = hash_password(pwd)
    if hashed_password:
        conn.users.insert_one(
            {
                "username": usr,
                "email": eml,
                "password": hashed_password,
                "role": "admin",
            }
        )
        print("User inserted successfully")
    else:
        print("Failed to insert user due to password hashing error")


# Find whether our special user exists
def find_user(db, usr):
    """search system user by name"""
    listing = db.command({"usersInfo": usr})
    return listing["users"]


# Add another non-privileged user to system
def add_system_user(db, usr, pwd):
    """create system non-root user within database"""
    db.command("createUser", usr, pwd=pwd, roles=roles)


client = maintain_connection(root_username, root_password, host)
admin_db = client.admin
if not find_user(admin_db, mongo_username):
    add_system_user(admin_db, mongo_username, mongo_password)

client.close()

# Insert a user with the desired credentials
client = maintain_connection(mongo_username, mongo_password, host)
database = client.chat_db

users = database.users.find_one({"role": "admin"})
if not users:
    insert_user(database, username, email, password)
    print("Initial data insertion is completed!")
