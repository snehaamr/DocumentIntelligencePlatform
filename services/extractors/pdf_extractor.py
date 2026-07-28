import PyPDF2



class PDFExtractor:


    def extract(self, file_path):

        text = ""

        with open(
            file_path,
            "rb"
        ) as file:

            reader = PyPDF2.PdfReader(file)

            for page in reader.pages:
                text += (
                    page.extract_text()
                    or ""
                )


        return text