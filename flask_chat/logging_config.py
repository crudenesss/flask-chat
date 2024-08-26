"""Special configuration for logging with gunicorn"""
from os import getenv
from utils.filters import FilterDebug, IgnoreDebug

LOG_LEVEL = getenv("LOG_LEVEL")

# Define the logging configuration
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "general": {
            "format": "[%(levelname)s] - %(asctime)s - %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "detailed": {
            "format": 
            "[%(levelname)s] - %(asctime)s - %(message)s - in %(pathname)s:%(funcName)s:%(lineno)d",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        }
    },
    "filters": {
        "filter_debug": {
            "()": FilterDebug,
        },
        "ignore_debug": {
            "()": IgnoreDebug,
        },
    },
    "handlers": {
        "stdout_debug": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "filters": ["filter_debug"],
            "level": "DEBUG",
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "general",
            "filters": ["ignore_debug"],
            "level": "INFO",
        }
    },
    "root": {"handlers": ["stdout", "stdout_debug"], "level": "INFO"},
    "loggers": {
        "gunicorn.access": {
            "handlers": ["stdout", "stdout_debug"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "setup": {
            "handlers": ["stdout", "stdout_debug"],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "pymongo.command": {
            "level": "INFO",
            "propagate": False,
        },
    },
}
