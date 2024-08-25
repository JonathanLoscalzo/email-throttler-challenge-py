from abc import ABC, abstractmethod


class Backoff(ABC):
    @abstractmethod
    def get_delay(self, attempt: int) -> int:
        pass
