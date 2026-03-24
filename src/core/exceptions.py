
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


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
            "path": str(request.url.path)
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
            "path": str(request.url.path)
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
    logger.warning(
        "Validation error occurred.",
        extra={
            "error": "VALIDATION_ERROR",
            "validation_errors": exc.errors(),
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
            "details": exc.errors(),
            "path": str(request.url.path),
        },
    )
