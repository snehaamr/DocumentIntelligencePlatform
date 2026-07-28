from abc import ABC, abstractmethod


class AIProvider(ABC):

    @abstractmethod
    def analyze(self, text: str):
        pass