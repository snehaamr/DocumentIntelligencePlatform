from docx import Document



class DOCXExtractor:


    def extract(self, file_path):

        document = Document(file_path)

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
        ]

        return "\n".join(paragraphs)