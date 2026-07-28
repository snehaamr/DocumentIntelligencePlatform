import os

from services.extractors.pdf_extractor import PDFExtractor
from services.extractors.docx_extractor import DOCXExtractor
from services.extractors.text_extractor import TextExtractor



class ExtractorFactory:


    @staticmethod
    def get_extractor(file_path):

        extension = (
            os.path.splitext(file_path)[1]
            .lower()
        )


        if extension == ".pdf":
            return PDFExtractor()


        if extension == ".docx":
            return DOCXExtractor()


        if extension in [".txt", ".text"]:
            return TextExtractor()


        raise ValueError(
            f"Unsupported file type: {extension}"
        )