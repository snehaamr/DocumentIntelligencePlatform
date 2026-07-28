from abc import ABC, abstractmethod


class DocumentExtractor(ABC):

    @abstractmethod
    def extract(self, file_path: str) -> str:
        pass