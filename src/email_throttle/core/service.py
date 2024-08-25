import functools
from typing import Any, Callable

from email_throttle.core.abstract.middleware import Middleware
from email_throttle.core.abstract.sender import EmailSender
from email_throttle.core.entity import EmailMessage


class EmailService:
    def __init__(
        self,
        vendor: EmailSender,
        middlewares: list[Middleware],
    ):
        self.service = vendor
        self.middlewares = middlewares
        self.name = vendor.name or vendor.__class__.__name__

    def _send_email(self, message: EmailMessage) -> Callable[..., Any]:
        return lambda: self.service.send_email(message)

    def send_email(self, message: EmailMessage) -> tuple[bool, Any]:
        functions = [self._send_email(message)] + self.middlewares[::-1]

        pipeline = functools.reduce(
            lambda func, middleware: lambda: middleware.call(func),
            functions,
        )

        try:
            result = pipeline()
            return True, result
        except Exception as e:
            return False, e
