from unittest.mock import MagicMock, patch

from email_throttle.cli.simulator import (
    command_simulate,
    create_services,
    generate_emails,
    parse_args,
    send_emails,
)
from email_throttle.core.entity import EmailMessage
from email_throttle.core.middlewares.default.circuit_breaker import CircuitBreaker
from email_throttle.core.middlewares.default.rate_limiter import RateLimiter
from email_throttle.core.middlewares.default.retry import Retry
from email_throttle.vendors.noop import NoOpEmailSender


class TestSimulator:
    def test_parse_args(self):
        args = MagicMock()
        args.vendor_count = 2
        args.vendors = ["vendor1", "vendor2"]
        args.middlewares = ["cb,rl", "retry"]
        args.circuit_breakers = ["2,10", ""]
        args.rate_limiters = ["3,20", ""]
        args.retries = ["", "5"]

        expected_output = [
            {
                "name": "vendor1",
                "middlewares": ["cb", "rl"],
                "circuit_breaker": {"threshold": 2, "reset_timeout": 10},
                "rate_limiter": {"max_attempts": 3, "per_seconds": 20},
            },
            {
                "name": "vendor2",
                "middlewares": ["retry"],
                "retry": {"retries": 5},
            },
        ]

        assert parse_args(args) == expected_output

    def test_create_services(self):
        vendors_config = [
            {
                "name": "vendor1",
                "middlewares": ["cb", "rl"],
                "circuit_breaker": {"threshold": 2, "reset_timeout": 10},
                "rate_limiter": {"max_attempts": 3, "per_seconds": 20},
            },
            {
                "name": "vendor2",
                "middlewares": ["retry"],
                "retry": {"retries": 5},
            },
        ]

        services = create_services(vendors_config)
        assert len(services) == 2
        assert isinstance(services[0].service, NoOpEmailSender)
        assert isinstance(services[0].middlewares[0], CircuitBreaker)
        assert isinstance(services[0].middlewares[1], RateLimiter)
        assert isinstance(services[1].middlewares[0], Retry)

    def test_generate_emails(self):
        emails = list(generate_emails(2))
        assert len(emails) == 2
        assert isinstance(emails[0], EmailMessage)
        assert emails[0].subject == "Test Email 0"
        assert emails[1].subject == "Test Email 1"

    @patch("email_throttle.cli.simulator.EmailFailoverWithState")
    @patch("email_throttle.cli.simulator.EmailFailover")
    def test_send_emails(self, mock_failover, mock_failover_with_state):
        services = [MagicMock(), MagicMock()]
        mock_failover.return_value.send_email.return_value = True
        mock_failover_with_state.return_value.send_email.return_value = True

        errors = send_emails(services, 2, with_state_failover=False)
        assert len(errors) == 0

        errors = send_emails(services, 2, with_state_failover=True)
        assert len(errors) == 0

    @patch("email_throttle.cli.simulator.logger")
    @patch("email_throttle.cli.simulator.send_emails")
    @patch("email_throttle.cli.simulator.create_services")
    def test_command_simulate(self, mock_create_services, mock_send_emails, mock_logger):
        args = MagicMock()
        args.vendors = ["vendor1", "vendor2"]
        args.vendor_count = 2
        args.middlewares = ["cb,rl", "retry"]
        args.circuit_breakers = ["2,3", "0,0"]
        args.retry = ["3", "3"]
        args.rate_limiters = ["3,10", "2"]
        args.email_count = 100
        args.with_state_failover = False
        mock_send_emails.return_value = []

        command_simulate(args)

        mock_create_services.assert_called_once()
        mock_send_emails.assert_called_once()
        mock_logger.info.assert_called()
