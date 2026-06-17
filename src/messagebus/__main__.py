import structlog
from messagebus.config import settings
from messagebus.logging import setup_logging


def main() -> None:
    # Initialize logging first!
    setup_logging()
    
    # Get a logger instance
    log = structlog.get_logger()
    
    # Log with structured key-value pairs
    log.info("app.starting", app_name=settings.app_name, env=settings.environment)
    
    try:
        # Simulate some work
        log.info("app.connecting_to_broker", host=settings.rabbitmq_host, port=settings.rabbitmq_port)
        
        # Simulate an error
        raise ValueError("Simulated connection failure!")
        
    except Exception as e:
        # structlog automatically formats the exception beautifully
        log.error("app.failed", error=str(e))
        return

    log.info("app.ready")


if __name__ == "__main__":
    main()