from fastapi import APIRouter, Depends

from email_throttle.api.endpoints.emails.dependencies import email_failover_with_state, rabbit_producer
from email_throttle.api.endpoints.emails.dtos import EmailDto
from email_throttle.core.entity import EmailMessage
from email_throttle.core.failover import EmailFailoverWithState
from email_throttle.infra.rabbit.handlers import RabbitProducer


router = APIRouter()


@router.post("/")
def send_email(email: EmailDto, sender: EmailFailoverWithState = Depends(email_failover_with_state)) -> bool:
    # TODO: add validations
    entity = EmailMessage(
        subject=email.subject,
        body=email.body,
        to=email.to,
        from_email=email.from_email,
    )
    result = sender.send_email(entity)

    return result


@router.post("/bulk")
def send_email_bulk(
    emails: list[EmailDto],
    producer: RabbitProducer = Depends(rabbit_producer),
) -> bool:
    # TODO: add validations

    for email in emails:
        producer.send(email)

    return True


"""
for i in {1..100}; do
curl -X 'POST' \
    'http://127.0.0.1:8000/email/' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
        "subject": "string",
        "body": "string",
        "to": [
            "string"
        ],
        "from_email": "string"
    }'
done

for i in {1..100}; do
curl -X 'POST' \
    'http://127.0.0.1:8000/email/bulk' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '[{
        "subject": "string",
        "body": "string",
        "to": [
            "string"
        ],
        "from_email": "string"
    }]'
done
"""
