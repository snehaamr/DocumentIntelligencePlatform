from pypdf import PdfReader

from services.extractors.base import DocumentExtractor


class PDFExtractor(DocumentExtractor):

    def extract(self, file_path: str) -> str:

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        return text