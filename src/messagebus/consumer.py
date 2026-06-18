import pika
import structlog
from messagebus.config import settings

log = structlog.get_logger()

def start_consumer() -> None:
    """Connects to RabbitMQ, creates a queue, and listens for messages."""
    
    log.info("consumer.connecting", url=settings.rabbitmq_host)
    
    connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
    channel = connection.channel()

    # 1. Declare the same exchange!
    channel.exchange_declare(exchange='messages_direct', exchange_type='direct')

    # 2. Declare a Queue
    # queue='' tells RabbitMQ to generate a random name for us.
    # durable=False means this queue disappears if RabbitMQ restarts (we'll fix this later)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # 3. Bind the Queue to the Exchange
    # We tell RabbitMQ: "Any message hitting 'messages_direct' with routing_key 'orders' 
    # should go into this specific queue."
    channel.queue_bind(exchange='messages_direct', queue=queue_name, routing_key='orders')

    log.info("consumer.waiting", queue_name=queue_name, routing_key='orders')

    # 4. Define what happens when a message arrives (The Callback)
    def callback(ch, method, properties, body):
        message = body.decode('utf-8')
        log.info("consumer.received", message=message, routing_key=method.routing_key)
        
        # Acknowledge the message! 
        # This tells RabbitMQ: "I successfully processed it, you can delete it."
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # 5. Tell RabbitMQ to use our callback for this queue
    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    # 6. Start listening forever (blocks the script)
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()