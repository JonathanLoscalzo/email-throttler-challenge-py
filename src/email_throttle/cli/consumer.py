import argparse

from loguru import logger
from pydantic_core import from_json

from email_throttle.api.endpoints.emails.dtos import EmailDto
from email_throttle.core.entity import EmailMessage
from email_throttle.core.failover import EmailFailover, EmailFailoverWithState
from email_throttle.infra.rabbit.factories import create_consumer
from email_throttle.cli.simulator import create_services as create_services_from_config


def install_consumer_command(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
):
    subparser = subparsers.add_parser("consumer", help="Create a worker for the queue")

    subparser.set_defaults(func=consumer_command)
    return subparser


def create_services():
    # TODO: should create a real instance
    vendors_config = dict(
        name="Consumer",
        middlewares=["retry", "rl", "cb"],
        rate_limiter=dict(
            max_attempts=10,
            per_seconds=5,
        ),
        circuit_breaker=dict(
            threshold=3,
            reset_timeout=10,
        ),
        retry=dict(
            retries=3,
        ),
    )

    services = create_services_from_config([vendors_config])
    failover = EmailFailoverWithState(services)

    rb_consumer = create_consumer(
        deserializer=lambda model: EmailDto.model_validate(from_json(model)),
        handler=factory_handler_message(failover),
    )

    return rb_consumer


def factory_handler_message(failover: EmailFailoverWithState | EmailFailover):
    def handle_message(msg: EmailDto):
        logger.info(f"Sending email {msg}")
        result = failover.send_email(
            EmailMessage(
                to=msg.to,
                subject=msg.subject,
                body=msg.body,
                from_email=msg.from_email,
            )
        )
        logger.info(f"Result for email {msg} = {result}")

    return handle_message


def send_emails(failover: EmailFailoverWithState | EmailFailover, message):
    if not failover.send_email(message):
        return False


def consumer_command(args):
    consumer = create_services()
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping consumer")
