import argparse
import asyncio  # <-- Add this

import structlog

from messagebus.async_consumer import start_async_consumer
from messagebus.config import settings
from messagebus.consumer import start_consumer
from messagebus.logging import setup_logging
from messagebus.producer import send_message
from messagebus.replay import replay_dlq_messages


def main() -> None:
    setup_logging()
    log = structlog.get_logger()

    parser = argparse.ArgumentParser(description="Message Bus Lab CLI")
    # Add 'receive-async'
    parser.add_argument(
        "action", choices=["send", "receive", "receive-async", "replay"], help="Action to perform"
    )
    parser.add_argument("--message", "-m", default="Hello World!", help="Message to send")
    parser.add_argument("--routing-key", "-r", default="orders", help="Routing key")

    args = parser.parse_args()

    log.info("app.starting", app_name=settings.app_name, action=args.action)

    if args.action == "send":
        send_message(routing_key=args.routing_key, message=args.message)
    elif args.action == "receive":
        start_consumer()
    elif args.action == "receive-async":
        asyncio.run(start_async_consumer())  # <-- Add this
    elif args.action == "replay":
        replay_dlq_messages()


if __name__ == "__main__":
    main()
