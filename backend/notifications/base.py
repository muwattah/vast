from abc import ABC, abstractmethod

class NotificationProvider(ABC):
    name: str = "base"
    @abstractmethod
    def send(self, title: str, body: str, **kwargs) -> bool:
        pass
    def available(self) -> bool:
        return False
