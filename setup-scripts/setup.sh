#!/bin/bash

createdb ${PGDATABASE}

psql -c "\c ${PGDATABASE};"

# Create all tables 
psql -c "CREATE TABLE roles ( 
    role_id VARCHAR(32) PRIMARY KEY,
    role_name VARCHAR(64)
);"

psql -c "CREATE TABLE users (
    user_id VARCHAR(80) PRIMARY KEY,
    username VARCHAR(32) NOT NULL,
    passwd VARCHAR(256) NOT NULL,
    email VARCHAR(320) NOT NULL,
    bio VARCHAR(256),
    profile_picture VARCHAR(128),
    role_id VARCHAR(32),

    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);"

psql -c "CREATE TABLE messages (
    message_id VARCHAR(80) PRIMARY KEY,
    message_content VARCHAR(4096) NOT NULL,
    message_timestamp VARCHAR(32) NOT NULL, 
    message_edited BOOLEAN NOT NULL,
    user_id VARCHAR(80),

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);"

# Create user who will communicate with database
psql -c "CREATE ROLE \"${POSTGRES_USERNAME}\" LOGIN PASSWORD '${POSTGRES_PASSWORD}' INHERIT;"

# Set inly required permissions
psql -c "GRANT SELECT, INSERT, UPDATE, DELETE ON \"roles\" TO \"${POSTGRES_USERNAME}\";" \
    -c "GRANT SELECT, INSERT, UPDATE, DELETE ON \"users\" TO \"${POSTGRES_USERNAME}\";" \
    -c "GRANT SELECT, INSERT, UPDATE, DELETE ON \"messages\" TO \"${POSTGRES_USERNAME}\";"

# Insert starter data
PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USERNAME} -c \
    "INSERT INTO roles VALUES 
    ('admin', 'Admin'),
    ('mod', 'Moderator'),
    ('user', NULL);"

# Set access rules into pg_hba.conf
echo "local ${PGDATABASE} ${POSTGRES_USERNAME} password
host ${PGDATABASE} ${POSTGRES_USERNAME} samenet password" > /var/lib/postgresql/data/pg_hba.conf