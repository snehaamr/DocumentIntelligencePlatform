import os

from services.extractors.pdf_extractor import PDFExtractor
from services.extractors.docx_extractor import DOCXExtractor
from services.extractors.text_extractor import TextExtractor



class ExtractorFactory:


    @staticmethod
    def get_extractor(file_path):

        extension = Path(file_path).suffix.lower()


        if extension == ".pdf":
            return PDFExtractor()


        if extension == ".docx":
            return DOCXExtractor()


        if extension == ".txt":
            return TextExtractor()


        raise Exception(
            f"Unsupported file type {extension}"
        )