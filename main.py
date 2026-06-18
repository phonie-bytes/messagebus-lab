import argparse
import structlog
from messagebus.config import settings
from messagebus.logging import setup_logging
from messagebus.producer import send_message
from messagebus.consumer import start_consumer

def main() -> None:
    setup_logging()
    log = structlog.get_logger()
    
    # Set up a simple command-line interface
    parser = argparse.ArgumentParser(description="Message Bus Lab CLI")
    parser.add_argument("action", choices=["send", "receive"], help="Send or receive a message")
    parser.add_argument("--message", "-m", default="Hello World!", help="Message to send")
    
    args = parser.parse_args()

    log.info("app.starting", app_name=settings.app_name, action=args.action)

    if args.action == "send":
        # We hardcode routing_key='orders' for this step
        send_message(routing_key="orders", message=args.message)
    elif args.action == "receive":
        start_consumer()

if __name__ == "__main__":
    main()