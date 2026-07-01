import pika

from messagebus import config, producer


def test_send_message_creates_queue_and_message(rabbitmq_container, monkeypatch):
    """Tests that our producer successfully sends a message to RabbitMQ."""

    # 1. Temporarily override the settings to point to the Testcontainer!
    monkeypatch.setattr(config.settings, "rabbitmq_host", rabbitmq_container["host"])
    monkeypatch.setattr(config.settings, "rabbitmq_port", rabbitmq_container["port"])
    monkeypatch.setattr(config.settings, "rabbitmq_user", rabbitmq_container["user"])
    monkeypatch.setattr(config.settings, "rabbitmq_password", rabbitmq_container["password"])

    test_url = config.settings.rabbitmq_url

    # 2. Create a direct channel to RabbitMQ to set up our "spy" queue
    connection = pika.BlockingConnection(pika.URLParameters(test_url))
    setup_channel = connection.channel()

    # 3. Declare the exchange AND the queue we expect the message to land in
    setup_channel.exchange_declare(exchange="messages_direct", exchange_type="direct", durable=True)
    setup_channel.queue_declare(queue="test_orders_queue", durable=True)
    setup_channel.queue_bind(
        exchange="messages_direct", queue="test_orders_queue", routing_key="orders"
    )

    # Close this setup channel so it doesn't interfere
    setup_channel.close()

    # 4. Call our actual production code! (It creates its own connection internally)
    producer.send_message(routing_key="orders", message="Test Order #999")

    # 5. Fetch the message from the queue to prove it arrived
    spy_channel = connection.channel()
    method, properties, body = spy_channel.basic_get(queue="test_orders_queue", auto_ack=True)

    # 6. Assertions
    assert method is not None, "No message was found in the queue!"
    assert body == b"Test Order #999", f"Expected Test Order #999, got {body}"

    connection.close()
