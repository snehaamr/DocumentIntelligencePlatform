from repositories.document_repository import DocumentRepository

from services.extraction_service import ExtractionService
from services.ai_document_service import AIDocumentService


class DocumentService:

    def __init__(self):

        self.repository = DocumentRepository()

        self.extraction_service = ExtractionService()

        self.ai_document_service = AIDocumentService()


    def upload_document(self, uploaded_file):

        document = self.repository.create(
            original_filename=uploaded_file.name,
            uploaded_file=uploaded_file,
            mime_type=uploaded_file.content_type,
            file_size=uploaded_file.size,
        )

        return document


    def process_document(self, document_id):

        document = self.repository.get_by_id(
            document_id
        )


        # 1. Update status
        document.status = "PROCESSING"
        document.save()


        try:

            # 2. Extract text
            extracted_text = (
                self.extraction_service.extract(
                    document.uploaded_file.path
                )
            )


            # 3. AI Analysis
            ai_result = (
                self.ai_document_service.analyze(
                    extracted_text
                )
            )


            # 4. Persist results

            document.extracted_text = extracted_text

            document.ai_response = (
                ai_result.model_dump()
            )

            document.document_type = (
                ai_result.document_type
            )

            document.summary = (
                ai_result.summary
            )

            document.confidence_score = (
                ai_result.confidence_score
            )

            document.status = "PROCESSED"

            document.save()


            return document


        except Exception as e:

            document.status = "FAILED"

            document.error_message = str(e)

            document.save()

            raise e