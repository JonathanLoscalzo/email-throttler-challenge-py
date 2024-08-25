from unittest.mock import Mock

import pytest
from email_throttle.core.entity import EmailMessage
from email_throttle.core.service import EmailService

from email_throttle.core.failover import EmailFailover, EmailFailoverWithState


class TestEmailFailover:
    def get_message(self):
        return EmailMessage(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="from email",
        )

    def test_send_email_success_on_first_try(self):
        mock_service = Mock(spec=EmailService)
        mock_service.send_email.return_value = (True, "Success")
        mock_service.name = "MockedEmailService"

        failover = EmailFailover(services=[mock_service])
        message = self.get_message()

        result = failover.send_email(message)

        assert result
        mock_service.send_email.assert_called_once_with(message)

    def test_send_email_success_on_second_try(self):
        mock_service1 = Mock(spec=EmailService)
        mock_service1.send_email.return_value = (False, "Failure")
        mock_service1.name = "MockedEmailService"

        mock_service2 = Mock(spec=EmailService)
        mock_service2.send_email.return_value = (True, "Success")
        mock_service2.name = "MockedEmailService2"

        failover = EmailFailover(services=[mock_service1, mock_service2])

        message = self.get_message()
        result = failover.send_email(message)

        assert result
        mock_service1.send_email.assert_called_once_with(message)
        mock_service2.send_email.assert_called_once_with(message)

    def test_send_email_all_fail(self):
        # Mock de dos servicios que fallan
        mock_service1 = Mock(spec=EmailService)
        mock_service1.send_email.return_value = (False, "Failure")
        mock_service1.name = "MockedEmailService"

        mock_service2 = Mock(spec=EmailService)
        mock_service2.send_email.return_value = (False, "Failure")
        mock_service2.name = "MockedEmailService2"

        # Instancia de EmailFailover con dos servicios que fallan
        failover = EmailFailover(services=[mock_service1, mock_service2])

        message = self.get_message()
        result = failover.send_email(message)

        assert not result
        mock_service1.send_email.assert_called_once_with(message)
        mock_service2.send_email.assert_called_once_with(message)


class TestEmailFailoverWithState:
    def get_message(self):
        return EmailMessage(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body",
            from_email="from email",
        )

    def test_send_email_success_on_first_try(self):
        mock_service = Mock(spec=EmailService)
        mock_service.send_email.return_value = (True, "Success")
        mock_service.name = "MockedEmailService"

        failover = EmailFailoverWithState(services=[mock_service])

        message = self.get_message()
        result = failover.send_email(message)

        assert result
        mock_service.send_email.assert_called_once_with(message)

    def test_send_email_all_fail_finish_after_max_retries_reached(self):
        mock_service1 = Mock(spec=EmailService)
        mock_service1.send_email.return_value = (False, "Success")
        mock_service1.name = "MockedEmailService"

        # Mock del segundo servicio que tiene éxito
        mock_service2 = Mock(spec=EmailService)
        mock_service2.send_email.return_value = (False, "Success")
        mock_service2.name = "MockedEmailService2"

        failover = EmailFailoverWithState(services=[mock_service1, mock_service2], max_retries=1)
        message = self.get_message()
        with pytest.raises(Exception):
            failover.send_email(message)

        mock_service1.send_email.assert_called_with(message)
        mock_service2.send_email.assert_called_with(message)
