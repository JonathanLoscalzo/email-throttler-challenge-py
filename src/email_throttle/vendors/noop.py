from loguru import logger

from email_throttle.core.abstract.sender import EmailSender
from email_throttle.core.entity import EmailMessage


class NoOpEmailSender(EmailSender):
    def __init__(self, name: str):
        super().__init__(name)

    def send_email(self, message: EmailMessage):
        logger.debug(f"Sending email from {self.name}: {message.subject}")
        return f"Email sent from {self.name}"
