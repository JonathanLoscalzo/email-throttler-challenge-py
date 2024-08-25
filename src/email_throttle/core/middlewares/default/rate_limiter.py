from datetime import datetime, timedelta
from typing import Any, Callable

from loguru import logger

from email_throttle.core.abstract.middleware import Middleware


class RateLimiter(Middleware):
    def __init__(self, max_requests: int, per_second: int):
        self.max_requests = max_requests
        self.per_second = per_second
        self.requests = []

    def allow_request(self):
        now = datetime.now()
        # Clean up old requests
        self.requests = [req_time for req_time in self.requests if req_time > now - timedelta(seconds=self.per_second)]

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def call(self, func: Callable) -> Any:
        if not self.allow_request():
            logger.error(f"Rate limited reached, max requests of {self.max_requests} on last {self.per_second} seconds")
            raise Exception("Too many requests")

        # current middleware is not checking if the request failed
        # in case of failure, exception must be raised inside the function
        return func()
