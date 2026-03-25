import sys

from pythonjsonlogger.json import JsonFormatter

JSON_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def get_json_formatter():
    """
    Returns a JSON formatter for logging.
    This formatter will convert log records into JSON format,
    making it easier to parse and analyze logs in structured logging systems.
    Sensitive data should never be logged.
    Always sanitize log messages before logging.
    """

    class SafeJsonFormatter(JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)
            # Remove or mask sensitive fields if present
            for sensitive_key in [
                "password",
                "token",
                "secret",
                "hashed_password",
            ]:
                if sensitive_key in log_record:
                    log_record[sensitive_key] = "***REDACTED***"

    formatter = SafeJsonFormatter(JSON_FORMAT)
    formatter.json_encoder = None
    return formatter


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": get_json_formatter,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": sys.stdout,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "src": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "src.main": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
