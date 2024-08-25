import time

from loguru import logger

from email_throttle.core.abstract.backoff import Backoff
from email_throttle.core.abstract.middleware import Middleware


class ExponentialBackoff(Backoff):
    def __init__(self, base=1, factor=2, max_delay=60):
        self.base = base
        self.factor = factor
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> int:
        delay = min(self.base * (self.factor**attempt), self.max_delay)
        return delay


class ConstantBackoff(Backoff):
    def __init__(self, seconds=10):
        self.seconds = seconds

    def get_delay(self, attempt) -> int:
        return self.seconds


class Retry(Middleware):
    def __init__(self, retries: int = 3, backoff: Backoff = None):
        self.retries = retries
        self.backoff = backoff or ExponentialBackoff()
        self.attempt = 0

    def allow_request(self) -> bool:
        return self.attempt < self.retries

    def call(self, func):
        while self.allow_request():
            try:
                logger.info(f"Trying Attempt {self.attempt + 1}...")
                result = func()
                self.attempt = 0
                return result
            except Exception as e:
                self.attempt += 1
                if not self.allow_request():
                    logger.error(f"Failed attempt because max retries reached ({self.attempt} retries)")
                    self.attempt = 0
                    raise e
                delay = self.backoff.get_delay(self.attempt)
                logger.warning(f"Attempt {self.attempt + 1} failed. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
