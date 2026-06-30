import asyncio
import aio_pika
import structlog
import tenacity
from messagebus.config import settings

log = structlog.get_logger()

# 1. Async Retry Policy
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=4),
    reraise=True
)
async def process_message(message: str):
    """Simulates an async task, like calling a database or API."""
    log.info("consumer.processing", message=message)
    if "poison" in message:
        raise ValueError("Poison pill detected!")
    
    # Simulate I/O bound work (e.g., waiting on a network request)
    await asyncio.sleep(1) 
    log.info("consumer.success", message=message)

# 2. The Callback
async def on_message(message: aio_pika.abc.AbstractIncomingMessage):
    """Triggered every time a message arrives."""
    async with message.process(requeue=False):
        # message.process(requeue=False) is a context manager!
        # If the code inside succeeds, it auto-acks.
        # If an exception escapes, it auto-nacks (requeue=False) -> Sends to DLQ!
        body = message.body.decode('utf-8')
        await process_message(body)

# 3. The Main Consumer Loop
async def start_async_consumer():
    log.info("consumer.connecting", url=settings.rabbitmq_host)
    
    # Connect asynchronously
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    
    async with connection:
        channel = await connection.channel()
        
        # Set prefetch count: only give us 10 messages at a time to process concurrently!
        await channel.set_qos(prefetch_count=10)

        # Declare DLQ
        dlx = await channel.declare_exchange('messages_dlx', aio_pika.ExchangeType.DIRECT, durable=True)
        dlq = await channel.declare_queue('dead_letter_queue', durable=True)
        await dlq.bind(dlx, routing_key='orders')

        # Declare Main Queue with DLQ args
        args = {
            'x-dead-letter-exchange': 'messages_dlx',
            'x-dead-letter-routing-key': 'orders'
        }
        main_exchange = await channel.declare_exchange('messages_direct', aio_pika.ExchangeType.DIRECT, durable=True)
        main_queue = await channel.declare_queue('orders_queue', durable=True, arguments=args)
        await main_queue.bind(main_exchange, routing_key='orders')

        log.info("consumer.waiting_async", queue_name='orders_queue', routing_key='orders')

        # Start consuming
        await main_queue.consume(on_message)
        
        # Keep the event loop running forever
        await asyncio.Future()

if __name__ == "__main__":
    # Start the asyncio event loop
    asyncio.run(start_async_consumer())