from unittest.mock import MagicMock, patch

from email_throttle.api.endpoints.emails.dtos import EmailDto
from email_throttle.cli.consumer import (
    consumer_command,
    create_services,
    factory_handler_message,
    send_emails,
)


class TestConsumer:
    @patch("email_throttle.cli.consumer.create_consumer")
    @patch("email_throttle.cli.consumer.create_services_from_config")
    def test_create_services(self, mock_create_services_from_config, mock_create_consumer):
        mock_service = MagicMock()
        # mock_failover = MagicMock()
        mock_consumer = MagicMock()

        mock_create_services_from_config.return_value = [mock_service]
        mock_create_consumer.return_value = mock_consumer

        result = create_services()

        mock_create_services_from_config.assert_called_once()
        mock_create_consumer.assert_called_once()
        assert result == mock_consumer

    def test_factory_handler_message(self):
        mock_failover = MagicMock()
        mock_msg = EmailDto(subject="test", body="test", to=["<EMAIL>"], from_email="<EMAIL>")
        handler = factory_handler_message(mock_failover)

        with patch("email_throttle.cli.consumer.logger") as mock_logger:
            handler(mock_msg)

            mock_failover.send_email.assert_called_once()
            mock_logger.info.assert_called()

    def test_send_emails_success(self):
        mock_failover = MagicMock()
        mock_failover.send_email.return_value = True
        mock_message = MagicMock()

        result = send_emails(mock_failover, mock_message)

        assert result is None  # Function returns nothing on success
        mock_failover.send_email.assert_called_once_with(mock_message)

    def test_send_emails_failure(self):
        mock_failover = MagicMock()
        mock_failover.send_email.return_value = False
        mock_message = MagicMock()

        result = send_emails(mock_failover, mock_message)

        assert result is False
        mock_failover.send_email.assert_called_once_with(mock_message)

    @patch("email_throttle.cli.consumer.create_services")
    @patch("email_throttle.cli.consumer.logger")
    def test_consumer_command(self, mock_logger, mock_create_services):
        mock_consumer = MagicMock()
        mock_create_services.return_value = mock_consumer

        consumer_command(MagicMock())

        mock_create_services.assert_called_once()
        mock_consumer.start_consuming.assert_called_once()

        # Test that it handles KeyboardInterrupt
        mock_consumer.start_consuming.side_effect = KeyboardInterrupt
        consumer_command(MagicMock())
        mock_logger.info.assert_called_with("Stopping consumer")
