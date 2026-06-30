import pytest
import pika
from testcontainers.rabbitmq import RabbitMqContainer


@pytest.fixture(scope="session")
def rabbitmq_container():
    """Starts a real RabbitMQ container for the entire test session."""
    with RabbitMqContainer("rabbitmq:3.13-management") as rabbitmq:
        host = rabbitmq.get_container_host_ip()
        port = rabbitmq.get_exposed_port(5672)
        
        #        # Yield a dictionary of the connection parts
        yield {
            "host": host,
            "port": port,
            "user": "guest",      # <-- Change to guest
            "password": "guest"   # <-- Change to guest
        }


@pytest.fixture(scope="session")
def rabbitmq_channel(rabbitmq_container):
    """Creates a connection and channel to the test RabbitMQ."""
    url = f"amqp://{rabbitmq_container['user']}:{rabbitmq_container['password']}@{rabbitmq_container['host']}:{rabbitmq_container['port']}/"
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    
    yield channel
    connection.close()