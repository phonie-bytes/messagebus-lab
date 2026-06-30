import pika
import structlog
from messagebus.config import settings

log = structlog.get_logger()

def send_message(routing_key: str, message: str) -> None:
    """Connects to RabbitMQ and sends a message to a Direct Exchange."""
    
    log.info("producer.connecting", url=settings.rabbitmq_host)
    
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()

    # 1. Declare the Exchange as DURABLE (matching the async consumer)
    channel.exchange_declare(exchange='messages_direct', exchange_type='direct', durable=True)

    # 2. Publish the message
    channel.basic_publish(
        exchange='messages_direct',
        routing_key=routing_key,
        body=message.encode('utf-8'),
        properties=pika.BasicProperties(
            delivery_mode=2  # 2 means persistent (save to disk)
        )
    )

    log.info("producer.sent", routing_key=routing_key, message=message)
    
    connection.close()