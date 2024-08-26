#!/bin/bash

# activates prepared virtual environment 
. ./.venv/bin/activate

# runs script to complete all the preparation steps for clean db
python ./init_db.py

# generates secret key for application
export FLASK_SECRET_KEY="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 256)"

# python -u ./app.py
# runs the app
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 -c logging_config.py app:app --log-level "${LOG_LEVEL}"
