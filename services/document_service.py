from repositories.document_repository import DocumentRepository

from services.extraction_service import ExtractionService
from services.ai_document_service import AIDocumentService


class DocumentService:

    def __init__(self):

        self.repository = DocumentRepository()

        self.extraction_service = ExtractionService()

        self.ai_document_service = AIDocumentService()

    def upload_document(
        self,
        uploaded_file,
    ):

        document = self.repository.create(
            original_filename=uploaded_file.name,
            uploaded_file=uploaded_file,
            mime_type=uploaded_file.content_type,
            file_size=uploaded_file.size,
        )

        return document

    def process_document(
        self,
        document_id,
    ):

        document = self.repository.get_by_id(
            document_id
        )

        document.status = "PROCESSING"

        self.repository.save(document)

        try:

            extracted_text = (
                self.extraction_service.extract(
                    document.uploaded_file.path
                )
            )

            ai_result = (
                self.ai_document_service.analyze(
                    extracted_text
                )
            )

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

            self.repository.save(
                document
            )

            return document

        except Exception as e:

            document.status = "FAILED"

            document.error_message = str(e)

            self.repository.save(
                document
            )

            raise e

    def get_document(
        self,
        document_id,
    ):

        return self.repository.get_by_id(
            document_id
        )

    def list_documents(
        self,
        status=None,
        document_type=None,
        search=None,
        min_confidence=None,
    ):

        return self.repository.filter_documents(
            status=status,
            document_type=document_type,
            search=search,
            min_confidence=min_confidence,
        )