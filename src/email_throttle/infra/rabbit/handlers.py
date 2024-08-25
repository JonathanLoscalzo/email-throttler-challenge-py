import pika
from typing import Callable
from pika.channel import Channel


def create_connection():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            "localhost",
            port=5672,
            credentials=pika.PlainCredentials("user", "password"),
        )
    )

    return connection


class RabbitConnector:
    def __init__(self, connection: pika.BlockingConnection):
        self.channel = connection.channel()
        self.channel.exchange_declare(exchange="throttler", exchange_type="direct")
        self.channel.queue_declare(queue="emails")
        self.channel.queue_bind(
            exchange="throttler",
            queue="emails",
        )


class RabbitProducer(RabbitConnector):
    def __init__(
        self,
        connection: pika.BlockingConnection,
        serializer: Callable[..., str],
    ):
        super().__init__(connection)
        self.serializer = serializer

    def send(self, messages):
        self.channel.basic_publish(
            exchange="throttler",
            routing_key="emails",
            body=self.serializer(messages),
        )


class RabbitConsumer(RabbitConnector):
    def __init__(
        self,
        connection: pika.BlockingConnection,
        consume_callback: Callable,
        deserializer: Callable,
    ):
        super().__init__(
            connection,
        )
        self.channel.basic_consume(
            queue="emails",
            on_message_callback=self.consume,
            auto_ack=False,
        )
        self.channel.basic_qos(prefetch_count=1)
        self.consume_callback = consume_callback
        self.deserializer = deserializer

    def start_consuming(self):
        self.channel.start_consuming()

    def consume(self, ch: Channel, method, properties, body):
        print(self, ch, method, properties, body)

        try:
            message = self.deserializer(body)
            self.consume_callback(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print("Error while consuming", e)
