import asyncio

import aio_pika
import structlog
import tenacity
from opentelemetry import trace

from messagebus.config import settings
from messagebus.metrics import (
    MESSAGES_DEAD_LETTERED,
    MESSAGES_PROCESSED,
    PROCESSING_TIME,
    start_metrics_server,
)

log = structlog.get_logger()
tracer = trace.get_tracer(__name__)  # OpenTelemetry tracer


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
async def process_message(message: str):
    # Create an OpenTelemetry span for this specific message
    with tracer.start_as_current_span("process_message") as span:
        span.set_attribute("message.body", message)

        log.info("consumer.processing", message=message)
        if "poison" in message:
            span.record_exception(ValueError("Poison pill detected!"))
            raise ValueError("Poison pill detected!")

        # Measure the time taken for this block
        with PROCESSING_TIME.time():
            await asyncio.sleep(1)

        log.info("consumer.success", message=message)


async def on_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process(requeue=False):
        body = message.body.decode("utf-8")
        try:
            await process_message(body)
            MESSAGES_PROCESSED.inc()  # Increment success counter
        except Exception:
            MESSAGES_DEAD_LETTERED.inc()  # Increment DLQ counter
            raise  # Let the context manager handle the nack


async def start_async_consumer():
    # Start the metrics server on port 9100!
    start_metrics_server(port=9100)
    log.info("metrics.started", port=9100)

    log.info("consumer.connecting", url=settings.rabbitmq_host)
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        dlx = await channel.declare_exchange(
            "messages_dlx", aio_pika.ExchangeType.DIRECT, durable=True
        )
        dlq = await channel.declare_queue("dead_letter_queue", durable=True)
        await dlq.bind(dlx, routing_key="orders")

        args = {"x-dead-letter-exchange": "messages_dlx", "x-dead-letter-routing-key": "orders"}
        main_exchange = await channel.declare_exchange(
            "messages_direct", aio_pika.ExchangeType.DIRECT, durable=True
        )
        main_queue = await channel.declare_queue("orders_queue", durable=True, arguments=args)
        await main_queue.bind(main_exchange, routing_key="orders")

        log.info("consumer.waiting_async", queue_name="orders_queue", routing_key="orders")
        await main_queue.consume(on_message)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(start_async_consumer())
