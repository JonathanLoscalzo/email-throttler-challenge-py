from abc import ABC, abstractmethod
from typing import Any, Callable


class Middleware(ABC):
    @abstractmethod
    def allow_request(self) -> bool:
        pass

    @abstractmethod
    def call(self, func: Callable) -> Any:
        pass
