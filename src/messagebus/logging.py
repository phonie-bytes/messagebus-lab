import logging
import structlog
from messagebus.config import settings


def setup_logging() -> None:
    """Configures structlog for beautiful, structured JSON logging."""
    
    # 1. Configure the standard library logging underneath
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    # 2. Define how structlog processes logs
    processors = [
        structlog.contextvars.merge_contextvars,  # Merges any global context
        structlog.processors.add_log_level,       # Adds "level": "info"
        structlog.processors.TimeStamper(fmt="iso"), # Adds ISO timestamp
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,     # Formats exceptions nicely
    ]

    # 3. Output format: JSON for production, pretty colors for local dev
    if settings.environment == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        # ConsoleRenderer gives us nice colors and formatting in the terminal
        processors.append(structlog.dev.ConsoleRenderer())

    # 4. Apply the configuration
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )