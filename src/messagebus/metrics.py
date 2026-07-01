from prometheus_client import Counter, Histogram, start_http_server

# 1. Count how many messages we process
MESSAGES_PROCESSED = Counter(
    "messagebus_messages_processed_total", "Total number of messages processed successfully"
)

# 2. Count how many messages fail and go to DLQ
MESSAGES_DEAD_LETTERED = Counter(
    "messagebus_messages_dead_lettered_total", "Total number of messages sent to DLQ"
)

# 3. Measure how long it takes to process a message
PROCESSING_TIME = Histogram("messagebus_processing_time_seconds", "Time spent processing a message")


def start_metrics_server(port: int = 8000) -> None:
    """Starts the HTTP server to expose metrics."""
    start_http_server(port)
