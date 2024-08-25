from datetime import datetime

from loguru import logger

from email_throttle.core.abstract.middleware import Middleware


class CircuitBreaker(Middleware):
    def __init__(self, failure_threshold: int, reset_timeout: int):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def allow_request(self) -> bool:
        """the method allow_request returns if the request can be made,
        depending on the state of the circuit breaker or
        if the timeout has expired.
        """
        if self.state == "OPEN":
            timeout = (datetime.now() - self.last_failure_time).seconds
            # if timeout between last failure surpased the reset timeout
            if timeout >= self.reset_timeout:
                self.state = "HALF-OPEN"
                return True
            return False  # continues open
        return True  # is closed

    def reset(self):
        """The reset method should be called when the circuit is in a
        half-open state and the wrapped function resumes operation."""

        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        """The record_failure method should be called when a failure occurs"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        # if the failure count is greater than or equal to the threshold,
        # open the circuit
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_failure_time = datetime.now()

    def call(self, func):
        if not self.allow_request():
            msg = f"Circuit is {self.state}, expect the timeout was expired"
            logger.error(msg)
            raise Exception(msg)
        try:
            result = func()
            if self.state == "HALF-OPEN":
                logger.info("Reopen CircuitBreaker")
                self.reset()
            return result
        except Exception as e:
            logger.error(f"{e}")
            self.record_failure()
            raise e
