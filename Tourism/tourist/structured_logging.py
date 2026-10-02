"""
Structured logging utilities — JSON-formatted logs for production.
"""
import json
import logging
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class StructuredLogFormatter(logging.Formatter):
    """Formats log records as JSON for production logging systems."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, default=str)


def configure_structured_logging():
    """Configure structured JSON logging for production."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)


class RequestContextFilter(logging.Filter):
    """Adds request context to log records."""

    def filter(self, record):
        try:
            from django.http import HttpRequest
            # This is a simplified version — in production you'd use
            # contextvars or thread-local storage to track request context
            record.request_id = getattr(record, "request_id", str(uuid.uuid4())[:12])
        except Exception:
            record.request_id = None
        return True
