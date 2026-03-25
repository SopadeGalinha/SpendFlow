import json
import logging
from decimal import Decimal

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal values."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


async def global_exception_handler(request: Request, exc: Exception):
    """
    Handles uncaught exceptions and returns a user-friendly error message.
    Logs the error with traceback for debugging.
    """
    logger = logging.getLogger("src.core.exceptions")
    logger.error(
        "Unhandled exception occurred.",
        extra={
            "error": "INTERNAL_SERVER_ERROR",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": str(request.url.path),
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": (
                "An unexpected error occurred. Please try again later. "
                "If the problem persists, contact support."
            ),
            "path": str(request.url.path),
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handles HTTPExceptions and returns a clear error message to the client.
    """
    logger = logging.getLogger("src.core.exceptions")
    logger.warning(
        "HTTP exception occurred.",
        extra={
            "error": "HTTP_EXCEPTION",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc.detail),
            "path": str(request.url.path),
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail or "A request error occurred.",
            "detail": exc.detail or "A request error occurred.",
            "path": str(request.url.path),
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    Handles validation errors and returns detailed information to the client.
    """
    logger = logging.getLogger("src.core.exceptions")

    # Convert validation errors that may contain Decimal or exception values.
    def convert_errors(errors):
        """Recursively convert non-JSON-serializable values in error list."""
        result = []
        for error in errors:
            error_dict = dict(error)
            # Convert nested context values into JSON-safe primitives.
            if "ctx" in error_dict and error_dict["ctx"]:
                error_dict["ctx"] = {
                    k: (
                        float(v)
                        if isinstance(v, Decimal)
                        else str(v)
                        if isinstance(v, Exception)
                        else v
                    )
                    for k, v in error_dict["ctx"].items()
                }
            result.append(error_dict)
        return result

    converted_errors = convert_errors(exc.errors())

    logger.warning(
        "Validation error occurred.",
        extra={
            "error": "VALIDATION_ERROR",
            "validation_errors": json.dumps(
                converted_errors,
                cls=DecimalEncoder,
            ),
            "path": str(request.url.path),
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": (
                "Invalid input data. Please check your request and try again."
            ),
            "details": converted_errors,
            "path": str(request.url.path),
        },
    )
