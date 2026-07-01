import pika
import structlog

from messagebus.config import settings

log = structlog.get_logger()


def replay_dlq_messages() -> None:
    """Reads messages from the DLQ and republishes them to the main exchange."""

    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()

    log.info("replay.starting", queue="dead_letter_queue")

    while True:
        # 1. Fetch one message from the DLQ without blocking the whole app
        # auto_ack=False means we only ack it AFTER we successfully republish it
        method, properties, body = channel.basic_get(queue="dead_letter_queue", auto_ack=False)

        # 2. If method is None, the queue is empty!
        if method is None:
            log.info("replay.empty", message="No more messages in DLQ to replay.")
            break

        message = body.decode("utf-8")
        log.info("replay.found", message=message)

        # 3. Publish the message back to the main exchange
        channel.basic_publish(
            exchange="messages_direct",
            routing_key="orders",
            body=body,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        log.info("replay.republished", message=message, exchange="messages_direct")

        # 4. Acknowledge the message in the DLQ so it is removed from there
        channel.basic_ack(delivery_tag=method.delivery_tag)

    connection.close()
