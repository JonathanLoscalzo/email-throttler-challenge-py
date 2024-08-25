from typing import Callable
from fastapi import Depends
from email_throttle.api.endpoints.emails.dtos import EmailDto
from email_throttle.core.failover import EmailFailover, EmailFailoverWithState
from email_throttle.core.service import EmailService
from email_throttle.vendors.noop import NoOpEmailSender
from email_throttle.infra.rabbit.factories import (
    create_connection as create_connection_factory,
    create_producer as create_producer_factory,
)


def email_services():
    return [EmailService(NoOpEmailSender(_), []) for _ in range(3)]


def email_failover_service(services: list[EmailService] = Depends(email_services)):
    return EmailFailover(services)


def email_failover_with_state(services: list[EmailService] = Depends(email_services)):
    return EmailFailoverWithState(services)


def rabbit_producer(connection_fn=create_connection_factory):
    serializer: Callable[[EmailDto], str] = lambda data: data.model_dump_json()

    return create_producer_factory(serializer, connection_fn)
