from abc import ABC, abstractmethod


class AbstractAzureService(ABC):
    @property
    @abstractmethod
    def client(self):
        ...

    @client.setter
    @abstractmethod
    def client(self):
        ...
