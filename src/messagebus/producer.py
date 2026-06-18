import pika
import structlog
from messagebus.config import settings

log = structlog.get_logger()

def send_message(routing_key: str, message: str) -> None:
    """Connects to RabbitMQ and sends a message to a Direct Exchange."""
    
    log.info("producer.connecting", url=settings.rabbitmq_host)
    
    # 1. Establish a connection to RabbitMQ
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()

    # 2. Declare the Exchange
    # We name it 'messages_direct'. 'direct' means it routes by exact routing_key match.
    channel.exchange_declare(exchange='messages_direct', exchange_type='direct')

    # 3. Publish the message
    channel.basic_publish(
        exchange='messages_direct',
        routing_key=routing_key,  # e.g., 'orders' or 'emails'
        body=message.encode('utf-8'), # Messages must be bytes
        properties=pika.BasicProperties(
            delivery_mode=2  # 2 means "persistent" - save to disk so it survives a crash
        )
    )

    log.info("producer.sent", routing_key=routing_key, message=message)
    
    # 4. Close the connection cleanly
    connection.close()