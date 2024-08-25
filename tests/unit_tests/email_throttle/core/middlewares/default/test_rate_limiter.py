from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from email_throttle.core.abstract.sender import EmailSender
from email_throttle.core.middlewares.default.rate_limiter import RateLimiter


class TestRateLimiter:

    def test_when_max_request_is_exceeded__should_raise_exception(self):
        mock_sender = MagicMock(EmailSender)
        rate_limiter = RateLimiter(max_requests=2, per_second=100)

        for _ in range(2):
            rate_limiter.call(lambda: mock_sender.send_email())

        with pytest.raises(Exception):
            rate_limiter.call(lambda: mock_sender.send_email())

        mock_sender.send_email.assert_called()
        assert mock_sender.send_email.call_count == 2

    def test_when_timeout_has_exceeded__should_start_working_again(self):
        mock_sender = MagicMock(EmailSender)
        rate_limiter = RateLimiter(max_requests=2, per_second=60)

        for dt in ["2019-03-18 20:00:00", "2019-03-18 20:00:30"]:
            with freeze_time(dt):
                rate_limiter.call(lambda: mock_sender.send_email())

        mock_sender.send_email.assert_called()
        assert mock_sender.send_email.call_count == 2

        # for these times, the rate limiter should be limited
        for dt in ["2019-03-18 20:00:45", "2019-03-18 20:00:59"]:
            with freeze_time(dt):
                assert not rate_limiter.allow_request()

        # after the timeout, the rate limiter should be unlimited again
        with freeze_time("2019-03-18 20:01:00"):
            assert rate_limiter.allow_request()
