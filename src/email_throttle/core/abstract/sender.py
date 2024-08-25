from abc import ABC, abstractmethod
from typing import Any

from email_throttle.core.entity import EmailMessage


class EmailSender(ABC):

    def __init__(self, name):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def send_email(self, message: "EmailMessage") -> Any:
        pass
