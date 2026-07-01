import pika
import structlog
import tenacity
from typing import Any
from messagebus.config import settings

log = structlog.get_logger()


def start_consumer() -> None:
    log.info("consumer.connecting", url=settings.rabbitmq_host)
    
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()

    channel.exchange_declare(exchange='messages_dlx', exchange_type='direct', durable=True)
    channel.queue_declare(queue='dead_letter_queue', durable=True)
    channel.queue_bind(exchange='messages_dlx', queue='dead_letter_queue', routing_key='orders')

    args = {
        'x-dead-letter-exchange': 'messages_dlx',
        'x-dead-letter-routing-key': 'orders'
    }
    channel.queue_declare(queue='orders_queue', durable=True, arguments=args)
    
    channel.exchange_declare(exchange='messages_direct', exchange_type='direct', durable=True)
    channel.queue_bind(exchange='messages_direct', queue='orders_queue', routing_key='orders')

    log.info("consumer.waiting", queue_name='orders_queue', routing_key='orders')

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=4),
        reraise=True
    )
    def process_message(message: str) -> None:
        log.info("consumer.processing", message=message)
        if "poison" in message:
            raise ValueError("Poison pill detected! Code crashed!")
        log.info("consumer.success", message=message)

    def callback(ch: Any, method: Any, properties: Any, body: bytes) -> None:
        message = body.decode('utf-8')
        try:
            process_message(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            log.error("consumer.failed_after_retries", message=message, error=str(e))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue='orders_queue', on_message_callback=callback)
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()