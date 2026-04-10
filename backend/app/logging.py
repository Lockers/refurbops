import logging
import sys
from typing import Any

import structlog

from app.config import Settings


_configured = False


def _configure_library_log_levels(*, settings: Settings) -> None:
    noisy_logger_names = [
        "pymongo",
        "pymongo.command",
        "pymongo.connection",
        "pymongo.serverSelection",
        "pymongo.topology",
        "pymongo.ocsp_support",
        "redis",
        "urllib3",
    ]

    level = logging.INFO if settings.app_debug else logging.WARNING
    for logger_name in noisy_logger_names:
        logging.getLogger(logger_name).setLevel(level)


def configure_logging(*, settings: Settings) -> None:
    global _configured
    if _configured:
        return

    app_level = logging.DEBUG if settings.app_debug else logging.INFO

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=app_level,
    )
    _configure_library_log_levels(settings=settings)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(app_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger(**values: Any):
    return structlog.get_logger().bind(**values)
