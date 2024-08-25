import pytest

from email_throttle.core.middlewares.default.retry import (ConstantBackoff,
                                                           ExponentialBackoff,
                                                           Retry)


class TestRetry:

    def test_retry_exceeds_attempts(self):
        attempt_counter = 0

        def always_fail():
            nonlocal attempt_counter
            attempt_counter += 1
            raise Exception("Failure")

        retry = Retry(retries=3, backoff=ConstantBackoff(0.01))

        with pytest.raises(Exception, match="Failure"):
            retry.call(always_fail)

        assert attempt_counter == 3

    def test_retry_succeed_on_second_attempt(self):
        attempt_counter = 0

        def fail_once():
            nonlocal attempt_counter
            attempt_counter += 1
            if attempt_counter < 2:
                raise Exception("Failure")
            return "Success"

        retry = Retry(retries=3, backoff=ConstantBackoff(0.01))
        result = retry.call(fail_once)

        assert result == "Success"
        assert attempt_counter == 2

    def test_retry_with_exponential_backoff(self):
        attempt_counter = 0

        def always_fail():
            nonlocal attempt_counter
            attempt_counter += 1
            raise Exception("Failure")

        retry = Retry(
            retries=3,
            backoff=ExponentialBackoff(
                base=0.1,
                factor=1.5,
                max_delay=0.5,
            ),
        )

        with pytest.raises(Exception, match="Failure"):
            retry.call(always_fail)

        assert attempt_counter == 3

    def test_retry_resets_after_success(self):
        attempt_counter = 0

        def succeed_after_three():
            nonlocal attempt_counter
            attempt_counter += 1
            if attempt_counter < 3:
                raise Exception("Failure")
            return "Success"

        retry = Retry(retries=5, backoff=ConstantBackoff(0.01))
        result = retry.call(succeed_after_three)
        assert result == "Success"

        # Ensure retry has reset its internal state
        result = retry.call(lambda: "Immediate Success")
        assert result == "Immediate Success"
