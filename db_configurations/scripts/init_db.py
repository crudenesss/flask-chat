#!/usr/bin/env python3

import os
import time
from argon2 import PasswordHasher
from pymongo import MongoClient

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
    for att in range(1, 4):
        try:
            conn = MongoClient(f"mongodb://{usr}:{pwd}@{hst}:27017/")
            print(f"ATTEMPT {att}: The connection is maintained!")
            return conn
        except Exception as e:
            print(f"ERROR AT ATTEMPT {att}: {e}")
            time.sleep(5)

    print("Failed to establish connection after maximum attempts.")
    exit(1)


# Hash the password using argon2
def hash_password(pwd):
    try:
        ph = PasswordHasher()
        return ph.hash(pwd)
    except Exception as e:
        print(f"Error hashing password: {e}")
        return None


# Insert user with Argon2-encrypted password into a "users" collection
def insert_user(conn, usr, eml, pwd):
    hashed_password = hash_password(pwd)
    if hashed_password:
        conn.users.insert_one(
            {
                "username": usr,
                "email": eml,
                "password": hashed_password,
                "role": "admin",
                "pp_path": "./static/profile_pictures/default/default.jpg",
            }
        )
        print("User inserted successfully")
    else:
        print("Failed to insert user due to password hashing error")


# Find whether our special user exists
def find_user(db, usr):
    listing = db.command({"usersInfo": usr})
    return listing["users"]


# Add another non-privileged user to system
def add_system_user(db, usr, pwd):
    db.command("createUser", usr, pwd=pwd, roles=roles)
    return


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
