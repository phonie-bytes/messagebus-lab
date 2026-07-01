import pika
import structlog
import tenacity

from messagebus.config import settings

log = structlog.get_logger()

# 1. Setup Tenacity Retry Rules
# Retries 3 times: wait 1s, then 2s, then 4s. If it still fails, give up.
retry_policy = tenacity.AsyncRetrying(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
# Note: Because Pika's BlockingConnection is synchronous, we'll use a sync version below.
# Let's adjust for a sync retry loop for simplicity with Pika's blocking connection.


def start_consumer() -> None:
    log.info("consumer.connecting", url=settings.rabbitmq_host)

    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()

    # 2. Declare the Dead Letter Exchange and Queue
    channel.exchange_declare(exchange="messages_dlx", exchange_type="direct")
    channel.queue_declare(queue="dead_letter_queue", durable=True)
    channel.queue_bind(exchange="messages_dlx", queue="dead_letter_queue", routing_key="orders")

    # 3. Declare the Main Queue WITH Dead Letter Arguments
    # We tell RabbitMQ: "If a message is rejected from 'orders_queue', send it to 'messages_dlx'"
    args = {
        "x-dead-letter-exchange": "messages_dlx",
        "x-dead-letter-routing-key": "orders",  # Route it to the dead_letter_queue
    }
    channel.queue_declare(queue="orders_queue", durable=True, arguments=args)

    # 4. Declare the Main Exchange and bind the Main Queue
    channel.exchange_declare(exchange="messages_direct", exchange_type="direct")
    channel.queue_bind(exchange="messages_direct", queue="orders_queue", routing_key="orders")

    log.info("consumer.waiting", queue_name="orders_queue", routing_key="orders")

    # 5. The Processing Logic with Sync Retries
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def process_message(message: str):
        """Simulates processing. Throws an error if message contains 'poison'."""
        log.info("consumer.processing", message=message)
        if "poison" in message:
            raise ValueError("Poison pill detected! Code crashed!")
        # Simulate successful work
        log.info("consumer.success", message=message)

    # 6. The Callback
    def callback(ch, method, properties, body):
        message = body.decode("utf-8")
        try:
            process_message(message)
            # If success, acknowledge and remove from queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            log.error("consumer.failed_after_retries", message=message, error=str(e))
            # If it fails 3 times, REJECT it and DO NOT requeue (requeue=False)
            # This sends it to the Dead Letter Exchange!
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue="orders_queue", on_message_callback=callback)
    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()
