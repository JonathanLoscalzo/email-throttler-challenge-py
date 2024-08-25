from datetime import datetime
from unittest.mock import MagicMock

import pytest
# from email_sender.core.failover import EmailFailover
from freezegun import freeze_time

from email_throttle.core.abstract.sender import EmailSender
from email_throttle.core.middlewares.default.circuit_breaker import \
    CircuitBreaker


class TestCircuitBreaker:

    def test_when_failure_threshold_is_exceeded__should_circuit_opened(
        self,
    ):
        mock_sender = MagicMock(EmailSender)
        middleware = CircuitBreaker(failure_threshold=3, reset_timeout=100)

        # simulate failures
        mock_sender.send_email.side_effect = Exception("ERRROR")

        # first 3 calls should not open the circuit, but should count the failures
        for _ in range(3):
            try:
                middleware.call(lambda: mock_sender.send_email())
            except Exception:
                pass

        # the 4th call should raise an exception
        with pytest.raises(Exception):
            middleware.call(lambda: mock_sender.send_email())

        assert middleware.state == "OPEN"
        assert mock_sender.send_email.call_count == 3

    def test_when_cb_is_closed_and_timeout_has_exceeded__should_circuit_be_half_open(
        self,
    ):
        mock_sender = MagicMock(EmailSender)
        middleware = CircuitBreaker(failure_threshold=3, reset_timeout=60)

        middleware.failure_count = 3
        middleware.state = "OPEN"
        middleware.last_failure_time = datetime(2019, 3, 18, 20, 00)
        mock_sender.send_email.return_value = "SUCCESS"

        with freeze_time("2019-03-18 20:00:00"):
            res = middleware.allow_request()
            assert res is False
            assert middleware.state == "OPEN"

        # if timeout has exceeded, then the circuit should be half open
        with freeze_time("2019-03-18 20:02:00"):
            res = middleware.allow_request()
            assert res is True
            assert middleware.state == "HALF-OPEN"

        middleware.call(lambda: mock_sender.send_email())

        assert middleware.state == "CLOSED"
        mock_sender.send_email.assert_called_once()
