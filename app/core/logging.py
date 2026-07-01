import json
import logging
import sys
from typing import Any, Dict
from app.core.config import settings


class StructuredJSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON-formatted logs for structured parsing.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Create a dictionary of standard log record fields
        log_payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt or "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
        }

        # Include additional attributes passed via extra={}
        extra_keys = set(record.__dict__.keys()) - {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message"
        }
        for key in extra_keys:
            log_payload[key] = getattr(record, key)

        # Include exception traceback if it exists
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable log formatter for development/console use.
    """
    # ANSI escape colors
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[41m\033[37m",  # White on Red
        "RESET": "\033[0m"
    }

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        reset = self.RESET

        # Format prefix: LEVEL [name] msg
        log_msg = f"{color}{levelname:<8}{reset} [{record.name}] {record.getMessage()}"

        # If extra details exist like path/method/status, print them
        extra_info = []
        for key in ["method", "path", "status_code", "elapsed_ms", "request_id"]:
            if hasattr(record, key):
                extra_info.append(f"{key}={getattr(record, key)}")
        if extra_info:
            log_msg += f" ({', '.join(extra_info)})"

        if record.exc_info:
            log_msg += f"\n{self.formatException(record.exc_info)}"

        return log_msg

    RESET = "\033[0m"


def configure_logging() -> None:
    """
    Initializes and configures the system-wide logging level and formatters.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to prevent double logging
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Standard stream console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Select formatter based on environment
    if settings.is_production:
        console_handler.setFormatter(StructuredJSONFormatter())
    else:
        console_handler.setFormatter(DevelopmentFormatter())

    root_logger.addHandler(console_handler)

    # Mute verbose logs from dependencies
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)

    logging.info(f"Logging initialized in environment: {settings.ENVIRONMENT} (level: {settings.LOG_LEVEL})")
