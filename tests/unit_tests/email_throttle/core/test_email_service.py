from datetime import datetime
from unittest.mock import MagicMock

from email_throttle.core.abstract.middleware import Middleware
from email_throttle.core.abstract.sender import EmailSender
from email_throttle.core.entity import EmailMessage
from email_throttle.core.service import EmailService


class TestEmailService:

    class StopwatchMiddleware(Middleware):
        def __init__(self):
            self.time = 0

        def allow_request(self) -> bool:
            return True

        def call(self, func):
            self.time = datetime.now().timestamp()
            return func()

    def test_middlewares_called_in_order(
        self,
    ):
        mock_sender = MagicMock(EmailSender)
        m1 = self.StopwatchMiddleware()
        m2 = self.StopwatchMiddleware()
        m3 = self.StopwatchMiddleware()

        email_service = EmailService(
            vendor=mock_sender,
            middlewares=[m1, m2, m3],
        )

        mock_sender.send_email.return_value = "Success"

        message = EmailMessage(
            subject="Test",
            body="Body",
            to="email",
            from_email="email",
        )
        result = email_service.send_email(message)
        assert result == (True, "Success")
        assert m1.time < m2.time < m3.time

    def test_when_email_sender_fails__middlewares_called_in_order(
        self,
    ):
        mock_sender = MagicMock(EmailSender)
        mock_sender.name.return_value = "Test"
        m1 = MagicMock(Middleware)
        m2 = MagicMock(Middleware)
        m3 = MagicMock(Middleware)

        for m in [m1, m2, m3]:
            m.call.side_effect = lambda func: func()

        email_service = EmailService(
            vendor=mock_sender,
            middlewares=[m1, m2, m3],
        )

        mock_sender.send_email.side_effect = lambda: Exception("Error")

        message = EmailMessage(
            subject="Test",
            body="Body",
            to="email",
            from_email="email",
        )
        result, err = email_service.send_email(message)
        for m in [m1, m2, m3]:
            m.call.assert_called_once()

        assert result is False
