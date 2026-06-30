import argparse
import structlog
from messagebus.config import settings
from messagebus.logging import setup_logging
from messagebus.producer import send_message
from messagebus.consumer import start_consumer
from messagebus.replay import replay_dlq_messages  # <-- Add this import

def main() -> None:
    setup_logging()
    log = structlog.get_logger()
    
    parser = argparse.ArgumentParser(description="Message Bus Lab CLI")
    # Add 'replay' to the choices
    parser.add_argument("action", choices=["send", "receive", "replay"], help="Action to perform")
    parser.add_argument("--message", "-m", default="Hello World!", help="Message to send")
    parser.add_argument("--routing-key", "-r", default="orders", help="Routing key")
    
    args = parser.parse_args()

    log.info("app.starting", app_name=settings.app_name, action=args.action)

    if args.action == "send":
        send_message(routing_key=args.routing_key, message=args.message)
    elif args.action == "receive":
        start_consumer()
    elif args.action == "replay":                 # <-- Add this block
        replay_dlq_messages()

if __name__ == "__main__":
    main()