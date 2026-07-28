from docx import Document

from services.extractors.base import DocumentExtractor


class DOCXExtractor(DocumentExtractor):

    def extract(self, file_path: str) -> str:

        document = Document(file_path)

        paragraphs = []

        for paragraph in document.paragraphs:
            paragraphs.append(
                paragraph.text
            )

        return "\n".join(paragraphs)