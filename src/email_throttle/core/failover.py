from loguru import logger

from email_throttle.core.entity import EmailMessage
from email_throttle.core.service import EmailService


class EmailFailover:
    """
    A class to manage email sending through multiple services with failover support.

    If one email service fails, the next service in the list is tried until either
    an email is successfully sent or all services have been attempted.
    """

    def __init__(self, services: list[EmailService]):
        self.services = services

    def send_email(self, message: EmailMessage) -> bool:
        """
        Attempts to send the given email message using the available services in order.

        This method tries to send the email using each service in the list until one succeeds.
        If all services fail, it returns False.
        """
        for service in self.services:
            logger.info(f"Trying to send email with {service.name}")
            result, _ = service.send_email(message)
            if result:
                logger.info(f"Email sent using {service.name}.")
                return True
            else:
                logger.warning(f"Service {service.name} failed. Trying next service.")
        logger.error("All email services failed.")
        return False


class EmailFailoverWithState:
    """
    A class to manage email sending through multiple services with failover support.

    Emails are sent one by one. If a service fails, the next service in the list is used.
    If a service succeeds, subsequent emails continue with this service until it fails.

    """

    def __init__(self, services: list[EmailService], max_retries: int = 10000):
        self.services = services
        self.current_service_index = 0
        self.cycles = 0
        self.max_retries = max_retries

    def send_email(self, message: EmailMessage) -> bool:
        """
        Attempts to send the given email message using the current email service.
        If the service fails, it moves to the next service in the list and tries again.
        """
        while self.current_service_index < len(self.services):
            current_service = self.services[self.current_service_index]
            logger.info(f"Trying to send email with {current_service.name}")
            result, _ = current_service.send_email(message)
            if result:
                logger.info(f"Email sent using {current_service.name}.")
                self.cycles = 0
                return True
            elif self.cycles > self.max_retries:
                logger.error("All email services failed. Raise and an error.")
                raise Exception("Max retries reached")
            else:
                logger.warning(f"Service {current_service.name} failed. Trying next service.")
                self.current_service_index = (self.current_service_index + 1) % len(self.services)
                if self.current_service_index == 0:
                    self.cycles += 1
        logger.info("All email services failed.")
        return False
