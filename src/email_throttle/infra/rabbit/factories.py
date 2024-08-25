import json
from typing import Any, Callable
from email_throttle.infra.rabbit.handlers import RabbitConsumer, RabbitProducer, create_connection


def create_producer(
    serializer: Callable[..., str] = json.dumps,
    create_connection_fn=create_connection,
):
    connection = create_connection_fn()

    return RabbitProducer(connection, serializer)


def create_consumer(
    deserializer: Callable[..., Any] = json.loads,
    handler: Callable = lambda data: data,
    create_connection_fn=create_connection,
):
    connection = create_connection_fn()

    return RabbitConsumer(connection, handler, deserializer)
