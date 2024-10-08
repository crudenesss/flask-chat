#!/bin/bash

# activates prepared virtual environment 
. ./.venv/bin/activate

# generates secret key for application
export FLASK_SECRET_KEY="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 256)"

# runs the app
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 -c logging_config.py app:app --log-level "${LOGGING_LEVEL}"
